import discord
from discord import app_commands
from discord.ext import commands
import traceback
import config

class playoffs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `playoffs.py`")

    @app_commands.command(name="series", description="Get who is playing who!")
    async def series(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/series` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            embed = discord.Embed(title="NHL Playoff Series", color=0x00ff00, url="https://www.nhl.com/playoffs/2024/bracket")
            embed.add_field(name="Round 1", value="**Eastern**\nFlorida Panthers vs Tampa Bay Lightning **(4-1)**\nBoston Bruins vs Toronto Maple Leafs **(4-3)**"+
                            "\nNew York Rangers vs Washing Capitals **(4-0)**\nCarolina Hurricanes vs New York Islanders **(4-1)**\n**Western**\nDallas Stars vs Vegas Golden Knights **(4-3)**\n"+
                            "Winnipeg Jets vs Colorado Avalanche **(1-4)**\nVancover Canucks vs Nashville Predators **(4-2)**\n Edmonton Oilers vs Los Angeles Kings **(4-1)**", inline=False)
            embed.add_field(name="Round 2", value="**Eastern**\nFlordia Panthers vs Boston Bruins **(4-2)**\nNew York Rangers vs Carolina Hurricanes **(4-2)**\n**Western**\nDallas Stars vs Colorado Avalanche **(3-2)**\n"+
                            "Vancover Canucks vs Edmonton Oilers **(3-2)**", inline=False)
            embed.add_field(name="Conference Finals", value="**Eastern**\nNew York Rangers vs Flordia Panthers\n**Western**\nTBD vs TBD", inline=False)
            embed.add_field(name="Stanley Cup Finals", value="TBD vs TBD", inline=False)
                
            await interaction.response.send_message(embed=embed)
        except:
            error_channel = self.bot.get_channel(920797181034778655)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(playoffs(bot))