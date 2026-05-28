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

TEAM_EMOJIS = {
    "ANA": config.anahiem_ducks_emoji, "BOS": config.boston_bruins_emoji, "BUF": config.buffalo_sabres_emoji,
    "CGY": config.calgary_flames_emoji, "CAR": config.carolina_hurricanes_emoji, "CHI": config.chicago_blackhawks_emoji,
    "COL": config.colorado_avalanche_emoji, "CBJ": config.columbus_blue_jackets_emoji, "DAL": config.dallas_stars_emoji,
    "DET": config.detroit_red_wings_emoji, "EDM": config.edmonton_oilers_emoji, "FLA": config.florida_panthers_emoji,
    "LAK": config.los_angeles_kings_emoji, "MIN": config.minnesota_wild_emoji, "MTL": config.montreal_canadiens_emoji,
    "NSH": config.nashville_predators_emoji, "NJD": config.new_jersey_devils_emoji, "NYI": config.new_york_islanders_emoji,
    "NYR": config.new_york_rangers_emoji, "OTT": config.ottawa_senators_emoji, "PHI": config.philadelphia_flyers_emoji,
    "PIT": config.pittsburgh_penguins_emoji, "SJS": config.san_jose_sharks_emoji, "SEA": config.seattle_kraken_emoji,
    "STL": config.st_louis_blues_emoji, "TBL": config.tampa_bay_lightning_emoji, "TOR": config.toronto_maple_leafs_emoji,
    "UTA": config.utah_hockey_club_emoji, "VAN": config.vancouver_canucks_emoji, "VGK": config.vegas_golden_knights_emoji,
    "WSH": config.washington_capitals_emoji, "WPG": config.winnipeg_jets_emoji,
}

class GameStatsView(discord.ui.View):
    def __init__(self, boxscore_data, original_embed):
        super().__init__(timeout=300)
        self.boxscore_data = boxscore_data
        self.original_embed = original_embed
        self.away_team_abbrev = boxscore_data.get('awayTeam', {}).get('abbrev', 'AWAY')
        self.home_team_abbrev = boxscore_data.get('homeTeam', {}).get('abbrev', 'HOME')

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        team_data = self.boxscore_data['awayTeam'] if team_type == 'away' else self.boxscore_data['homeTeam']
        stats_data = self.boxscore_data.get('playerByGameStats', {}).get(f'{team_type}Team', {})
        display_name = team_data.get('commonName', {}).get('default') or team_data.get('placeName', {}).get('default', 'Team')
        
        embed = discord.Embed(title=f"{display_name} Roster Stats", color=self.original_embed.color)
        embed.set_thumbnail(url=team_data.get('logo'))

        try:
            def fmt(p): return f"#{p['sweaterNumber']} {p['name']['default']} ({p.get('goals',0)}G, {p.get('assists',0)}A)"
            fwd = "\n".join([fmt(p) for p in stats_data.get('forwards', [])])
            dfe = "\n".join([fmt(p) for p in stats_data.get('defense', [])])
            embed.add_field(name="Forwards", value=fwd[:1024] if fwd else "N/A", inline=False)
            embed.add_field(name="Defense", value=dfe[:1024] if dfe else "N/A", inline=False)
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

