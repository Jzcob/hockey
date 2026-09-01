import discord
from discord.ext import commands, tasks
from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy
# from strategies.ahl_strategy import AHLStrategy
import config
from datetime import datetime, time, timedelta
import pytz
import traceback

class DailySchedules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Mapping leagues to their strategy logic
        self.strategies = {
            "nhl": NHL(bot),
            "pwhl": PWHLStrategy(bot),
            # "ahl": AHLStrategy(bot),
        }
        
        self.schedule_channel_id = 1
        self.eastern = pytz.timezone("US/Eastern")
        
        # Start the loops
        self.post_morning_schedule.start()
        self.live_update_loop.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `daily_schedules.py` with Strategy Pattern")

    # 1. THE MORNING POST (5:30 AM EST)
    # Using the time parameter is much more efficient than checking every minute
    @tasks.loop(time=time(hour=5, minute=30, tzinfo=pytz.timezone("US/Eastern")))
    async def post_morning_schedule(self):
        print("Running morning schedule post...")
        channel = self.bot.get_channel(self.schedule_channel_id)
        if not channel: return

        for league, strategy in self.strategies.items():
            try:
                # Every strategy MUST implement this in base_strategy.py
                await strategy.post_daily_schedule(channel)
            except Exception as e:
                print(f"Error posting {league} morning schedule: {e}")

    # 2. THE LIVE UPDATE LOOP (Every 5 Minutes)
    @tasks.loop(minutes=5)
    async def live_update_loop(self):
        """
        Iterates through active strategies and updates 
        their existing schedule messages if games are live.
        """
        for league, strategy in self.strategies.items():
            try:
                # We delegate the "Should I update?" logic to the strategy itself
                # The strategy should check its own database/cache for the message_id
                await strategy.update_live_scores()
            except Exception as e:
                print(f"Error in live update for {league}: {e}")

    @post_morning_schedule.before_loop
    @live_update_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DailySchedules(bot), guilds=[discord.Object(id=config.hockey_discord_server)])