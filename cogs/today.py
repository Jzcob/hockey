import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import config
from datetime import datetime, timedelta
import pytz

def strings(awayAbbreviation, homeAbbreviation, home, away):
    if awayAbbreviation == "ANA":
        awayString = f"{config.anahiem_ducks_emoji} {away}"
    elif awayAbbreviation == "ARI":
        awayString = f"{config.arizona_coyotes_emoji} {away}"
    elif awayAbbreviation == "BOS":
        awayString = f"{config.boston_bruins_emoji} {away}"
    elif awayAbbreviation == "BUF":
        awayString = f"{config.buffalo_sabres_emoji} {away}"
    elif awayAbbreviation == "CGY":
        awayString = f"{config.calgary_flames_emoji} {away}"
    elif awayAbbreviation == "CAR":
        awayString = f"{config.carolina_hurricanes_emoji} {away}"
    elif awayAbbreviation == "CHI":
        awayString = f"{config.chicago_blackhawks_emoji} {away}"
    elif awayAbbreviation == "COL":
        awayString = f"{config.colorado_avalanche_emoji} {away}"
    elif awayAbbreviation == "CBJ":
        awayString = f"{config.columbus_blue_jackets_emoji} {away}"
    elif awayAbbreviation == "DAL":
        awayString = f"{config.dallas_stars_emoji} {away}"
    elif awayAbbreviation == "DET":
        awayString = f"{config.detroit_red_wings_emoji} {away}"
    elif awayAbbreviation == "EDM":
        awayString = f"{config.edmonton_oilers_emoji} {away}"
    elif awayAbbreviation == "FLA":
        awayString = f"{config.florida_panthers_emoji} {away}"
    elif awayAbbreviation == "LAK":
        awayString = f"{config.los_angeles_kings_emoji} {away}"
    elif awayAbbreviation == "MIN":
        awayString = f"{config.minnesota_wild_emoji} {away}"
    elif awayAbbreviation == "MTL":
        awayString = f"{config.montreal_canadiens_emoji} {away}"
    elif awayAbbreviation == "NSH":
        awayString = f"{config.nashville_predators_emoji} {away}"
    elif awayAbbreviation == "NJD":
        awayString = f"{config.new_jersey_devils_emoji} {away}"
    elif awayAbbreviation == "NYI":
        awayString = f"{config.new_york_islanders_emoji} {away}"
    elif awayAbbreviation == "NYR":
        awayString = f"{config.new_york_rangers_emoji} {away}"
    elif awayAbbreviation == "OTT":
        awayString = f"{config.ottawa_senators_emoji} {away}"
    elif awayAbbreviation == "PHI":
        awayString = f"{config.philadelphia_flyers_emoji} {away}"
    elif awayAbbreviation == "PIT":
        awayString = f"{config.pittsburgh_penguins_emoji} {away}"
    elif awayAbbreviation == "SJS":
        awayString = f"{config.san_jose_sharks_emoji} {away}"
    elif awayAbbreviation == "STL":
        awayString = f"{config.st_louis_blues_emoji} {away}"
    elif awayAbbreviation == "TBL":
        awayString = f"{config.tampa_bay_lightning_emoji} {away}"
    elif awayAbbreviation == "TOR":
        awayString = f"{config.toronto_maple_leafs_emoji} {away}"
    elif awayAbbreviation == "VAN":
        awayString = f"{config.vancouver_canucks_emoji} {away}"
    elif awayAbbreviation == "VGK":
        awayString = f"{config.vegas_golden_knights_emoji} {away}"
    elif awayAbbreviation == "WSH":
        awayString = f"{config.washington_capitals_emoji} {away}"
    elif awayAbbreviation == "WPG":
        awayString = f"{config.winnipeg_jets_emoji} {away}"
    else:
        awayString = f"{away}"
    if homeAbbreviation == "ANA":
        homeString = f"{home} {config.anahiem_ducks_emoji}"
    elif homeAbbreviation == "ARI":
        homeString = f"{home} {config.arizona_coyotes_emoji}"
    elif homeAbbreviation == "BOS":
        homeString = f"{home} {config.boston_bruins_emoji}"
    elif homeAbbreviation == "BUF":
        homeString = f"{home} {config.buffalo_sabres_emoji}"
    elif homeAbbreviation == "CGY":
        homeString = f"{home} {config.calgary_flames_emoji}"
    elif homeAbbreviation == "CAR":
        homeString = f"{home} {config.carolina_hurricanes_emoji}"
    elif homeAbbreviation == "CHI":
        homeString = f"{home} {config.chicago_blackhawks_emoji}"
    elif homeAbbreviation == "COL":
        homeString = f"{home} {config.colorado_avalanche_emoji}"
    elif homeAbbreviation == "CBJ":
        homeString = f"{home} {config.columbus_blue_jackets_emoji}"
    elif homeAbbreviation == "DAL":
        homeString = f"{home} {config.dallas_stars_emoji}"
    elif homeAbbreviation == "DET":
        homeString = f"{home} {config.detroit_red_wings_emoji}"
    elif homeAbbreviation == "EDM":
        homeString = f"{home} {config.edmonton_oilers_emoji}"
    elif homeAbbreviation == "FLA":
        homeString = f"{home} {config.florida_panthers_emoji}"
    elif homeAbbreviation == "LAK":
        homeString = f"{home} {config.los_angeles_kings_emoji}"
    elif homeAbbreviation == "MIN":
        homeString = f"{home} {config.minnesota_wild_emoji}"
    elif homeAbbreviation == "MTL":
        homeString = f"{home} {config.montreal_canadiens_emoji}"
    elif homeAbbreviation == "NSH":
        homeString = f"{home} {config.nashville_predators_emoji}"
    elif homeAbbreviation == "NJD":
        homeString = f"{home} {config.new_jersey_devils_emoji}"
    elif homeAbbreviation == "NYI":
        homeString = f"{home} {config.new_york_islanders_emoji}"
    elif homeAbbreviation == "NYR":
        homeString = f"{home} {config.new_york_rangers_emoji}"
    elif homeAbbreviation == "OTT":
        homeString = f"{home} {config.ottawa_senators_emoji}"
    elif homeAbbreviation == "PHI":
        homeString = f"{home} {config.philadelphia_flyers_emoji}"
    elif homeAbbreviation == "PIT":
        homeString = f"{home} {config.pittsburgh_penguins_emoji}"
    elif homeAbbreviation == "SJS":
        homeString = f"{home} {config.san_jose_sharks_emoji}"
    elif homeAbbreviation == "STL":
        homeString = f"{home} {config.st_louis_blues_emoji}"
    elif homeAbbreviation == "TBL":
        homeString = f"{home} {config.tampa_bay_lightning_emoji}"
    elif homeAbbreviation == "TOR":
        homeString = f"{home} {config.toronto_maple_leafs_emoji}"
    elif homeAbbreviation == "VAN":
        homeString = f"{home} {config.vancouver_canucks_emoji}"
    elif homeAbbreviation == "VGK":
        homeString = f"{home} {config.vegas_golden_knights_emoji}"
    elif homeAbbreviation == "WSH":
        homeString = f"{home} {config.washington_capitals_emoji}"
    elif homeAbbreviation == "WPG":
        homeString = f"{home} {config.winnipeg_jets_emoji}"
    else:
        homeString = f"{home}"
    
    return awayString, homeString

