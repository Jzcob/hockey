import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime, timedelta
import json
import config

class today(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `today.py`")
    
    @app_commands.command(name="today", description="Gets the schedule for today!")
    async def today(self, interaction: discord.Interaction, team: str=None):
        #https://statsapi.web.nhl.com/api/v1/schedule
        if team == None:
            await interaction.response.send_message("Searching for schedule...", ephemeral=True)
            try:
                scheduleURL = "https://statsapi.web.nhl.com/api/v1/schedule"
                scheduleGet = requests.get(scheduleURL)
                scheduleTotalGames = scheduleGet.json()['totalGames']
                embed = discord.Embed(title=f"Today's games", color=config.color)
                embed.set_author(icon_url=interaction.user.avatar.url, name="Today's Game(s)")
                for i in range(scheduleTotalGames):
                    game = scheduleGet.json()['dates'][0]['games'][i]
                    away = game['teams']['away']['team']['name']
                    awayScore = game['teams']['away']['score']
                    awayWins = game['teams']['away']['leagueRecord']['wins']
                    awayLosses = game['teams']['away']['leagueRecord']['losses']
                    try:
                        awayOT = game['teams']['away']['leagueRecord']['ot']
                    except:
                        awayOT = 0

                    home = game['teams']['home']['team']['name']
                    homeScore = game['teams']['home']['score']
                    homeWins = game['teams']['home']['leagueRecord']['wins']
                    homeLosses = game['teams']['home']['leagueRecord']['losses']
                    try:
                        homeOT = game['teams']['home']['leagueRecord']['ot']
                    except:
                        homeOT = 0
                    gameID = game['gamePk']
                    gamestatus = game['status']['detailedState']
                    gameDate = scheduleGet.json()['dates'][0]['games'][i]['gameDate']
                    gameDate = datetime.strptime(gameDate, "%Y-%m-%dT%H:%M:%SZ")
                    gameDate = gameDate.timestamp()

                    if gamestatus == "Final":
                        embed.add_field(name=f"{away} @ {home}", value=f"Final Score: {awayScore} - {homeScore}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    elif gamestatus == "Pre-Game":
                        start = games['gameDate']
                        t = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
                        t.timestamp()
                        embed.add_field(name=f"{away} @ {home}", value=f"Game starts at <t:{int(t.timestamp())}:F>\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    elif gamestatus == "In Progress":
                        embed.add_field(name=f"{away} @ {home}", value=f"Game is in progress! Score: {awayScore} - {homeScore}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    else:
                        embed.add_field(name=f"{away} @ {home}", value=f"Game is {gamestatus}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"Error getting schedule! `{e}`")
                return await interaction.followup.send("Error getting schedule! Message has been sent to Bot Developers", ephemeral=True)
        else:
            teamID = config.checkForTeam(team)
            if teamID == None:
                await interaction.response.send_message("Team not found!", ephemeral=True)
                return
            try:
                scheduleURL = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamID}"
                scheduleGet = requests.get(scheduleURL)
                scheduleTotalGames = scheduleGet.json()['totalGames']
                embed = discord.Embed(title=f"Today's games", color=config.color)
                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
                if scheduleTotalGames == 0:
                    await interaction.response.send_message("No games found!")
                    return
                for i in range(scheduleTotalGames):
                    games = scheduleGet.json()['dates'][0]['games'][i]
                    away = games['teams']['away']['team']['name']
                    awayScore = games['teams']['away']['score']
                    awayWins = games['teams']['away']['leagueRecord']['wins']
                    awayLosses = games['teams']['away']['leagueRecord']['losses']
                    try:
                        awayOT = games['teams']['away']['leagueRecord']['ot']
                    except:
                        awayOT = 0
                    home = games['teams']['home']['team']['name']
                    homeScore = games['teams']['home']['score']
                    homeWins = games['teams']['home']['leagueRecord']['wins']
                    homeLosses = games['teams']['home']['leagueRecord']['losses']
                    try:
                        homeOT = games['teams']['home']['leagueRecord']['ot']
                    except:
                        homeOT = 0
                    gameID = games['gamePk']
                    gamestatus = games['status']['detailedState']

                    if gamestatus == "Final":
                        embed.add_field(name=f"{away} @ {home}", value=f"Final Score: {awayScore} - {homeScore}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    elif gamestatus == "Pre-Game":
                        start = games['gameDate']
                        t = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
                        t.timestamp()
                        embed.add_field(name=f"{away} @ {home}", value=f"Game starts at <t:{int(t.timestamp())}:F>\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    elif gamestatus == "In Progress":
                        embed.add_field(name=f"{away} @ {home}", value=f"Game is in progress! Score: {awayScore} - {homeScore}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                    else:
                        embed.add_field(name=f"{away} @ {home}", value=f"Game is {gamestatus}\n{awayWins}-{awayLosses}-{awayOT} | {homeWins}-{homeLosses}-{homeOT}", inline=False)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"Error getting schedule! `{e}`")
                return await interaction.followup.send("Error getting schedule! THERE IS CURRENTLY AN ERROR WITH THE NHL API ALL HOCKEY BOTS DO NOT WORK!!!", ephemeral=True)
                #return await interaction.followup.send("Error getting schedule! Message has been sent to Bot Developers", ephemeral=True)


async def setup(bot):
    await bot.add_cog(today(bot))