import discord
from discord import app_commands
from discord.ext import commands
import config
from typing import Literal

from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy

class HockeyLeagues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.strategies = {
            "nhl": self.bot.get_cog("nhl") or NHL(bot),
            "pwhl": self.bot.get_cog("pwhl") or PWHLStrategy(bot)
        }

    async def get_strat(self, interaction: discord.Interaction, league_val: str):
        strat = self.strategies.get(league_val)
        if not strat:
            strat = self.bot.get_cog(league_val)
            self.strategies[league_val] = strat
            
        if not strat:
            await interaction.response.send_message("League logic not implemented or loaded yet!", ephemeral=True)
            return None
        return strat

    @app_commands.command(name="today", description="Get today's schedule and scores")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
    async def today_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], date: str = None):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_today_games(interaction, date_str=date)

    @app_commands.command(name="yesterday", description="Get yesterday's scores")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def yesterday_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_yesterday_games(interaction)

    @app_commands.command(name="standings", description="Get the league standings")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
    async def standings_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], date: str = None):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_standings(interaction, date_str=date)

    @app_commands.command(name="schedule", description="Get the schedule for a specific team")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(date="Override date/context if needed (YYYY-MM-DD)")
    async def schedule_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], abbreviation: str, date: str = None):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_schedule(interaction, abbreviation, date_str=date)

    @app_commands.command(name="game", description="Check live or past game stats for a team")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(date="Override date for testing (YYYY-MM-DD)")
    async def game_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], abbreviation: str, date: str = None):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_game_info(interaction, abbreviation, date_str=date)

    @app_commands.command(name="player", description="Gets the complete career overview of a player")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def player_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], name: str):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_player_info(interaction, name)

    @app_commands.command(name="teams", description="Get all available team codes and abbreviations")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def teams_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_all_teams(interaction)

async def setup(bot):
    await bot.add_cog(HockeyLeagues(bot), guilds=[discord.Object(id=config.hockey_discord_server)])