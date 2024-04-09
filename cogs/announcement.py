import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import json
import config
import traceback
watching = discord.Activity(name="Hockey!", type=discord.ActivityType.watching)

#hello world
class announcement(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `announcement.py`")
        await self.bot.change_presence(activity=watching)
    
    @app_commands.command(name="announce", description="Sends an announcement to every server the bot is in!")
    async def announcement(self, interaction: discord.Interaction, title: str, description: str):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/announce` used by {interaction.user.mention} in {interaction.guild.name} at {datetime.now()}\n---")
        try:
            if interaction.user.id == 920797181034778655:
                guilds = self.bot.guilds
                for guild in guilds:
                    try:
                        embed = discord.Embed(title=title, description=description, color=config.color)
                        embed.set_author(icon_url=interaction.user.avatar.url, name="Hockey Bot Announcement")
                        try:
                            await guild.public_updates_channel.send(embed=embed)
                        except:
                            await guild.system_channel.send(embed=embed)
                    except:
                        pass
                return await interaction.response.send_message(f"Sent announcement!\n\n**Title:** " + title + "\n**Description:** " + description)
            else:
                return await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")

async def setup(bot):
    await bot.add_cog(announcement(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
