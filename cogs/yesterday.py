import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime, timedelta
import config
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

class yesterday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="yesterday", description="Get yesterday's schedule!")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = interaction.guild.name if interaction.guild else "DMs"
            await command_log_channel.send(f"`/yesterday` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")

        await interaction.response.defer()
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            y_date = (datetime.now(hawaii_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{y_date}"
            
            r = requests.get(url)
            data = r.json()

            if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
                await interaction.followup.send(embed=discord.Embed(title="Yesterday's Games", description="No games yesterday.", color=config.color))
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Yesterday's Games ({y_date})", description=f"Total games: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhle.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            for game in games:
                h_t, a_t = game["homeTeam"], game["awayTeam"]
                h_name = h_t.get("placeName", {}).get("default") or h_t.get("commonName", {}).get("default", "TBD")
                a_name = a_t.get("placeName", {}).get("default") or a_t.get("commonName", {}).get("default", "TBD")
                
                a_str, h_str = strings(a_t["abbrev"], h_t["abbrev"], h_name, a_name)
                
                outcome = game.get("gameOutcome", {}).get("lastPeriodType", "REG")
                status = "Final"
                if outcome == "OT": status = "Final (OT)"
                elif outcome == "SO": status = "Final (SO)"

                embed.add_field(
                    name=status,
                    value=f"{a_str} @ {h_str}\nScore: {a_t.get('score',0)} | {h_t.get('score',0)}",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("Error occurred.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(yesterday(bot))