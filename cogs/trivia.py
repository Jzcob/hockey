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

    @app_commands.command(name="trivia-leaderboard", description="View the trivia leaderboards!")
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def trivia_leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        try:
            await interaction.response.defer()
            msg = await interaction.original_response()

            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            self.migrate_guild_id(mycursor, interaction.user.id, interaction.guild.id)

            if global_view:
                mycursor.execute("""
                    SELECT ts.user_id, SUM(ts.points) AS total_points, tu.allow_leaderboard
                    FROM trivia_scores ts
                    JOIN trivia_users tu ON ts.user_id = tu.user_id
                    GROUP BY ts.user_id
                    HAVING tu.allow_leaderboard = 1
                    ORDER BY total_points DESC
                    LIMIT 10
                """)
            else:
                mycursor.execute("""
                    SELECT ts.user_id, ts.points, tu.allow_leaderboard
                    FROM trivia_scores ts
                    JOIN trivia_users tu ON ts.user_id = tu.user_id
                    WHERE ts.guild_id = %s AND tu.allow_leaderboard = 1
                    ORDER BY ts.points DESC
                    LIMIT 10
                """, (interaction.guild.id,))

            myresult = mycursor.fetchall()
            title = "🌐 Global Trivia Leaderboard" if global_view else "Trivia Leaderboard"
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_footer(text=config.footer)
            lb = ""
            for i, (user_id, points, allow) in enumerate(myresult, start=1):
                name = "Anonymous" if not allow else (await self.bot.fetch_user(user_id)).name
                lb += f"{i}. `{name}` - `{points:,}` point{'s' if points != 1 else ''}\n"

            embed.description = lb or "No entries yet!"
            await msg.edit(embed=embed)
            mydb.commit()
            mydb.close()
        except Exception as e:
            traceback.print_exc()
            await msg.edit(content="An error occurred. Please try again later.")

    @app_commands.command(name="trivia-leaderboard-status", description="Toggles if you are displayed on the trivia leaderboard!")
    @app_commands.describe(allow="On to be shown (default), Off to not be shown.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def trivia_leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        try:
            allow_bool = allow.value == 't'
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
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE allow_leaderboard = %s
            """, (interaction.user.id, allow_bool, allow_bool))
            mydb.commit()
            mydb.close()
            await interaction.response.send_message(f"Trivia leaderboard status updated to `{allow_bool}`", ephemeral=True)
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message("Error occurred while updating your leaderboard status.", ephemeral=True)

    @app_commands.command(name="my-trivia-points", description="View your trivia points!")
    async def my_trivia_points(self, interaction: discord.Interaction):
        try:
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            self.migrate_guild_id(mycursor, interaction.user.id, interaction.guild.id)
            mycursor.execute("SELECT points FROM trivia_scores WHERE user_id = %s AND guild_id = %s",
                             (interaction.user.id, interaction.guild.id))
            result = mycursor.fetchone()

            if not result:
                points = 0
                mycursor.execute("""
                    INSERT INTO trivia_users (user_id, allow_leaderboard) 
                    VALUES (%s, 1) 
                    ON DUPLICATE KEY UPDATE user_id = user_id
                """, (interaction.user.id,))
                mycursor.execute("""
                    INSERT INTO trivia_scores (user_id, guild_id, points) 
                    VALUES (%s, %s, 0)
                """, (interaction.user.id, interaction.guild.id))
                mydb.commit()
            else:
                points = result[0]

            await interaction.response.send_message(f"You have `{points:,}` point{'s' if points != 1 else ''} in this server!", ephemeral=True)
            mydb.commit()
            mydb.close()
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message("An error occurred while retrieving your points.", ephemeral=True)

    @app_commands.command(name="trivia", description="Answer trivia questions to earn points!")
    async def trivia(self, interaction: discord.Interaction):
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
