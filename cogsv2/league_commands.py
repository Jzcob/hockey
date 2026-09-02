import discord
from discord import app_commands
from discord.ext import commands
import config
import json

from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy, PWHL_TEAMS

# Global Autocomplete Function for Team Resolution
async def team_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    # Retrieve the 'league' parameter selected by the user
    league_param = getattr(interaction.namespace, 'league', None)
    
    # Safely extract string value regardless of whether Discord passes a Choice or str
    if hasattr(league_param, 'value'):
        league_val = str(league_param.value).lower()
    elif league_param:
        league_val = str(league_param).lower()
    else:
        league_val = "nhl"
    
    choices = []

    if league_val == "pwhl":
        for abbr, (name, emoji) in PWHL_TEAMS.items():
            if current.lower() in name.lower() or current.lower() in abbr.lower():
                choices.append(app_commands.Choice(name=f"{emoji} {name} ({abbr})", value=abbr))
    else:
        try:
            with open("teams.json", "r", encoding="utf-8") as f:
                teams_data = json.load(f)
            for abbr, name in teams_data.items():
                if current.lower() in name.lower() or current.lower() in abbr.lower():
                    choices.append(app_commands.Choice(name=f"{name} ({abbr})", value=abbr))
        except Exception:
            pass

    return choices[:25]


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
    async def today_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_today_games(interaction, date_str=None)

    @app_commands.command(name="tomorrow", description="Get tomorrow's schedule")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def tomorrow_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_tomorrow_games(interaction)

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
    async def standings_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_standings(interaction, date_str=None)

    @app_commands.command(name="schedule", description="Get the schedule for a specific team")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list")
    @app_commands.autocomplete(abbreviation=team_autocomplete)
    async def schedule_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], abbreviation: str):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_schedule(interaction, abbreviation, date_str=None)

    @app_commands.command(name="game", description="Check live or past game stats for a team")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list")
    @app_commands.autocomplete(abbreviation=team_autocomplete)
    async def game_cmd(self, interaction: discord.Interaction, league: app_commands.Choice[str], abbreviation: str):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_game_info(interaction, abbreviation, date_str=None)

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
    await bot.add_cog(HockeyLeagues(bot))