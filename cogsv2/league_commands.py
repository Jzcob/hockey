import discord
from discord import app_commands
from discord.ext import commands
import config
# Import the classes directly
from strategies.nhl_strategy import NHL
from strategies.pwhl_strategy import PWHLStrategy

class HockeyLeagues(commands.GroupCog, name="league"):
    def __init__(self, bot):
        self.bot = bot
        # We instantiate the strategies here for the hub to use
        self.strategies = {
            "nhl": self.bot.get_cog("NHL") or NHL(bot),
            "pwhl": PWHLStrategy(bot)
        }

    async def get_strat(self, interaction: discord.Interaction, league_val: str):
        strat = self.strategies.get(league_val)
        if league_val == "nhl" and strat is None:
            strat = self.bot.get_cog("NHL")
            self.strategies["nhl"] = strat
            
        if not strat:
            await interaction.response.send_message("League logic not implemented or loaded yet!", ephemeral=True)
            return None
        return strat

    @app_commands.command(name="today", description="Get today's games for a specific league")
    @app_commands.choices(league=[
        app_commands.Choice(name="NHL", value="nhl"),
        app_commands.Choice(name="PWHL", value="pwhl")
    ])
    async def today(self, interaction: discord.Interaction, league: app_commands.Choice[str]):
        strat = await self.get_strat(interaction, league.value)
        if strat:
            # Calls the shared logic method
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

async def setup(bot):
    # Added guild ID support as per your previous snippet
    await bot.add_cog(HockeyLeagues(bot), guilds=[discord.Object(id=config.hockey_discord_server)])