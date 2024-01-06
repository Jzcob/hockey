import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import random
import config
import asyncio

class guessThePlayer(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `guessThePlayer.py`")
    

    @app_commands.command(name="guess-the-player", description="Guess the player!")
    async def guessThePlayer(self, interaction : discord.Interaction):
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
            
            team = random.choice(list(teams.keys()))
            
            # Get the team name from the abbreviation
            url = f"https://api-web.nhle.com/v1/roster/{team}/current"
            response = requests.get(url)
            x = response.json()
            positions = ["forwards", "defensemen", "goalies"]
            position = random.choice(positions)
            roster = x[position]
            length = len(roster)
            randomChoice = random.randint(0, length)
            personID = x[position][randomChoice]["id"]
            print(personID)
            playerURL = f"https://api-web.nhle.com/v1/player/{personID}/landing"
            response = requests.get(playerURL)
            y = response.json()
            firstName = y["firstName"]['default']
            lastName = y["lastName"]['default']
            fullName = f"{firstName} {lastName}"
            position = y["position"]
            if position == "G":
                position = "Goalie"
            elif position == "D":
                position = "Defenseman"
            elif position == "C":
                position = "Center"
            elif position == "L":
                position = "Left Wing"
            elif position == "R":
                position = "Right Wing"
            await msg.edit(content=f"Guess the player from the `{teams[team]}`! You have 30 seconds! (Hint: Their first name starts with `{firstName[0]}`) (Hint: They play `{position}`)")
            
            def check(message):
                return message.content.lower() == fullName.lower()
            try:
                message = await self.bot.wait_for("message", check=check, timeout=30.0)
                await interaction.followup.send(f"Congratulations, {message.author.mention}! You guessed the Player!")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Sorry, time's up!, the correct answer was `{fullName}`.")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await interaction.followup.send("Error with the command | Message has been sent to Bot Developers", ephemeral=True)
            await error_channel.send(f"Error with `/guess-the-player`\n`{e}`")

async def setup(bot):
    await bot.add_cog(guessThePlayer(bot))