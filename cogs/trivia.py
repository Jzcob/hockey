import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import os
import mysql.connector
from datetime import datetime
import traceback
import config
from thefuzz import fuzz

# --- Global Variables & Constants ---
used = {}
SIMILARITY_THRESHOLD = 85 # You can adjust this value (0-100)

# --- Cog Class Definition ---
class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.used = {} # Instance-specific used dictionary

    def migrate_guild_id(self, cursor, user_id, actual_guild_id):
        cursor.execute("SELECT points FROM trivia_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
        row = cursor.fetchone()
        if row:
            points_from_zero = row[0]
            cursor.execute("SELECT points FROM trivia_scores WHERE user_id = %s AND guild_id = %s", (user_id, actual_guild_id))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE trivia_scores
                    SET points = points + %s
                    WHERE user_id = %s AND guild_id = %s
                """, (points_from_zero, user_id, actual_guild_id))
                cursor.execute("DELETE FROM trivia_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
            else:
                cursor.execute("""
                    UPDATE trivia_scores
                    SET guild_id = %s
                    WHERE user_id = %s AND guild_id = 0
                """, (actual_guild_id, user_id))

    @app_commands.command(name="trivia", description="Answer trivia questions to earn points!")
    async def trivia(self, interaction: discord.Interaction):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = "DMs" if interaction.guild is None else f"`{interaction.guild.name}`"
            await command_log_channel.send(f"`/trivia` used by `{interaction.user.name}` in {guild_name} at `{datetime.now()}`\n---")
            
        try:
            if interaction.user.id in self.used:
                await interaction.response.send_message("You already have an active trivia question!", ephemeral=True)
                return
            
            self.used[interaction.user.id] = True
            await interaction.response.defer()

            with open("trivia.json", "r", encoding="utf-8") as f:
                trivia_data = json.load(f)

            question, answer = random.choice(list(trivia_data.items()))

            await interaction.followup.send(f"Trivia Question: {question}\nYou have 60 seconds to answer!")

            def check(message):
                return message.channel == interaction.channel and message.author == interaction.user

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                user_answer = msg.content.strip().lower()

                possible_answers = [a.strip().lower() for a in answer.split(" or ")]
                correct = False
                
                # --- Fuzzy Matching Logic ---
                if user_answer in possible_answers:
                    correct = True
                else:
                    for correct_ans in possible_answers:
                        similarity_score = fuzz.partial_ratio(user_answer, correct_ans)
                        if similarity_score >= SIMILARITY_THRESHOLD:
                            confirm_msg = await interaction.followup.send(
                                f"Your answer is very close. Did you mean `{correct_ans.title()}`? (yes/no)",
                                wait=True
                            )
                            def confirm_check(m):
                                return m.author == interaction.user and m.channel == interaction.channel and m.content.lower() in ['yes', 'no', 'y', 'n']
                            try:
                                confirm_response = await self.bot.wait_for('message', check=confirm_check, timeout=15.0)
                                if confirm_response.content.lower() == 'yes' or confirm_response.content.lower() == 'y':
                                    correct = True
                                try:
                                    await confirm_msg.delete()
                                    await confirm_response.delete()
                                except:
                                    pass
                                break
                            except asyncio.TimeoutError:
                                await confirm_msg.edit(content="Confirmation timed out.", delete_after=5)
                                break
                
                # --- Award Points or Give Correct Answer ---
                if correct:
                    mydb = mysql.connector.connect(
                        host=os.getenv("db_host"),
                        user=os.getenv("db_user"),
                        password=os.getenv("db_password"),
                        database=os.getenv("db_name")
                    )
                    mycursor = mydb.cursor()
                    if interaction.guild:
                        self.migrate_guild_id(mycursor, interaction.user.id, interaction.guild.id)
                    
                    mycursor.execute("""
                        INSERT INTO trivia_users (user_id, allow_leaderboard) VALUES (%s, 1)
                        ON DUPLICATE KEY UPDATE user_id = user_id
                    """, (interaction.user.id,))
                    mycursor.execute("""
                        INSERT INTO trivia_scores (user_id, guild_id, points) VALUES (%s, %s, 1)
                        ON DUPLICATE KEY UPDATE points = points + 1
                    """, (interaction.user.id, interaction.guild.id))
                    mydb.commit()
                    mydb.close()
                    await interaction.followup.send(f"Correct! 🎉 {interaction.user.mention}, you earned a point!")
                else:
                    await interaction.followup.send(f"Sorry, that's not correct. The answer was: `{answer}`")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was: `{answer}`")
        except Exception as e:
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.followup.send("An error occurred. Please try again later.", ephemeral=True)
        finally:
            self.used.pop(interaction.user.id, None)

# --- Cog Setup Function ---
async def setup(bot):
    await bot.add_cog(Trivia(bot))