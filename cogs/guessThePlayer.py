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
        """Called when the cog is unloaded."""
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

    async def get_random_player(self):
        """Helper to fetch a random team and player from the NHL API."""
        try:
            with open("teams.json", "r") as f:
                teams = json.load(f)
            
            max_retries = 5
            x = None
            team_name = ""
            while max_retries > 0:
                team_abbr = random.choice(list(teams.keys()))
                team_name = teams[team_abbr]
                url = f"https://api-web.nhle.com/v1/roster/{team_abbr}/current"
                
                async with self.http_session.get(url) as response:
                    if response.status == 200:
                        x = await response.json()
                        break
                    max_retries -= 1
            
            if not x: return None

            positions = ["forwards", "defensemen", "goalies"]
            position = random.choice(positions)
            roster = x.get(position, [])
            if not roster: return None

            player_data = random.choice(roster)
            return {
                "team_name": team_name,
                "first": player_data.get("firstName", {}).get("default", "Unknown"),
                "last": player_data.get("lastName", {}).get("default", "Unknown"),
                "pos_code": player_data.get("positionCode", "Unknown")
            }
        except:
            return None

    @app_commands.command(name="guess-the-player", description="Solo mode: Guess the player yourself!")
    async def guess_the_player(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        data = await self.get_random_player()
        if not data:
            return await interaction.followup.send("Could not fetch a player. Please try again.")

        full_name = f"{data['first']} {data['last']}"
        pos_full = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}.get(data['pos_code'], "Unknown")
        hint = f"(Hint: Their name starts with `{data['first'][0]}` and they play `{pos_full}`)"

        embed = discord.Embed(title="🎯 Guess The Player!", description=f"Guess the NHL player from the `{data['team_name']}`! You have 15 seconds! {hint}", color=discord.Color.green())
        await interaction.followup.send(embed=embed)

        def check(m):
            return m.channel == interaction.channel and m.author == interaction.user

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=15.0)
            user_answer = msg.content.strip().lower()
            correct_answer = full_name.lower()

            if user_answer == correct_answer or fuzz.partial_ratio(user_answer, correct_answer) >= SIMILARITY_THRESHOLD:
                async with self.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        if interaction.guild:
                            await self.migrate_gtp_async(cursor, interaction.user.id, interaction.guild.id)
                        await cursor.execute("INSERT INTO gtp_users (user_id, allow_leaderboard) VALUES (%s, 1) ON DUPLICATE KEY UPDATE user_id = user_id", (interaction.user.id,))
                        await cursor.execute("INSERT INTO gtp_scores (user_id, guild_id, points) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE points = points + 1", (interaction.user.id, interaction.guild.id if interaction.guild else 0))
                
                await interaction.followup.send(f"Correct! 🎉 The player was `{full_name}`. Well done, {interaction.user.mention}!")
            else:
                await interaction.followup.send(f"Sorry, that's not right. The player was `{full_name}`.")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"Time's up! The correct answer was `{full_name}`.")

    @app_commands.command(name="gtp-race", description="Head-to-Head: First person in the channel to guess wins!")
    async def gtp_race(self, interaction: discord.Interaction):
        await interaction.response.defer()

        data = await self.get_random_player()
        if not data:
            return await interaction.followup.send("Could not fetch a player. Try again later.")

        full_name = f"{data['first']} {data['last']}"
        pos_full = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}.get(data['pos_code'], "Unknown")
        
        embed = discord.Embed(title="🏁 GuessThePlayer RACE START!", color=discord.Color.blue())
        embed.description = f"First person to guess the player from the **{data['team_name']}** wins!\n\n**Hint:** Starts with `{data['first'][0]}` | Position: `{pos_full}`"
        embed.set_footer(text="You have 20 seconds!")
        
        await interaction.followup.send(embed=embed)

        start_time = datetime.now()
        
        def race_check(m):
            return m.channel == interaction.channel and not m.author.bot

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = 20.0 - elapsed
            
            if remaining <= 0:
                await interaction.followup.send(f"⏱️ Time is up! No one guessed it. The player was `{full_name}`.")
                break

            try:
                msg = await self.bot.wait_for("message", check=race_check, timeout=remaining)
                user_ans = msg.content.strip().lower()
                
                if user_ans == full_name.lower() or fuzz.partial_ratio(user_ans, full_name.lower()) >= SIMILARITY_THRESHOLD:
                    try:
                        async with self.db_pool.acquire() as conn:
                            async with conn.cursor() as cursor:
                                g_id = interaction.guild.id if interaction.guild else 0
                                await self.migrate_gtp_async(cursor, msg.author.id, g_id)
                                await cursor.execute("INSERT INTO gtp_users (user_id, allow_leaderboard) VALUES (%s, 1) ON DUPLICATE KEY UPDATE user_id = user_id", (msg.author.id,))
                                await cursor.execute("INSERT INTO gtp_scores (user_id, guild_id, points) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE points = points + 1", (msg.author.id, g_id))
                    except Exception as e:
                        print(f"Race DB Error: {e}")

                    await msg.reply(f"🏆 **{msg.author.display_name}** got it first! The player was `{full_name}`!")
                    break
                else:
                    try: await msg.add_reaction("❌")
                    except: pass
                    
            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏱️ Time is up! No one guessed it. The player was `{full_name}`.")
                break

async def setup(bot):
    await bot.add_cog(GTP(bot), guilds=[discord.Object(id=config.hockey_discord_server)])