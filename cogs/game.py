import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import pytz

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
                await msg.edit("Please enter a valid team abbreviation. e.g. `/game BOS`")
                return
            hawaii = pytz.timezone('US/Hawaii')
            dt = datetime.now(hawaii)
            today = dt.strftime('%Y-%m-%d')
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/now'
            response = requests.get(url)
            data = response.json()
            games = data['games']
            for i in range(len(games)):
                if f"{games[i]['gameDate']}" == f"{today}":
                    game = games[i]
                    gameID = game['id']
                    break
                else:
                    await msg.edit(content=f"**{team}** do not play today.")
                    return
            url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
            response2 = requests.get(url2)
            data2 = response2.json()
            home = data2['homeTeam']['name']['default']
            away = data2['awayTeam']['name']['default']
            tvBroadcasts= data2['tvBroadcasts']
            for i in range(len(tvBroadcasts)):
                network = tvBroadcasts[i]['network']
                countryCode = tvBroadcasts[i]['countryCode']
                networks += f"{network} ({countryCode})\n"
            embed.add_field(name="TV Broadcast", value=f"{networks}", inline=False)
            if game['gameState'] == "FUT":
                embed = discord.Embed(title=f"{away} @ {home}", description=f"Game is scheduled!", color=config.color)
                embed.add_field(name="Network", value=f"{networks}", inline=False)
                embed.add_field(name="Game ID", value=gameID, inline=False)
                await msg.edit(embed=embed)
                return
            homeScore = data2['boxscore']['linescore']['totals']['home']
            awayScore = data2['boxscore']['linescore']['totals']['away']
            clock = data2['clock']['timeRemaining']
            clockRunning = data2['clock']['running']
            clockIntermission = data2['clock']['inIntermission']
            venue = data2['venue']['default']
            shotsByPeriod = data2['boxscore']['shotsByPeriod']
            
            homeShots = 0
            awayShots = 0
            networks = ""
            
            if game['gameState'] == "FINAL" or game['gameState'] == "OFF":
                embed = discord.Embed(title=f"{away} @ {home}", description=f"Final!\nScore: {awayScore} | {homeScore}", color=config.color)
                await msg.edit(embed=embed)
                return
            embed = discord.Embed(title=f"{away} @ {home}", description=f"{awayScore} - {homeScore}", color=config.color)
            for i in range(len(shotsByPeriod)):
                homeShots += shotsByPeriod[i]['home']
                awayShots += shotsByPeriod[i]['away']
            embed.add_field(name="Shots", value=f"{away}: {awayShots}\n{home}: {homeShots}", inline=False)
            if clockRunning == True:
                embed.add_field(name="Clock", value=f"{clock}\nRunning", inline=False)
            else:
                embed.add_field(name="Clock", value=f"{clock}", inline=False)
            if clockIntermission == True:
                embed.add_field(name="Clock", value=f"Intermission", inline=False)
            embed.set_footer(text=config.footer)
            for i in range(len(tvBroadcasts)):
                network = tvBroadcasts[i]['network']
                countryCode = tvBroadcasts[i]['countryCode']
                networks += f"{network} ({countryCode})\n"
            embed.add_field(name="TV Broadcast", value=f"{networks}", inline=False)
            embed.add_field(name="Venue", value=venue, inline=False)
            embed.add_field(name="Game ID", value=gameID, inline=False)
            await msg.edit(embed=embed)
        except Exception as e:
            print(e)
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/game`", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Team", value=team)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.name)
            embed.set_footer(text=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            await interaction.followup.send("Error getting game! Message has been sent to Bot Developers", ephemeral=True)
            return await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(game(bot))