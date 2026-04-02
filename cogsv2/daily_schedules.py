# The day's schedules that get posted to the schedule channel every morning at 5:30 AM EST, 
# no matter the league. Uses the same strategy pattern as the other commands to get the schedules for each league.

import discord
from discord.ext import commands, tasks
from strategies.base_strategy import BaseStrategy
from strategies.nhl_strategy import NHLStrategy
from strategies.ahl_strategy import AHLStrategy
from strategies.pwhl_strategy import PWHLStrategy
from strategies.kwl_strategy import KWLStrategy
import config
from datetime import datetime, time, timedelta
import asyncio
import traceback
import aiomysql

class DailySchedules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategies = {
            "nhl": NHLStrategy(bot),
            "ahl": AHLStrategy(bot),
            "pwhl": PWHLStrategy(bot),
            "kwl": KWLStrategy(bot)
        }
        self.schedule_channel_id = config.schedule_channel
        self.post_schedules.start()  # Start the background task

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `daily_schedules.py`")

    @tasks.loop(minutes=1)
    async def post_schedules(self):
        now = datetime.now()
        target_time = time(5, 30)  # 5:30 AM EST
        if now.time() >= target_time and now.time() < (datetime.combine(now.date(), target_time) + timedelta(minutes=1)).time():
            schedule_channel = self.bot.get_channel(self.schedule_channel_id)
            if schedule_channel:
                for league, strategy in self.strategies.items():
                    try:
                        await strategy.post_daily_schedule(schedule_channel)
                    except Exception as e:
                        print(f"Error posting {league} schedule: {e}")
                        traceback.print_exc()
            else:
                print(f"Schedule channel with ID {self.schedule_channel_id} not found.")
    