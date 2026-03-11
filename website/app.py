import os
import logging
import requests
from flask import Flask, render_template, redirect, request, session, url_for, jsonify, abort
from dotenv import load_dotenv
import mysql.connector
from functools import wraps
from datetime import datetime

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
secret = os.getenv("FLASK_SECRET")
if not secret:
    raise RuntimeError("FLASK_SECRET environment variable must be set before starting the server.")
app.secret_key = secret

# Inject discord_client_id into every template context
@app.context_processor
def inject_globals():
    return {"discord_client_id": DISCORD_CLIENT_ID or ""}

# ─── Discord OAuth2 Config ────────────────────────────────────────────────────
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
DISCORD_API = "https://discord.com/api/v10"

BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "920797181034778655"))

OAUTH_SCOPES = "identify guilds"
AUTHORIZE_URL = (
    f"https://discord.com/api/oauth2/authorize"
    f"?client_id={DISCORD_CLIENT_ID}"
    f"&redirect_uri={DISCORD_REDIRECT_URI}"
    f"&response_type=code"
    f"&scope={OAUTH_SCOPES.replace(' ', '%20')}"
)

# ─── DB helper ────────────────────────────────────────────────────────────────

def get_db():
    return mysql.connector.connect(
        host=os.getenv("db_host"),
        port=3306,
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        database=os.getenv("db_name"),
    )


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if int(session["user"]["id"]) != BOT_OWNER_ID:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_user_guilds_with_admin():
    """Return guilds where the logged-in user has ADMINISTRATOR (0x8)."""
    guilds = session.get("guilds", [])
    return [g for g in guilds if (int(g.get("permissions", 0)) & 0x8) == 0x8]


def get_guild_icon_url(guild):
    if guild.get("icon"):
        return f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png"
    return None


# ─── OAuth2 Routes ────────────────────────────────────────────────────────────

@app.route("/login")
def login():
    return redirect(AUTHORIZE_URL)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization failed.", 400

    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_resp = requests.post(f"{DISCORD_API}/oauth2/token", data=token_data, headers=headers)
    token_resp.raise_for_status()
    tokens = token_resp.json()
    access_token = tokens["access_token"]

    auth_headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(f"{DISCORD_API}/users/@me", headers=auth_headers)
    user_resp.raise_for_status()
    session["user"] = user_resp.json()

    guilds_resp = requests.get(f"{DISCORD_API}/users/@me/guilds", headers=auth_headers)
    guilds_resp.raise_for_status()
    session["guilds"] = guilds_resp.json()

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ─── Public Pages ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)


@app.route("/commands")
def commands_page():
    user = session.get("user")
    return render_template("commands.html", user=user)


# ─── Server Dashboard ─────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    admin_guilds = get_user_guilds_with_admin()
    for g in admin_guilds:
        g["icon_url"] = get_guild_icon_url(g)
    user = session["user"]
    return render_template("dashboard.html", user=user, guilds=admin_guilds)


@app.route("/dashboard/<guild_id>")
@login_required
def guild_settings(guild_id):
    admin_guilds = get_user_guilds_with_admin()
    guild = next((g for g in admin_guilds if g["id"] == guild_id), None)
    if not guild:
        abort(403)

    guild["icon_url"] = get_guild_icon_url(guild)
    settings = {}
    premium = False

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM guild_settings WHERE guild_id = %s", (guild_id,)
        )
        row = cursor.fetchone()
        if row:
            settings = row

        cursor.execute(
            "SELECT is_premium, tier FROM premium_status WHERE entity_id = %s",
            (int(guild_id),),
        )
        prow = cursor.fetchone()
        if prow and prow["is_premium"]:
            premium = True
            settings["tier"] = prow["tier"]

        cursor.close()
        db.close()
    except Exception as e:
        logger.error("DB error loading guild settings for %s: %s", guild_id, e)

    return render_template(
        "guild_settings.html",
        user=session["user"],
        guild=guild,
        settings=settings,
        premium=premium,
    )


