import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import pytz
import traceback

gameIDs = {}

gameButton = Button(label="Game Reports", style=discord.ButtonStyle.success)

async def gameButton_callback(interaction):
    try:
        if interaction.user.id in gameIDs:
            url = f"https://api-web.nhle.com/v1/gamecenter/{gameIDs[interaction.user.id]}/boxscore"
            response = requests.get(url)
            data = response.json()
            home = data['homeTeam']['name']['default']
            away = data['awayTeam']['name']['default']
            gameReports = data['boxscore']['gameReports']
            gameSummary = gameReports['gameSummary']
            gameEvents = gameReports['eventSummary']
            playByPlay = gameReports['playByPlay']
            faceOffSummary = gameReports['faceoffSummary']
            faceOffComparison = gameReports['faceoffComparison']
            rosters = gameReports['rosters']
            shotSummary = gameReports['shotSummary']
            toiAway = gameReports['toiAway']
            toiHome = gameReports['toiHome']
            embed = discord.Embed(title=f"Game Reports for {away} @ {home}", color=config.color)
            embed.add_field(name="Game Summary", value=gameSummary, inline=False)
            embed.add_field(name="Game Events", value=gameEvents, inline=False)
            embed.add_field(name="Play By Play", value=playByPlay, inline=False)
            embed.add_field(name="Faceoff Summary", value=faceOffSummary, inline=False)
            embed.add_field(name="Faceoff Comparison", value=faceOffComparison, inline=False)
            embed.add_field(name="Rosters", value=rosters, inline=False)
            embed.add_field(name="Shot Summary", value=shotSummary, inline=False)
            embed.add_field(name="Time on Ice Away", value=toiAway, inline=False)
            embed.add_field(name="Time on Ice Home", value=toiHome, inline=False)
            embed.set_footer(text=config.footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            gameIDs.pop(interaction.user.id)
        else:
            await interaction.response.send_message("Please use the `/game` command first!", ephemeral=True)
    except Exception as e:
        error_channel = interaction.bot.get_channel(config.error_channel)
        string = f"{traceback.format_exc()}"
        await error_channel.send(f"```{string}```")

class game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `game.py`")
    
    @app_commands.command(name="game", description="Check the information for a game today! (e.g. BOS, NYR, etc.)")
    async def game(self, interaction: discord.Interaction, abbreviation: str):
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
                "SEA": "Seattle Kraken",   
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
                await msg.edit(content="Please enter a valid team abbreviation. e.g. `/game BOS`")
                return
            view = View()
            view.add_item(gameButton)
            hawaii = pytz.timezone('US/Hawaii')
            dt = datetime.now(hawaii)
            today = dt.strftime('%Y-%m-%d')
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/{today}'
            response = requests.get(url)
            data = response.json()
            games = data['games']
            if len(games) == 0:
                return await msg.edit(content=f"**{team}** do not play today!")
            for i in range(len(games)):
                if f"{games[i]['gameDate']}" == f"{today}":
                    game = games[i]
                    gameID = game['id']
                    gameIDs[interaction.user.id] = gameID
                    break
                else:
                    return await msg.edit(content=f"**{team}** do not play today!")
            url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
            response2 = requests.get(url2)
            data2 = response2.json()
            home = data2['homeTeam']['name']['default']
            away = data2['awayTeam']['name']['default']
            tvBroadcasts= data2['tvBroadcasts']
            networks = ""
            for i in range(len(tvBroadcasts)):
                network = tvBroadcasts[i]['network']
                countryCode = tvBroadcasts[i]['countryCode']
                if countryCode == "US" and network == "NESN" and interaction.user.id == config.jacob:
                    networks += f"{network} ({countryCode}) :star:\n "
                else: 
                    networks += f"{network} ({countryCode})\n"
            if game['gameState'] == "FUT" or game['gameState'] == "PRE":
                startTime = data2["startTimeUTC"]
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime - timedelta(hours=5)
                startTime = startTime.strftime('%I:%M %p')
                embed = discord.Embed(title=f"{away} @ {home}", description=f"Game is scheduled! for {startTime}", color=config.color)
                embed.add_field(name="TV Broadcast", value=f"{networks}", inline=False)
                embed.add_field(name="Game ID", value=gameID, inline=False)
                embed.set_footer(text=config.footer)
                await msg.edit(embed=embed)
                return
            homeScore = data2['boxscore']['linescore']['totals']['home']
            awayScore = data2['boxscore']['linescore']['totals']['away']
            clock = data2['clock']['timeRemaining']
            clockRunning = data2['clock']['running']
            clockIntermission = data2['clock']['inIntermission']
            shotsByPeriod = data2['boxscore']['shotsByPeriod']
            homeShots = 0
            awayShots = 0
            if game['gameState'] == "FINAL" or game['gameState'] == "OFF":
                embed = discord.Embed(title=f"{away} @ {home}", description=f"Final!\nScore: {awayScore} | {homeScore}", color=config.color)
                
                embed.set_footer(text=config.footer)
                await msg.edit(embed=embed, view=view)
                gameButton.callback = gameButton_callback
                return
            embed = discord.Embed(title=f"{away} @ {home}", description=f"{awayScore} - {homeScore}", color=config.color)
            
            for i in range(len(shotsByPeriod)):
                homeShots += shotsByPeriod[i]['home']
                awayShots += shotsByPeriod[i]['away']
            embed.description = f"GAME IS LIVE!!!\n\nScore: {awayScore} - {homeScore}\nShots: {awayShots} - {homeShots}"
            if clockRunning == True:
                embed.add_field(name="Clock", value=f"{clock}\nRunning", inline=False)
            else:
                embed.add_field(name="Clock", value=f"{clock}", inline=False)
            if clockIntermission == True:
                embed.add_field(name="Clock", value=f"Intermission", inline=False)
            embed.set_footer(text=config.footer)
            embed.add_field(name="TV Broadcast", value=f"{networks}", inline=False)
            embed.add_field(name="Game ID", value=gameID, inline=False)
            await msg.edit(embed=embed, view=view)
            gameButton.callback = gameButton_callback
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")

async def setup(bot):
    await bot.add_cog(game(bot))