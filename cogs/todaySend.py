import discord
from discord import app_commands
from discord.ext import commands, tasks
import pytz
import traceback
from datetime import datetime, time, timedelta
import aiohttp
import aiomysql
import asyncio
import config

TEAM_EMOJIS = {
    "ANA": config.anahiem_ducks_emoji,
    "BOS": config.boston_bruins_emoji,
    "BUF": config.buffalo_sabres_emoji,
    "CGY": config.calgary_flames_emoji,
    "CAR": config.carolina_hurricanes_emoji,
    "CHI": config.chicago_blackhawks_emoji,
    "COL": config.colorado_avalanche_emoji,
    "CBJ": config.columbus_blue_jackets_emoji,
    "DAL": config.dallas_stars_emoji,
    "DET": config.detroit_red_wings_emoji,
    "EDM": config.edmonton_oilers_emoji,
    "FLA": config.florida_panthers_emoji,
    "LAK": config.los_angeles_kings_emoji,
    "MIN": config.minnesota_wild_emoji,
    "MTL": config.montreal_canadiens_emoji,
    "NSH": config.nashville_predators_emoji,
    "NJD": config.new_jersey_devils_emoji,
    "NYI": config.new_york_islanders_emoji,
    "NYR": config.new_york_rangers_emoji,
    "OTT": config.ottawa_senators_emoji,
    "PHI": config.philadelphia_flyers_emoji,
    "PIT": config.pittsburgh_penguins_emoji,
    "SJS": config.san_jose_sharks_emoji,
    "SEA": config.seattle_kraken_emoji,
    "STL": config.st_louis_blues_emoji,
    "TBL": config.tampa_bay_lightning_emoji,
    "TOR": config.toronto_maple_leafs_emoji,
    "UTA": config.utah_hockey_club_emoji,
    "VAN": config.vancouver_canucks_emoji,
    "VGK": config.vegas_golden_knights_emoji,
    "WSH": config.washington_capitals_emoji,
    "WPG": config.winnipeg_jets_emoji,
}

def strings(awayAbbreviation, homeAbbreviation, home, away):
    away_emoji = TEAM_EMOJIS.get(awayAbbreviation, "")
    home_emoji = TEAM_EMOJIS.get(homeAbbreviation, "")
    awayString = f"{away_emoji} {away}".lstrip()
    homeString = f"{home} {home_emoji}".rstrip()
    return awayString, homeString

eastern_tz = pytz.timezone("US/Eastern")
run_time = time(hour=5, minute=30, tzinfo=eastern_tz)

class DailySchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_pool = bot.db_pool
        self.http_session = aiohttp.ClientSession()
        self.send_daily_schedule.start()

    def cog_unload(self):
        self.send_daily_schedule.cancel()
        if hasattr(self, 'http_session'):
            asyncio.create_task(self.http_session.close())

    @tasks.loop(time=run_time)
    async def send_daily_schedule(self):
        print(f"Running daily schedule task... (5:30 AM EST)")
        db_conn = None
        cursor = None
        channel_records = []
        try:
            schedule_embed = await self.get_schedule_embed()

            if not schedule_embed:
                print("DailySchedule: Failed to generate schedule embed. Skipping.")
                return

            try:
                async with self.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT daily_schedule_channel_id FROM servers WHERE daily_schedule_channel_id IS NOT NULL")
                        channel_records = await cursor.fetchall()
            
            except Exception as e:
                print(f"DailySchedule: Database error: {e}")
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"**CRITICAL Error in daily_schedule task (DB query):**\n```{traceback.format_exc()}```")
                return


            if not channel_records:
                print("DailySchedule: No channels are set. Skipping.")
                return

            for (channel_id,) in channel_records:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(embed=schedule_embed)
                    except discord.Forbidden:
                        print(f"DailySchedule: Failed to send to {channel_id}: Missing permissions.")
                else:
                    print(f"DailySchedule: Could not find channel {channel_id}. It was likely deleted.")
        
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"**CRITICAL Error in daily_schedule task (Main):**\n```{traceback.format_exc()}```")

    @send_daily_schedule.before_loop
    async def before_daily_schedule(self):
        await self.bot.wait_until_ready()
        print(f"Daily schedule task is ready and waiting for {run_time}.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `todaySend.py`")


    @app_commands.command(name="set-schedule-channel", description="Sets the channel for daily NHL schedule messages.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.describe(channel="The text channel where daily schedules will be sent.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_schedule_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            if config.command_log_bool:
                try:
                    command_log_channel = self.bot.get_channel(config.command_log)
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    await command_log_channel.send(
                        f"`/set-schedule-channel` used by `{interaction.user.name}` in `{guild_name}` to set channel `{channel.name}` at `{datetime.now()}`\n---"
                    )
                except Exception as e:
                    print(f"Command logging failed: {e}")
        except Exception as e:
            print(f"Command logging failed: {e}")
        try:    
            try:
                async with self.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        sql = "INSERT INTO servers (guild_id, daily_schedule_channel_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE daily_schedule_channel_id = %s"
                        values = (interaction.guild.id, channel.id, channel.id)
                        await cursor.execute(sql, values)
                
                await interaction.response.send_message(f"✅ Daily schedule messages will now be sent to {channel.mention}.", ephemeral=True)

            except Exception as e:
                print(f"Error in set_schedule_channel: {e}")
                await interaction.response.send_message("An error occurred while setting the schedule channel. Please try again later.", ephemeral=True)
        
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"**CRITICAL Error in set_schedule_channel (outer):**\n```{traceback.format_exc()}```")
            

    @app_commands.command(name="remove-schedule-channel", description="Disables daily NHL schedule messages for this server.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_schedule_channel(self, interaction: discord.Interaction):
        try:
            if config.command_log_bool:
                try:
                    command_log_channel = self.bot.get_channel(config.command_log)
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    await command_log_channel.send(
                        f"`/remove-schedule-channel` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                    )
                except Exception as e:
                    print(f"Command logging failed: {e}")
        except Exception as e:
            print(f"Command logging failed: {e}")
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "UPDATE servers SET daily_schedule_channel_id = NULL WHERE guild_id = %s"
                    await cursor.execute(sql, (interaction.guild.id,))
            
            await interaction.response.send_message("❌ Daily schedule messages have been disabled for this server.", ephemeral=True)
        
        except Exception as e:
            print(f"Error in remove_schedule_channel: {e}")
            await interaction.response.send_message("An error occurred while disabling schedule messages. Please try again later.", ephemeral=True)

    @set_schedule_channel.error
    @remove_schedule_channel.error
    async def on_schedule_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You must have the 'Manage Server' permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message("An unknown error occurred.", ephemeral=True)


    async def get_schedule_embed_async(self):
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            today_str = datetime.now(hawaii_tz).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{today_str}"
            
            # --- ASYNC REQUEST 1 ---
            async with self.http_session.get(url) as r:
                r.raise_for_status()
                data = await r.json()
            
            if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
                embed = discord.Embed(title=f"Today's Games ({today_str})", description="No games scheduled for today.", color=config.color)
                embed.set_footer(text=config.footer)
                return embed

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games ({today_str})", description=f"Total games today: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            for game in games:
                gameState = game["gameState"]
                home_team = game["homeTeam"]
                away_team = game["awayTeam"]
                
                # Handle potential missing placeName (e.g., All-Star games)
                home_name = home_team.get("placeName", {}).get("default", "")
                away_name = away_team.get("placeName", {}).get("default", "")
                
                home_abbreviation = home_team["abbrev"]
                away_abbreviation = away_team["abbrev"]
                away_string, home_string = strings(away_abbreviation, home_abbreviation, home_name, away_name)
                utc_start_time = datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                timestamp_utc = int(utc_start_time.timestamp())

                if gameState in ("FUT", "PRE"):
                    embed.add_field(name=f"<t:{timestamp_utc}:t>", value=f"{away_string} @ {home_string}\nGame is scheduled!", inline=False)
                
                elif gameState in ("FINAL", "OFF"):
                    home_score = home_team.get('score', 0)
                    away_score = away_team.get('score', 0)
                    game_outcome = game.get("gameOutcome", {}).get("lastPeriodType")
                    
                    if game_outcome == "OT":
                        embed.add_field(name=f"Final (OT)", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    elif game_outcome == "SO":
                        embed.add_field(name=f"Final (SO)", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    else:
                        embed.add_field(name=f"Final", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)

                elif gameState in ("LIVE", "CRIT"):
                    game_id = game['id']
                    url2 = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                    
                    # --- ASYNC REQUEST 2 (NESTED) ---
                    async with self.http_session.get(url2) as r2:
                        game2 = await r2.json() # r2.raise_for_status() might be good here too
                    
                    home_score = game2['homeTeam']['score']
                    away_score = game2['awayTeam']['score']
                    clock = game2.get('clock', {})
                    period = game.get('periodDescriptor', {}).get('number')
                    period_ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "OT"}.get(period, f"P{period}")

                    if clock.get('inIntermission'):
                        embed.add_field(name=f"Intermission", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    else:
                        time_remaining = clock.get('timeRemaining', '00:00')
                        embed.add_field(name=f"🔴 LIVE - {period_ordinal}", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}\n`{time_remaining}`", inline=False)
            
            return embed

        except Exception:
            print(f"Error in get_schedule_embed_async:\n{traceback.format_exc()}")
            return None

async def setup(bot):
    await bot.add_cog(DailySchedule(bot))