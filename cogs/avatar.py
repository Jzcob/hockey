import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback
from datetime import datetime


class avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `avatar.py`")
    
    @app_commands.command(name="avatar", description="Get the avatar of a user! Or the bot if no user is specified.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(
                    f"`/avatar` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                )
            except Exception as e:
                print(f"Logging failed: {e}")
        
        try:
            await interaction.response.defer()
            target_user = user or self.bot.user
            avatar_url = target_user.display_avatar.url

            embed = discord.Embed(
                title=f"{target_user.name}'s Avatar",
                color=0x00ff00
            )
            embed.set_image(url=avatar_url)
            embed.set_footer(text=config.footer)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send(
                "An error occurred while fetching the avatar. The issue has been reported to the bot developers.",
                ephemeral=True
            )

    
async def setup(bot):
    await bot.add_cog(avatar(bot))