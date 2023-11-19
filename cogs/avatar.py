import discord
from discord.ext import commands
from discord import app_commands


class avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `avatar.py`")
    
    @app_commands.command(name="avatar", description="Get the bot's avatar!")
    async def avatar(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            msg = await interaction.original_response()
            embed = discord.Embed(title="Avatar", url="https://www.craiyon.com/image/srRf0fglTs-NwjWKUC3vNg", color=0x00ff00)
            embed.set_image(url=self.bot.user.avatar)
            await msg.edit(embed=embed)
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(avatar(bot))