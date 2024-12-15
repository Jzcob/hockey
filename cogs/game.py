import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import pytz
import traceback

gameIDs = {}

class game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `game.py`")
    
    @app_commands.command(name="game", description="Check the information for a game today! (e.g. BOS, NYR, etc.)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def game(self, interaction: discord.Interaction, abbreviation: str):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = interaction.guild.name if interaction.guild else "DMs"
            await command_log_channel.send(
                f"`/game` used by `{interaction.user.name}` in `{guild_name}` team `{abbreviation}` at `{datetime.now()}`\n---"
            )
        try:
            await interaction.response.defer()
            teams = {
                "ANA": "Anaheim Ducks", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres",
                "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes", "CHI": "Chicago Blackhawks",
                "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets", "DAL": "Dallas Stars",
                "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers",
                "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "MTL": "Montreal Canadiens",
                "NSH": "Nashville Predators", "NJD": "New Jersey Devils", "NYI": "New York Islanders",
                "NYR": "New York Rangers", "OTT": "Ottawa Senators", "PHI": "Philadelphia Flyers",
                "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks", "SEA": "Seattle Kraken",
                "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs",
                "UTA": "Utah Hockey Club", "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights",
                "WSH": "Washington Capitals", "WPG": "Winnipeg Jets"
            }

            abbreviation = abbreviation.upper()
            if abbreviation not in teams:
                await interaction.followup.send(
                    "Invalid team abbreviation. Use `/teams` to see all of the abbreviations!"
                )
                return

            team_name = teams[abbreviation]
            hawaii = pytz.timezone('US/Hawaii')
            today = datetime.now(hawaii).strftime('%Y-%m-%d')
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/{today}'
            
            response = requests.get(url)
            if response.status_code != 200:
                await interaction.followup.send(f"Failed to fetch schedule data for `{team_name}`.")
                return

            data = response.json()
            games = data.get('games', [])
            if not games:
                await interaction.followup.send(f"**{team_name}** do not play today!")
                return

            game = next((g for g in games if g.get('gameDate') == today), None)
            if not game:
                await interaction.followup.send(f"**{team_name}** do not play today!")
                return

            gameID = game.get('id')
            if not gameID:
                await interaction.followup.send("Could not retrieve game details. Please try again later.")
                return

            url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
            response2 = requests.get(url2)
            if response2.status_code != 200:
                await interaction.followup.send("Failed to fetch game details. Please try again later.")
                return

            data2 = response2.json()
            home = data2.get('homeTeam', {}).get('commonName', {}).get('default', 'Unknown Team')
            away = data2.get('awayTeam', {}).get('commonName', {}).get('default', 'Unknown Team')
            tvBroadcasts = data2.get('tvBroadcasts', [])
            networks = "\n".join(
                f"{b['network']} ({b.get('countryCode', 'Unknown')})"
                for b in tvBroadcasts
                if not (interaction.guild and interaction.guild.id in config.bruins_servers and b['network'] != "NESN")
            )

            if game['gameState'] in ["FUT", "PRE"]:
                startTime = datetime.strptime(
                    data2.get("startTimeUTC", ""), '%Y-%m-%dT%H:%M:%SZ'
                ) - timedelta(hours=5)
                startTimeFormatted = startTime.strftime('%I:%M %p')
                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"Game is scheduled for {startTimeFormatted}",
                    color=config.color
                )
            elif game['gameState'] in ["FINAL", "OFF"]:
                homeScore = data2.get('homeTeam', {}).get('score', 0)
                awayScore = data2.get('awayTeam', {}).get('score', 0)
                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"Final!\nScore: {awayScore} | {homeScore}",
                    color=config.color
                )
            else:
                homeScore = data2.get('homeTeam', {}).get('score', 0)
                awayScore = data2.get('awayTeam', {}).get('score', 0)
                homeShots = data2.get('homeTeam', {}).get('sog', 0)
                awayShots = data2.get('awayTeam', {}).get('sog', 0)
                clock = data2.get('clock', {}).get('timeRemaining', 'Unknown Time')
                clockRunning = data2.get('clock', {}).get('running', False)
                clockIntermission = data2.get('clock', {}).get('inIntermission', False)
                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"GAME IS LIVE!!!\n\nScore: {awayScore} - {homeScore}\nShots: {awayShots} - {homeShots}",
                    color=config.color
                )
                embed.add_field(name="Clock", value="Intermission" if clockIntermission else f"{clock}\n{'Running' if clockRunning else ''}", inline=False)

            embed.add_field(name="TV Broadcast", value=networks, inline=False)
            embed.add_field(name="Game ID", value=gameID, inline=False)
            embed.set_footer(text=config.footer)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")


    @game.error
    async def game_error(self, interaction: discord.Interaction, error):
        interaction.response.send_message("Error with command, Message has been sent to Bot Developers", ephemeral=True)
        error_channel = self.bot.get_channel(config.error_channel)
        await error_channel.send(f"<@920797181034778655>```{error}```")

async def setup(bot):
    await bot.add_cog(game(bot))