@app.route("/dashboard/<guild_id>/save", methods=["POST"])
@login_required
def save_guild_settings(guild_id):
    admin_guilds = get_user_guilds_with_admin()
    if not any(g["id"] == guild_id for g in admin_guilds):
        abort(403)

    data = request.get_json()
    allowed_keys = {
        "schedule_channel_id",
        "mod_log_channel_id",
        "mute_role_id",
        "welcome_channel_id",
        "welcome_message",
        "language",
        "prefix",
    }
    updates = {k: v for k, v in data.items() if k in allowed_keys}

    try:
        db = get_db()
        cursor = db.cursor()
        if updates:
            # Column names are validated against allowed_keys above; safe to interpolate.
            cols = ", ".join(updates.keys())
            placeholders = ", ".join(["%s"] * len(updates))
            set_clause = ", ".join(f"{k} = VALUES({k})" for k in updates)
            sql = (
                f"INSERT INTO guild_settings (guild_id, {cols}) VALUES (%s, {placeholders}) "
                f"ON DUPLICATE KEY UPDATE {set_clause}"
            )
            cursor.execute(sql, [guild_id] + list(updates.values()))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        logger.error("Error saving guild settings for %s: %s", guild_id, e)
        return jsonify({"success": False, "error": "Failed to save settings. Please try again."}), 500


# ─── Owner Panel ──────────────────────────────────────────────────────────────

@app.route("/owner")
@owner_required
def owner_panel():
    servers = []
    stats = {"server_count": 0, "premium_count": 0}

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT ps.entity_id, ps.is_premium, ps.tier,
                   gs.schedule_channel_id, gs.mod_log_channel_id
            FROM premium_status ps
            LEFT JOIN guild_settings gs ON gs.guild_id = ps.entity_id
            ORDER BY ps.is_premium DESC
            """
        )
        servers = cursor.fetchall()
        stats["premium_count"] = sum(1 for s in servers if s["is_premium"])
        stats["server_count"] = len(servers)

        cursor.close()
        db.close()
    except Exception as e:
        logger.error("Owner panel DB error: %s", e)

    return render_template(
        "owner.html",
        user=session["user"],
        servers=servers,
        stats=stats,
    )


@app.route("/owner/premium", methods=["POST"])
@owner_required
def owner_toggle_premium():
    data = request.get_json()
    guild_id = data.get("guild_id")
    action = data.get("action")  # "grant" or "revoke"
    tier = data.get("tier", "referee")

    try:
        db = get_db()
        cursor = db.cursor()
        if action == "grant":
            cursor.execute(
                """
                INSERT INTO premium_status (entity_id, is_premium, tier)
                VALUES (%s, 1, %s)
                ON DUPLICATE KEY UPDATE is_premium = 1, tier = %s
                """,
                (int(guild_id), tier, tier),
            )
        elif action == "revoke":
            cursor.execute(
                "UPDATE premium_status SET is_premium = 0 WHERE entity_id = %s",
                (int(guild_id),),
            )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"success": True})
    except Exception as e:
        logger.error("Owner premium toggle error for guild %s: %s", guild_id, e)
        return jsonify({"success": False, "error": "Failed to update premium status. Please try again."}), 500
@owner_required
def owner_stats():
    """JSON endpoint for live stat refresh."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM guild_settings")
        row = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM premium_status WHERE is_premium = 1"
        )
        prow = cursor.fetchone()
        cursor.close()
        db.close()
        return jsonify(
            {
                "server_count": row["total"] if row else 0,
                "premium_count": prow["cnt"] if prow else 0,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        logger.error("Owner stats endpoint error: %s", e)
        return jsonify({"error": "Failed to load stats."}), 500


# ─── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You don't have permission to view this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=int(os.getenv("PORT", "5000")))
