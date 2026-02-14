import discord
from discord import app_commands
from discord.ext import commands
import requests
import config
from datetime import datetime
import pytz
import traceback

TEAM_EMOJIS = {
    "ANA": config.anahiem_ducks_emoji, "BOS": config.boston_bruins_emoji, "BUF": config.buffalo_sabres_emoji,
    "CGY": config.calgary_flames_emoji, "CAR": config.carolina_hurricanes_emoji, "CHI": config.chicago_blackhawks_emoji,
    "COL": config.colorado_avalanche_emoji, "CBJ": config.columbus_blue_jackets_emoji, "DAL": config.dallas_stars_emoji,
    "DET": config.detroit_red_wings_emoji, "EDM": config.edmonton_oilers_emoji, "FLA": config.florida_panthers_emoji,
    "LAK": config.los_angeles_kings_emoji, "MIN": config.minnesota_wild_emoji, "MTL": config.montreal_canadiens_emoji,
    "NSH": config.nashville_predators_emoji, "NJD": config.new_jersey_devils_emoji, "NYI": config.new_york_islanders_emoji,
    "NYR": config.new_york_rangers_emoji, "OTT": config.ottawa_senators_emoji, "PHI": config.philadelphia_flyers_emoji,
    "PIT": config.pittsburgh_penguins_emoji, "SJS": config.san_jose_sharks_emoji, "SEA": config.seattle_kraken_emoji,
    "STL": config.st_louis_blues_emoji, "TBL": config.tampa_bay_lightning_emoji, "TOR": config.toronto_maple_leafs_emoji,
    "UTA": config.utah_hockey_club_emoji, "VAN": config.vancouver_canucks_emoji, "VGK": config.vegas_golden_knights_emoji,
    "WSH": config.washington_capitals_emoji, "WPG": config.winnipeg_jets_emoji,
}

def strings(awayAbbrev, homeAbbrev, home, away):
    a_emoji = TEAM_EMOJIS.get(awayAbbrev, "")
    h_emoji = TEAM_EMOJIS.get(homeAbbrev, "")
    return f"{a_emoji} {away}".lstrip(), f"{home} {h_emoji}".rstrip()

class today(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="today", description="Get today's schedule!")
    async def today_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            hawaii = pytz.timezone('US/Hawaii')
            t_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{t_str}"
            
            r = requests.get(url)
            data = r.json()
            
            if not data["gameWeek"] or not data["gameWeek"][0]["games"]:
                await interaction.followup.send("No games today.")
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")

            for game in games:
                gs = game["gameState"]
                h_t, a_t = game["homeTeam"], game["awayTeam"]
                
                # FIX: Fallback logic
                h_name = h_t.get("placeName", {}).get("default") or h_t.get("commonName", {}).get("default", "TBD")
                a_name = a_t.get("placeName", {}).get("default") or a_t.get("commonName", {}).get("default", "TBD")
                
                a_str, h_str = strings(a_t["abbrev"], h_t["abbrev"], h_name, a_name)
                ts = int(datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc).timestamp())

                if gs in ("FUT", "PRE"):
                    embed.add_field(name=f"<t:{ts}:t>", value=f"{a_str} @ {h_str}\nScheduled", inline=False)
                else:
                    embed.add_field(name="Live/Final", value=f"{a_str} @ {h_str}\n{a_t.get('score',0)} - {h_t.get('score',0)}", inline=False)

            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error fetching schedule.")

async def setup(bot):
    await bot.add_cog(today(bot))