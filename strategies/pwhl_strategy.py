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
    async def summary_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self.original_embed)

    @discord.ui.button(label="Away Roster", style=discord.ButtonStyle.secondary)
    async def away_roster_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('away'))

    @discord.ui.button(label="Home Roster", style=discord.ButtonStyle.secondary)
    async def home_roster_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('home'))


class PWHL(commands.GroupCog, name="pwhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # --- API HELPER ---
    
    def fetch_ht_api(self, feed: str, **kwargs) -> dict:
        """Wrapper for the HockeyTech LeagueStat API."""
        base_url = "https://lscluster.hockeytech.com/feed/index.php"
        params = {
            "key": PWHL_API_KEY,
            "client_code": PWHL_CLIENT_CODE,
            "feed": feed,
            "lang": "en"
        }
        params.update(kwargs)
        response = requests.get(base_url, params=params)
        return response.json()

    @staticmethod
    def get_team_emoji(abbrev: str) -> str:
        return PWHL_TEAMS.get(abbrev.upper(), ("", ""))[1]

    @staticmethod
    def get_team_name(abbrev: str) -> str:
        return PWHL_TEAMS.get(abbrev.upper(), (abbrev, ""))[0]

    # --- DISCORD COMMAND INTERFACES ---

    @app_commands.command(name="today", description="Get today's PWHL schedule and scores")
    async def today_cmd(self, interaction: discord.Interaction):
        await self.get_today_games(interaction)

    @app_commands.command(name="yesterday", description="Get yesterday's PWHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)

    @app_commands.command(name="standings", description="Get the PWHL standings")
    async def standings_cmd(self, interaction: discord.Interaction):
        await self.get_standings(interaction)

    @app_commands.command(name="schedule", description="Get the schedule for a PWHL team")
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_schedule(interaction, abbreviation)

    @app_commands.command(name="game", description="Check live or past game stats for a PWHL team")
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_game_info(interaction, abbreviation)

    @app_commands.command(name="player", description="Gets the complete career overview of a PWHL player")
    async def player_cmd(self, interaction: discord.Interaction, name: str):
        await self.get_player_info(interaction, name)

    @app_commands.command(name="teams", description="Get all available PWHL team codes and abbreviations")
    async def teams_cmd(self, interaction: discord.Interaction):
        await self.get_all_teams(interaction)

    # --- SHARED STRATEGY ARCHITECTURE LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "pwhl today")
        try:
            embed = await self.build_schedule_embed()
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

    async def get_standings(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "pwhl standings")
        try:
            data = self.fetch_ht_api(
                feed="modulekit", 
                view="statviewtype", 
                stat="conference", 
                type="standings", 
                season_id=CURRENT_SEASON_ID
            )
            
            standings_data = data.get("SiteKit", {}).get("Statviewtype", [])
            
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

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl schedule {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            if abbrev not in PWHL_TEAMS:
                return await interaction.followup.send("Invalid team identifier. Try matching format via `/pwhl teams`.")

            # HockeyTech requires internal team IDs for schedules, we fetch teams first to map it
            team_data = self.fetch_ht_api(feed="modulekit", view="teamsbyseason", season_id=CURRENT_SEASON_ID)
            team_id = None
            for t in team_data.get("SiteKit", {}).get("Teamsbyseason", []):
                if t.get("team_code") == abbrev:
                    team_id = t.get("id")
                    break
            
            if not team_id:
                return await interaction.followup.send("Could not map team abbreviation to LeagueStat ID.")

            data = self.fetch_ht_api(feed="statviewfeed", view="schedule", team=team_id, season=CURRENT_SEASON_ID, month=-1)
            games = data.get("SiteKit", {}).get("Schedule", [])
            
            embed = discord.Embed(title=f"{self.get_team_name(abbrev)} Schedule", color=config.color)
            
            # Filter for upcoming games
            upcoming = [g for g in games if int(g.get("status", 0)) < 3][:7] # Get next 7 games
            
            for game in upcoming:
                home = game.get("home_team_name", "TBD")
                away = game.get("visiting_team_name", "TBD")
                date_str = game.get("date_with_day", "")
                embed.add_field(name=date_str, value=f"{away} @ {home}", inline=False)

            embed.set_thumbnail(url="https://www.thepwhl.com/wp-content/uploads/sites/2/2023/10/PWHL_Logo_Color_RGB.png")
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Failed to extract look-ahead week schedules.")

    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl game {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            hawaii = pytz.timezone('US/Hawaii')
            today = datetime.now(hawaii).strftime('%Y-%m-%d')
            
            # Find today's game ID for this team
            schedule = self.fetch_ht_api(feed="modulekit", view="gamesperday", start_date=today, end_date=today)
            games = schedule.get("SiteKit", {}).get("Gamesperday", [])
            
            target_game = None
            for date_key, date_games in games.items():
                if not isinstance(date_games, list): continue
                for g in date_games:
                    if g.get("home_team_code") == abbrev or g.get("visiting_team_code") == abbrev:
                        target_game = g
                        break
            
            if not target_game:
                return await interaction.followup.send(f"Selected team specified (`{abbrev}`) has no matches slated today.")

            game_id = target_game.get("game_id")
            
            # Get verbose Game Center Data
            gc_data = self.fetch_ht_api(feed="gc", tab="gamesummary", game_id=game_id)
            parsed_gc = gc_data.get("GC", {}).get("Gamesummary", {})
            
            h_t = target_game.get("home_team_name", "Home")
            a_t = target_game.get("visiting_team_name", "Away")
            
            status = "Scheduled" if target_game.get("status") == "1" else "Final" if target_game.get("status") == "4" else "Live"

            embed = discord.Embed(title=f"{a_t} @ {h_t}", color=config.color)
            embed.add_field(name="Current State", value=status, inline=True)
            embed.add_field(name="Scoreboard Status", value=f"{target_game.get('visiting_goal_count', 0)} - {target_game.get('home_goal_count', 0)}", inline=True)
            
            view = PWHLGameStatsView(parsed_gc, embed)
            await interaction.followup.send(embed=embed, view=view)
        except Exception:
            await interaction.followup.send("Failed to build real-time interactive dashboard components.")

    async def get_player_info(self, interaction: discord.Interaction, player_name: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"pwhl player {player_name}")
        try:
            search_data = self.fetch_ht_api(feed="modulekit", view="searchplayers", search_term=player_name)
            results = search_data.get("SiteKit", {}).get("Searchplayers", [])
            
            if not results:
                return await interaction.followup.send("Player details not resolved inside open data rosters.")
                
            # Take the first match
            player_id = results[0].get("player_id")
            
            # Fetch full profile
            p_data = self.fetch_ht_api(feed="modulekit", view="player", category="profile", player_id=player_id)
            profile = p_data.get("SiteKit", {}).get("Player", {}).get("profile", {})
            
            embed = discord.Embed(
                title=f"{profile.get('first_name', '')} {profile.get('last_name', '')}", 
                description=f"{profile.get('position', 'Skater')} for {profile.get('team_name', 'PWHL')} #{profile.get('jersey_number', 'N/A')}", 
                color=config.color
            )
            
            if profile.get('player_image'):
                embed.set_thumbnail(url=profile.get('player_image'))
                
            embed.add_field(name="Birth Date", value=profile.get("birthdate_year", "Unknown"))
            embed.add_field(name="Place of Origin", value=profile.get("hometown", "Unknown"))
            
            # Fetch recent season stats
            stats_data = self.fetch_ht_api(feed="modulekit", view="player", category="mostrecentseasonstats", player_id=player_id)
            stats = stats_data.get("SiteKit", {}).get("Player", {}).get("mostrecentseasonstats", {})
            
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
        games_data = data.get("SiteKit", {}).get("Gamesperday", {})
        
        # Check if HockeyTech returned an empty list instead of a dict
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
            
            # Status mapping: 1 = Scheduled, 2 = Live (period), 4 = Final
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
                # Note: Make sure 'daily_schedule_message_id' doesn't conflict with the NHL message ID in your DB! 
                # You might need a 'pwhl_daily_schedule_message_id' column if you want both in the same channel.
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