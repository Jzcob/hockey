# base_strategy.py
from abc import ABC, abstractmethod
from datetime import datetime
import discord
import config

class LeagueStrategy(ABC):
    @abstractmethod
    async def get_today_games(self):
        pass

    @abstractmethod
    async def get_standings(self):
        pass

    @abstractmethod
    async def get_schedule(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_game_info(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_player_info(self, player_name):
        pass

    @abstractmethod
    async def get_team_info(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_all_teams(self):
        pass

    @abstractmethod
    async def get_tomorrow_games(self):
        pass

    @abstractmethod
    async def get_yesterday_games(self):
        pass

    @abstractmethod
    async def set_schedule_channel(self, channel_id):
        pass

    @abstractmethod
    async def remove_schedule_channel(self):
        pass

    @abstractmethod
    async def post_daily_schedule(self):
        pass

    @abstractmethod
    async def get_playoff_bracket(self):
        pass

    @abstractmethod
    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    # For grouped commands, the full name is needed
                    full_command_name = f"{interaction.command.parent.name} {interaction.command.name}"
                    await command_log_channel.send(f"`/{full_command_name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /{interaction.command.name}: {e}")
