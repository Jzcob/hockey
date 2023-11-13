import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import config

class guessTheTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def on_ready(self):
        print("LOADED: `guessTheTeam.py`")
    
    @app_commands.command(name="guess-the-team", description="Guess the team!")
    async def guessTheTeam(self, interaction: discord.Interaction):
        try:
            teams = [
                "Anaheim Ducks",
                "Arizona Coyotes",
                "Boston Bruins",
                "Buffalo Sabres",
                "Calgary Flames",
                "Carolina Hurricanes",
                "Chicago Blackhawks",
                "Colorado Avalanche",
                "Columbus Blue Jackets",
                "Dallas Stars",
                "Detroit Red Wings",
                "Edmonton Oilers",
                "Florida Panthers",
                "Los Angeles Kings",
                "Minnesota Wild",
                "Montreal Canadiens",
                "Nashville Predators",
                "New Jersey Devils",
                "New York Islanders",
                "New York Rangers",
                "Ottawa Senators",
                "Philadelphia Flyers",
                "Pittsburgh Penguins",
                "San Jose Sharks",
                "St. Louis Blues",
                "Tampa Bay Lightning",
                "Toronto Maple Leafs",
                "Vancouver Canucks",
                "Vegas Golden Knights",
                "Washington Capitals",
                "Winnipeg Jets"
            ]
            team = random.choice(teams)
            scramble_team = ''.join(random.sample(team, len(team)))
            embed = discord.Embed(title="Guess The Team", description=f"Guess the team you have 30 seconds!\n\n{scramble_team}", color=config.color)

            await interaction.response.send_message(embed=embed, ephemeral=True)

            def check(message):
                return message.content.lower() == team.lower()
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                await interaction.followup.send(f"Correct! {msg.author.mention} guessed the team!", ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send("You didn't answer in time!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/guess-the-team`", description=f"```{e}```", color=config.color)
            embed.add_field(name="Team Chosen", value=f"{team}", inline=False)
            embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
            embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
            await interaction.followup.send("Error with `/guess-the-team`! Message has been sent to Bot Developers", ephemeral=True)
            await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuessTheTeam(bot))