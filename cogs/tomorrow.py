import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import config
from datetime import datetime, timedelta
import pytz
import traceback
import asyncio

TEAM_EMOJIS = {
    "ANA": config.anahiem_ducks_emoji,
    "BOS": config.boston_bruins_emoji,
    "BUF": config.buffalo_sabres_emoji,
    "CGY": config.calgary_flames_emoji,
    "CAR": config.carolina_hurricanes_emoji,
    "CHI": config.chicago_blackhawks_emoji,
    "COL": config.colorado_avalanche_emoji,
    "CBJ": config.columbus_blue_jackets_emoji,
    "DAL": config.dallas_stars_emoji,
    "DET": config.detroit_red_wings_emoji,
    "EDM": config.edmonton_oilers_emoji,
    "FLA": config.florida_panthers_emoji,
    "LAK": config.los_angeles_kings_emoji,
    "MIN": config.minnesota_wild_emoji,
    "MTL": config.montreal_canadiens_emoji,
    "NSH": config.nashville_predators_emoji,
    "NJD": config.new_jersey_devils_emoji,
    "NYI": config.new_york_islanders_emoji,
    "NYR": config.new_york_rangers_emoji,
    "OTT": config.ottawa_senators_emoji,
    "PHI": config.philadelphia_flyers_emoji,
    "PIT": config.pittsburgh_penguins_emoji,
    "SJS": config.san_jose_sharks_emoji,
    "SEA": config.seattle_kraken_emoji,
    "STL": config.st_louis_blues_emoji,
    "TBL": config.tampa_bay_lightning_emoji,
    "TOR": config.toronto_maple_leafs_emoji,
    "UTA": config.utah_hockey_club_emoji,
    "VAN": config.vancouver_canucks_emoji,
    "VGK": config.vegas_golden_knights_emoji,
    "WSH": config.washington_capitals_emoji,
    "WPG": config.winnipeg_jets_emoji,
}

def strings(awayAbbreviation, homeAbbreviation, home, away):
    away_emoji = TEAM_EMOJIS.get(awayAbbreviation, "")
    home_emoji = TEAM_EMOJIS.get(homeAbbreviation, "")

    awayString = f"{away_emoji} {away}".lstrip()
    homeString = f"{home} {home_emoji}".rstrip()
    
    return awayString, homeString

class tomorrow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `tomorrow.py`")
    
    @app_commands.command(name="tomorrow", description="Get tomorrow's schedule!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def team(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/tomorrow` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/tomorrow` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/tomorrow` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        try:
            hawaii = pytz.timezone('US/Hawaii')
            dt = datetime.now(hawaii) + timedelta(days=1)
            today = dt.strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{today}"
            await interaction.response.defer()
            msg = await interaction.original_response()
            r = requests.get(url)
            global data
            data = r.json()
            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Tomorrow's Games", description=f"Total games tomorrow: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)
            for i in range(len(games)):
                game = data["gameWeek"][0]["games"][i]
                gameState = game["gameState"]
                gameID = game['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                startTime = game["startTimeUTC"]
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime - timedelta(hours=4)
                timestampUTC = int(round(startTime.timestamp()))
                startTime = startTime.strftime('%I:%M %p')
            
                if gameState == "FINAL" or gameState == "OFF":
                    homeScore = game2['homeTeam']['score']
                    awayScore = game2['awayTeam']['score']
                    home = game2["homeTeam"]["commonName"]["default"]
                    away = game2["awayTeam"]["commonName"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"Final!", value=f"\n{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\n", inline=False)
                    embed.set_footer(text=f"ID: {gameID}")
                else:
                    home = game2["homeTeam"]["commonName"]["default"]
                    away = game2["awayTeam"]["commonName"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"<t:{timestampUTC}:t>", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
                await asyncio.sleep(0.5)
            return await msg.edit(embed=embed)
        except:
            error_channel = self.bot.get_channel(error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)


async def setup(bot):
    await bot.add_cog(tomorrow(bot))