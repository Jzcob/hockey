import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
import random
import asyncio
import requests
import config
from datetime import datetime
import traceback
from thefuzz import fuzz
import json

# --- Global Constants ---
SIMILARITY_THRESHOLD = 85 # You can adjust this value (0-100)

class GTP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.used = {}

    def migrate_gtp(self, cursor, user_id, actual_guild_id):
        cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
        row = cursor.fetchone()
        if row:
            points_from_zero = row[0]
            cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = %s", (user_id, actual_guild_id))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE gtp_scores
                    SET points = points + %s
                    WHERE user_id = %s AND guild_id = %s
                """, (points_from_zero, user_id, actual_guild_id))
                cursor.execute("DELETE FROM gtp_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
            else:
                cursor.execute("""
                    UPDATE gtp_scores
                    SET guild_id = %s
                    WHERE user_id = %s AND guild_id = 0
                """, (actual_guild_id, user_id))

    @app_commands.command(name="guess-the-player", description="Guess the player!")
    async def guess_the_player(self, interaction: discord.Interaction):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = "DMs" if interaction.guild is None else f"`{interaction.guild.name}`"
            await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in {guild_name} at `{datetime.now()}`\n---")
        
        await interaction.response.defer()

        try:
            with open("teams.json", "r") as f:
                teams = json.load(f)
            team = random.choice(list(teams.keys()))
            team_name = teams[team]
            url = f"https://api-web.nhle.com/v1/roster/{team}/current"

            response = requests.get(url)
            response.raise_for_status()
            x = response.json()

            positions = ["forwards", "defensemen", "goalies"]
            position = random.choice(positions)
            roster = x.get(position, [])
            if not roster:
                await interaction.followup.send(f"No players found for `{team_name}` ({position})")
                return

            player = random.choice(roster)
            first_name = player.get("firstName", {}).get("default", "Unknown")
            last_name = player.get("lastName", {}).get("default", "Unknown")
            full_name = f"{first_name} {last_name}"
            position_code = player.get("positionCode", "Unknown")
            position_full = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}.get(position_code, "Unknown")
            hint = f"(Hint: Their name starts with `{first_name[0]}` and they play `{position_full}`)"

            await interaction.followup.send(f"Guess the player from the `{team_name}`! You have 15 seconds! {hint}")

            # This check now only verifies the author and channel
            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)
                user_answer = msg.content.strip().lower()
                correct_answer = full_name.lower()
                correct = False

                # --- Fuzzy Matching Logic ---
                if user_answer == correct_answer:
                    correct = True
                else:
                    similarity_score = fuzz.partial_ratio(user_answer, correct_answer)
                    if similarity_score >= SIMILARITY_THRESHOLD:
                        confirm_msg = await interaction.followup.send(
                            f"Your answer is very close. Did you mean `{full_name}`? (yes/no)",
                            wait=True
                        )
                        def confirm_check(m):
                            return m.author == interaction.user and m.channel == interaction.channel and m.content.lower() in ['yes', 'no']
                        try:
                            confirm_response = await self.bot.wait_for('message', check=confirm_check, timeout=15.0)
                            if confirm_response.content.lower() == 'yes':
                                correct = True
                            await confirm_msg.delete()
                            await confirm_response.delete()
                        except asyncio.TimeoutError:
                            await confirm_msg.edit(content="Confirmation timed out.", delete_after=5)

                if correct:
                    mydb = mysql.connector.connect(
                        host=os.getenv("db_host"),
                        user=os.getenv("db_user"),
                        password=os.getenv("db_password"),
                        database=os.getenv("db_name")
                    )
                    mycursor = mydb.cursor()
                    if interaction.guild:
                        self.migrate_gtp(mycursor, msg.author.id, interaction.guild.id)

                    mycursor.execute("""
                        INSERT INTO gtp_users (user_id, allow_leaderboard) VALUES (%s, 1)
                        ON DUPLICATE KEY UPDATE user_id = user_id
                    """, (msg.author.id,))
                    mycursor.execute("""
                        INSERT INTO gtp_scores (user_id, guild_id, points) VALUES (%s, %s, 1)
                        ON DUPLICATE KEY UPDATE points = points + 1
                    """, (msg.author.id, interaction.guild.id))
                    mydb.commit()
                    mydb.close()

                    await interaction.followup.send(f"Correct! 🎉 The player was `{full_name}`. Well done, {msg.author.mention}!")
                else:
                    await interaction.followup.send(f"Sorry, that's not right. The player was `{full_name}`.")

            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was `{full_name}`.")

        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send("An error occurred while processing your request.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GTP(bot))