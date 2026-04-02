import discord
from discord import app_commands
from discord.ext import commands
# Import your strategies
from strategies.nhl_strategy import NHLStrategy
from strategies.pwhl_strategy import PWHLStrategy
# from strategies.ahl_strategy import AHLStrategy
# from strategies.khl_strategy import KHLStrategy

class HockeyLeagues(commands.GroupCog, name="league"):
    def __init__(self, bot):
        self.bot = bot
        # This mapping is the heart of the Open/Closed Principle
        self.strategies = {
            "nhl": NHLStrategy(bot),
            "pwhl": PWHLStrategy(bot)
            # "ahl": AHLStrategy(bot),
            # "khl": KHLStrategy(bot)
        }

    # Helper to get strategy and handle errors
    async def get_strat(self, interaction: discord.Interaction, league_val: str):
        strat = self.strategies.get(league_val)
        if not strat:
            await interaction.response.send_message("League logic not implemented yet!", ephemeral=True)
            return None
        return strat

    @app_commands.command(name="today", description="Get today's games for a league")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def today(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_today_games(interaction)

    @app_commands.command(name="standings", description="Get the league standings")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def standings(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_standings(interaction)

    @app_commands.command(name="guess-the-player", description="Play Guess the Player for this league")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def gtp(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            await strat.get_random_player(interaction)

async def setup(bot):
    await bot.add_cog(HockeyLeagues(bot))