import mysql.connector
import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback
import os


class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `leaderboards.py`")

    @app_commands.command(name="leaderboard", description="View the leaderboards!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def leaderboards(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            if interaction.guild == None:
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/leaderboard` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
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
            mycursor.execute("SELECT * FROM gtp ORDER BY points DESC LIMIT 10")
            myresult = mycursor.fetchall()
            embed = discord.Embed(title="Leaderboard", color=0x00ff00)
            embed.set_footer(text=config.footer)
            i = 1
            lb = ""
            for x in myresult:
                if x[2] == False:
                    name = "Anonymous"
                else:
                    name = await self.bot.fetch_user(x[0])
                    name = name.name
                if x[1] == 1:
                    lb += f"{i}. `{name}` - `{x[1]}` point\n"
                else:
                    lb += f"{i}. `{name}` - `{x[1]:,}` points\n"
                i += 1
            embed.description = f"Points are based on correct guesses from `/guess-the-player`!\n\n {lb}"
            await msg.edit(embed=embed)
            mydb.close()
        except Exception as e:
            print(traceback.format_exc())
            await msg.edit(content="An error occurred. Please try again later.")
            if config.error_log_bool == True:
                error_log_channel = self.bot.get_channel(config.error_log)
                await error_log_channel.send(f"An error occurred in `/leaderboards`:\n```{traceback.format_exc()}```")
    
    @app_commands.command(name="leaderboard-status", description="Toggles if you are displayed on the leaderboard!")
    @app_commands.describe(allow="On to be shown (default), Off to not be shown.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/leaderboard-status` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            if allow.value == "t":
                allow = True
            else:
                allow = False
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            mycursor.execute(f"UPDATE gtp SET allow_leaderboard = {allow} WHERE id = {interaction.user.id}")
            mydb.commit()
            await interaction.response.send_message(content=f"Leaderboard status updated to `{allow}`", ephemeral=True)
            mydb.close()
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("Error with command, Message has been sent to Bot Developers")
            if config.error_log_bool == True:
                error_log_channel = self.bot.get_channel(config.error_log)
                await error_log_channel.send(f"An error occurred in `/leaderboard-status`:\n```{traceback.format_exc()}```")
    
    @app_commands.command(name="my-points", description="View your points!")
    async def my_points(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/my-points` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            mydb = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT points FROM gtp WHERE id = {interaction.user.id}")
            myresult = mycursor.fetchall()
            if len(myresult) == 0:
                mycursor.execute(f"INSERT INTO gtp (id, points, allow_leaderboard) VALUES ({interaction.user.id}, 0, true)")
                mydb.commit()
                points = 0
            else:
                points = myresult[0][0]
            await interaction.response.send_message(content=f"You have `{points:,}` points!", ephemeral=True)
            mydb.close()
        except Exception as e:
            print(traceback.format_exc())
            await interaction.response.send_message("Error with command, Message has been sent to Bot Developers")
            if config.error_log_bool == True:
                error_log_channel = self.bot.get_channel(config.error_log)
                await error_log_channel.send(f"An error occurred in `/my-points`:\n```{traceback.format_exc()}```")
    

        
async def setup(bot):
    await bot.add_cog(Leaderboards(bot))

