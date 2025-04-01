import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import config
import traceback
from datetime import datetime

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
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if interaction.guild:
                    guild_name = interaction.guild.name or "Unknown Server"
                    await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
                else:
                    await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            except Exception as log_error:
                print(f"Command logging failed: {log_error}")

        await interaction.response.defer()

        try:
            teams = [
                "Anaheim Ducks", "Boston Bruins", "Buffalo Sabres", "Calgary Flames",
                "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
                "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings",
                "Edmonton Oilers", "Florida Panthers", "Los Angeles Kings",
                "Minnesota Wild", "Montréal Canadiens", "Nashville Predators",
                "New Jersey Devils", "New York Islanders", "New York Rangers",
                "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins",
                "Seattle Kraken", "San Jose Sharks", "St. Louis Blues",
                "Tampa Bay Lightning", "Toronto Maple Leafs", "Utah Hockey Club",
                "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals",
                "Winnipeg Jets"
            ]

            allTeams = random.sample(teams, 3)
            correct_team = random.choice(allTeams)
            scrambled_team = ''.join(random.sample(correct_team, len(correct_team)))

            # Create and send the embed
            embed = discord.Embed(
                title="Guess The Team",
                description=f"Guess the team! You have 30 seconds.\n\n`{scrambled_team}`",
                color=config.color
            )
            await interaction.followup.send(embed=embed)

            def check(message):
                return message.channel == interaction.channel and message.content.lower() == correct_team.lower()

            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                await interaction.followup.send(f"Correct! {msg.author.mention} guessed the team!")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was **{correct_team}**.")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            error_message = f"An error occurred in `/guess-the-team`:\n```{traceback.format_exc()}```"
            if error_channel:
                await error_channel.send(error_message)
            await interaction.followup.send(
                "An error occurred while processing your request. The issue has been reported to the bot developers.",
                ephemeral=True
            )
    
    @guessTheTeam.error
    async def guessTheTeam_error(self, interaction: discord.Interaction , error):
        await interaction.response.send_message(f"Command on cooldown! Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        

async def setup(bot):
    await bot.add_cog(GuessTheTeam(bot))