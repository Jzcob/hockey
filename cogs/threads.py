import discord
from discord.ext import commands
from discord import app_commands
import config
import requests
from datetime import datetime
import traceback

class thread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `thread.py`")
    
    @app_commands.command(name="thread", description="Creates a hockey thread!")
    async def thread(self, interaction: discord.Interaction, abbreviation: str, channel: discord.TextChannel):
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
                for team in teams:
                    if abbreviation.upper() == team:
                        team = teams[team]
                        break
                channel = interaction.client.get_channel(channel)
                today = datetime.now()
                today = today.strftime("%Y-%m-%d")
                url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/{today}'
                response = requests.get(url)
                data = response.json()
                games = data['games']
                for i in range(len(games)):
                    print(f"{games[i]['gameDate']}")
                    print(f"{today}")
                    if f"{games[i]['gameDate']}" == f"{today}":
                        game = games[i]
                        gameID = game['id']
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
                embed = discord.Embed(title=f"**{away} @ {home}**", description=f"**{team}** game thread!", color=config.color)
                await channel.create_thread(name=f"{away} @ {home}", message=interaction.user.mention, reason=f"Game Thread for {away} @ {home}", auto_archive_duration=1440, start_message=embed)
                await msg.edit(content=f"Game Thread for **{away} @ {home}** has been created in {channel.mention}!")
                return
            else:
                await msg.edit("Please enter a valid team abbreviation. e.g. `/thread BOS`")
                return

        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(thread(bot), guilds=[discord.Object(id=config.hockey_discord_server)])