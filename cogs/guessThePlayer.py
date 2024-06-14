import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import random
import config
import asyncio
import traceback
import mysql.connector
import os
from datetime import datetime
import time

class guessThePlayer(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `guessThePlayer.py`")
    

    @app_commands.command(name="guess-the-player", description="Guess the player!")
    @app_commands.checks.cooldown(1.0, 15.0, key=lambda i: (i.guild.id))
    @app_commands.checks.cooldown(1.0, 60.0, key=lambda i: (i.user.id))
    async def guessThePlayer(self, interaction : discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")

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
            randomChoice = random.randint(0, length - 1)
            personID = x[position][randomChoice]["id"]
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
            await msg.edit(content=f"Guess the player from the `{teams[team]}`! You have 15 seconds! (Hint: Their first name starts with `{firstName[0]}`) (Hint: They play `{position}`)")
            if config.dev_mode == True:
                if interaction.user.id is config.jacob:
                    await msg.edit(content=f"**DEBUG**: The player is `{fullName}`")
            def check(message):
                return message.content.lower() == fullName.lower()
            try:
                message = await self.bot.wait_for("message", check=check, timeout=15.0)
                
                mydb = mysql.connector.connect(
                    host=os.getenv("db_host"),
                    user=os.getenv("db_user"),
                    password=os.getenv("db_password"),
                    database=os.getenv("db_name")
                )
                mycursor = mydb.cursor()
                mycursor.execute(f"SELECT * FROM users WHERE id = {message.author.id}")
                myresult = mycursor.fetchone()
                if myresult == None:
                    mycursor.execute(f"INSERT INTO users (id, points, allow_leaderboard) VALUES ({message.author.id}, 1, TRUE)")
                    await interaction.followup.send(f"Congratulations, {message.author.mention}! You guessed the Player! You have been added to the leaderboard!\n**The leaderboard is global across the entire bot. If you wish to not be showed on the leaderboard please use `/leaderboard-status`**")
                else:
                    points = myresult[1] + 1
                    mycursor.execute(f"UPDATE users SET points = {points} WHERE id = {message.author.id}")
                    await interaction.followup.send(f"Congratulations, {message.author.mention}! You guessed the Player!")
                mydb.commit()
                mydb.close()
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Sorry, time's up!, the correct answer was `{fullName}`.")
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
    
    @guessThePlayer.error
    async def guessThePlayer_error(self, interaction: discord.Interaction , error):
        now = datetime.now()
        cmd_cool = int(error.retry_after) + 1
        new_time = time.mktime(now.timetuple()) + cmd_cool
        await interaction.response.send_message(f"Command on cooldown! Try again <t:{int(new_time)}:R>.", ephemeral=True)
        


async def setup(bot):
    await bot.add_cog(guessThePlayer(bot))