import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import json
import config

class game(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `game.py`")
    

    @app_commands.command(name="game", description="Gets the information of a game!")
    async def game(self, interaction: discord.Interaction, team: str):
        try:
            if team == None:
                return await interaction.response.send_message("Must provide a team name!")
            else:
                await interaction.response.send_message("Searching for game...", ephemeral=True)
                teamID = config.checkForTeam(team)
                if teamID == None:
                    return await interaction.response.send_message("Team not found!", ephemeral=True)
                else:
                    scheduleURL = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamID}"
                    scheduleGet = requests.get(scheduleURL)
                    scheduleTotalGames = scheduleGet.json()['totalGames']
                    if scheduleTotalGames == 0:
                        return await interaction.followup.send("No games found!", ephemeral=True)
                    else:
                        for i in range(scheduleTotalGames):
                            gameID = scheduleGet.json()['dates'][i]['games'][0]['gamePk']
                            gameBoxScoreURL = f"https://statsapi.web.nhl.com/api/v1/game/{gameID}/boxscore"
                            gameBoxScoreGet = requests.get(gameBoxScoreURL)
                            home = gameBoxScoreGet.json()['teams']['home']['team']['name']
                            homeScore = gameBoxScoreGet.json()['teams']['home']['teamStats']['teamSkaterStats']['goals']
                            homeShots = gameBoxScoreGet.json()['teams']['home']['teamStats']['teamSkaterStats']['shots']
                            away = gameBoxScoreGet.json()['teams']['away']['team']['name']
                            awayScore = gameBoxScoreGet.json()['teams']['away']['teamStats']['teamSkaterStats']['goals']
                            awayShots = gameBoxScoreGet.json()['teams']['away']['teamStats']['teamSkaterStats']['shots']
                            embed = discord.Embed(title=f"{away} @ {home}", description=f"Score: {awayScore} - {homeScore}\nShots: {awayShots} - {homeShots}", color=config.color)
                            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
                            embed.set_footer(text=f"Game ID: {gameID}")
                            return await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Team", value=team)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.mention)
            embed.set_footer(text=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            await interaction.followup.send("Error getting game! Message has been sent to Bot Developers", ephemeral=True)
            return await error_channel.send(content="<@920797181034778655>",embed=embed)
    

async def setup(bot):
    await bot.add_cog(game(bot))