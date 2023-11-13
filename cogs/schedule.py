import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import time

class schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `schedule.py`")
    
    @app_commands.command(name="schedule", description="Get the schedule for the week for a team! (e.g. BOS, NYR, etc.)")
    async def schedule(self, interaction: discord.Interaction, abbreviation: str):
        teams = {
            "ANA": "Anaheim Ducks",
            "ARI": "Arizona Coyotes",
            "BOS": "Boston Bruins",
            "BUF": "Buffalo Sabres",
            "CGY": "Calgary Flames",
            "CAR": "Carolina Hurricanes",
            "CHI": "Chicago Blackhawks",
            "COL": "Colorado Avalanche",
            "CBJ": "Columbus Blue Jackets",
            "DAL": "Dallas Stars",
            "DET": "Detroit Red Wings",
            "EDM": "Edmonton Oilers",
            "FLA": "Florida Panthers",
            "LAK": "Los Angeles Kings",
            "MIN": "Minnesota Wild",
            "MTL": "Montreal Canadiens",
            "NSH": "Nashville Predators",
            "NJD": "New Jersey Devils",
            "NYI": "New York Islanders",
            "NYR": "New York Rangers",
            "OTT": "Ottawa Senators",
            "PHI": "Philadelphia Flyers",
            "PIT": "Pittsburgh Penguins",
            "SJS": "San Jose Sharks",
            "STL": "St. Louis Blues",
            "TBL": "Tampa Bay Lightning",
            "TOR": "Toronto Maple Leafs",
            "VAN": "Vancouver Canucks",
            "VGK": "Vegas Golden Knights",
            "WSH": "Washington Capitals",
            "WPG": "Winnipeg Jets"
        }
        if abbreviation.upper() in teams:
            team = abbreviation.upper()
            team = teams[team]

        else:
            await interaction.response.send_message("Invalid team abbreviation. Please try again. e.g. `/schedule BOS`", ephemeral=True)
            return
        try:
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/now'
            r = requests.get(url)
            data = r.json()
            await interaction.response.defer()
            msg = await interaction.original_response()
            games = data['games']
            embed = discord.Embed(title=f"{team} Schedule", color=config.color)
            for i in range(len(games)):
                gameID = data['games'][i]['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                home = game2["homeTeam"]["name"]["default"]
                away = game2["awayTeam"]["name"]["default"]
                startTime = games[i]['startTimeUTC']
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                start_timestamp = int(startTime.timestamp())
                
                

                embed.add_field(name=f"<t:{start_timestamp}:F>", value=f"{away} @ {home}", inline=False)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=f"NHL API | https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/now")
            await msg.edit(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/schedule`", description=f"Something went wrong! `{e}`", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Game")
            embed.add_field(name="Team", value=team, inline=True)
            embed.set_footer(text=f"Game ID: {gameID}")
            embed.add_field(name="User", value=interaction.user.mention, inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            embed.add_field(name="Channel", value=interaction.channel.name, inline=True)
            await interaction.followup.send("Error getting schedule! Message has been sent to Bot Developers", ephemeral=True)
            return await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(schedule(bot))