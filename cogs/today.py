import discord
from discord import app_commands
from discord.ext import commands
import requests
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

class today(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `today.py`")
    
    @app_commands.command(name="today", description="Get today's schedule!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def today(self, interaction: discord.Interaction):
        try:
            eastern = pytz.timezone('US/Hawaii')
            today_str = datetime.now(eastern).strftime('%Y-%m-%d')
            
            url = f"https://api-web.nhle.com/v1/schedule/{today_str}"
            await interaction.response.defer()
            
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            
            if not data["gameWeek"] or not data["gameWeek"][0]["games"]:
                embed = discord.Embed(title="Today's Games", description="No games scheduled for today.", color=config.color)
                embed.set_footer(text=config.footer)
                await interaction.followup.send(embed=embed)
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games", description=f"Total games today: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            for game in games:
                gameState = game["gameState"]
                
                home_team = game["homeTeam"]
                away_team = game["awayTeam"]

                home_name = home_team["placeName"]["default"]
                away_name = away_team["placeName"]["default"]
                home_abbreviation = home_team["abbrev"]
                away_abbreviation = away_team["abbrev"]

                away_string, home_string = strings(away_abbreviation, home_abbreviation, home_name, away_name)

                utc_start_time = datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                timestamp_utc = int(utc_start_time.timestamp())

                if gameState in ("FUT", "PRE"):
                    embed.add_field(name=f"<t:{timestamp_utc}:t>", value=f"{away_string} @ {home_string}\nGame is scheduled!", inline=False)
                
                elif gameState in ("FINAL", "OFF"):
                    home_score = home_team.get('score', 0)
                    away_score = away_team.get('score', 0)
                    game_outcome = game.get("gameOutcome", {}).get("lastPeriodType")
                    
                    if game_outcome == "OT":
                        embed.add_field(name=f"Final (OT)", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    elif game_outcome == "SO":
                        embed.add_field(name=f"Final (SO)", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    else:
                        embed.add_field(name=f"Final", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)

                elif gameState in ("LIVE", "CRIT"):
                    game_id = game['id']
                    url2 = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                    r2 = requests.get(url2)
                    game2 = r2.json()

                    home_score = game2['homeTeam']['score']
                    away_score = game2['awayTeam']['score']
                    clock = game2.get('clock', {})
                    
                    period = game.get('periodDescriptor', {}).get('number')
                    period_ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "OT"}.get(period, f"P{period}")

                    if clock.get('inIntermission'):
                        embed.add_field(name=f"Intermission", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}", inline=False)
                    else:
                        time_remaining = clock.get('timeRemaining', '00:00')
                        embed.add_field(name=f"🔴 LIVE - {period_ordinal}", value=f"{away_string} @ {home_string}\nScore: {away_score} | {home_score}\n`{time_remaining}`", inline=False)

            await interaction.followup.send(embed=embed)

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(f"An error occurred while fetching data from the NHL API: {e}", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred with the command. Developers have been notified.", ephemeral=True)
    
    @today.error
    async def today_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command is on cooldown! Try again in {error.retry_after:.2f} seconds.")
        else:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await ctx.send("Error with command, Message has been sent to Bot Developers")
    


async def setup(bot):
    await bot.add_cog(today(bot))