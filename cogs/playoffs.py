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
            embed = discord.Embed(title="NHL Playoff Series", color=0x00ff00)
            embed.add_field(name="Round 1", value="**Eastern**\nFlorida Panthers vs Tampa Bay Lightning\nBoston Bruins vs Toronto Maple Leafs"+
                            "\nNew York Rangers vs Washing Capitals\nCarolina Hurricanes vs New York Islanders\n**Western**\nDallas Stars vs Vegas Golden Knights\n"+
                            "Winnipeg Jets vs Colorado Avalanche\nVancover Canucks vs Nashville Predators\n Edmonton Oilers vs Los Angeles Kings", inline=False)
            embed.add_field(name="Round 2", value="**Eastern**\nTBD vs TBD\n**Western**\nTBD vs TBD", inline=False)
            embed.add_field(name="Conference Finals", value="**Eastern**\nTBD vs TBD\n**Western**\nTBD vs TBD", inline=False)
            embed.add_field(name="Stanley Cup Finals", value="TBD vs TBD", inline=False)
                
            await interaction.response.send_message(embed=embed)
        except:
            error_channel = self.bot.get_channel(920797181034778655)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(playoffs(bot))