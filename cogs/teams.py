import discord
from discord.ext import commands
from discord import app_commands
import config

class teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `teams.py`")
    
    @app_commands.command(name="teams", description="Get the teams in the league!")
    async def teams(self, interaction: discord.Interaction):
        teams = {
            "ANA": "Anaheim Ducks",
            "ARI": "Arizona Coyotes",
            "BOS": "Boston Bruins",
            "BUF": "Buffalo Sabres",
            "CGY": "Calgary Flames",
            "CAR": "Carolina Hurricanes",
            "CHI": "Chicago Blackhawks",
            "COL": "Colorado Avalanche",
            "CBJ": "Columbus Blue Jackets",
            "DAL": "Dallas Stars",
            "DET": "Detroit Red Wings",
            "EDM": "Edmonton Oilers",
            "FLA": "Florida Panthers",
            "LAK": "Los Angeles Kings",
            "MIN": "Minnesota Wild",
            "MTL": "Montreal Canadiens",
            "NSH": "Nashville Predators",
            "NJD": "New Jersey Devils",
            "NYI": "New York Islanders",
            "NYR": "New York Rangers",
            "OTT": "Ottawa Senators",
            "PHI": "Philadelphia Flyers",
            "PIT": "Pittsburgh Penguins",
            "SJS": "San Jose Sharks",
            "STL": "St. Louis Blues",
            "TBL": "Tampa Bay Lightning",
            "TOR": "Toronto Maple Leafs",
            "VAN": "Vancouver Canucks",
            "VGK": "Vegas Golden Knights",
            "WSH": "Washington Capitals",
            "WPG": "Winnipeg Jets"
        }
    
        try:
            embed = discord.Embed(title="Teams", description=f"Here are the teams in the league!", color=0x00ff00)
            for team in teams:
                embed.add_field(name=team, value=teams[team], inline=False)
            embed.set_footer(text=config.footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await interaction.response.send_message("Error getting teams! Message has been sent to Bot Developers", ephemeral=True)
            embed = discord.Embed(title="Error with `/teams`", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Team", value=team)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            await error_channel.send(embed=embed)
            return

async def setup(bot):
    await bot.add_cog(teams(bot))