class today(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `today.py`")
    
    @app_commands.command(name="today", description="Get today's schedule!")
    async def team(self, interaction: discord.Interaction):
        try:
            hawaii = pytz.timezone('US/Hawaii')
            dt = datetime.now(hawaii)
            today = dt.strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{today}"
            await interaction.response.defer()
            msg = await interaction.original_response()
            r = requests.get(url)
            global data
            data = r.json()
        except Exception as e:
            print(e)
        try:
            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games", description=f"Total games today: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)
            for i in range(len(games)):
                game = data["gameWeek"][0]["games"][i]
                gameState = game["gameState"]
                gameID = game['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                startTime = game["startTimeUTC"]
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime - timedelta(hours=5)
                startTime = startTime.strftime('%I:%M %p')
                try:
                    if gameState == "FUT":
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        homeAbbreviation = game2["homeTeam"]["abbrev"]
                        awayAbbreviation = game2["awayTeam"]["abbrev"]
                        awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                        embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
                    elif gameState == "FINAL" or gameState == "OFF":
                        homeScore = game2['boxscore']['linescore']['totals']['home']
                        awayScore = game2['boxscore']['linescore']['totals']['away']
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        homeAbbreviation = game2["homeTeam"]["abbrev"]
                        awayAbbreviation = game2["awayTeam"]["abbrev"]
                        awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                        embed.add_field(name=f"Final!", value=f"\n{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\n", inline=False)
                        embed.set_footer(text=f"ID: {gameID}")
                    elif gameState == "LIVE":
                        homeScore = game2['boxscore']['linescore']['totals']['home']
                        awayScore = game2['boxscore']['linescore']['totals']['away']
                        clock = game2['clock']['timeRemaining']
                        clockRunning = game2['clock']['running']
                        clockIntermission = game2['clock']['inIntermission']
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        homeAbbreviation = game2["homeTeam"]["abbrev"]
                        awayAbbreviation = game2["awayTeam"]["abbrev"]
                        awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                        if clockRunning == True:
                            embed.add_field(name=f"LIVE", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\nTime: {clock}", inline=False)
                        if clockIntermission == True:
                            embed.add_field(name=f"Intermission!", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}", inline=False)
                    else:
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        homeAbbreviation = game2["homeTeam"]["abbrev"]
                        awayAbbreviation = game2["awayTeam"]["abbrev"]
                        awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                        embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
                except:
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
            return await msg.edit(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await interaction.response.send_message("Error getting today's schedule! Message has been sent to Bot Developers", ephemeral=True)
            embed = discord.Embed(title="Error with `/today`", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            await error_channel.send(embed=embed)
            return


async def setup(bot):
    await bot.add_cog(today(bot))