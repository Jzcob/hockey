import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import requests
import json
import config

class player(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `player.py`")
    
    @app_commands.command(name="player", description="Gets the information of a player!")
    async def player(self, interaction: discord.Interaction, name: str):
        return await interaction.response.send_message("This command is currently disabled! Due to the NHL API.", ephemeral=True)
        await interaction.response.defer()
        msg = await interaction.original_response()
        try:
            teams= {
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
            for team in teams:
                url = f"https://api-web.nhle.com/v1/roster/{team}/20232024"
                data = requests.get(url)
                x = json.loads(data.text)
                for player in x['roster']:
                    firstName = player['person']['default']['firstName']
                    lastName = player['person']['default']['lastName']
                    fullName = f"{firstName} {lastName}"
                    if fullName.lower() == name.lower():
                        playerID = player['person']['id']
                        shoots = player['person']['shootsCatches']
                        birthDate = player['birthDate']
                        birthCity = player['birthCity']['default']
                        birthCountry = player['birthCountry']['default']
                        drafted = player['draftDetails']['year']
                        draftedRound = player['draftDetails']['round']
                        draftedOverall = player['draftDetails']['overallPickNumber']
                        draftedTeam = player['draftDetails']['team']['name']
                        gamesPlayed = player['featuredStats']['career']['gamesPlayed']
                        goals = player['featuredStats']['career']['goals']
                        assists = player['featuredStats']['career']['assists']
                        points = player['featuredStats']['career']['points']
                        plusMinus = player['featuredStats']['career']['plusMinus']
                        penaltyMinutes = player['featuredStats']['careerTotals']['regularSeason']['penaltyMinutes']
                        powerPlayGoals = player['featuredStats']['careerTotals']['regularSeason']['powerPlayGoals']
                        powerPlayPoints = player['featuredStats']['careerTotals']['regularSeason']['powerPlayPoints']
                        shortHandedGoals = player['featuredStats']['careerTotals']['regularSeason']['shortHandedGoals']
                        shortHandedPoints = player['featuredStats']['careerTotals']['regularSeason']['shortHandedPoints']
                        gameWinningGoals = player['featuredStats']['careerTotals']['regularSeason']['gameWinningGoals']
                        overtimeGoals = player['featuredStats']['careerTotals']['regularSeason']['overtimeGoals']
                        shots = player['featuredStats']['careerTotals']['regularSeason']['shots']
                        shootingPercentage = player['featuredStats']['careerTotals']['regularSeason']['shootingPctg']
                        faceoffPercentage = player['featuredStats']['careerTotals']['regularSeason']['faceoffWinPctg']
                        playerPosition = player['position']['name']
                        playerNumber = player['sweaterNumber']
                        embed = discord.Embed(title=f"{fullName}", color=config.color, url=f"https://www.nhl.com/player/{playerID}")
                        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                        embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Player Information")
                        embed.description = f"{playerPosition} for the {teams[team]}"
                        embed.add_field(name="Number", value=f"{playerNumber}", inline=True)
                        embed.add_field(name="Shoots", value=f"{shoots}", inline=True)
                        embed.add_field(name="Birth Date", value=f"{birthDate}", inline=True)
                        embed.add_field(name="Birth City", value=f"{birthCity}", inline=True)
                        embed.add_field(name="Birth Country", value=f"{birthCountry}", inline=True)
                        embed.add_field(name="Drafted", value=f"{drafted}", inline=True)
                        embed.add_field(name="Drafted Round", value=f"{draftedRound}", inline=True)
                        embed.add_field(name="Drafted Overall", value=f"{draftedOverall}", inline=True)
                        embed.add_field(name="Drafted Team", value=f"{draftedTeam}", inline=True)
                        embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                        embed.add_field(name="Goals", value=f"{goals}", inline=True)
                        embed.add_field(name="Assists", value=f"{assists}", inline=True)
                        embed.add_field(name="Points", value=f"{points}", inline=True)
                        embed.add_field(name="Plus/Minus", value=f"{plusMinus}", inline=True)
                        embed.add_field(name="Penalty Minutes", value=f"{penaltyMinutes}", inline=True)
                        embed.add_field(name="Power Play Goals", value=f"{powerPlayGoals}", inline=True)
                        embed.add_field(name="Power Play Points", value=f"{powerPlayPoints}", inline=True)
                        embed.add_field(name="Short Handed Goals", value=f"{shortHandedGoals}", inline=True)
                        embed.add_field(name="Short Handed Points", value=f"{shortHandedPoints}", inline=True)
                        embed.add_field(name="Game Winning Goals", value=f"{gameWinningGoals}", inline=True)
                        embed.add_field(name="Overtime Goals", value=f"{overtimeGoals}", inline=True)
                        embed.add_field(name="Shots", value=f"{shots}", inline=True)
                        embed.add_field(name="Shooting Percentage", value=f"{shootingPercentage}", inline=True)
                        embed.add_field(name="Faceoff Percentage", value=f"{faceoffPercentage}", inline=True)
                        embed.set_footer(text=f"Player ID: {playerID}")
                        await msg.edit(embed=embed)
                        return
            else:
                await interaction.followup.send("Player not found!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Player Name", value=name)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.mention)
            embed.set_footer(text=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            await interaction.followup.send("Error getting player! Message has been sent to Bot Developers", ephemeral=True)
            await error_channel.send(f"Something went wrong `{e}`")

async def setup(bot):
    await bot.add_cog(player(bot))