import discord
import config
from datetime import datetime

# We remove ABC and abstractmethod to avoid metaclass conflicts with GroupCog
class LeagueStrategy:
    async def get_today_games(self, interaction: discord.Interaction):
        pass

    async def get_standings(self, interaction: discord.Interaction):
        pass

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str):
        pass

    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str):
        pass

    async def get_player_info(self, interaction: discord.Interaction, player_name: str):
        pass

    async def get_team_info(self, interaction: discord.Interaction, team_abbreviation: str):
        pass

    async def get_all_teams(self, interaction: discord.Interaction):
        pass

    async def get_tomorrow_games(self, interaction: discord.Interaction):
        pass

    async def get_yesterday_games(self, interaction: discord.Interaction):
        pass

    async def set_schedule_channel(self, interaction: discord.Interaction, channel_id: int):
        pass

    async def remove_schedule_channel(self, interaction: discord.Interaction):
        pass

    async def post_daily_schedule(self, channel: discord.TextChannel):
        pass

    async def get_playoff_bracket(self, interaction: discord.Interaction):
        pass

    async def update_live_scores(self):
        pass

# Static logging helper
def log_command(bot, interaction: discord.Interaction, custom_path=None):
    if config.command_log_bool:
        try:
            command_log_channel = bot.get_channel(config.command_log)
            if command_log_channel:
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                # Handle GroupCog naming
                if not custom_path:
                    try:
                        custom_path = f"{interaction.command.parent.name} {interaction.command.name}"
                    except:
                        custom_path = interaction.command.name
                
                # Run the send as a background task so it doesn't slow the bot down
                bot.loop.create_task(command_log_channel.send(
                    f"`/{custom_path}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                ))
        except Exception as e:
            print(f"Command logging failed: {e}")