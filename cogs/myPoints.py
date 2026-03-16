import discord
from discord.ext import commands
from discord import app_commands
import aiomysql
import os
from dotenv import load_dotenv
import config
import traceback
from datetime import datetime

load_dotenv()

class MyPoints(commands.Cog, name="MyPoints"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = bot.db_pool 
        print("MyPoints Cog: Database pool is accessible.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `myPoints.py`")

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    # Fix: Safe check for guild name
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    
                    # Fix: Safe check for parent command name
                    if interaction.command.parent:
                        full_command_name = f"{interaction.command.parent.name} {interaction.command.name}"
                    else:
                        full_command_name = interaction.command.name
                        
                    await command_log_channel.send(f"`/{full_command_name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed: {e}")

    mypoints = app_commands.Group(name="mypoints", description="Commands for viewing your points in various games.")

    @mypoints.command(name="fantasy", description="View your points in the fantasy league.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fantasy_points(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            result = None
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT points FROM rosters WHERE user_id = %s", (interaction.user.id,))
                    result = await cursor.fetchone()
            
            points = result['points'] if result else 0
            await interaction.followup.send(f"You have `{points:,}` fantasy point{'s' if points != 1 else ''}!", ephemeral=True)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error in fantasy_points:```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    # --- Trivia Points ---
    @mypoints.command(name="trivia", description="View your trivia points for this server.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def trivia_points(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Fix: Fallback for DM context
            guild_id = interaction.guild.id if interaction.guild else 0
            location_text = "in this server" if interaction.guild else "in DMs"

            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT points FROM trivia_scores WHERE user_id = %s AND guild_id = %s", (interaction.user.id, guild_id))
                    result = await cursor.fetchone()

            points = result['points'] if result else 0
            await interaction.followup.send(f"You have `{points:,}` trivia point{'s' if points != 1 else ''} {location_text}!", ephemeral=True)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error in trivia_points:```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @mypoints.command(name="gtp", description="Check your Guess The Player points for this server.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def gtp_points(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)

            # Fix: Fallback for DM context
            guild_id = interaction.guild.id if interaction.guild else 0
            location_text = "in this server" if interaction.guild else "in DMs"

            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = %s", (interaction.user.id, guild_id))
                    result = await cursor.fetchone()

            points = result['points'] if result else 0
            await interaction.followup.send(f"You have `{points:,}` Guess The Player point{'s' if points != 1 else ''} {location_text}!", ephemeral=True)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error in gtp_points:```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MyPoints(bot))