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

used = {}



class guessThePlayer(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `guessThePlayer.py`")
    

    @app_commands.command(name="guess-the-player", description="Guess the player!")
    @app_commands.checks.cooldown(1.0, 15.0, key=lambda i: (i.guild.id))
    @app_commands.checks.cooldown(1.0, 60.0, key=lambda i: (i.user.id))
    async def guessThePlayer(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as log_error:
                print(f"Command logging failed: {log_error}")

        used.update({interaction.user.id: True})
        await interaction.response.defer()

        try:
            teams = {
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

            team = random.choice(list(teams.keys()))
            team_name = teams[team]
            url = f"https://api-web.nhle.com/v1/roster/{team}/current"
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                x = response.json()
            except requests.exceptions.RequestException as e:
                await interaction.followup.send("Could not fetch team data. Please try again later.", ephemeral=True)
                raise e

            positions = ["forwards", "defensemen", "goalies"]
            position = random.choice(positions)
            roster = x.get(position, [])
            if not roster:
                await interaction.followup.send(f"No players found for position `{position}` in the `{team_name}`.")
                return

            player = random.choice(roster)
            first_name = player.get("firstName", {}).get("default", "Unknown")
            last_name = player.get("lastName", {}).get("default", "Unknown")
            full_name = f"{first_name} {last_name}"
            position_code = player.get("positionCode", "Unknown")

            position_full = {
                "G": "Goalie",
                "D": "Defenseman",
                "C": "Center",
                "L": "Left Wing",
                "R": "Right Wing"
            }.get(position_code, "Unknown Position")

            hint = f"(Hint: Their first name starts with `{first_name[0]}` and they play `{position_full}`)"
            await interaction.followup.send(f"Guess the player from the `{team_name}`! You have 15 seconds! {hint}")

            if config.dev_mode and interaction.user.id == config.jacob:
                await interaction.followup.send(f"**DEBUG**: The player is `{full_name}`")

            def check(message):
                return message.channel == interaction.channel and message.content.lower() == full_name.lower()

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)

                mydb = mysql.connector.connect(
                    host=os.getenv("db_host"),
                    user=os.getenv("db_user"),
                    password=os.getenv("db_password"),
                    database=os.getenv("db_name")
                )
                mycursor = mydb.cursor()
                mycursor.execute("SELECT * FROM gtp WHERE id = %s", (msg.author.id,))
                myresult = mycursor.fetchone()

                if not myresult:
                    mycursor.execute(
                        "INSERT INTO gtp (id, points, allow_leaderboard) VALUES (%s, %s, %s)",
                        (msg.author.id, 1, True)
                    )
                    await interaction.followup.send(
                        f"Congratulations, {msg.author.mention}! You guessed the player! You have been added to the leaderboard!"
                    )
                else:
                    points = myresult[1] + 1
                    mycursor.execute("UPDATE gtp SET points = %s WHERE id = %s", (points, msg.author.id))
                    await interaction.followup.send(f"Congratulations, {msg.author.mention}! You guessed the player!")

                mydb.commit()
                mydb.close()
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was `{full_name}`.")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error at {datetime.now()}:\n```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported to the developers.", ephemeral=True)

        finally:
            used.pop(interaction.user.id, None)
    
    @guessThePlayer.error
    async def guessThePlayer_error(self, interaction: discord.Interaction , error):
        if used.get(interaction.user.id) == True:
            await interaction.response.send_message("You have already used the command! Please allow the timer to end before using the command again!", ephemeral=True)
            return
        else:
            now = datetime.now()
            cmd_cool = int(error.retry_after) + 1
            new_time = time.mktime(now.timetuple()) + cmd_cool
            await interaction.response.send_message(f"Command on cooldown! Try again <t:{int(new_time)}:R>.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(guessThePlayer(bot))