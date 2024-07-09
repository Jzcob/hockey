import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback


class avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `avatar.py`")
    
    @app_commands.command(name="avatar", description="Get the avatar of a user! or the bot if no user is specified.")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/avatar` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            if user == None:
                await interaction.response.defer()
                msg = await interaction.original_response()
                embed = discord.Embed(title="Avatar", url="https://www.craiyon.com", color=0x00ff00)
                embed.set_image(url=self.bot.user.avatar)
                embed.set_footer(text=f"{config.footer}")
                await msg.edit(embed=embed)
            else:
                await interaction.response.defer()
                msg = await interaction.original_response()
                embed = discord.Embed(title="Avatar", url=user.avatar, color=0x00ff00)
                embed.set_image(url=user.avatar)
                embed.set_footer(text=f"{config.footer}")
                await msg.edit(embed=embed)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
    
async def setup(bot):
    await bot.add_cog(avatar(bot))