class NHL(commands.GroupCog, name="nhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @staticmethod
    def format_team_strings(awayAbbrev, homeAbbrev, home, away):
        a_emoji = TEAM_EMOJIS.get(awayAbbrev, "")
        h_emoji = TEAM_EMOJIS.get(homeAbbrev, "")
        return f"{a_emoji} {away}".lstrip(), f"{home} {h_emoji}".rstrip()

    @staticmethod
    def get_division_string(name):
        return TEAM_EMOJIS.get(name[:3].upper(), "") + f" {name}"

    # --- DISCORD COMMAND INTERFACES ---

    @app_commands.command(name="today", description="Get today's NHL schedule and scores")
    async def today_cmd(self, interaction: discord.Interaction):
        await self.get_today_games(interaction)

    @app_commands.command(name="yesterday", description="Get yesterday's NHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)

    @app_commands.command(name="standings", description="Get the NHL standings")
    async def standings_cmd(self, interaction: discord.Interaction):
        await self.get_standings(interaction)

    @app_commands.command(name="schedule", description="Get the schedule for the week for an NHL team")
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_schedule(interaction, abbreviation)

    @app_commands.command(name="game", description="Check live or past game stats for an NHL team")
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_game_info(interaction, abbreviation)

    @app_commands.command(name="player", description="Gets the complete career overview of an NHL player")
    async def player_cmd(self, interaction: discord.Interaction, name: str):
        await self.get_player_info(interaction, name)

    @app_commands.command(name="teams", description="Get all available NHL team codes and abbreviations")
    async def teams_cmd(self, interaction: discord.Interaction):
        await self.get_all_teams(interaction)

    # --- SHARED STRATEGY ARCHITECTURE LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl today")
        try:
            embed = await self.build_schedule_embed()
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing schedule request.")

    async def get_yesterday_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl yesterday")
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            y_date = (datetime.now(hawaii_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
            embed = await self.build_schedule_embed(date_str=y_date)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing retrospective scores.")

    async def get_standings(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl standings")
        try:
            today = datetime.today().strftime('%Y-%m-%d')
            data = requests.get(f"https://api-web.nhle.com/v1/standings/{today}").json()
            
            divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for record in data.get("standings", []):
                div = record.get("divisionName")
                if div in divisions:
                    emoji_name = self.get_division_string(record['teamName']['default'])
                    wildcard = "🃏" if record.get("wildcardSequence") in [1, 2] else ""
                    divisions[div].append(f"{emoji_name} ({record['wins']}-{record['losses']}-{record['otLosses']}) {record['points']}pts {wildcard}")

            embed = discord.Embed(title="NHL Standings Overview", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            for div_name, lines in divisions.items():
                embed.add_field(name=f"{div_name} Division", value="\n".join(lines) if lines else "No data", inline=False)
            embed.set_footer(text=config.footer)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing standings.")

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl schedule {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            with open("teams.json", "r") as f: teams = json.load(f)
            if abbrev not in teams:
                return await interaction.followup.send("Invalid team identifier. Try matching format via `/nhl teams`.")

            data = requests.get(f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/now').json()
            embed = discord.Embed(title=f"{teams[abbrev]} Weekly Outlook", color=config.color)
            
            for game in data.get('games', []):
                b_data = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game['id']}/boxscore").json()
                home = b_data["homeTeam"]["commonName"]["default"]
                away = b_data["awayTeam"]["commonName"]["default"]
                utc_start = datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                embed.add_field(name=f"<t:{int(utc_start.timestamp())}:F>", value=f"{away} @ {home}", inline=False)

            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Failed to extract look-ahead week schedules.")

    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl game {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            hawaii = pytz.timezone('US/Hawaii')
            today = datetime.now(hawaii).strftime('%Y-%m-%d')
            
            data = requests.get(f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/{today}').json()
            game_data = next((g for g in data.get('games', []) if g.get('gameDate') == today), None)
            
            if not game_data:
                return await interaction.followup.send(f"Selected team specified (`{abbrev}`) has no matches slated today.")

            g_id = game_data['id']
            b_data = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{g_id}/boxscore").json()
            
            h_t, a_t = b_data['homeTeam'], b_data['awayTeam']
            h_n = h_t.get('commonName', {}).get('default') or 'Home'
            a_n = a_t.get('commonName', {}).get('default') or 'Away'

            embed = discord.Embed(title=f"{a_n} @ {h_n}", color=config.color)
            embed.add_field(name="Current State", value=b_data.get('gameState', 'FUT'), inline=True)
            embed.add_field(name="Scoreboard Status", value=f"{a_t.get('score',0)} - {h_t.get('score',0)}", inline=True)
            
            view = GameStatsView(b_data, embed)
            await interaction.followup.send(embed=embed, view=view)
        except Exception:
            await interaction.followup.send("Failed to build real-time interactive dashboard components.")

    async def get_player_info(self, interaction: discord.Interaction, player_name: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl player {player_name}")
        try:
            with open("teams.json", "r") as f: teams = json.load(f)
            found_player = None
            
            for team_abbr in teams.keys():
                roster = requests.get(f"https://api-web.nhle.com/v1/roster/{team_abbr}/current").json()
                for group in ["forwards", "defensemen", "goalies"]:
                    for p in roster.get(group, []):
                        fn = p.get("firstName", {}).get("default", "")
                        ln = p.get("lastName", {}).get("default", "")
                        if f"{fn} {ln}".lower() == player_name.lower():
                            found_player = (p["id"], teams[team_abbr])
                            break
                if found_player: break

            if not found_player:
                return await interaction.followup.send("Player details not resolved inside open data rosters.")

            p_data = requests.get(f"https://api-web.nhle.com/v1/player/{found_player[0]}/landing").json()
            pos_map = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}
            
            embed = discord.Embed(title=player_name, description=f"{pos_map.get(p_data.get('position'), 'Skater')} for the {found_player[1]} #{p_data.get('sweaterNumber', 'N/A')}", color=config.color)
            embed.set_thumbnail(url=p_data.get("headshot"))
            embed.add_field(name="Birth Date", value=p_data.get("birthDate", "Unknown"))
            embed.add_field(name="Place of Origin", value=f"{p_data.get('birthCity', {}).get('default', 'Unknown')}, {p_data.get('birthCountry', '')}")
            
            c_stats = p_data.get("featuredStats", {}).get("regularSeason", {}).get("career", {})
            embed.add_field(name="Career Summary (GP/G/A/PTS)", value=f"`{c_stats.get('gamesPlayed','N/A')}` GP | `{c_stats.get('goals','N/A')}` G | `{c_stats.get('assists','N/A')}` A | `{c_stats.get('points','N/A')}` PTS", inline=False)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Roster parser error.")

    async def get_all_teams(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): 
            await interaction.response.defer(ephemeral=True)
        try:
            with open("teams.json", "r", encoding="utf-8") as f: 
                teams_data = json.load(f)
            
            lines = []
            for abbr, name in teams_data.items():
                # Clean the name safely outside of the f-string expression block
                attr_name = f"{name.lower().replace(' ', '_')}_emoji"
                emoji = getattr(config, attr_name, "")
                lines.append(f"**{abbr}** - {name} {emoji}")
                
            embed = discord.Embed(
                title="Registered NHL Configurations", 
                description="\n".join(lines), 
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            await interaction.followup.send("Asset serialization read error.")

    # --- GAMES LOGIC ATTACHMENTS ---

    async def get_random_player_data(self):
        try:
            with open("teams.json", "r") as f: teams = json.load(f)
            team_abbr = random.choice(list(teams.keys()))
            roster = requests.get(f"https://api-web.nhle.com/v1/roster/{team_abbr}/current").json()
            group = random.choice(["forwards", "defensemen", "goalies"])
            p = random.choice(roster[group])
            return {"team": teams[team_abbr], "first": p["firstName"]["default"], "last": p["lastName"]["default"], "code": p["positionCode"]}
        except: return None

    async def run_gtp_game(self, interaction: discord.Interaction, is_race=False):
        data = await self.get_random_player_data()
        if not data: return await interaction.followup.send("Failed to extract sample roster entities.")
        
        full_name = f"{data['first']} {data['last']}"
        pos = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}.get(data['code'], "Skater")
        
        embed = discord.Embed(title="🎯 Guess The NHL Player!" if not is_race else "🏁 GTP Race!", description=f"Unmask the player belonging to the **{data['team']}**!\nHint: Name starts with `{data['first'][0]}` | Position: `{pos}`", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

        def check(m): return m.channel == interaction.channel and not m.author.bot
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20.0)
            if fuzz.partial_ratio(msg.content.strip().lower(), full_name.lower()) >= 85:
                async with self.bot.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("INSERT INTO gtp_scores (user_id, guild_id, points) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE points = points + 1", (msg.author.id, interaction.guild.id if interaction.guild else 0))
                await msg.reply(f"🏆 Match confirmed! The individual was `{full_name}`!")
            else:
                await interaction.followup.send(f"Incorrect tracking metrics. Answer resolved to: `{full_name}`.")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"Time metrics expired. Targeted answer was: `{full_name}`.")

    # --- REFRESH INFRASTRUCTURE ENGINE ---

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

    async def build_schedule_embed(self, date_str=None):
        if not date_str:
            hawaii = pytz.timezone('US/Hawaii')
            date_str = datetime.now(hawaii).strftime('%Y-%m-%d')
        data = requests.get(f"https://api-web.nhle.com/v1/schedule/{date_str}").json()
        
        if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
            return discord.Embed(title=f"NHL Schedule Overview ({date_str})", description="No games scheduled for specified tracking metrics.", color=config.color)

        games = data["gameWeek"][0]["games"]
        embed = discord.Embed(title=f"NHL Game Logs ({date_str})", color=config.color)
        embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")

        for game in games:
            h_t, a_t = game["homeTeam"], game["awayTeam"]
            a_str, h_str = self.format_team_strings(a_t["abbrev"], h_t["abbrev"], h_t.get("commonName",{}).get("default","TBD"), a_t.get("commonName",{}).get("default","TBD"))
            status = f"Final: {a_t.get('score',0)} - {h_t.get('score',0)}" if game["gameState"] in ("FINAL", "OFF") else f"🔴 LIVE: {a_t.get('score',0)} - {h_t.get('score',0)}" if game["gameState"] in ("LIVE", "CRIT") else "Scheduled"
            embed.add_field(name=status, value=f"{a_str} @ {h_str}", inline=False)
        return embed

async def setup(bot):
    cog = NHL(bot)
    await bot.add_cog(cog, guilds=[discord.Object(id=config.hockey_discord_server)])

NHLStrategy = NHL