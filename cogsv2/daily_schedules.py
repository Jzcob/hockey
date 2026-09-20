import discord
from discord.ext import commands, tasks
from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy
from datetime import datetime, time
import pytz
import traceback


class DailySchedules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategies = {
            "nhl": NHL(bot),
            "pwhl": PWHLStrategy(bot),
        }
        self.eastern = pytz.timezone("US/Eastern")
        self.post_morning_schedule.start()
        self.live_update_loop.start()

    def cog_unload(self):
        self.post_morning_schedule.cancel()
        self.live_update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `daily_schedules.py` (NHL + PWHL database scheduling)")

    def _is_offseason(self) -> bool:
        # Temporary 2026 gate. Remove this method/check once you no longer need it.
        return datetime.now(self.eastern).date() < datetime(2026, 9, 20).date()

    @staticmethod
    def _columns(league: str):
        if league == "nhl":
            return "nhl_schedule_channel_id", "nhl_schedule_message_id"
        return "pwhl_schedule_channel_id", "pwhl_schedule_message_id"

    async def _get_channel(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel
        try:
            return await self.bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def _configured_targets(self, league: str, require_message: bool = False):
        channel_col, message_col = self._columns(league)
        where = f"{channel_col} IS NOT NULL"
        if require_message:
            where += f" AND {message_col} IS NOT NULL"

        sql = f"SELECT guild_id, {channel_col}, {message_col} FROM guild_settings WHERE {where}"
        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)
            async with conn.cursor() as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()

    async def _save_message_id(self, league: str, guild_id: int, message_id):
        _, message_col = self._columns(league)
        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE guild_settings SET {message_col} = %s WHERE guild_id = %s",
                    (message_id, guild_id),
                )
                await conn.commit()

    @tasks.loop(time=time(hour=5, minute=30, tzinfo=pytz.timezone("US/Eastern")))
    async def post_morning_schedule(self):
        if self._is_offseason():
            return

        print("Running NHL/PWHL morning schedule post...")
        for league, strategy in self.strategies.items():
            try:
                embed = await strategy.build_schedule_embed(date_str=None)
                targets = await self._configured_targets(league)
                for guild_id, channel_id, _ in targets:
                    channel = await self._get_channel(channel_id)
                    if channel is None:
                        print(f"{league.upper()}: channel {channel_id} unavailable for guild {guild_id}")
                        continue
                    try:
                        msg = await channel.send(embed=embed)
                        await self._save_message_id(league, guild_id, msg.id)
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        print(f"{league.upper()}: failed posting in guild {guild_id}: {exc}")
            except Exception:
                print(f"Error posting {league.upper()} morning schedule:\n{traceback.format_exc()}")

    @tasks.loop(minutes=5)
    async def live_update_loop(self):
        if self._is_offseason():
            return

        for league, strategy in self.strategies.items():
            try:
                targets = await self._configured_targets(league, require_message=True)
                if not targets:
                    continue

                embed = await strategy.build_schedule_embed(date_str=None)
                for guild_id, channel_id, message_id in targets:
                    channel = await self._get_channel(channel_id)
                    if channel is None:
                        continue
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.edit(embed=embed)
                    except discord.NotFound:
                        await self._save_message_id(league, guild_id, None)
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        print(f"{league.upper()}: failed live update in guild {guild_id}: {exc}")
            except Exception:
                print(f"Error in {league.upper()} live update:\n{traceback.format_exc()}")

    @post_morning_schedule.before_loop
    @live_update_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailySchedules(bot))
