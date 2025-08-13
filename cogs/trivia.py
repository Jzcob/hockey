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
import time

used = {}

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.used = {}

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
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/trivia` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/trivia` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/trivia` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            self.used[interaction.user.id] = True
            await interaction.response.defer()

            with open("trivia.json", "r", encoding="utf-8") as f:
                trivia_data = json.load(f)

            q1, a1 = random.choice(list(trivia_data.items()))
            q2, a2 = random.choice(list(trivia_data.items()))
            q3, a3 = random.choice(list(trivia_data.items()))
            question, answer = random.choice([(q1, a1), (q2, a2), (q3, a3)])

            await interaction.followup.send(f"Trivia Question: {question}\nYou have 60 seconds to answer!")

            def check(message):
                return message.channel == interaction.channel and message.author == interaction.user

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                user_answer = msg.content.strip().lower()

                correct = False
                if " or " in answer:
                    correct = user_answer in [a.strip().lower() for a in answer.split(" or ")]
                elif ", " in answer:
                    correct = sorted(user_answer.split(", ")) == sorted(answer.lower().split(", "))
                else:
                    correct = user_answer == answer.lower()

                if correct:
                    mydb = mysql.connector.connect(
                        host=os.getenv("db_host"),
                        user=os.getenv("db_user"),
                        password=os.getenv("db_password"),
                        database=os.getenv("db_name")
                    )
                    mycursor = mydb.cursor()
                    self.migrate_guild_id(mycursor, interaction.user.id, interaction.guild.id)
                    mycursor.execute("""
                        INSERT INTO trivia_users (user_id, allow_leaderboard)
                        VALUES (%s, 1)
                        ON DUPLICATE KEY UPDATE user_id = user_id
                    """, (interaction.user.id,))

                    mycursor.execute("""
                        INSERT INTO trivia_scores (user_id, guild_id, points)
                        VALUES (%s, %s, 1)
                        ON DUPLICATE KEY UPDATE points = points + 1
                    """, (interaction.user.id, interaction.guild.id))
                    mydb.commit()
                    mydb.close()

                    await interaction.followup.send(f"Correct! 🎉 {interaction.user.mention}, you earned a point!")
                else:
                    await interaction.followup.send(f"Wrong answer! The correct answer was: `{answer}`")

            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was: `{answer}`")

        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send("An error occurred. Please try again later.", ephemeral=True)

        finally:
            self.used.pop(interaction.user.id, None)

async def setup(bot):
    await bot.add_cog(Trivia(bot))
