import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import config
from datetime import datetime
from datetime import timedelta

class today(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `today.py`")
    
    @app_commands.command(name="today", description="Get today's schedule!")
    async def team(self, interaction: discord.Interaction):
        #https://api-web.nhle.com/v1/schedule/2023-11-07
        today = datetime.today().strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/schedule/{today}"
        await interaction.response.defer()
        msg = await interaction.original_response()
        r = requests.get(url)
        data = r.json()
        try:
            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=f"NHL API | https://api-web.nhle.com/api/v1/schedule/{today}")
            for i in range(len(games)):
                game = data["gameWeek"][0]["games"][i]
                gameState = game["gameState"]
                gameID = game['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                startTime = game["startTimeUTC"]

                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime -= timedelta(hours=4)
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime.strftime('%I:%M %p')
                try:
                    if gameState == "FUT":
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        embed.add_field(name=f"{startTime}", value=f"{away} @ {home}\nGame is scheduled!", inline=False)
                    elif gameState == "FINAL":
                        homeScore = game2['boxscore']['linescore']['totals']['home']
                        awayScore = game2['boxscore']['linescore']['totals']['away']
                        homeShots = game2['boxscore']['shotsByPeriod'][-1]['home']
                        awayShots = game2['boxscore']['shotsByPeriod'][-1]['away']
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        embed.add_field(name=f"Final!", value=f"\n{away} @ {home}\nScore: {awayScore} | {homeScore}\nShots: {awayShots} | {homeShots}", inline=False)
                    elif gameState == "LIVE":
                        homeScore = game2['boxscore']['linescore']['totals']['home']
                        awayScore = game2['boxscore']['linescore']['totals']['away']
                        homeShots = game2['boxscore']['shotsByPeriod'][-1]['home']
                        awayShots = game2['boxscore']['shotsByPeriod'][-1]['away']
                        clock = game2['clock']['timeRemaining']
                        clockRunning = game2['clock']['running']
                        clockIntermission = game2['clock']['inIntermission']
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        if clockRunning == True:
                            embed.add_field(name=f"LIVE", value=f"{away} @ {home}\nScore: {awayScore} | {homeScore}\nShots: {awayShots} | {homeShots}\nTime: {clock}", inline=False)
                        if clockIntermission == True:
                            embed.add_field(name=f"Intermission!", value=f"{away} @ {home}\nScore: {awayScore} | {homeScore}\nShots: {awayShots} | {homeShots}", inline=False)
                    else:
                        home = game2["homeTeam"]["name"]["default"]
                        away = game2["awayTeam"]["name"]["default"]
                        embed.add_field(name=f"{startTime}", value=f"{away} @ {home}\nGame is scheduled!", inline=False)
                except:
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    embed.add_field(name=f"{startTime}", value=f"{away} @ {home}\nGame is scheduled!", inline=False)
            
            return await msg.edit(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error getting schedule! `{e}`")


async def setup(bot):
    await bot.add_cog(today(bot))