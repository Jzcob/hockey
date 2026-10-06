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

        # Stores the date associated with each schedule message.
        #
        # Key:
        # (league, guild_id)
        #
        # Value:
        # YYYY-MM-DD
        #
        # This prevents yesterday's message from being replaced with
        # today's schedule when the live updater runs after midnight.
        self.schedule_dates = {}

        self.post_morning_schedule.start()
        self.live_update_loop.start()

    def cog_unload(self):
        self.post_morning_schedule.cancel()
        self.live_update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(
            "LOADED: `daily_schedules.py` "
            "(NHL + PWHL database scheduling)"
        )

    def _is_offseason(self) -> bool:
        # Temporary 2026 NHL gate.
        return (
            datetime.now(self.eastern).date()
            < datetime(2026, 9, 20).date()
        )

    def _league_is_active(self, league: str) -> bool:
        today = datetime.now(self.eastern).date()

        # PWHL automatic schedules begin December 6, 2026.
        if league == "pwhl":
            return today >= datetime(2026, 12, 6).date()

        return True

    def _today_string(self) -> str:
        """
        Returns today's date in Eastern Time.

        Example:
        2026-10-06
        """
        return datetime.now(self.eastern).strftime("%Y-%m-%d")

    @staticmethod
    def _columns(league: str):
        if league == "nhl":
            return (
                "nhl_schedule_channel_id",
                "nhl_schedule_message_id",
            )

        return (
            "pwhl_schedule_channel_id",
            "pwhl_schedule_message_id",
        )

    async def _get_channel(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)

        if channel is not None:
            return channel

        try:
            return await self.bot.fetch_channel(channel_id)

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            return None

    async def _configured_targets(
        self,
        league: str,
        require_message: bool = False,
    ):
        channel_col, message_col = self._columns(league)

        where = f"{channel_col} IS NOT NULL"

        if require_message:
            where += f" AND {message_col} IS NOT NULL"

        sql = (
            f"SELECT guild_id, {channel_col}, {message_col} "
            f"FROM guild_settings WHERE {where}"
        )

        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)

            async with conn.cursor() as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()

    async def _save_message_id(
        self,
        league: str,
        guild_id: int,
        message_id,
    ):
        _, message_col = self._columns(league)

        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)

            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE guild_settings "
                    f"SET {message_col} = %s "
                    f"WHERE guild_id = %s",
                    (message_id, guild_id),
                )

                await conn.commit()

    @tasks.loop(
        time=time(
            hour=5,
            minute=30,
            tzinfo=pytz.timezone("US/Eastern"),
        )
    )
    async def post_morning_schedule(self):
        if self._is_offseason():
            return

        today = self._today_string()

        print(
            f"Running NHL/PWHL morning schedule post "
            f"for {today}..."
        )

        for league, strategy in self.strategies.items():

            # PWHL stays disabled until December 6, 2026.
            if not self._league_is_active(league):
                continue

            try:
                # IMPORTANT:
                # Explicitly build today's schedule instead of relying
                # on date_str=None.
                embed = await strategy.build_schedule_embed(
                    date_str=today
                )

                targets = await self._configured_targets(league)

                for guild_id, channel_id, _ in targets:
                    channel = await self._get_channel(channel_id)

                    if channel is None:
                        print(
                            f"{league.upper()}: "
                            f"channel {channel_id} unavailable "
                            f"for guild {guild_id}"
                        )
                        continue

                    try:
                        msg = await channel.send(embed=embed)

                        await self._save_message_id(
                            league,
                            guild_id,
                            msg.id,
                        )

                        # Remember which date this particular schedule
                        # message belongs to.
                        self.schedule_dates[
                            (league, guild_id)
                        ] = today

                        print(
                            f"{league.upper()}: "
                            f"posted {today} schedule "
                            f"in guild {guild_id}"
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                    ) as exc:
                        print(
                            f"{league.upper()}: "
                            f"failed posting in guild "
                            f"{guild_id}: {exc}"
                        )

            except Exception:
                print(
                    f"Error posting "
                    f"{league.upper()} morning schedule:\n"
                    f"{traceback.format_exc()}"
                )

    @tasks.loop(minutes=5)
    async def live_update_loop(self):
        if self._is_offseason():
            return

        today = self._today_string()

        for league, strategy in self.strategies.items():

            # No automatic PWHL updates before December 6, 2026.
            if not self._league_is_active(league):
                continue

            try:
                targets = await self._configured_targets(
                    league,
                    require_message=True,
                )

                if not targets:
                    continue

                for guild_id, channel_id, message_id in targets:

                    channel = await self._get_channel(channel_id)

                    if channel is None:
                        continue

                    # Find the date belonging to this message.
                    schedule_date = self.schedule_dates.get(
                        (league, guild_id)
                    )

                    # If the bot restarted, schedule_dates will be empty.
                    #
                    # Try to recover the date from the existing embed
                    # title before editing the message.
                    if schedule_date is None:
                        try:
                            existing_msg = await channel.fetch_message(
                                message_id
                            )

                            if existing_msg.embeds:
                                existing_embed = existing_msg.embeds[0]

                                title = existing_embed.title or ""

                                # Expected old format:
                                # Today's Games (2026-03-26)
                                if "(" in title and ")" in title:
                                    possible_date = (
                                        title
                                        .split("(")[-1]
                                        .split(")")[0]
                                        .strip()
                                    )

                                    try:
                                        datetime.strptime(
                                            possible_date,
                                            "%Y-%m-%d",
                                        )

                                        schedule_date = possible_date

                                    except ValueError:
                                        pass

                        except (
                            discord.NotFound,
                            discord.Forbidden,
                            discord.HTTPException,
                        ):
                            pass

                    # If we still cannot determine the original date,
                    # only assume today for a currently active message.
                    if schedule_date is None:
                        schedule_date = today

                    self.schedule_dates[
                        (league, guild_id)
                    ] = schedule_date

                    try:
                        # CRITICAL CHANGE:
                        #
                        # Build the embed for the date this message
                        # originally belonged to.
                        #
                        # We no longer use:
                        #
                        # date_str=None
                        #
                        # because that can cause yesterday's message
                        # to become today's schedule.
                        embed = await strategy.build_schedule_embed(
                            date_str=schedule_date
                        )

                        msg = await channel.fetch_message(
                            message_id
                        )

                        await msg.edit(embed=embed)

                    except discord.NotFound:
                        await self._save_message_id(
                            league,
                            guild_id,
                            None,
                        )

                        self.schedule_dates.pop(
                            (league, guild_id),
                            None,
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                    ) as exc:
                        print(
                            f"{league.upper()}: "
                            f"failed live update in guild "
                            f"{guild_id}: {exc}"
                        )

            except Exception:
                print(
                    f"Error in "
                    f"{league.upper()} live update:\n"
                    f"{traceback.format_exc()}"
                )

    @post_morning_schedule.before_loop
    @live_update_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailySchedules(bot))