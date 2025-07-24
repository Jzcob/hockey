import discord
import random
from discord.ext import commands
from discord import app_commands
import config
import mysql.connector
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("db_host"),
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        database=os.getenv("db_name")
    )

async def ensure_user_exists(db_conn, cursor, user: discord.Member):
    user_query = """
        INSERT INTO users (user_id, username)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE username = VALUES(username)
    """
    cursor.execute(user_query, (user.id, user.name))

    cursor.execute("SELECT user_id FROM user_levels WHERE user_id = %s", (user.id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO user_levels (user_id) VALUES (%s)", (user.id,))
    
    db_conn.commit()

class Confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red, custom_id='confirm_reset_all_levels_no_econ')
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor()
            cursor.execute("UPDATE user_levels SET level = 0, xp = 0.00")
            db_conn.commit()
            await interaction.response.send_message("All levels have been reset.", ephemeral=True)
            button.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("An error occurred while resetting levels.", ephemeral=True)
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()

class levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `leveling.py`")
    
    @app_commands.command(name='reset-levels', description="Resets the XP levels in the server.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def resetLevels(self, interaction: discord.Interaction):
        await interaction.response.send_message("Are you sure you would like to reset all of the levels in the server? This action is irreversible.", view=Confirm(), ephemeral=True)

    @app_commands.command(name='reset-member-level', description="Resets the XP and levels of a specified user.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def resetMemberLevel(self, interaction: discord.Interaction, user: discord.Member):
        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor()
            await ensure_user_exists(db_conn, cursor, user)
            query = "UPDATE user_levels SET level = 0, xp = 0.00 WHERE user_id = %s"
            cursor.execute(query, (user.id,))
            db_conn.commit()
            await interaction.response.send_message("Level reset.")
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("An error occurred.", ephemeral=True)
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()
    
    @app_commands.command(name='set-member-level', description="Set the level of a specified user.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def setMemberLevel(self, interaction: discord.Interaction, user: discord.Member, level: int):
        if level < 1:
            return await interaction.response.send_message("The number must be greater than 0")
        
        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor()
            await ensure_user_exists(db_conn, cursor, user)
            limit = [150.0, 225.0, 337.5, 506.25, 759.38, 1139.06, 1708.59, 2562.89, 3844.34, 5766.5, 8649.76, 12974.63, 19461.95, 29192.93, 43789.39, 65684.08, 98526.13, 147789.19, 221683.78, 332525.67]
            xp_for_level = limit[level - 1]
            
            query = "UPDATE user_levels SET level = %s, xp = %s WHERE user_id = %s"
            cursor.execute(query, (level, xp_for_level, user.id))
            db_conn.commit()
            await interaction.response.send_message("Level set.")
        except IndexError:
            await interaction.response.send_message(f"The max level you can set is {len(limit)}.", ephemeral=True)
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("An error occurred.", ephemeral=True)
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()

    @app_commands.command(name='level', description="Check what level you are.")
    async def level(self, interaction: discord.Interaction, user: discord.Member=None):
        target_user = user or interaction.user
        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor(dictionary=True)
            await ensure_user_exists(db_conn, cursor, target_user)
            
            query = "SELECT level, xp FROM user_levels WHERE user_id = %s"
            cursor.execute(query, (target_user.id,))
            user_data = cursor.fetchone()

            embed = discord.Embed(color=config.color)
            embed.set_author(name=f"{target_user.name}'s Level", icon_url=target_user.avatar.url if target_user.avatar else None)
            embed.add_field(name="__Level__", value=user_data['level'])
            embed.add_field(name="__XP__", value=f"{user_data['xp']:,.2f}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("Could not retrieve level information.", ephemeral=True)
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()

    @app_commands.command(name="level-leaderboard", description="Displays the leveling leaderboard for everyone in the server.")
    async def levelLeaderboard(self, interaction: discord.Interaction):
        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor(dictionary=True)
            query = """
                SELECT ul.user_id, ul.level, ul.xp
                FROM user_levels ul
                ORDER BY ul.level DESC, ul.xp DESC
                LIMIT 10
            """
            cursor.execute(query)
            leaderboard_data = cursor.fetchall()

            embed = discord.Embed(title="Level Leaderboard", color=config.color)
            if not leaderboard_data:
                embed.description = "The leaderboard is empty!"
            else:
                description = []
                for i, row in enumerate(leaderboard_data, 1):
                    user = self.bot.get_user(row['user_id']) or await self.bot.fetch_user(row['user_id'])
                    description.append(f"**{i}.** {user.mention} - Level: **{row['level']}** | XP: **{row['xp']:,.2f}**")
                embed.description = "\n".join(description)

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("An error occurred while fetching the leaderboard.", ephemeral=True)
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id != config.hockey_discord_server:
            return
        if message.author.bot or message.guild is None:
            return
        
        bad_channels = [892573395273789520, 942934115609608213, 865107660624756775]
        if message.channel.id in bad_channels:
            return

        db_conn = None
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor(dictionary=True)
            await ensure_user_exists(db_conn, cursor, message.author)
            
            cursor.execute("SELECT level, xp FROM user_levels WHERE user_id = %s", (message.author.id,))
            user_data = cursor.fetchone()
            
            current_level = user_data['level']
            current_xp = float(user_data['xp'])
            
            xp_to_add = random.uniform(1, 3)
            new_xp = round(current_xp + xp_to_add, 2)
            
            limit = [150.0, 225.0, 337.5, 506.25, 759.38, 1139.06, 1708.59, 2562.89, 3844.34, 5766.5, 8649.76, 12974.63, 19461.95, 29192.93, 43789.39, 65684.08, 98526.13, 147789.19, 221683.78, 332525.67]
            
            new_level = current_level
            if current_level < len(limit) and new_xp >= limit[current_level]:
                new_level += 1
                await message.channel.send(f'{message.author.mention} has leveled up to level **{new_level}**!')
                update_query = "UPDATE user_levels SET level = %s, xp = %s WHERE user_id = %s"
                cursor.execute(update_query, (new_level, new_xp, message.author.id))
            else:
                update_query = "UPDATE user_levels SET xp = %s WHERE user_id = %s"
                cursor.execute(update_query, (new_xp, message.author.id))
            
            db_conn.commit()
        except Exception as e:
            print(traceback.format_exc())
        finally:
            if db_conn and db_conn.is_connected():
                db_conn.close()

async def setup(bot):
    await bot.add_cog(levels(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
