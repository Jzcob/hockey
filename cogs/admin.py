import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import config
import traceback

watching = discord.CustomActivity(name="👀 New Feature Coming?")

#hello world
class announcement(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `announcement.py`")
        await self.bot.change_presence(activity=watching)
    
    @app_commands.command(name="dev-mode", description="Toggles dev mode!")
    async def dev_mode(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/dev-mode` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}` \n---")
        try:
            if interaction.user.id == 920797181034778655:
                if config.dev_mode == False:
                    config.dev_mode = True
                    return await interaction.response.send_message("Dev mode is now enabled!")
                else:
                    config.dev_mode = False
                    return await interaction.response.send_message("Dev mode is now disabled!")
            else:
                return await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")

    @app_commands.command(name="send", description="Make the bot say something.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def say(self, interaction: discord.Interaction, *, message: str, channel: discord.TextChannel = None):
        try:
            if channel == None:
                channel = interaction.channel
                await channel.send(message)
                await interaction.response.send_message(f"Sent message to {channel.mention}", ephemeral=True)
            else:
                await channel.send(message)
                await interaction.response.send_message(f"Sent message to {channel.mention}", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")

async def setup(bot):
    await bot.add_cog(announcement(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
