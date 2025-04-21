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
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/guess-the-player` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
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
                "MTL": "Montréal Canadiens",
                "NSH": "Nashville Predators",
                "NJD": "New Jersey Devils",
                "NYI": "New York Islanders",
                "NYR": "New York Rangers",
                "OTT": "Ottawa Senators",
                "PHI": "Philadelphia Flyers",
                "PIT": "Pittsburgh Penguins",
                "SEA": "Seattle Kraken",
                "SJS": "San Jose Sharks",
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

            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user and m.content.lower() == full_name.lower()

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)

                mydb = mysql.connector.connect(
                    host=os.getenv("db_host"),
                    user=os.getenv("db_user"),
                    password=os.getenv("db_password"),
                    database=os.getenv("db_name")
                )
                mycursor = mydb.cursor()
                self.migrate_gtp(mycursor, msg.author.id, interaction.guild.id)

                mycursor.execute("""
                    INSERT INTO gtp_users (user_id, allow_leaderboard)
                    VALUES (%s, 1)
                    ON DUPLICATE KEY UPDATE user_id = user_id
                """, (msg.author.id,))

                mycursor.execute("""
                    INSERT INTO gtp_scores (user_id, guild_id, points)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE points = points + 1
                """, (msg.author.id, interaction.guild.id))
                mydb.commit()
                mydb.close()

                await interaction.followup.send(f"Correct! 🎉 The player was `{full_name}`. Well done, {msg.author.mention}!")

            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was `{full_name}`.")

        except Exception:
            await interaction.followup.send("An error occurred while processing your request.", ephemeral=True)
            traceback.print_exc()

    @app_commands.command(name="leaderboard", description="View Guess the Player leaderboard")
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        await interaction.response.defer()
        msg = await interaction.original_response()

        try:
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            self.migrate_gtp(mycursor, interaction.user.id, interaction.guild.id)

            if global_view:
                mycursor.execute("""
                    SELECT gs.user_id, SUM(gs.points) AS total_points, gu.allow_leaderboard
                    FROM gtp_scores gs
                    JOIN gtp_users gu ON gs.user_id = gu.user_id
                    GROUP BY gs.user_id
                    HAVING gu.allow_leaderboard = 1
                    ORDER BY total_points DESC
                    LIMIT 10
                """)
            else:
                mycursor.execute("""
                    SELECT gs.user_id, gs.points, gu.allow_leaderboard
                    FROM gtp_scores gs
                    JOIN gtp_users gu ON gs.user_id = gu.user_id
                    WHERE gs.guild_id = %s AND gu.allow_leaderboard = 1
                    ORDER BY gs.points DESC
                    LIMIT 10
                """, (interaction.guild.id,))

            rows = mycursor.fetchall()
            embed = discord.Embed(title="🏒 Guess The Player Leaderboard", color=0x00ff00)
            embed.set_footer(text=config.footer)
            lb = ""
            for i, (uid, pts, show) in enumerate(rows, start=1):
                name = "Anonymous" if not show else (await self.bot.fetch_user(uid)).name
                lb += f"{i}. `{name}` - `{pts:,}` point{'s' if pts != 1 else ''}\n"
            embed.description = lb or "No entries yet!"
            await msg.edit(embed=embed)
            mydb.close()
        except Exception as e:
            traceback.print_exc()
            await msg.edit(content="Failed to load leaderboard. Please try again later.")

    @app_commands.command(name="leaderboard-status", description="Toggle your leaderboard visibility")
    @app_commands.choices(allow=[
        app_commands.Choice(name="on", value="t"),
        app_commands.Choice(name="off", value="f")
    ])
    async def leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/leaderboard-status` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/leaderboard-status` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/leaderboard-status` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            allow_bool = allow.value == "t"
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            self.migrate_gtp(mycursor, interaction.user.id, interaction.guild.id)
            mycursor.execute("""
                INSERT INTO gtp_users (user_id, allow_leaderboard)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE allow_leaderboard = %s
            """, (interaction.user.id, allow_bool, allow_bool))
            mydb.commit()
            mydb.close()
            await interaction.response.send_message(f"Your leaderboard status is now `{allow_bool}`", ephemeral=True)
        except Exception:
            traceback.print_exc()
            await interaction.response.send_message("Error updating leaderboard status.", ephemeral=True)

    @app_commands.command(name="my-points", description="Check your Guess the Player points")
    async def my_points(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/my-points` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/my-points` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/my-points` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            self.migrate_gtp(mycursor, interaction.user.id, interaction.guild.id)

            mycursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = %s",
                             (interaction.user.id, interaction.guild.id))
            row = mycursor.fetchone()
            points = row[0] if row else 0

            await interaction.response.send_message(f"You have `{points:,}` point{'s' if points != 1 else ''} in this server!", ephemeral=True)
            mydb.commit()
            mydb.close()
        except Exception:
            traceback.print_exc()
            await interaction.response.send_message("Error retrieving your points.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GTP(bot))
