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
    @app_commands.describe(conference="The conference the series is in.")
    @app_commands.choices(conference=[
        app_commands.Choice(name="Eastern", value="eastern"),
        app_commands.Choice(name="Western", value="western")
        ])
    async def series(self, interaction: discord.Interaction, conference: discord.app_commands.Choice[str]):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            import datetime
            await command_log_channel.send(f"`/series` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            embed = discord.Embed(title="NHL Playoff Series", color=0x00ff00)
            if conference.value == "eastern":
                embed.add_field(name="FLA vs TBL", value="Florida Panthers vs Tampa Bay Lightning", inline=False)
                embed.add_field(name="BOS vs TOR", value="Boston Bruins vs Toronto Maple Leafs", inline=False)
                embed.add_field(name="NYR vs WSH", value="New York Rangers vs Washington Capitals", inline=False)
                embed.add_field(name="CAR vs NYI", value="Carolina Hurricanes vs New York Islanders", inline=False)
            else:
                embed.add_field(name="DAL vs VGK", value="Dallas Stars vs Vegas Golden Knights", inline=False)
                embed.add_field(name="WPG vs COL", value="Winnipeg Jets vs Colorado Avalanche", inline=False)
                embed.add_field(name="VAN vs NSH", value="Vancouver Canucks vs Nashville Predators", inline=False)
                embed.add_field(name="EDM vs LAK", value="Edmonton Oilers vs Los Angeles Kings", inline=False)
            await interaction.response.send_message(embed=embed)
        except:
            error_channel = self.bot.get_channel(920797181034778655)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(playoffs(bot))