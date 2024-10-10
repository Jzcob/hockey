import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import requests
import config
import traceback

class player(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `player.py`")
    
    @app_commands.command(name="player", description="Gets the information of a player!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def player(self, interaction: discord.Interaction, name: str):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/player` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/player` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/player` used by `{interaction.user.name}` in `{interaction.guild.name}` player requested `{name}` at `{datetime.now()}`\n---")
        try:
            await interaction.response.defer()
            msg = await interaction.original_response()
            teams= {
                "ANA": "Anaheim Ducks",
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
                "UTA": "Utah Hockey Club",
                "VAN": "Vancouver Canucks",
                "VGK": "Vegas Golden Knights",
                "WSH": "Washington Capitals",
                "WPG": "Winnipeg Jets"
            }
            for team in teams:
                url = f"https://api-web.nhle.com/v1/roster/{team}/current"
                response = requests.get(url)
                x = response.json()
                for player in range(len(x['forwards'])):
                    firstName = x['forwards'][player]['firstName']['default']
                    lastName = x['forwards'][player]['lastName']['default']
                    fullName = f"{firstName} {lastName}"
                    if fullName.lower() == name.lower():
                        playerID = x['forwards'][player]['id']
                        playerURL = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
                        data = requests.get(playerURL)
                        y = data.json()
                        birthDate = y['birthDate']
                        birthCity = y['birthCity']['default']
                        birthCountry = y['birthCountry']
                        try:
                            gamesPlayed = y['featuredStats']['regularSeason']['career']['gamesPlayed']
                            goals = y['featuredStats']['regularSeason']['career']['goals']
                            assists = y['featuredStats']['regularSeason']['career']['assists']
                            points = y['featuredStats']['regularSeason']['career']['points']
                        except:
                            gamesPlayed = "N/A"
                            goals = "N/A"
                            assists = "N/A"
                            points = "N/A"
                        playerPosition = y['position']
                        try:
                            playerNumber = y['sweaterNumber']
                        except:
                            playerNumber = "N/A"
                        headshot = y['headshot']
                        embed = discord.Embed(title=f"{fullName}", color=config.color, url=f"https://www.nhl.com/player/{playerID}")
                        embed.set_thumbnail(url=headshot)
                        try:
                            avatar = interaction.user.avatar.url
                        except:
                            avatar = self.bot.user.avatar.url
                        embed.set_author(icon_url=avatar, name="NHL Player Information")
                        if playerPosition == "G":
                            playerPosition = "Goalie"
                        elif playerPosition == "D":
                            playerPosition = "Defenseman"
                        elif playerPosition == "C":
                            playerPosition = "Center"
                        elif playerPosition == "L":
                            playerPosition = "Left Wing"
                        elif playerPosition == "R":
                            playerPosition = "Right Wing"
                        embed.description = f"{playerPosition} for the {teams[team]} #{playerNumber}"
                        embed.add_field(name="Birth Date", value=f"{birthDate}", inline=True)
                        embed.add_field(name="Birth City", value=f"{birthCity}", inline=True)
                        embed.add_field(name="Birth Country", value=f"{birthCountry}", inline=True)
                        embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                        embed.add_field(name="Goals", value=f"{goals}", inline=True)
                        embed.add_field(name="Assists", value=f"{assists}", inline=True)
                        embed.add_field(name="Points", value=f"{points}", inline=True)
                        embed.set_footer(text=f"Player ID: {playerID}")
                        await msg.edit(embed=embed)
                        return
                for player in range(len(x['defensemen'])):
                    firstName = x['defensemen'][player]['firstName']['default']
                    lastName = x['defensemen'][player]['lastName']['default']
                    fullName = f"{firstName} {lastName}"
                    if fullName.lower() == name.lower():
                        playerID = x['defensemen'][player]['id']
                        playerURL = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
                        data = requests.get(playerURL)
                        y = data.json()
                        shoots = y['shootsCatches']
                        birthDate = y['birthDate']
                        birthCity = y['birthCity']['default']
                        birthCountry = y['birthCountry']
                        try:
                            gamesPlayed = y['featuredStats']['regularSeason']['career']['gamesPlayed']
                            goals = y['featuredStats']['regularSeason']['career']['goals']
                            assists = y['featuredStats']['regularSeason']['career']['assists']
                            points = y['featuredStats']['regularSeason']['career']['points']
                        except:
                            gamesPlayed = "N/A"
                            goals = "N/A"
                            assists = "N/A"
                            points = "N/A"
                        playerPosition = y['position']
                        try:
                            playerNumber = y['sweaterNumber']
                        except:
                            playerNumber = "N/A"
                        headshot = y['headshot']
                        embed = discord.Embed(title=f"{fullName}", color=config.color, url=f"https://www.nhl.com/player/{playerID}")
                        embed.set_thumbnail(url=headshot)
                        try:
                            avatar = interaction.user.avatar.url
                        except:
                            avatar = self.bot.user.avatar.url
                        embed.set_author(icon_url=avatar, name="NHL Player Information")
                        if playerPosition == "G":
                            playerPosition = "Goalie"
                        elif playerPosition == "D":
                            playerPosition = "Defenseman"
                        elif playerPosition == "C":
                            playerPosition = "Center"
                        elif playerPosition == "L":
                            playerPosition = "Left Wing"
                        elif playerPosition == "R":
                            playerPosition = "Right Wing"
                        embed.description = f"{playerPosition} for the {teams[team]}"
                        embed.add_field(name="Number", value=f"{playerNumber}", inline=True)
                        embed.add_field(name="Birth Date", value=f"{birthDate}", inline=True)
                        embed.add_field(name="Birth City", value=f"{birthCity}", inline=True)
                        embed.add_field(name="Birth Country", value=f"{birthCountry}", inline=True)
                        embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                        embed.add_field(name="Goals", value=f"{goals}", inline=True)
                        embed.add_field(name="Assists", value=f"{assists}", inline=True)
                        embed.add_field(name="Points", value=f"{points}", inline=True)
                        embed.set_footer(text=f"Player ID: {playerID}")
                        await msg.edit(embed=embed)
                        return
                for player in range(len(x['goalies'])):
                    firstName = x['goalies'][player]['firstName']['default']
                    lastName = x['goalies'][player]['lastName']['default']
                    fullName = f"{firstName} {lastName}"
                    if fullName.lower() == name.lower():
                        playerID = x['goalies'][player]['id']
                        playerURL = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
                        data = requests.get(playerURL)
                        y = data.json()
                        shoots = y['shootsCatches']
                        birthDate = y['birthDate']
                        birthCity = y['birthCity']['default']
                        birthCountry = y['birthCountry']
                        try:
                            gamesPlayed = y['featuredStats']['regularSeason']['career']['gamesPlayed']
                        except:
                            gamesPlayed = "N/A"
                        playerPosition = y['position']
                        try:
                            playerNumber = y['sweaterNumber']
                        except:
                            playerNumber = "N/A"
                        headshot = y['headshot']
                        embed = discord.Embed(title=f"{fullName}", color=config.color, url=f"https://www.nhl.com/player/{playerID}")
                        embed.set_thumbnail(url=headshot)
                        try:
                            avatar = interaction.user.avatar.url
                        except:
                            avatar = self.bot.user.avatar.url
                        embed.set_author(icon_url=avatar, name="NHL Player Information")
                        if playerPosition == "G":
                            playerPosition = "Goalie"
                        elif playerPosition == "D":
                            playerPosition = "Defenseman"
                        elif playerPosition == "C":
                            playerPosition = "Center"
                        elif playerPosition == "L":
                            playerPosition = "Left Wing"
                        elif playerPosition == "R":
                            playerPosition = "Right Wing"
                        embed.description = f"{playerPosition} for the {teams[team]}"
                        embed.add_field(name="Number", value=f"{playerNumber}", inline=True)
                        embed.add_field(name="Shoots", value=f"{shoots}", inline=True)
                        embed.add_field(name="Birth Date", value=f"{birthDate}", inline=True)
                        embed.add_field(name="Birth City", value=f"{birthCity}", inline=True)
                        embed.add_field(name="Birth Country", value=f"{birthCountry}", inline=True)
                        embed.set_footer(text=f"Player ID: {playerID}")
                        await msg.edit(embed=embed)
                        return
            else:
                await interaction.followup.send("Player not found!", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(player(bot))