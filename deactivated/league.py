import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import config

class League(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        self.cursor = self.db.cursor()

    @app_commands.command(name="create-league", description="Create a new league")
    async def create_league(self, interaction: discord.Interaction, league_name: str):
        SQL = "CREATE TABLE IF NOT EXISTS league (id INT PRIMARY KEY AUTO_INCREMENT, team_one VARCHAR(255), team_two VARCHAR(255), team_three VARCHAR(255), team_four VARCHAR(255), team_five VARCHAR(255), bench_one VARCHAR(255), bench_two VARCHAR(255), bench_three VARCHAR(255), swapped BOOLEAN DEFAULT FALSE, aced BOOLEAN DEFAULT FALSE)"
        