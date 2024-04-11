import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import config
import traceback

class team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `team.py`")
    
    @app_commands.command(name="team", description="Get the information for a team! (e.g. BOS, NYR, etc.)")
    async def team(self, interaction: discord.Interaction, abbreviation: str):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/team` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
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
                "SEA": "Seattle Kraken",
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
                return await msg.edit("Please enter a valid team abbreviation. e.g. `/team BOS`\n`/teams` to view the full list of teams!", ephemeral=True)
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
                        embed = discord.Embed(description=f"**{confrence} confrence & {division} division**", color=config.color)
                        if teamAbbreviation == "ANA":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.anahiem_ducks_emoji}"
                        elif teamAbbreviation == "ARI":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.arizona_coyotes_emoji}"
                        elif teamAbbreviation == "BOS":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.boston_bruins_emoji}"
                        elif teamAbbreviation == "BUF":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.buffalo_sabres_emoji}"
                        elif teamAbbreviation == "CGY":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.calgary_flames_emoji}"
                        elif teamAbbreviation == "CAR":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.carolina_hurricanes_emoji}"
                        elif teamAbbreviation == "CHI":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.chicago_blackhawks_emoji}"
                        elif teamAbbreviation == "COL":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.colorado_avalanche_emoji}"
                        elif teamAbbreviation == "CBJ":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.columbus_blue_jackets_emoji}"
                        elif teamAbbreviation == "DAL":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.dallas_stars_emoji}"
                        elif teamAbbreviation == "DET":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.detroit_red_wings_emoji}"
                        elif teamAbbreviation == "EDM":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.edmonton_oilers_emoji}"
                        elif teamAbbreviation == "FLA":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.florida_panthers_emoji}"
                        elif teamAbbreviation == "LAK":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.los_angeles_kings_emoji}"
                        elif teamAbbreviation == "MIN":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.minnesota_wild_emoji}"
                        elif teamAbbreviation == "MTL":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.montreal_canadiens_emoji}"
                        elif teamAbbreviation == "NSH":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.nashville_predators_emoji}"
                        elif teamAbbreviation == "NJD":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.new_jersey_devils_emoji}"
                        elif teamAbbreviation == "NYI":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.new_york_islanders_emoji}"
                        elif teamAbbreviation == "NYR":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.new_york_rangers_emoji}"
                        elif teamAbbreviation == "OTT":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.ottawa_senators_emoji}"
                        elif teamAbbreviation == "PHI":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.philadelphia_flyers_emoji}"
                        elif teamAbbreviation == "PIT":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.pittsburgh_penguins_emoji}"
                        elif teamAbbreviation == "SEA":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.seattle_kraken_emoji}"
                        elif teamAbbreviation == "SJS":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.san_jose_sharks_emoji}"
                        elif teamAbbreviation == "STL":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.st_louis_blues_emoji}"
                        elif teamAbbreviation == "TBL":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.tampa_bay_lightning_emoji}"
                        elif teamAbbreviation == "TOR":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.toronto_maple_leafs_emoji}"
                        elif teamAbbreviation == "VAN":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.vancouver_canucks_emoji}"
                        elif teamAbbreviation == "VGK":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.vegas_golden_knights_emoji}"
                        elif teamAbbreviation == "WSH":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.washington_capitals_emoji}"
                        elif teamAbbreviation == "WPG":
                            embed.title = f"{teamName} ({teamAbbreviation}) {config.winnipeg_jets_emoji}"

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
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)


    
async def setup(bot):
    await bot.add_cog(team(bot))