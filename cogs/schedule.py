import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import traceback

class schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `schedule.py`")
    
    @app_commands.command(name="schedule", description="Get the schedule for the week for a team! (e.g. BOS, NYR, etc.)")
    @app_commands.allowed_installs(guilds=True, users=True)
    async def schedule(self, interaction: discord.Interaction, abbreviation: str):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/schedule` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/schedule` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/schedule` used by `{interaction.user.name}` in `{interaction.guild.name}` team `{abbreviation}` at `{datetime.now()}`\n---")
        teams = {
            "ANA": "Anaheim Ducks",
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
            "SEA": "Seattle Kraken",
            "SJS": "San Jose Sharks",
            "STL": "St. Louis Blues",
            "TBL": "Tampa Bay Lightning",
            "TOR": "Toronto Maple Leafs",
            "UTA": "Utah Hockey Club",
            "VAN": "Vancouver Canucks",
            "VGK": "Vegas Golden Knights",
            "WSH": "Washington Capitals",
            "WPG": "Winnipeg Jets"
        }
        if abbreviation.upper() in teams:
            team = abbreviation.upper()
            team = teams[team]

        else:
            await interaction.response.send_message("Invalid team abbreviation. `/teams` to see all of the abbreviations!", ephemeral=True)
            return
        try:
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/now'
            r = requests.get(url)
            data = r.json()
            await interaction.response.defer()
            msg = await interaction.original_response()
            games = data['games']
            embed = discord.Embed(title=f"{team}'s schedule!", color=config.color)
            for i in range(len(games)):
                gameID = data['games'][i]['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                home = game2["homeTeam"]["name"]["default"]
                away = game2["awayTeam"]["name"]["default"]
                startTime = games[i]['startTimeUTC']
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime - timedelta(hours=5)
                start_timestamp = int(startTime.timestamp())
                embed.add_field(name=f"<t:{start_timestamp}:F>", value=f"{away} @ {home}", inline=False)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)
            await msg.edit(embed=embed)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
async def setup(bot):
    await bot.add_cog(schedule(bot))