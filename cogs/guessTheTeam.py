import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import config
import traceback

class GuessTheTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `guessTheTeam.py`")
    
    @app_commands.command(name="guess-the-team", description="Guess the team!")
    @app_commands.checks.cooldown(1.0, 5.0, key=lambda i: (i.guild.id))
    @app_commands.checks.cooldown(1.0, 60.0, key=lambda i: (i.user.id))
    async def guessTheTeam(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            if interaction.guild == None:
                await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            teams = [
                "Anaheim Ducks",
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
                "Seattle Kraken",
                "San Jose Sharks",
                "St. Louis Blues",
                "Tampa Bay Lightning",
                "Toronto Maple Leafs",
                "Utah Hockey Club",
                "Vancouver Canucks",
                "Vegas Golden Knights",
                "Washington Capitals",
                "Winnipeg Jets"
            ]
            team = random.choice(teams)
            team2 = random.choice(teams)
            team3 = random.choice(teams)

            allTeams = [team, team2, team3]
            team = random.choice(allTeams)
            scramble_team = ''.join(random.sample(team, len(team)))
            embed = discord.Embed(title="Guess The Team", description=f"Guess the team you have 30 seconds!\n\n`{scramble_team}`", color=config.color)

            await interaction.response.send_message(embed=embed)

            def check(message):
                return message.content.lower() == team.lower()
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                await interaction.followup.send(f"Correct! {msg.author.mention} guessed the team!")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"You didn't answer in time! It was {team}")
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
    
    @guessTheTeam.error
    async def guessTheTeam_error(self, interaction: discord.Interaction , error):
        await interaction.response.send_message(f"Command on cooldown! Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        

async def setup(bot):
    await bot.add_cog(GuessTheTeam(bot))