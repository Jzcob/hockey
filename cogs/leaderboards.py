# leaderboards.py
import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os
from dotenv import load_dotenv
import config
import traceback
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class Leaderboards(commands.Cog, name="Leaderboards"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = self.bot.db_pool 
        print("Leaderboards Cog: Database pool is accessible.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `leaderboards.py`")

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    # For grouped commands, the full name is needed
                    full_command_name = f"{interaction.command.parent.name} {interaction.command.name}"
                    await command_log_channel.send(f"`/{full_command_name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /{interaction.command.name}: {e}")

    # --- Parent Command Group ---
    leaderboard = app_commands.Group(name="leaderboard", description="Commands for viewing game leaderboards and stats.")

    # --- Fantasy League Leaderboard ---
    @leaderboard.command(name="fantasy", description="Displays the top 10 players in the fantasy league.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fantasy_leaderboard(self, interaction: discord.Interaction):
        if interaction.guild.id != config.hockey_discord_server:
            await interaction.response.send_message("This command can only be used in the bot development server for now.", ephemeral=True)
            return
        await self.log_command(interaction)
        db_conn = None
        cursor = None
        try:
            await interaction.response.defer()
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, points FROM rosters ORDER BY points DESC LIMIT 10")
            leaders = cursor.fetchall()

            if not leaders:
                if not interaction.is_expired():
                    await interaction.followup.send("There are no players on the fantasy leaderboard yet!")
                return

            embed = discord.Embed(title="🏆 Fantasy League Leaderboard", color=discord.Color.gold())
            description = []
            for rank, leader in enumerate(leaders, 1):
                try:
                    user = await self.bot.fetch_user(leader['user_id'])
                    user_name = user.display_name
                except discord.errors.NotFound:
                    user_name = f"Unknown User ({leader['user_id']})"
                
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                description.append(f"{rank_emoji} {user_name} - **{leader['points']}** points")
            
            embed.description = "\n".join(description)
            if not interaction.is_expired():
                await interaction.followup.send(embed=embed)

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

    # --- Trivia Leaderboard ---
    @leaderboard.command(name="trivia", description="View the trivia leaderboards!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def trivia_leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        await self.log_command(interaction)
        db_conn = None
        cursor = None
        try:
            await interaction.response.defer()
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor(dictionary=True)

            if global_view:
                cursor.execute("""
                    SELECT ts.user_id, SUM(ts.points) AS total_points
                    FROM trivia_scores ts
                    JOIN trivia_users tu ON ts.user_id = tu.user_id
                    WHERE tu.allow_leaderboard = 1
                    GROUP BY ts.user_id
                    ORDER BY total_points DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT ts.user_id, ts.points
                    FROM trivia_scores ts
                    JOIN trivia_users tu ON ts.user_id = tu.user_id
                    WHERE ts.guild_id = %s AND tu.allow_leaderboard = 1
                    ORDER BY ts.points DESC
                    LIMIT 10
                """, (interaction.guild.id,))

            myresult = cursor.fetchall()
            title = "🌐 Global Trivia Leaderboard" if global_view else f"Trivia Leaderboard for {interaction.guild.name}"
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_footer(text=config.footer)
            
            description = []
            for i, row in enumerate(myresult, start=1):
                user_id = row['user_id']
                points = row.get('total_points') or row.get('points', 0)
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except discord.errors.NotFound:
                    name = "Unknown User"
                description.append(f"{i}. `{name}` - `{points:,}` point{'s' if points != 1 else ''}")

            embed.description = "\n".join(description) if description else "No entries yet!"
            if not interaction.is_expired():
                await interaction.followup.send(embed=embed)

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

    # --- Guess The Player Leaderboard ---
    @leaderboard.command(name="gtp", description="View the Guess The Player leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def gtp_leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        await self.log_command(interaction)
        db_conn = None
        cursor = None
        try:
            await interaction.response.defer()
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor(dictionary=True)

            if global_view:
                cursor.execute("""
                    SELECT gs.user_id, SUM(gs.points) AS total_points
                    FROM gtp_scores gs
                    JOIN gtp_users gu ON gs.user_id = gu.user_id
                    WHERE gu.allow_leaderboard = 1
                    GROUP BY gs.user_id
                    ORDER BY total_points DESC
                    LIMIT 10
                """)
            else:
                cursor.execute("""
                    SELECT gs.user_id, gs.points
                    FROM gtp_scores gs
                    JOIN gtp_users gu ON gs.user_id = gu.user_id
                    WHERE gs.guild_id = %s AND gu.allow_leaderboard = 1
                    ORDER BY gs.points DESC
                    LIMIT 10
                """, (interaction.guild.id,))

            rows = cursor.fetchall()
            title = "🌐 Global Guess The Player Leaderboard" if global_view else f"GTP Leaderboard for {interaction.guild.name}"
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_footer(text=config.footer)

            description = []
            for i, row in enumerate(rows, start=1):
                user_id = row['user_id']
                points = row.get('total_points') or row.get('points', 0)
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except discord.errors.NotFound:
                    name = "Unknown User"
                description.append(f"{i}. `{name}` - `{points:,}` point{'s' if points != 1 else ''}")

            embed.description = "\n".join(description) if description else "No entries yet!"
            if not interaction.is_expired():
                await interaction.followup.send(embed=embed)

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

    # --- Trivia Leaderboard Status ---
    @leaderboard.command(name="trivia-status", description="Toggles if you are displayed on the trivia leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(allow="Choose 'on' to be shown (default), or 'off' to be hidden.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def trivia_leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        await self.log_command(interaction)
        db_conn = None
        cursor = None
        try:
            await interaction.response.defer(ephemeral=True)
            allow_bool = allow.value == 't'
            
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor()
            cursor.execute("""
                INSERT INTO trivia_users (user_id, allow_leaderboard)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE allow_leaderboard = %s
            """, (interaction.user.id, allow_bool, allow_bool))
            db_conn.commit()
            
            if not interaction.is_expired():
                await interaction.followup.send(f"Your trivia leaderboard visibility has been set to `{allow.name}`.", ephemeral=True)
        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

    # --- GTP Leaderboard Status ---
    @leaderboard.command(name="gtp-status", description="Toggles if you are displayed on the Guess The Player leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(allow="Choose 'on' to be shown (default), or 'off' to be hidden.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def gtp_leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        await self.log_command(interaction)
        db_conn = None
        cursor = None
        try:
            await interaction.response.defer(ephemeral=True)
            allow_bool = allow.value == 't'
            
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor()
            cursor.execute("""
                INSERT INTO gtp_users (user_id, allow_leaderboard)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE allow_leaderboard = %s
            """, (interaction.user.id, allow_bool, allow_bool))
            db_conn.commit()
            
            if not interaction.is_expired():
                await interaction.followup.send(f"Your Guess The Player leaderboard visibility has been set to `{allow.name}`.", ephemeral=True)
        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()


async def setup(bot):
    await bot.add_cog(Leaderboards(bot))
