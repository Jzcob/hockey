import discord
from discord.ext import commands
from discord import app_commands
import requests
import json
import config
import asyncio
import random

class GuessTheTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `guessTheTeam.py`")
    
    @app_commands.command(name="guess-the-team", description="Guess the team!")
    async def guessTheTeam(self, interaction: discord.Interaction):
        # Get a team from the API
        try:
            response = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
            teams = json.loads(response.text)["teams"]
            team = random.choice(teams)["name"]
            
            # Scramble the team name
            scrambled_team = "".join(random.sample(team, len(team)))
            
            # Send the scrambled team name
            await interaction.response.send_message(f"Unscramble this team name: `{scrambled_team}`, you have 30 seconds!")
            
            # Wait for a response from the user that sent the message
            def check(message):
                return message.content.lower() == team.lower()
            
            try:
                message = await self.bot.wait_for("message", check=check, timeout=30.0)
                await interaction.followup.send(f"Congratulations, {message.author.mention}! You unscrambled the team name!")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Sorry, time's up!, the correct answer was `{team}`.")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/guess-the-team`", description=f"```{e}```", color=config.color)
            embed.add_field(name="Team Chosen", value=f"{team}", inline=False)
            embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
            embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
            await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GuessTheTeam(bot))