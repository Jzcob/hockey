import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime, timedelta
import time
import json
import config

class schedule(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `schedule.py`")
    

    @app_commands.command(name="schedule", description="Gets the schedule of a team!")
    @app_commands.choices(length=[
        discord.app_commands.Choice(name="Today", value="today"),
        discord.app_commands.Choice(name="Tomorrow", value="tomorrow"),
        discord.app_commands.Choice(name="1 Week", value="week"),
    ])
    async def schedule(self, interaction: discord.Interaction, length: discord.app_commands.Choice[str],  team: str):
        teamID = config.checkForTeam(team)
        if teamID == None:
            return await interaction.response.send_message("Team not found!", ephemeral=True)
        await interaction.response.send_message("Searching for game...", ephemeral=True)
        try:
            if length.value == "today":
                date = datetime.today().strftime('%Y-%m-%d')
                scheduleURL = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamID}&date={date}"
                scheduleGet = requests.get(scheduleURL)
                scheduleTotalGames = scheduleGet.json()['totalGames']
                if scheduleTotalGames == 0:
                    return await interaction.followup.send("No games found!", ephemeral=True)
                for i in range(scheduleTotalGames):
                    games = scheduleGet.json()['dates'][i]['games']
                    for game in games:
                        gameID = game['gamePK']
                        gameBoxScoreURL = f"https://statsapi.web.nhl.com/api/v1/game/{gameID}/boxscore"
                        gameBoxScoreGet = requests.get(gameBoxScoreURL)
                        home = gameBoxScoreGet.json()['teams']['home']['team']['name']
                        homeScore = gameBoxScoreGet.json()['teams']['home']['teamStats']['teamSkaterStats']['goals']
                        homeShots = gameBoxScoreGet.json()['teams']['home']['teamStats']['teamSkaterStats']['shots']
                        homeWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['wins']
                        homeLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['losses']
                        homeOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['ot']
                        homeRecord = f"{homeWins}-{homeLosses}-{homeOT}"
                        away = gameBoxScoreGet.json()['teams']['away']['team']['name']
                        awayScore = gameBoxScoreGet.json()['teams']['away']['teamStats']['teamSkaterStats']['goals']
                        awayShots = gameBoxScoreGet.json()['teams']['away']['teamStats']['teamSkaterStats']['shots']
                        awayWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['wins']
                        awayLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['losses']
                        awayOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['ot']
                        awayRecord = f"{awayWins}-{awayLosses}-{awayOT}"
                        embed = discord.Embed(title=f"{away} @ {home}", description=f"Score: {awayScore} - {homeScore}\nShots: {awayShots} - {homeShots}", color=config.color)
                        embed.add_field(name=f"{away}", value=f"Record: {awayRecord}", inline=True)
                        embed.add_field(name=f"{home}", value=f"Record: {homeRecord}", inline=True)
                        embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
                        embed.set_footer(text=f"Game ID: {gameID}")
                        return await interaction.followup.send(embed=embed, ephemeral=True)
            elif length.value == "tomorrow":
                try:
                    date = datetime.today() + timedelta(days=1)
                    date = date.strftime('%Y-%m-%d')
                    scheduleURL = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamID}&date={date}"
                    scheduleGet = requests.get(scheduleURL)
                    scheduleTotalGames = scheduleGet.json()['totalGames']
                    if scheduleTotalGames == 0:
                        return await interaction.followup.send("No games found!", ephemeral=True)
                    for i in range(scheduleTotalGames):
                        games = scheduleGet.json()['dates'][i]['games']
                        for game in games:
                            gameID = scheduleGet.json()['dates'][i]['games'][0]['gamePk']
                            gameBoxScoreURL = f"https://statsapi.web.nhl.com/api/v1/game/{gameID}/boxscore"
                            gameBoxScoreGet = requests.get(gameBoxScoreURL)
                            home = gameBoxScoreGet.json()['teams']['home']['team']['name']
                            homeWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['wins']
                            homeLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['losses']
                            homeOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['ot']
                            homeRecord = f"{homeWins}-{homeLosses}-{homeOT}"
                            away = gameBoxScoreGet.json()['teams']['away']['team']['name']
                            awayWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['wins']
                            awayLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['losses']
                            awayOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['ot']
                            awayRecord = f"{awayWins}-{awayLosses}-{awayOT}"
                            gameDate = scheduleGet.json()['dates'][i]['games'][0]['gameDate']
                            gameDate = datetime.strptime(gameDate, "%Y-%m-%dT%H:%M:%SZ")
                            newDate = gameDate - timedelta(hours=4)
                            gameDate = newDate.timestamp()
                            embed = discord.Embed(title=f"{away} @ {home}", description=f"Game Date: <t:{int(gameDate)}>", color=config.color)
                            embed.add_field(name=f"{away}", value=f"Record: {awayRecord}", inline=True)
                            embed.add_field(name=f"{home}", value=f"Record: {homeRecord}", inline=True)
                            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
                            embed.set_footer(text=f"Game ID: {gameID}")
                            await interaction.followup.send(embed=embed, ephemeral=True)
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"Something went wrong! `{e}`", ephemeral=True)
            elif length.value == "week":
                startDate = datetime.today()
                startDate = startDate.strftime('%Y-%m-%d')
                endDate = datetime.today() + timedelta(days=7)
                endDate = endDate.strftime('%Y-%m-%d')
                scheduleURL = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamID}&startDate={startDate}&endDate={endDate}"
                scheduleGet = requests.get(scheduleURL)
                scheduleTotalGames = scheduleGet.json()['totalGames']
                x = 0
                embed = discord.Embed(title=f"Schedule for the week", color=config.color)
                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
                if scheduleTotalGames == 0:
                    return await interaction.followup.send("No games found!", ephemeral=True)
                for i in range(scheduleTotalGames):
                    games = scheduleGet.json()['dates'][i]['games']
                    try:
                        for game in games:
                            try:
                                gameID = scheduleGet.json()['dates'][i]['games'][x]['gamePk']
                            except Exception as e:
                                error_channel = self.bot.get_channel(config.error_channel)
                                embed = discord.Embed(title="Error with `/schedule`", description=f"Something went wrong! `{e}`", color=config.color)
                            gameBoxScoreURL = f"https://statsapi.web.nhl.com/api/v1/game/{gameID}/boxscore"
                            gameBoxScoreGet = requests.get(gameBoxScoreURL)
                            home = gameBoxScoreGet.json()['teams']['home']['team']['name']
                            homeWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['wins']
                            homeLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['losses']
                            homeOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['home']['leagueRecord']['ot']
                            homeRecord = f"{homeWins}-{homeLosses}-{homeOT}"
                            away = gameBoxScoreGet.json()['teams']['away']['team']['name']
                            awayWins = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['wins']
                            awayLosses = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['losses']
                            awayOT = scheduleGet.json()['dates'][i]['games'][0]['teams']['away']['leagueRecord']['ot']
                            awayRecord = f"{awayWins}-{awayLosses}-{awayOT}"
                            gameDate = scheduleGet.json()['dates'][i]['games'][x]['gameDate']
                            gameDate = datetime.strptime(gameDate, "%Y-%m-%dT%H:%M:%SZ")
                            gameDate = gameDate.timestamp()
                            embed.add_field(name=f"{away} @ {home}", value=f"Game Date: <t:{int(gameDate)}> \n\n Away Record: {awayRecord}\nHome Record: {homeRecord}\nGame ID: {gameID}", inline=False)
                            x += 1
                    except Exception as e:
                        error_channel = self.bot.get_channel(config.error_channel)
                        embed = discord.Embed(title="Error with `/schedule`", description=f"Something went wrong! `{e}`", color=config.color)
                    x = 0
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/schedule`", description=f"Something went wrong! `{e}`", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
            embed.add_field(name="Team", value=team, inline=True)
            embed.add_field(name="Length", value=length.value, inline=True)
            embed.set_footer(text=f"Game ID: {gameID}")
            embed.add_field(name="User", value=interaction.user.mention, inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            embed.add_field(name="Channel", value=interaction.channel.name, inline=True)
            return await error_channel.send(content="<@920797181034778655>", embed=embed)

async def setup(bot):
    await bot.add_cog(schedule(bot))