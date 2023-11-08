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
            await interaction.response.send_message("Generating for player..")
            team_ids = {
                "Anaheim Ducks": 24,
                "Arizona Coyotes": 53,
                "Boston Bruins": 6,
                "Buffalo Sabres": 7,
                "Calgary Flames": 20,
                "Carolina Hurricanes": 12,
                "Chicago Blackhawks": 16,
                "Colorado Avalanche": 21,
                "Columbus Blue Jackets": 29,
                "Dallas Stars": 25,
                "Detroit Red Wings": 17,
                "Edmonton Oilers": 22,
                "Florida Panthers": 13,
                "Los Angeles Kings": 26,
                "Minnesota Wild": 30,
                "Montreal Canadiens": 8,
                "Nashville Predators": 18,
                "New Jersey Devils": 1,
                "New York Islanders": 2,
                "New York Rangers": 3,
                "Ottawa Senators": 9,
                "Philadelphia Flyers": 4,
                "Pittsburgh Penguins": 5,
                "San Jose Sharks": 28,
                "St. Louis Blues": 19,
                "Tampa Bay Lightning": 14,
                "Toronto Maple Leafs": 10,
                "Vancouver Canucks": 23,
                "Vegas Golden Knights": 54,
                "Washington Capitals": 15,
                "Winnipeg Jets": 52
            }
            
            # Choose a random NHL team
            team_name = random.choice(list(team_ids.keys()))
            
            # Get the team's roster
            team_id = team_ids[team_name]
            url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}/roster"
            response = requests.get(url)
            roster = json.loads(response.text)["roster"]
            randomChoice = random.choice(roster)
            personID = randomChoice["person"]["id"]
            url = f"https://statsapi.web.nhl.com/api/v1/people/{personID}"
            response = requests.get(url)
            try:
                player = response.json()["people"][0]["fullName"]
                playerBirthCountry = response.json()["people"][0]["birthCountry"]
                playerBirthCity = response.json()["people"][0]["birthCity"]
                embed = discord.Embed(title=f"{player}", color=config.color)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                embed = discord.Embed(title="Error with `/guess-the-player`", description=f"```{e}```", color=config.color)
            
            # Send a message to the user with the name of the NHL team and ask them to guess the player
            await interaction.followup.send(f"Guess the player from the `{team_name}`! You have 30 seconds! (Hint: Their first name starts with `{player[0]}`) (Hint: They were born in `{playerBirthCity}`, `{playerBirthCountry}`)")

            def check(message):
                return message.content.lower() == player.lower()
            
            try:
                message = await self.bot.wait_for("message", check=check, timeout=30.0)
                await interaction.followup.send(f"Congratulations, {message.author.mention}! You guessed the Player!")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Sorry, time's up!, the correct answer was `{player}`.")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/guess-the-player`", description=f"```{e}```", color=config.color)
            embed.add_field(name="Player Chosen", value=f"{player}", inline=False)
            embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="Guild", value=f"{interaction.guild.name}", inline=False)
            embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
            await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(guessThePlayer(bot))