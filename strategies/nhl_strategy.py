import discord
from discord import app_commands
from discord.ext import commands
import config
from datetime import datetime, timedelta
import requests
import pytz
import traceback
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

class NHL(commands.GroupCog, name="nhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Moving strings inside the class as a static method
    @staticmethod
    def format_team_strings(awayAbbrev, homeAbbrev, home, away):
        a_emoji = TEAM_EMOJIS.get(awayAbbrev, "")
        h_emoji = TEAM_EMOJIS.get(homeAbbrev, "")
        return f"{a_emoji} {away}".lstrip(), f"{home} {h_emoji}".rstrip()

    # --- DISCORD COMMANDS (/nhl shortcut) ---

    @app_commands.command(name="today", description="Get today's NHL schedule and scores")
    async def today_cmd(self, interaction: discord.Interaction):
        await self.get_today_games(interaction)

    @app_commands.command(name="yesterday", description="Get yesterday's NHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)

    # --- SHARED STRATEGY LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()
            
        base_strategy.log_command(self.bot, interaction, "nhl today")
        try:
            hawaii = pytz.timezone('US/Hawaii')
            t_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{t_str}"
            
            r = requests.get(url)
            data = r.json()
            
            if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
                embed = discord.Embed(title="Today's Games", description="No games scheduled for today.", color=config.color)
                await interaction.followup.send(embed=embed)
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title="Today's NHL Games", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")

            for game in games:
                h_t, a_t = game["homeTeam"], game["awayTeam"]
                h_name = h_t.get("commonName", {}).get("default", "TBD")
                a_name = a_t.get("commonName", {}).get("default", "TBD")
                
                # Calling the static method via self
                a_str, h_str = self.format_team_strings(a_t["abbrev"], h_t["abbrev"], h_name, a_name)
                
                embed.add_field(name="Game", value=f"{a_str} @ {h_str}", inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error fetching NHL schedule.")
            traceback.print_exc()

    # Stubbing other methods for clarity
    async def get_yesterday_games(self, interaction: discord.Interaction): pass
    async def get_standings(self, interaction: discord.Interaction): pass
    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_player_info(self, interaction: discord.Interaction, player_name: str): pass
    async def get_team_info(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_all_teams(self, interaction: discord.Interaction): pass
    async def get_tomorrow_games(self, interaction: discord.Interaction): pass
    async def set_schedule_channel(self, interaction: discord.Interaction, channel_id: int): pass
    async def remove_schedule_channel(self, interaction: discord.Interaction): pass
    async def get_playoff_bracket(self, interaction: discord.Interaction): pass

    async def post_daily_schedule(self, channel: discord.TextChannel):
        """Initial morning post at 5:30 AM."""
        # Use your new builder to get the fresh embed!
        embed = await self.build_schedule_embed()
        
        msg = await channel.send(embed=embed)
        
        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE guild_settings SET daily_schedule_message_id = %s WHERE guild_id = %s",
                    (msg.id, channel.guild.id)
                )
                await conn.commit() # Don't forget the commit!

    async def update_live_scores(self):
        """The 5-minute refresh logic called by DailySchedules cog."""
        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT daily_schedule_message_id, daily_schedule_channel_id FROM guild_settings WHERE daily_schedule_message_id IS NOT NULL")
                records = await cursor.fetchall()

        if not records:
            return

        # Build the fresh embed ONCE
        updated_embed = await self.build_schedule_embed()

        for msg_id, chan_id in records:
            try:
                channel = self.bot.get_channel(chan_id)
                if channel:
                    msg = await channel.fetch_message(msg_id)
                    # Check if the embed actually needs updating to save API rate limits
                    await msg.edit(embed=updated_embed)
            except Exception:
                continue
    
    async def build_schedule_embed(self, date_str=None):
        """Internal helper to create a schedule embed for any given date."""
        if not date_str:
            hawaii = pytz.timezone('US/Hawaii')
            date_str = datetime.now(hawaii).strftime('%Y-%m-%d')

        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
        r = requests.get(url)
        data = r.json()

        if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
            return discord.Embed(title=f"NHL Schedule ({date_str})", description="No games scheduled.", color=config.color)

        games = data["gameWeek"][0]["games"]
        embed = discord.Embed(title=f"NHL Schedule ({date_str})", color=config.color)
        embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")

        for game in games:
            h_t, a_t = game["homeTeam"], game["awayTeam"]
            a_str, h_str = self.format_team_strings(a_t["abbrev"], h_t["abbrev"], h_t.get("commonName", {}).get("default", "TBD"), a_t.get("commonName", {}).get("default", "TBD"))
            
            status = "Scheduled"
            if game["gameState"] in ("FINAL", "OFF"):
                status = f"Final: {a_t.get('score', 0)} - {h_t.get('score', 0)}"
            elif game["gameState"] in ("LIVE", "CRIT"):
                status = f"🔴 LIVE: {a_t.get('score', 0)} - {h_t.get('score', 0)}"

            embed.add_field(name=status, value=f"{a_str} @ {h_str}", inline=False)
        
        embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')} EST")
        return embed

async def setup(bot):
    cog = NHL(bot)
    # Force add to the tree for your specific server
    guild = discord.Object(id=config.hockey_discord_server)
    await bot.add_cog(cog, guilds=[guild])
    
    # Debug print to confirm the tree actually saw it
    print(f"DEBUG: NHL Cog added to tree for guild {guild.id}")

# Alias for other files
NHLStrategy = NHL