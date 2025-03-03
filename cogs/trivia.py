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

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `trivia.py`")

    @app_commands.command(name="trivia", description="Answer trivia questions to earn points!")
    @app_commands.checks.cooldown(1.0, 15.0, key=lambda i: (i.guild.id))
    @app_commands.checks.cooldown(1.0, 60.0, key=lambda i: (i.user.id))
    async def trivia(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/trivia` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as log_error:
                print(f"Command logging failed: {log_error}")

        used.update({interaction.user.id: True})
        await interaction.response.defer()

        try:
            with open("trivia.json", "r", encoding="utf-8") as f:
                trivia_data = json.load(f)

            question, answer = random.choice(list(trivia_data.items()))

            # Send the trivia question
            await interaction.followup.send(f"Trivia Question: {question}\nYou have 60 seconds to answer!")

            def check(message):
                return message.channel == interaction.channel and message.author == interaction.user

            try:
                # Wait for the user's answer
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                user_answer = msg.content.strip().lower()

                # Special handling for list answers
                if " or " in answer:
                    # If answer contains "or", split and check if user guessed either option
                    possible_answers = [a.strip().lower() for a in answer.split(" or ")]
                    if user_answer in possible_answers:
                        is_correct = True
                elif ", " in answer:
                    correct_answer_list = sorted(answer.lower().split(", "))
                    user_answer_list = sorted(user_answer.split(", "))
                    is_correct = correct_answer_list == user_answer_list
                else:
                    is_correct = user_answer == answer.lower()
                
                await command_log_channel.send(f"User answer: {user_answer}\nCorrect answer: {answer}\nIs correct: {is_correct}")
                if is_correct:
                    # Correct answer
                    mydb = mysql.connector.connect(
                        host=os.getenv("db_host"),
                        user=os.getenv("db_user"),
                        password=os.getenv("db_password"),
                        database=os.getenv("db_name")
                    )
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT * FROM trivia WHERE id = %s", (msg.author.id,))
                    myresult = mycursor.fetchone()

                    if not myresult:
                        mycursor.execute(
                            "INSERT INTO trivia (id, points, allow_leaderboard) VALUES (%s, %s, %s)",
                            (msg.author.id, 1, True)
                        )
                        await interaction.followup.send(
                            f"Correct! 🎉 {msg.author.mention}, you earned your first point! You've been added to the leaderboard!"
                        )
                    else:
                        points = myresult[1] + 1
                        mycursor.execute("UPDATE trivia SET points = %s WHERE id = %s", (points, msg.author.id))
                        await interaction.followup.send(
                            f"Correct! 🎉 {msg.author.mention}, you've earned another point! You now have `{points}` points!"
                        )

                    mydb.commit()
                    mydb.close()
                else:
                    # Incorrect answer
                    await interaction.followup.send(f"Wrong answer! The correct answer was: `{answer}`")

            except asyncio.TimeoutError:
                # No answer in time
                await interaction.followup.send(f"Time's up! The correct answer was: `{answer}`")

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error at {datetime.now()}:\n```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported to the developers.", ephemeral=True)

        finally:
            used.pop(interaction.user.id, None)

    @trivia.error
    async def trivia_error(self, interaction: discord.Interaction , error):
        if used.get(interaction.user.id) == True:
            await interaction.response.send_message("You have already used the command! Please allow the timer to end before using the command again!", ephemeral=True)
            return
        else:
            now = datetime.now()
            cmd_cool = int(error.retry_after) + 1
            new_time = time.mktime(now.timetuple()) + cmd_cool
            await interaction.response.send_message(f"Command on cooldown! Try again <t:{int(new_time)}:R>.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Trivia(bot))
