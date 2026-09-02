import discord
from discord.ext import commands, tasks
from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy
import config
from datetime import datetime, time, timedelta
import pytz
import traceback

class DailySchedules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategies = {
            "nhl": NHL(bot),
            "pwhl": PWHLStrategy(bot),
        }
        
        self.schedule_channel_id = getattr(config, "schedule_channel_id", 1)
        self.eastern = pytz.timezone("US/Eastern")
        
        # Start the loops
        self.post_morning_schedule.start()
        self.live_update_loop.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `daily_schedules.py` with Strategy Pattern")

    # Helper check to disable functionality until September 20th, 2026
    def _is_offseason(self) -> bool:
        current_date = datetime.now(self.eastern).date()
        season_start_threshold = datetime(2026, 9, 20).date()
        return current_date < season_start_threshold

    # 1. THE MORNING POST (5:30 AM EST)
    @tasks.loop(time=time(hour=5, minute=30, tzinfo=pytz.timezone("US/Eastern")))
    async def post_morning_schedule(self):
        if self._is_offseason():
            return  # Suppress posts entirely during the offseason until September 20th

        print("Running morning schedule post...")
        channel = self.bot.get_channel(self.schedule_channel_id)
        if not channel: return

        for league, strategy in self.strategies.items():
            try:
                if hasattr(strategy, "post_daily_schedule"):
                    await strategy.post_daily_schedule(channel)
            except Exception as e:
                print(f"Error posting {league} morning schedule: {e}")

    # 2. THE LIVE UPDATE LOOP (Every 5 Minutes)
    @tasks.loop(minutes=5)
    async def live_update_loop(self):
        if self._is_offseason():
            return  # Skip live updates during the offseason

        for league, strategy in self.strategies.items():
            try:
                if hasattr(strategy, "update_live_scores"):
                    await strategy.update_live_scores()
            except Exception as e:
                # Suppress missing attribute errors quietly, log other exceptions if needed
                if "has no attribute 'update_live_scores'" not in str(e):
                    print(f"Error in live update for {league}: {e}")

    @post_morning_schedule.before_loop
    @live_update_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DailySchedules(bot), guilds=[discord.Object(id=config.hockey_discord_server)])