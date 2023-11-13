import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config

class team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `team.py`")
    
    @app_commands.command(name="team", description="Get the schedule for the week for a team! (e.g. BOS, NYR, etc.)")
    async def team(self, interaction: discord.Interaction, abbreviation: str):
        try:
            await interaction.response.defer()
            msg = await interaction.original_response()
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
            if abbreviation.upper() in teams:
                team = abbreviation.upper()
                team = teams[team]
            else:    
                await interaction.response.send_message("Please enter a valid team abbreviation. e.g. `/team BOS`", ephemeral=True)
                return
            today = datetime.today().strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/standings/{today}"
            r = requests.get(url)
            data = r.json()
            for i in range(len(data['standings'])):
                tN = data['standings'][i]['teamName']['default']
                try:
                    if tN == team:
                        wins = data['standings'][i]['wins']
                        losses = data['standings'][i]['losses']
                        otLosses = data['standings'][i]['otLosses']
                        points = data['standings'][i]['points']
                        teamName = data['standings'][i]['teamName']['default']
                        teamAbbreviation = data['standings'][i]['teamAbbrev']['default']
                        confrence = data['standings'][i]['conferenceName']
                        division = data['standings'][i]['divisionName']
                        goalsFor = data['standings'][i]['goalFor']
                        goalsAgainst = data['standings'][i]['goalAgainst']
                        gamesPlayed = data['standings'][i]['gamesPlayed']
                        goalDifference = data['standings'][i]['goalDifferential']
                        streakCode = data['standings'][i]['streakCode']
                        streakNumber = data['standings'][i]['streakCount']
                        embed = discord.Embed(title=f"{teamName} ({teamAbbreviation})", description=f"**{confrence} confrence & {division} division**", color=config.color)
                        embed.add_field(name="Wins", value=wins)
                        embed.add_field(name="Losses", value=losses)
                        embed.add_field(name="OT Losses", value=otLosses)
                        embed.add_field(name="Goals For", value=goalsFor)
                        embed.add_field(name="Goals Against", value=goalsAgainst)
                        embed.add_field(name="Goal Differencial", value=goalDifference)
                        embed.add_field(name="Games Played", value=gamesPlayed)
                        embed.add_field(name="Points", value=points)
                        embed.add_field(name="Streak", value=f"{streakCode} {streakNumber}")
                        embed.set_footer(text=config.footer)
                except Exception as e:
                    print(e)
            await msg.edit(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await interaction.response.send_message("Error getting team! Message has been sent to Bot Developers", ephemeral=True)
            embed = discord.Embed(title="Error with `/team`", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Team", value=team)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.mention)
            await error_channel.send(embed=embed)


    
async def setup(bot):
    await bot.add_cog(team(bot))