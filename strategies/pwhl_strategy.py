import discord
from discord import app_commands
from discord.ext import commands
import config
from datetime import datetime, timedelta
import requests
import pytz
import traceback
import json
import asyncio
from thefuzz import fuzz
import strategies.base_strategy as base_strategy

# Toggleable Debug Mode: Set to True to enable console logging, False to disable
DEBUG_MODE = True

PWHL_TEAMS = {
    "BOS": ("Boston Fleet", config.boston_fleet_emoji if hasattr(config, 'boston_fleet_emoji') else "⚓"),
    "MIN": ("Minnesota Frost", config.minnesota_frost_emoji if hasattr(config, 'minnesota_frost_emoji') else "❄️"),
    "MTL": ("Montréal Victoire", config.montreal_victoire_emoji if hasattr(config, 'montreal_victoire_emoji') else "⚜️"),
    "NY":  ("New York Sirens", config.new_york_sirens_emoji if hasattr(config, 'new_york_sirens_emoji') else "🚨"),
    "OTT": ("Ottawa Charge", config.ottawa_charge_emoji if hasattr(config, 'ottawa_charge_emoji') else "⚡"),
    "TOR": ("Toronto Sceptres", config.toronto_sceptres_emoji if hasattr(config, 'toronto_sceptres_emoji') else "👑"),
    "DET": ("PWHL Detroit", "🏒"),
    "HAM": ("PWHL Hamilton", "🏒"),
    "LV":  ("PWHL Las Vegas", "🎲"),
    "SJ":  ("PWHL San Jose", "🦈"),
    "SEA": ("Seattle Torrent", "🌊"),
    "VAN": ("Vancouver Goldeneyes", "🦅"),
}

PWHL_API_KEY = "446521baf8c38984"
PWHL_CLIENT_CODE = "pwhl"
CURRENT_SEASON_ID = 5

async def pwhl_team_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = []
    for abbr, (name, emoji) in PWHL_TEAMS.items():
        if current.lower() in name.lower() or current.lower() in abbr.lower():
            choices.append(app_commands.Choice(name=f"{emoji} {name} ({abbr})", value=abbr))
    return choices[:25]


