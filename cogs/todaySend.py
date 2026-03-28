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

    @tasks.loop(time=run_time)
    async def send_daily_schedule(self):
        print(f"Running daily schedule task... (5:30 AM EST)")
        channel_records = []
        try:
            # Unpack the new return values
            schedule_embed, earliest_start, all_final = await self.get_schedule_embed_async()
            if not schedule_embed: return
        except Exception:
            print(f"DailySchedule: Error generating embed:\n{traceback.format_exc()}")
            return

        try:
            async with self.db_pool.acquire() as conn:
                await conn.ping(reconnect=True)
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT guild_id, daily_schedule_channel_id FROM guild_settings WHERE daily_schedule_channel_id IS NOT NULL")
                    channel_records = await cursor.fetchall()
        except Exception as e:
            print(f"DailySchedule: Database error: {e}")
            return

        for guild_id, channel_id in channel_records:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    msg = await channel.send(embed=schedule_embed)
                    
                    async with self.db_pool.acquire() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute(
                                "UPDATE guild_settings SET daily_schedule_message_id = %s WHERE guild_id = %s",
                                (msg.id, guild_id)
                            )
                            await conn.commit()
                except Exception as e:
                    print(f"Failed to send/save schedule for guild {guild_id}: {e}")

        if earliest_start and not all_final:
            now = datetime.now(pytz.utc)
            delay = (earliest_start - now).total_seconds()
            
            if delay > 0:
                print(f"Sleeping for {delay} seconds until the first game...")
                await asyncio.sleep(delay)
            
            # Start the 5-minute update loop right as the first game begins
            if not self.update_live_scores.is_running():
                print("First game starting! Launching live updates.")
                self.update_live_scores.start()

    @tasks.loop(minutes=5)
    async def update_live_scores(self):
        try:
            updated_embed, earliest_start, all_final = await self.get_schedule_embed_async()
            if not updated_embed: return
            
            records = []
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.ping(reconnect=True)
                    async with conn.cursor() as cursor:
                        await cursor.execute("""
                            SELECT guild_id, daily_schedule_channel_id, daily_schedule_message_id 
                            FROM guild_settings 
                            WHERE daily_schedule_channel_id IS NOT NULL 
                            AND daily_schedule_message_id IS NOT NULL
                        """)
                        records = await cursor.fetchall()
            except Exception as e:
                print(f"DailySchedule Update: Database error: {e}")
                return

            for guild_id, channel_id, message_id in records:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.edit(embed=updated_embed)
                    except discord.NotFound:
                        async with self.db_pool.acquire() as conn:
                            async with conn.cursor() as cursor:
                                await cursor.execute("UPDATE guild_settings SET daily_schedule_message_id = NULL WHERE guild_id = %s", (guild_id,))
                                await conn.commit()
                    except Exception:
                        continue

            if all_final:
                print("All games are final. Last update sent. Shutting down live updates.")
                self.update_live_scores.cancel()

        except Exception:
            print(f"Error in update loop: {traceback.format_exc()}")
            return

    @send_daily_schedule.before_loop
    @update_live_scores.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()

    # --- ORIGINAL API LOGIC ---
    async def get_schedule_embed_async(self):
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            today_str = datetime.now(hawaii_tz).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{today_str}"
            
            async with self.http_session.get(url) as r:
                r.raise_for_status()
                data = await r.json()
            
            if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
                embed = discord.Embed(title=f"Today's Games ({today_str})", description="No games scheduled.", color=config.color)
                # Updated return to include the new variables
                return embed, None, True 

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games ({today_str})", description=f"Total games: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            # New variables to track the day's progress
            earliest_start = None
            all_final = True

            for game in games:
                gs = game["gameState"]
                home_t, away_t = game["homeTeam"], game["awayTeam"]
                
                h_name = home_t.get("placeName", {}).get("default") or home_t.get("commonName", {}).get("default", "TBD")
                a_name = away_t.get("placeName", {}).get("default") or away_t.get("commonName", {}).get("default", "TBD")
                
                away_s, home_s = strings(away_t["abbrev"], home_t["abbrev"], h_name, a_name)
                utc_start = datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                ts = int(utc_start.timestamp())

                # Track the earliest game of the day
                if earliest_start is None or utc_start < earliest_start:
                    earliest_start = utc_start
                    
                # Track if any games are still active or unplayed
                if gs not in ("FINAL", "OFF"):
                    all_final = False

                if gs in ("FUT", "PRE"):
                    embed.add_field(name=f"<t:{ts}:t>", value=f"{away_s} @ {home_s}\nScheduled", inline=False)
                elif gs in ("FINAL", "OFF"):
                    embed.add_field(name="Final", value=f"{away_s} @ {home_s}\n{away_t.get('score',0)} - {home_t.get('score',0)}", inline=False)
                elif gs in ("LIVE", "CRIT"):
                    embed.add_field(name="🔴 LIVE", value=f"{away_s} @ {home_s}\n{away_t.get('score',0)} - {home_t.get('score',0)}", inline=False)
            
            # Return the embed alongside the tracking data
            return embed, earliest_start, all_final
        except Exception:
            return None, None, True

    # --- COMMANDS ---
    @app_commands.command(name="set-schedule-channel", description="Sets the channel for daily schedule.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_schedule_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = """
                    INSERT INTO guild_settings (guild_id, daily_schedule_channel_id) 
                    VALUES (%s, %s) 
                    ON DUPLICATE KEY UPDATE daily_schedule_channel_id = %s
                """
                await cursor.execute(sql, (interaction.guild.id, channel.id, channel.id))
                await conn.commit()
        await interaction.response.send_message(f"✅ Daily hockey schedule will now be sent to {channel.mention}", ephemeral=True)
    
    @app_commands.command(name="clear-schedule-channel", description="Clears the daily schedule channel setting.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clear_schedule_channel(self, interaction: discord.Interaction):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "UPDATE guild_settings SET daily_schedule_channel_id = NULL, daily_schedule_message_id = NULL WHERE guild_id = %s"
                await cursor.execute(sql, (interaction.guild.id,))
                await conn.commit()
        await interaction.response.send_message("✅ Daily hockey schedule channel cleared.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DailySchedule(bot))