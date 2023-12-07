import discord
from discord.ext import commands
from discord import app_commands
import config


class avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `avatar.py`")
    
    @app_commands.command(name="avatar", description="Get the avatar of a user! or the bot if no user is specified.")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            if user == None:
                await interaction.response.defer()
                msg = await interaction.original_response()
                embed = discord.Embed(title="Avatar", url="https://www.craiyon.com/image/srRf0fglTs-NwjWKUC3vNg", color=0x00ff00)
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
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(avatar(bot))