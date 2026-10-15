import re
import traceback
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy


class DailySchedules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategies = {"nhl": NHL(bot), "pwhl": PWHLStrategy(bot)}
        self.eastern = ZoneInfo("America/New_York")
        self.next_updates = {}
        self.post_morning_schedule.start()
        self.live_update_loop.start()

    def cog_unload(self):
        self.post_morning_schedule.cancel()
        self.live_update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: daily_schedules.py (game-start-aware updates)")

    def _is_offseason(self):
        return datetime.now(self.eastern).date() < datetime(2026, 9, 20).date()

    def _league_is_active(self, league):
        return league != "pwhl" or datetime.now(self.eastern).date() >= datetime(2026, 12, 6).date()

    @staticmethod
    def _columns(league):
        prefix = "nhl" if league == "nhl" else "pwhl"
        return f"{prefix}_schedule_channel_id", f"{prefix}_schedule_message_id"

    async def _get_channel(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel
        try:
            return await self.bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def _configured_targets(self, league, require_message=False):
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

    async def _save_message_id(self, league, guild_id, message_id):
        _, message_col = self._columns(league)
        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE guild_settings SET {message_col} = %s WHERE guild_id = %s",
                    (message_id, guild_id),
                )
                await conn.commit()

    @staticmethod
    def _all_games_final(embed):
        return bool(embed and embed.fields) and all(
            field.name.strip().lower() == "final" for field in embed.fields
        )

    @staticmethod
    def _score_count(embed):
        if not embed:
            return 0
        return sum(
            "final" in field.name.lower() or "live" in field.name.lower()
            for field in embed.fields
        )

    @staticmethod
    def _first_start_timestamp(embed):
        """Read scheduled UTC timestamps already included in both strategy embeds."""
        if not embed:
            return None
        starts = []
        for field in embed.fields:
            match = re.search(r"<t:(\d+):[tTfFdDR]>", field.name)
            if match:
                starts.append(int(match.group(1)))
        return min(starts) if starts else None

    @tasks.loop(time=time(hour=5, minute=30, tzinfo=ZoneInfo("America/New_York")))
    async def post_morning_schedule(self):
        if self._is_offseason():
            return
        today = datetime.now(self.eastern).date().isoformat()
        for league, strategy in self.strategies.items():
            if not self._league_is_active(league):
                continue
            try:
                targets = await self._configured_targets(league)
                if not targets:
                    continue
                embed = await strategy.build_schedule_embed(date_str=today)
                embed.title = f"Today's Games ({today})"
                for guild_id, channel_id, _ in targets:
                    channel = await self._get_channel(channel_id)
                    if channel is None:
                        continue
                    try:
                        message = await channel.send(embed=embed)
                        await self._save_message_id(league, guild_id, message.id)
                        self.next_updates.pop((league, guild_id, message.id), None)
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        print(f"{league.upper()} posting failed for guild {guild_id}: {exc}")
            except Exception:
                print(f"{league.upper()} morning posting error:\n{traceback.format_exc()}")

    @tasks.loop(minutes=1)
    async def live_update_loop(self):
        """Lightweight timer; no schedule API calls until the first game's start."""
        if self._is_offseason():
            return
        now = datetime.now(timezone.utc)
        for league, strategy in self.strategies.items():
            if not self._league_is_active(league):
                continue
            try:
                targets = await self._configured_targets(league, require_message=True)
                for guild_id, channel_id, message_id in targets:
                    channel = await self._get_channel(channel_id)
                    if channel is None:
                        continue
                    try:
                        message = await channel.fetch_message(message_id)
                    except discord.NotFound:
                        await self._save_message_id(league, guild_id, None)
                        continue
                    except (discord.Forbidden, discord.HTTPException):
                        continue

                    # The stored message is the active scoreboard until the next
                    # morning post replaces its ID, even when games run past midnight.
                    posted_date = message.created_at.astimezone(self.eastern).date()
                    eastern_now = now.astimezone(self.eastern)
                    age_days = (eastern_now.date() - posted_date).days
                    if age_days < 0 or age_days > 1:
                        continue
                    # Do not resume a previous day's unfinished scoreboard after
                    # the next morning's posting window has passed.
                    if age_days == 1 and eastern_now.time() >= time(5, 30):
                        continue
                    old_embed = message.embeds[0] if message.embeds else None
                    if self._all_games_final(old_embed):
                        continue
                    first_start = self._first_start_timestamp(old_embed)
                    if first_start is None:
                        # No timestamp available: do not guess a game start.
                        # For unknown/TBD start times, fall back to a 5-minute
                        # refresh only if the existing embed already shows live results.
                        if self._score_count(old_embed) == 0:
                            continue
                        first_start = 0
                    if now.timestamp() < first_start:
                        continue

                    key = (league, guild_id, message_id)
                    next_due = self.next_updates.get(key, 0)
                    if now.timestamp() < next_due:
                        continue
                    self.next_updates[key] = now.timestamp() + 300

                    try:
                        embed = await strategy.build_schedule_embed(date_str=posted_date.isoformat())
                        embed.title = f"Today's Games ({posted_date.isoformat()})"
                        # Keep already-final games final if a feed briefly returns
                        # stale scheduled/live data. Fields retain game order.
                        if old_embed and len(old_embed.fields) == len(embed.fields):
                            for index, old_field in enumerate(old_embed.fields):
                                new_field = embed.fields[index]
                                old_state = old_field.name.strip().lower()
                                new_state = new_field.name.strip().lower()
                                if old_state == "final" and new_state != "final":
                                    embed.set_field_at(
                                        index, name=old_field.name,
                                        value=old_field.value,
                                        inline=old_field.inline,
                                    )
                                elif ("live" in old_state or old_state == "final") and (
                                    "live" not in new_state and new_state != "final"
                                ):
                                    embed.set_field_at(
                                        index, name=old_field.name,
                                        value=old_field.value,
                                        inline=old_field.inline,
                                    )
                        elif self._score_count(old_embed) > 0 and self._score_count(embed) == 0:
                            print(f"{league.upper()}: ignored regressed scores for {posted_date}")
                            continue
                        if old_embed and old_embed.to_dict() == embed.to_dict():
                            continue
                        await message.edit(embed=embed)
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        print(f"{league.upper()} update failed for guild {guild_id}: {exc}")
                    except Exception:
                        print(f"{league.upper()} live update error:\n{traceback.format_exc()}")
            except Exception:
                print(f"{league.upper()} live loop error:\n{traceback.format_exc()}")

    @post_morning_schedule.before_loop
    @live_update_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailySchedules(bot))
