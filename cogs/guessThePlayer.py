import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import asyncio
import aiomysql
import aiohttp
import config
from datetime import datetime
import traceback
from thefuzz import fuzz
import json

# --- Global Constants ---
SIMILARITY_THRESHOLD = 85 

class GTP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_pool = bot.db_pool  
        self.http_session = aiohttp.ClientSession() 
        self.used = {}

    async def cog_unload(self):
        await self.http_session.close()

    async def migrate_gtp_async(self, cursor, user_id, actual_guild_id):
        await cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
        row = await cursor.fetchone()
        if row:
            points_from_zero = row[0]
            await cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s AND guild_id = %s", (user_id, actual_guild_id))
            exists = await cursor.fetchone()
            if exists:
                await cursor.execute("""
                    UPDATE gtp_scores
                    SET points = points + %s
                    WHERE user_id = %s AND guild_id = %s
                """, (points_from_zero, user_id, actual_guild_id))
                await cursor.execute("DELETE FROM gtp_scores WHERE user_id = %s AND guild_id = 0", (user_id,))
            else:
                await cursor.execute("""
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
            
            max_retries = 5
            x = None
            while max_retries > 0:
                team = random.choice(list(teams.keys()))
                team_name = teams[team]
                url = f"https://api-web.nhle.com/v1/roster/{team}/current"
                
                async with self.http_session.get(url) as response:
                    if response.status == 200:
                        x = await response.json()
                        break
                    else:
                        max_retries -= 1
                        continue
            
            if not x:
                return await interaction.followup.send("Could not fetch a roster from the NHL API right now. Please try again later.")

            positions = ["forwards", "defensemen", "goalies"]
            position = random.choice(positions)
            roster = x.get(position, [])
            
            if not roster:
                return await interaction.followup.send(f"No players found for `{team_name}` ({position}). Try again!")

            player = random.choice(roster)
            first_name = player.get("firstName", {}).get("default", "Unknown")
            last_name = player.get("lastName", {}).get("default", "Unknown")
            full_name = f"{first_name} {last_name}"
            position_code = player.get("positionCode", "Unknown")
            position_full = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}.get(position_code, "Unknown")
            hint = f"(Hint: Their name starts with `{first_name[0]}` and they play `{position_full}`)"

            await interaction.followup.send(f"Guess the player from the `{team_name}`! You have 15 seconds! {hint}")

            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=15.0)
                user_answer = msg.content.strip().lower()
                correct_answer = full_name.lower()
                correct = False

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
                            
                            try:
                                await confirm_msg.delete()
                                await confirm_response.delete()
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                        except asyncio.TimeoutError:
                            await interaction.edit_original_response(content="Confirmation timed out.")

                if correct:
                    try:
                        async with self.db_pool.acquire() as conn:
                            async with conn.cursor() as cursor:
                                if interaction.guild:
                                    await self.migrate_gtp_async(cursor, msg.author.id, interaction.guild.id)
                                
                                await cursor.execute("""
                                    INSERT INTO gtp_users (user_id, allow_leaderboard) VALUES (%s, 1)
                                    ON DUPLICATE KEY UPDATE user_id = user_id
                                """, (msg.author.id,))
                                await cursor.execute("""
                                    INSERT INTO gtp_scores (user_id, guild_id, points) VALUES (%s, %s, 1)
                                    ON DUPLICATE KEY UPDATE points = points + 1
                                """, (msg.author.id, interaction.guild.id))
                    except Exception as db_error:
                        print(f"GTP DB Error: {db_error}")
                        return await interaction.followup.send("A database error occurred.", ephemeral=True)

                    await interaction.followup.send(f"Correct! 🎉 The player was `{full_name}`. Well done, {msg.author.mention}!")
                else:
                    await interaction.followup.send(f"Sorry, that's not right. The player was `{full_name}`.")

            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was `{full_name}`.")

        except Exception as e:
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GTP(bot))