class PWHLGameStatsView(discord.ui.View):
    def __init__(self, gc_data, original_embed):
        super().__init__(timeout=300)
        self.gc_data = gc_data
        self.original_embed = original_embed
        
        self.home_lineup = self.gc_data.get('home_team_lineup', {})
        self.away_lineup = self.gc_data.get('visitor_team_lineup', {})
        self.home_info = self.gc_data.get('home', {})
        self.away_info = self.gc_data.get('visitor', {})

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        is_away = (team_type == 'away')
        team_data = self.away_lineup if is_away else self.home_lineup
        team_info = self.away_info if is_away else self.home_info
        team_name = team_info.get('name') or team_info.get('city') or 'Team'
        
        embed = discord.Embed(title=f"{team_name} Game Roster", color=self.original_embed.color)
        
        try:
            players = team_data.get('players', [])
            skater_lines = []
            for p in players:
                num = p.get('jersey_number', '00')
                fname = p.get('first_name', '')
                lname = p.get('last_name', '')
                pos = p.get('position_str', 'F')
                g = p.get('goals', 0)
                a = p.get('assists', 0)
                skater_lines.append(f"#{num} **{fname} {lname}** ({pos}) - {g}G, {a}A")
            
            formatted_skaters = "\n".join(skater_lines[:20])
            embed.add_field(name="Active Skaters", value=formatted_skaters[:1024] if formatted_skaters else "N/A", inline=False)
            
            goalies = team_data.get('goalies', [])
            goalie_lines = []
            for g in goalies:
                num = g.get('jersey_number', '00')
                fname = g.get('first_name', '')
                lname = g.get('last_name', '')
                saves = g.get('saves', 0)
                ga = g.get('goals_against', 0)
                time_str = g.get('time', '0:00')
                goalie_lines.append(f"#{num} **{fname} {lname}** - {saves} SV / {ga} GA ({time_str})")
            
            formatted_goalies = "\n".join(goalie_lines)
            embed.add_field(name="Goalies", value=formatted_goalies[:1024] if formatted_goalies else "N/A", inline=False)
            
        except Exception: 
            embed.description = "Stats temporarily unavailable."
        return embed

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.primary)
    async def summary_button(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.edit_message(embed=self.original_embed)

    @discord.ui.button(label="Away Roster", style=discord.ButtonStyle.secondary)
    async def away_roster_button(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('away'))

    @discord.ui.button(label="Home Roster", style=discord.ButtonStyle.secondary)
    async def home_roster_button(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('home'))


class PWHL(commands.GroupCog, name="pwhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def fetch_ht_api(self, feed: str, **kwargs) -> dict:
        base_url = "https://lscluster.hockeytech.com/feed/index.php"
        params = {
            "key": PWHL_API_KEY,
            "client_code": PWHL_CLIENT_CODE,
            "feed": feed,
            "lang": "en"
        }
        params.update(kwargs)
        
        req = requests.Request('GET', base_url, params=params)
        prepared = req.prepare()
        if DEBUG_MODE:
            print(f"[PWHL API Request]: {prepared.url}")

        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code != 200 or not response.text.strip():
                if DEBUG_MODE:
                    print(f"[PWHL API Error]: Status Code {response.status_code}, Body: {response.text[:200]}")
                return {}
            
            clean_text = response.text.strip()
            if clean_text.startswith("(") and clean_text.endswith(")"):
                clean_text = clean_text[1:-1]
            
            return json.loads(clean_text)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[PWHL API Exception]: {e}")
            return {}

    @staticmethod
    def get_team_emoji(abbrev: str) -> str:
        return PWHL_TEAMS.get(abbrev.upper(), ("", "🏒"))[1]

    @staticmethod
    def get_team_name(abbrev: str) -> str:
        return PWHL_TEAMS.get(abbrev.upper(), (abbrev, ""))[0]

    # --- DISCORD COMMAND INTERFACES ---

    @app_commands.command(name="today", description="Get today's PWHL schedule and scores")
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
    async def today_cmd(self, interaction: discord.Interaction, date: str = None):
        await self.get_today_games(interaction, date_str=date)

    @app_commands.command(name="yesterday", description="Get yesterday's PWHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)

    @app_commands.command(name="standings", description="Get the PWHL standings")
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
    async def standings_cmd(self, interaction: discord.Interaction, date: str = None):
        await self.get_standings(interaction, date_str=date)

    @app_commands.command(name="schedule", description="Get the schedule for a PWHL team")
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list", date="Override date/month context if needed")
    @app_commands.autocomplete(abbreviation=pwhl_team_autocomplete)
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str, date: str = None):
        await self.get_schedule(interaction, abbreviation, date_str=date)

    @app_commands.command(name="game", description="Check live or past game stats for a PWHL team")
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list", date="Override date for testing (YYYY-MM-DD)")
    @app_commands.autocomplete(abbreviation=pwhl_team_autocomplete)
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str, date: str = None):
        await self.get_game_info(interaction, abbreviation, date_str=date)

    @app_commands.command(name="player", description="Gets the complete career overview of a PWHL player")
    async def player_cmd(self, interaction: discord.Interaction, name: str):
        await self.get_player_info(interaction, name)

    @app_commands.command(name="teams", description="Get all available PWHL team codes and abbreviations")
    async def teams_cmd(self, interaction: discord.Interaction):
        await self.get_all_teams(interaction)

    # --- SHARED STRATEGY ARCHITECTURE LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "pwhl today")
        try:
            embed = await self.build_schedule_embed(date_str=date_str)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send(f"Error processing schedule request: {e}")

    async def get_yesterday_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "pwhl yesterday")
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            y_date = (datetime.now(hawaii_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
            embed = await self.build_schedule_embed(date_str=y_date)
            await interaction.followup.send(embed=embed)
        except Exception:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send("Error processing retrospective scores.")

    async def get_standings(self, interaction: discord.Interaction, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "pwhl standings")
        try:
            params = {
                "feed": "modulekit", 
                "view": "statviewtype", 
                "stat": "conference", 
                "type": "standings", 
                "season_id": CURRENT_SEASON_ID
            }
            if date_str:
                params["date"] = date_str

            data = self.fetch_ht_api(**params)
            site_kit = data.get("SiteKit", {})
            standings_data = site_kit.get("statviewtype") or site_kit.get("Statviewtype") or []
            
            embed = discord.Embed(title="PWHL Standings", color=config.color)
            embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")
            
            lines = []
            for record in standings_data:
                if not isinstance(record, dict) or "team_code" not in record:
                    continue
                team_code = record.get("team_code", "UNK")
                name = record.get("team_name") or record.get("name", team_code)
                emoji = self.get_team_emoji(team_code)
                wins = record.get("wins", 0)
                losses = record.get("losses", 0)
                ot_losses = record.get("ot_losses", 0)
                points = record.get("points", 0)
                
                lines.append(f"{emoji} **{name}** ({wins}-{losses}-{ot_losses}) - **{points}** pts")

            embed.description = "\n".join(lines) if lines else "Standings data unavailable."
            embed.set_footer(text=config.footer)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send("Error processing standings.")

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl schedule {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            if abbrev not in PWHL_TEAMS:
                return await interaction.followup.send("Invalid team identifier. Try matching format via `/pwhl teams`.")

            team_data = self.fetch_ht_api(feed="modulekit", view="teamsbyseason", season_id=CURRENT_SEASON_ID)
            site_kit = team_data.get("SiteKit", {})
            raw_teams = site_kit.get("teamsbyseason") or site_kit.get("Teamsbyseason") or []
            
            team_id = None
            for t in raw_teams:
                code = (t.get("team_code") or t.get("code") or "").upper()
                if code == abbrev:
                    team_id = t.get("id") or t.get("team_id")
                    break
            
            if not team_id:
                return await interaction.followup.send("Could not map team abbreviation to LeagueStat ID.")

            data = self.fetch_ht_api(feed="statviewfeed", view="schedule", team=team_id, season=CURRENT_SEASON_ID, month=-1)
            
            games = []
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    sections = item.get("sections", [])
                    for section in sections:
                        rows = section.get("data", [])
                        for r in rows:
                            row_info = r.get("row", {})
                            if row_info:
                                games.append({
                                    "game_id": row_info.get("game_id"),
                                    "date": row_info.get("date_with_day"),
                                    "date_with_day": row_info.get("date_with_day"),
                                    "status": row_info.get("game_status"),
                                    "home_team_name": row_info.get("home_team_city"),
                                    "visiting_team_name": row_info.get("visiting_team_city"),
                                    "home_goal_count": row_info.get("home_goal_count", "0"),
                                    "visiting_goal_count": row_info.get("visiting_goal_count", "0")
                                })
            else:
                sched_site_kit = data.get("SiteKit", {})
                games = sched_site_kit.get("schedule") or sched_site_kit.get("Schedule") or []
            
            embed = discord.Embed(title=f"{self.get_team_name(abbrev)} Schedule", color=config.color)
            
            if date_str:
                upcoming = [g for g in games if date_str in str(g.get("date", ""))]
                if not upcoming:
                    upcoming = games[:7]
            else:
                upcoming = games[:7]
            
            for game in upcoming:
                home = game.get("home_team_name", "TBD")
                away = game.get("visiting_team_name", "TBD")
                d_str = game.get("date_with_day", "")
                status_txt = game.get("status", "Scheduled")
                h_goals = game.get("home_goal_count", "")
                v_goals = game.get("visiting_goal_count", "")
                
                score_str = f" ({v_goals} - {h_goals})" if h_goals and v_goals else ""
                embed.add_field(name=f"{d_str} - {status_txt}", value=f"{away} @ {home}{score_str}", inline=False)

            embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send(f"Failed to extract look-ahead week schedules: {e}")

    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl game {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            if not date_str:
                hawaii = pytz.timezone('US/Hawaii')
                date_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            
            scorebar_data = self.fetch_ht_api(feed="modulekit", view="scorebar", numberofdaysback=180, numberofdaysahead=180)
            site_kit = scorebar_data.get("SiteKit", {})
            scorebar_games = site_kit.get("Scorebar") or site_kit.get("scorebar") or []
            
            target_game = None
            for g in scorebar_games:
                g_date = g.get("Date") or g.get("date")
                if g_date == date_str or date_str in str(g.get("GameDateISO8601", "")):
                    if g.get("HomeCode") == abbrev or g.get("VisitorCode") == abbrev:
                        target_game = {
                            "game_id": g.get("ID") or g.get("game_id"),
                            "home_team_name": g.get("HomeLongName") or g.get("HomeCity"),
                            "visiting_team_name": g.get("VisitorLongName") or g.get("VisitorCity"),
                            "home_goal_count": g.get("HomeGoals", 0),
                            "visiting_goal_count": g.get("VisitorGoals", 0),
                            "status": g.get("GameStatus"),
                            "status_string": g.get("GameStatusStringLong") or g.get("GameStatusString")
                        }
                        break

            if not target_game:
                team_data = self.fetch_ht_api(feed="modulekit", view="teamsbyseason", season_id=CURRENT_SEASON_ID)
                raw_teams = team_data.get("SiteKit", {}).get("Teamsbyseason") or []
                team_id = next((t.get("id") for t in raw_teams if (t.get("code") or "").upper() == abbrev), None)
                
                if team_id:
                    sched_data = self.fetch_ht_api(feed="statviewfeed", view="schedule", team=team_id, season=CURRENT_SEASON_ID, month=-1)
                    if isinstance(sched_data, list):
                        for item in sched_data:
                            for section in item.get("sections", []):
                                for r in section.get("data", []):
                                    row = r.get("row", {})
                                    row_date = r.get("prop", {}).get("game_summary_long", {}).get("link", "")
                                    if date_str in str(row) or date_str in row_date:
                                        target_game = {
                                            "game_id": row.get("game_id"),
                                            "home_team_name": row.get("home_team_city"),
                                            "visiting_team_name": row.get("visiting_team_city"),
                                            "home_goal_count": row.get("home_goal_count", 0),
                                            "visiting_goal_count": row.get("visiting_goal_count", 0),
                                            "status_string": row.get("game_status")
                                        }
                                        break

            if not target_game:
                return await interaction.followup.send(f"Selected team specified (`{abbrev}`) has no matches slated for `{date_str}`.")

            game_id = target_game.get("game_id")
            
            gc_data = self.fetch_ht_api(feed="gc", tab="gamesummary", game_id=game_id)
            parsed_gc = gc_data.get("GC", {}).get("Gamesummary", {})
            
            meta = parsed_gc.get("meta", {})
            h_t = target_game.get("home_team_name") or parsed_gc.get("home", {}).get("name", "Home")
            a_t = target_game.get("visiting_team_name") or parsed_gc.get("visitor", {}).get("name", "Away")
            
            status = target_game.get("status_string") or parsed_gc.get("status_value", "Final")
            v_score = meta.get("visiting_goal_count") or target_game.get("visiting_goal_count", 0)
            h_score = meta.get("home_goal_count") or target_game.get("home_goal_count", 0)

            embed = discord.Embed(title=f"{a_t} @ {h_t} ({date_str})", color=config.color)
            embed.add_field(name="Current State", value=status, inline=True)
            embed.add_field(name="Scoreboard Status", value=f"{v_score} - {h_score}", inline=True)
            
            venue = parsed_gc.get("venue")
            if venue:
                embed.add_field(name="Venue", value=venue, inline=False)
            
            view = PWHLGameStatsView(parsed_gc, embed)
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send(f"Failed to build real-time interactive dashboard components: {e}")

    async def get_player_info(self, interaction: discord.Interaction, player_name: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl player {player_name}")
        try:
            search_data = self.fetch_ht_api(feed="modulekit", view="searchplayers", search_term=player_name)
            site_kit = search_data.get("SiteKit", {})
            results = site_kit.get("searchplayers") or site_kit.get("Searchplayers") or []
            
            if not results:
                return await interaction.followup.send("Player details not resolved inside open data rosters.")
                
            player_id = results[0].get("player_id")
            
            p_data = self.fetch_ht_api(feed="modulekit", view="player", category="profile", player_id=player_id)
            p_site_kit = p_data.get("SiteKit", {})
            
            # Extract player object safely regardless of capitalization
            player_obj = p_site_kit.get("Player") or p_site_kit.get("player") or {}
            profile = player_obj.get("profile") if isinstance(player_obj.get("profile"), dict) else player_obj
            
            # Map field fallbacks
            first_name = profile.get("first_name", "")
            last_name = profile.get("last_name", "")
            full_name = profile.get("name") or f"{first_name} {last_name}".strip()
            
            position = profile.get("position", "Skater")
            team_name = profile.get("most_recent_team_name") or profile.get("team_name") or "PWHL"
            jersey_num = profile.get("jersey_number") or "N/A"
            
            embed = discord.Embed(
                title=full_name, 
                description=f"{position} for {team_name} #{jersey_num}", 
                color=config.color
            )
            
            thumb_url = profile.get("primary_image") or profile.get("player_image")
            if thumb_url:
                embed.set_thumbnail(url=thumb_url)
                
            birth_date = profile.get("birthdate") or profile.get("birthdate_year") or "Unknown"
            origin = profile.get("hometown") or profile.get("birthtown") or "Unknown"
            
            embed.add_field(name="Birth Date", value=birth_date)
            embed.add_field(name="Place of Origin", value=origin)
            
            # Statistics Extraction
            stats_data = self.fetch_ht_api(feed="modulekit", view="player", category="mostrecentseasonstats", player_id=player_id)
            stats_site_kit = stats_data.get("SiteKit", {})
            stats_obj = stats_site_kit.get("Player") or stats_site_kit.get("player") or {}
            stats = stats_obj.get("mostrecentseasonstats") if isinstance(stats_obj.get("mostrecentseasonstats"), dict) else stats_obj
            
            if isinstance(stats, dict) and stats.get("games_played"):
                embed.add_field(
                    name=f"Latest Season Statistics ({stats.get('season_name', 'Regular Season')})", 
                    value=f"`{stats.get('games_played','0')}` GP | `{stats.get('goals','0')}` G | `{stats.get('assists','0')}` A | `{stats.get('points','0')}` PTS", 
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send(f"Roster parser error: {e}")

    async def get_all_teams(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): 
            await interaction.response.defer(ephemeral=True)
        try:
            lines = []
            for abbr, (name, emoji) in PWHL_TEAMS.items():
                lines.append(f"**{abbr}** - {name} {emoji}")
                
            embed = discord.Embed(
                title="Registered PWHL Configurations", 
                description="\n".join(lines), 
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            await interaction.followup.send("Asset serialization read error.")

    async def build_schedule_embed(self, date_str=None):
        if not date_str:
            hawaii = pytz.timezone('US/Hawaii')
            date_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            
        scorebar_data = self.fetch_ht_api(feed="modulekit", view="scorebar", numberofdaysback=30, numberofdaysahead=30)
        site_kit = scorebar_data.get("SiteKit", {})
        scorebar_games = site_kit.get("Scorebar") or site_kit.get("scorebar") or []
        
        games = [g for g in scorebar_games if g.get("Date") == date_str or date_str in str(g.get("GameDateISO8601", ""))]
        
        if not games:
            gpd_data = self.fetch_ht_api(feed="modulekit", view="gamesperday", start_date=date_str, end_date=date_str)
            site_kit_gpd = gpd_data.get("SiteKit", {})
            raw_gpd = site_kit_gpd.get("gamesperday") or site_kit_gpd.get("Gamesperday") or []
            
            if isinstance(raw_gpd, list) and len(raw_gpd) > 0 and "home_team_code" in raw_gpd[0]:
                games = raw_gpd
            elif isinstance(raw_gpd, dict):
                games = raw_gpd.get(date_str, [])

        if not games:
            return discord.Embed(title=f"PWHL Schedule Overview ({date_str})", description="No games scheduled for specified tracking metrics.", color=config.color)

        embed = discord.Embed(title=f"PWHL Game Logs ({date_str})", color=config.color)
        embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")

        for game in games:
            h_code = game.get("HomeCode") or game.get("home_team_code")
            a_code = game.get("VisitorCode") or game.get("visiting_team_code")
            
            h_name = game.get("HomeLongName") or self.get_team_name(h_code)
            a_name = game.get("VisitorLongName") or self.get_team_name(a_code)
            h_emoji, a_emoji = self.get_team_emoji(h_code), self.get_team_emoji(a_code)
            
            a_str = f"{a_emoji} {a_name}".lstrip()
            h_str = f"{h_name} {h_emoji}".rstrip()
            
            status_code = str(game.get("GameStatus") or game.get("status", "1"))
            v_goals = game.get("VisitorGoals") or game.get("visiting_goal_count", 0)
            h_goals = game.get("HomeGoals") or game.get("home_goal_count", 0)
            
            if status_code in ("4", "FINAL", "OFF"):
                status = f"Final: {v_goals} - {h_goals}"
            elif status_code in ("2", "3", "LIVE", "CRIT"):
                status = f"🔴 LIVE ({game.get('GameClock', '')}): {v_goals} - {h_goals}"
            else:
                status = f"Scheduled ({game.get('ScheduledFormattedTime', 'TBD')})"
                
            embed.add_field(name=status, value=f"{a_str} @ {h_str}", inline=False)
            
        return embed

async def setup(bot):
    cog = PWHL(bot)
    await bot.add_cog(cog, guilds=[discord.Object(id=config.hockey_discord_server)])

PWHLStrategy = PWHL