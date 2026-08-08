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

# Updated with official PWHL franchise identities
PWHL_TEAMS = {
    "BOS": ("Boston Fleet", config.boston_fleet_emoji if hasattr(config, 'boston_fleet_emoji') else "⚓"),
    "MIN": ("Minnesota Frost", config.minnesota_frost_emoji if hasattr(config, 'minnesota_frost_emoji') else "❄️"),
    "MTL": ("Montréal Victoire", config.montreal_victoire_emoji if hasattr(config, 'montreal_victoire_emoji') else "⚜️"),
    "NY":  ("New York Sirens", config.new_york_sirens_emoji if hasattr(config, 'new_york_sirens_emoji') else "🚨"),
    "OTT": ("Ottawa Charge", config.ottawa_charge_emoji if hasattr(config, 'ottawa_charge_emoji') else "⚡"),
    "TOR": ("Toronto Sceptres", config.toronto_sceptres_emoji if hasattr(config, 'toronto_sceptres_emoji') else "👑"),
}

PWHL_API_KEY = "446521baf8c38984"
PWHL_CLIENT_CODE = "pwhl"
CURRENT_SEASON_ID = 5 # Update this integer for future seasons

class PWHLGameStatsView(discord.ui.View):
    def __init__(self, gc_data, original_embed):
        super().__init__(timeout=300)
        self.gc_data = gc_data
        self.original_embed = original_embed
        
        # HockeyTech GameCenter data hierarchy
        self.game_info = self.gc_data.get('Parameters', {})
        self.home_team = self.gc_data.get('Home', {})
        self.away_team = self.gc_data.get('Visitor', {})

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        team_data = self.away_team if team_type == 'away' else self.home_team
        team_name = team_data.get('info', {}).get('name', 'Team')
        
        embed = discord.Embed(title=f"{team_name} Roster Stats", color=self.original_embed.color)
        
        try:
            skaters = team_data.get('skaters', [])
            def fmt(p): return f"#{p.get('jerseyNumber', '00')} {p.get('firstName')} {p.get('lastName')} ({p.get('goals',0)}G, {p.get('assists',0)}A)"
            
            # HockeyTech doesn't always split F/D cleanly in the basic GC return, so we list top skaters
            formatted_skaters = "\n".join([fmt(p) for p in skaters[:20]]) 
            
            embed.add_field(name="Active Skaters", value=formatted_skaters[:1024] if formatted_skaters else "N/A", inline=False)
            
            goalies = team_data.get('goalies', [])
            def fmt_g(g): return f"#{g.get('jerseyNumber', '00')} {g.get('firstName')} {g.get('lastName')} (SV%: {g.get('savePct', '.000')})"
            formatted_goalies = "\n".join([fmt_g(g) for g in goalies])
            
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

    # --- API HELPER ---
    
    def fetch_ht_api(self, feed: str, **kwargs) -> dict:
        """Wrapper for the HockeyTech LeagueStat API with request URL logging and safe JSON handling."""
        base_url = "https://lscluster.hockeytech.com/feed/index.php"
        params = {
            "key": PWHL_API_KEY,
            "client_code": PWHL_CLIENT_CODE,
            "feed": feed,
            "lang": "en"
        }
        params.update(kwargs)
        
        # Build full request URL and print to console for inspection
        req = requests.Request('GET', base_url, params=params)
        prepared = req.prepare()
        print(f"[PWHL API Request]: {prepared.url}")

        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code != 200 or not response.text.strip():
                print(f"[PWHL API Error]: Status Code {response.status_code}, Body: {response.text[:200]}")
                return {}
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"[PWHL API Exception]: {e}")
            return {}

    @staticmethod
    def get_team_emoji(abbrev: str) -> str:
        return PWHL_TEAMS.get(abbrev.upper(), ("", ""))[1]

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
    @app_commands.describe(date="Override date/month context if needed")
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str, date: str = None):
        await self.get_schedule(interaction, abbreviation, date_str=date)

    @app_commands.command(name="game", description="Check live or past game stats for a PWHL team")
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
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
                team_code = record.get("team_code", "UNK")
                name = record.get("name", team_code)
                emoji = self.get_team_emoji(team_code)
                wins = record.get("wins", 0)
                losses = record.get("losses", 0)
                ot_losses = record.get("ot_losses", 0)
                points = record.get("points", 0)
                
                lines.append(f"{emoji} **{name}** ({wins}-{losses}-{ot_losses}) - {points} pts")

            embed.description = "\n".join(lines) if lines else "Standings data unavailable."
            embed.set_footer(text=config.footer)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing standings.")

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl schedule {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            if abbrev not in PWHL_TEAMS:
                return await interaction.followup.send("Invalid team identifier. Try matching format via `/pwhl teams`.")

            # HockeyTech requires internal team IDs for schedules, we fetch teams first to map it
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

            # Note: statviewfeed schedule feed requires 'team' and 'season' parameters
            data = self.fetch_ht_api(feed="statviewfeed", view="schedule", team=team_id, season=CURRENT_SEASON_ID, month=-1)
            
            # The second payload sample shows a nested structure: [ { "sections": [ { "data": [...] } ] } ]
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
                upcoming = [g for g in games if g.get("date") == date_str or date_str in g.get("date", "")]
                if not upcoming:
                    upcoming = games[:7]
            else:
                upcoming = games[:7]
            
            for game in upcoming:
                home = game.get("home_team_name", "TBD")
                away = game.get("visiting_team_name", "TBD")
                d_str = game.get("date_with_day", "")
                embed.add_field(name=d_str or "Game", value=f"{away} @ {home}", inline=False)

            embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")
            await interaction.followup.send(embed=embed)
        except Exception as e:
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
            
            # Use the scorebar feed which reliably includes games and scores across dates
            scorebar_data = self.fetch_ht_api(feed="modulekit", view="scorebar", numberofdaysback=30, numberofdaysahead=30)
            
            target_game = None
            # HockeyTech scorebar usually returns games grouped by date or inside SiteKit
            site_kit = scorebar_data.get("SiteKit", {})
            scorebar_games = site_kit.get("scorebar") or site_kit.get("Scorebar") or []
            
            # If scorebar structure varies, let's search team schedule directly as a robust fallback
            if not scorebar_games:
                team_data = self.fetch_ht_api(feed="modulekit", view="teamsbyseason", season_id=CURRENT_SEASON_ID)
                raw_teams = site_kit.get("teamsbyseason") or site_kit.get("Teamsbyseason") or []
                team_id = None
                for t in raw_teams:
                    if (t.get("team_code") or t.get("code") or "").upper() == abbrev:
                        team_id = t.get("id") or t.get("team_id")
                        break
                
                if team_id:
                    sched_data = self.fetch_ht_api(feed="statviewfeed", view="schedule", team=team_id, season=CURRENT_SEASON_ID, month=-1)
                    for item in sched_data:
                        for section in item.get("sections", []):
                            for r in section.get("data", []):
                                row = r.get("row", {})
                                if row.get("date_with_day") or date_str in str(row):
                                    # Map row fields to target game structure
                                    if abbrev in row.get("home_team_city", "").upper() or abbrev in row.get("visiting_team_city", "").upper():
                                        target_game = {
                                            "game_id": row.get("game_id"),
                                            "home_team_name": row.get("home_team_city"),
                                            "visiting_team_name": row.get("visiting_team_city"),
                                            "home_goal_count": row.get("home_goal_count", 0),
                                            "visiting_goal_count": row.get("visiting_goal_count", 0),
                                            "status": 4 if "Final" in row.get("game_status", "") else 1
                                        }
                                        break
            else:
                for g in scorebar_games:
                    g_date = g.get("date") or g.get("game_date")
                    if g_date == date_str:
                        if g.get("home_team_code") == abbrev or g.get("visiting_team_code") == abbrev:
                            target_game = g
                            break

            if not target_game:
                return await interaction.followup.send(f"Selected team specified (`{abbrev}`) has no matches slated for `{date_str}`.")

            game_id = target_game.get("game_id")
            
            # Get verbose Game Center Data
            gc_data = self.fetch_ht_api(feed="gc", tab="gamesummary", game_id=game_id)
            parsed_gc = gc_data.get("GC", {}).get("Gamesummary", {})
            
            h_t = target_game.get("home_team_name", "Home")
            a_t = target_game.get("visiting_team_name", "Away")
            
            status = "Scheduled" if str(target_game.get("status")) == "1" else "Final" if str(target_game.get("status")) == "4" else "Live"

            embed = discord.Embed(title=f"{a_t} @ {h_t} ({date_str})", color=config.color)
            embed.add_field(name="Current State", value=status, inline=True)
            embed.add_field(name="Scoreboard Status", value=f"{target_game.get('visiting_goal_count', 0)} - {target_game.get('home_goal_count', 0)}", inline=True)
            
            view = PWHLGameStatsView(parsed_gc, embed)
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
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
            profile = p_site_kit.get("player", {}).get("profile") or p_site_kit.get("Player", {}).get("profile", {})
            
            embed = discord.Embed(
                title=f"{profile.get('first_name', '')} {profile.get('last_name', '')}", 
                description=f"{profile.get('position', 'Skater')} for {profile.get('team_name', 'PWHL')} #{profile.get('jersey_number', 'N/A')}", 
                color=config.color
            )
            
            if profile.get('player_image'):
                embed.set_thumbnail(url=profile.get('player_image'))
                
            embed.add_field(name="Birth Date", value=profile.get("birthdate_year", "Unknown"))
            embed.add_field(name="Place of Origin", value=profile.get("hometown", "Unknown"))
            
            stats_data = self.fetch_ht_api(feed="modulekit", view="player", category="mostrecentseasonstats", player_id=player_id)
            stats_site_kit = stats_data.get("SiteKit", {})
            stats = stats_site_kit.get("player", {}).get("mostrecentseasonstats") or stats_site_kit.get("Player", {}).get("mostrecentseasonstats", {})
            
            if stats:
                embed.add_field(name="Latest Season (GP/G/A/PTS)", value=f"`{stats.get('games_played','0')}` GP | `{stats.get('goals','0')}` G | `{stats.get('assists','0')}` A | `{stats.get('points','0')}` PTS", inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Roster parser error.")

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

    # --- REFRESH INFRASTRUCTURE ENGINE ---

    async def build_schedule_embed(self, date_str=None):
        if not date_str:
            hawaii = pytz.timezone('US/Hawaii')
            date_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            
        data = self.fetch_ht_api(feed="modulekit", view="gamesperday", start_date=date_str, end_date=date_str)
        site_kit = data.get("SiteKit", {})
        games_data = site_kit.get("gamesperday") or site_kit.get("Gamesperday", {})
        
        if isinstance(games_data, list):
            games = []
        else:
            games = games_data.get(date_str, [])
        
        if not games:
            return discord.Embed(title=f"PWHL Schedule Overview ({date_str})", description="No games scheduled for specified tracking metrics.", color=config.color)

        embed = discord.Embed(title=f"PWHL Game Logs ({date_str})", color=config.color)
        embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")

        for game in games:
            h_code, a_code = game.get("home_team_code"), game.get("visiting_team_code")
            h_name, a_name = self.get_team_name(h_code), self.get_team_name(a_code)
            h_emoji, a_emoji = self.get_team_emoji(h_code), self.get_team_emoji(a_code)
            
            a_str = f"{a_emoji} {a_name}".lstrip()
            h_str = f"{h_name} {h_emoji}".rstrip()
            
            status_code = str(game.get("status", "1"))
            if status_code == "4":
                status = f"Final: {game.get('visiting_goal_count', 0)} - {game.get('home_goal_count', 0)}"
            elif status_code in ("2", "3"):
                status = f"🔴 LIVE: {game.get('visiting_goal_count', 0)} - {game.get('home_goal_count', 0)}"
            else:
                status = "Scheduled"
                
            embed.add_field(name=status, value=f"{a_str} @ {h_str}", inline=False)
            
        return embed

    async def post_daily_schedule(self, channel: discord.TextChannel):
        embed = await self.build_schedule_embed()
        msg = await channel.send(embed=embed)
        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE guild_settings SET daily_schedule_message_id = %s WHERE guild_id = %s", (msg.id, channel.guild.id))

    async def update_live_scores(self):
        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT daily_schedule_message_id, daily_schedule_channel_id FROM guild_settings WHERE daily_schedule_message_id IS NOT NULL")
                records = await cursor.fetchall()
        if not records: return
        updated_embed = await self.build_schedule_embed()
        for m_id, c_id in records:
            try:
                ch = self.bot.get_channel(c_id)
                if ch:
                    msg = await ch.fetch_message(m_id)
                    await msg.edit(embed=updated_embed)
            except: continue

async def setup(bot):
    cog = PWHL(bot)
    await bot.add_cog(cog, guilds=[discord.Object(id=config.hockey_discord_server)])

PWHLStrategy = PWHL