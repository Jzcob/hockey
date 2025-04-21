import discord
from discord import app_commands
from discord.ext import commands
import traceback
import config
import requests
import json
import datetime
from discord.ui import View, Button
from discord import Embed, Interaction, ButtonStyle

class BracketPaginator(View):
    def __init__(self, embeds, user):
        super().__init__(timeout=120) 
        self.embeds = embeds
        self.user = user
        self.index = 0

        self.prev_button = Button(label="Previous", style=ButtonStyle.gray)
        self.next_button = Button(label="Next", style=ButtonStyle.gray)

        self.prev_button.callback = self.go_previous
        self.next_button.callback = self.go_next

        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.embeds) - 1

    async def go_previous(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You can't use this paginator.", ephemeral=True)
            return

        self.index -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    async def go_next(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You can't use this paginator.", ephemeral=True)
            return

        self.index += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)


def strings(awayAbbreviation, homeAbbreviation, home, away):
    if awayAbbreviation == "ANA":
        awayString = f"{config.anahiem_ducks_emoji} {away}"
    elif awayAbbreviation == "BOS":
        awayString = f"{config.boston_bruins_emoji} {away}"
    elif awayAbbreviation == "BUF":
        awayString = f"{config.buffalo_sabres_emoji} {away}"
    elif awayAbbreviation == "CGY":
        awayString = f"{config.calgary_flames_emoji} {away}"
    elif awayAbbreviation == "CAR":
        awayString = f"{config.carolina_hurricanes_emoji} {away}"
    elif awayAbbreviation == "CHI":
        awayString = f"{config.chicago_blackhawks_emoji} {away}"
    elif awayAbbreviation == "COL":
        awayString = f"{config.colorado_avalanche_emoji} {away}"
    elif awayAbbreviation == "CBJ":
        awayString = f"{config.columbus_blue_jackets_emoji} {away}"
    elif awayAbbreviation == "DAL":
        awayString = f"{config.dallas_stars_emoji} {away}"
    elif awayAbbreviation == "DET":
        awayString = f"{config.detroit_red_wings_emoji} {away}"
    elif awayAbbreviation == "EDM":
        awayString = f"{config.edmonton_oilers_emoji} {away}"
    elif awayAbbreviation == "FLA":
        awayString = f"{config.florida_panthers_emoji} {away}"
    elif awayAbbreviation == "LAK":
        awayString = f"{config.los_angeles_kings_emoji} {away}"
    elif awayAbbreviation == "MIN":
        awayString = f"{config.minnesota_wild_emoji} {away}"
    elif awayAbbreviation == "MTL":
        awayString = f"{config.montreal_canadiens_emoji} {away}"
    elif awayAbbreviation == "NSH":
        awayString = f"{config.nashville_predators_emoji} {away}"
    elif awayAbbreviation == "NJD":
        awayString = f"{config.new_jersey_devils_emoji} {away}"
    elif awayAbbreviation == "NYI":
        awayString = f"{config.new_york_islanders_emoji} {away}"
    elif awayAbbreviation == "NYR":
        awayString = f"{config.new_york_rangers_emoji} {away}"
    elif awayAbbreviation == "OTT":
        awayString = f"{config.ottawa_senators_emoji} {away}"
    elif awayAbbreviation == "PHI":
        awayString = f"{config.philadelphia_flyers_emoji} {away}"
    elif awayAbbreviation == "PIT":
        awayString = f"{config.pittsburgh_penguins_emoji} {away}"
    elif awayAbbreviation == "SJS":
        awayString = f"{config.san_jose_sharks_emoji} {away}"
    elif awayAbbreviation == "SEA":
        awayString = f"{config.seattle_kraken_emoji} {away}"
    elif awayAbbreviation == "STL":
        awayString = f"{config.st_louis_blues_emoji} {away}"
    elif awayAbbreviation == "TBL":
        awayString = f"{config.tampa_bay_lightning_emoji} {away}"
    elif awayAbbreviation == "TOR":
        awayString = f"{config.toronto_maple_leafs_emoji} {away}"
    elif awayAbbreviation == "UTA":
        awayString = f"{config.utah_hockey_club_emoji} {away}"
    elif awayAbbreviation == "VAN":
        awayString = f"{config.vancouver_canucks_emoji} {away}"
    elif awayAbbreviation == "VGK":
        awayString = f"{config.vegas_golden_knights_emoji} {away}"
    elif awayAbbreviation == "WSH":
        awayString = f"{config.washington_capitals_emoji} {away}"
    elif awayAbbreviation == "WPG":
        awayString = f"{config.winnipeg_jets_emoji} {away}"
    else:
        awayString = f"{away}"
    if homeAbbreviation == "ANA":
        homeString = f"{home} {config.anahiem_ducks_emoji}"
    elif homeAbbreviation == "BOS":
        homeString = f"{home} {config.boston_bruins_emoji}"
    elif homeAbbreviation == "BUF":
        homeString = f"{home} {config.buffalo_sabres_emoji}"
    elif homeAbbreviation == "CGY":
        homeString = f"{home} {config.calgary_flames_emoji}"
    elif homeAbbreviation == "CAR":
        homeString = f"{home} {config.carolina_hurricanes_emoji}"
    elif homeAbbreviation == "CHI":
        homeString = f"{home} {config.chicago_blackhawks_emoji}"
    elif homeAbbreviation == "COL":
        homeString = f"{home} {config.colorado_avalanche_emoji}"
    elif homeAbbreviation == "CBJ":
        homeString = f"{home} {config.columbus_blue_jackets_emoji}"
    elif homeAbbreviation == "DAL":
        homeString = f"{home} {config.dallas_stars_emoji}"
    elif homeAbbreviation == "DET":
        homeString = f"{home} {config.detroit_red_wings_emoji}"
    elif homeAbbreviation == "EDM":
        homeString = f"{home} {config.edmonton_oilers_emoji}"
    elif homeAbbreviation == "FLA":
        homeString = f"{home} {config.florida_panthers_emoji}"
    elif homeAbbreviation == "LAK":
        homeString = f"{home} {config.los_angeles_kings_emoji}"
    elif homeAbbreviation == "MIN":
        homeString = f"{home} {config.minnesota_wild_emoji}"
    elif homeAbbreviation == "MTL":
        homeString = f"{home} {config.montreal_canadiens_emoji}"
    elif homeAbbreviation == "NSH":
        homeString = f"{home} {config.nashville_predators_emoji}"
    elif homeAbbreviation == "NJD":
        homeString = f"{home} {config.new_jersey_devils_emoji}"
    elif homeAbbreviation == "NYI":
        homeString = f"{home} {config.new_york_islanders_emoji}"
    elif homeAbbreviation == "NYR":
        homeString = f"{home} {config.new_york_rangers_emoji}"
    elif homeAbbreviation == "OTT":
        homeString = f"{home} {config.ottawa_senators_emoji}"
    elif homeAbbreviation == "PHI":
        homeString = f"{home} {config.philadelphia_flyers_emoji}"
    elif homeAbbreviation == "PIT":
        homeString = f"{home} {config.pittsburgh_penguins_emoji}"
    elif homeAbbreviation == "SJS":
        homeString = f"{home} {config.san_jose_sharks_emoji}"
    elif homeAbbreviation == "SEA":
        homeString = f"{home} {config.seattle_kraken_emoji}"
    elif homeAbbreviation == "STL":
        homeString = f"{home} {config.st_louis_blues_emoji}"
    elif homeAbbreviation == "TBL":
        homeString = f"{home} {config.tampa_bay_lightning_emoji}"
    elif homeAbbreviation == "TOR":
        homeString = f"{home} {config.toronto_maple_leafs_emoji}"
    elif homeAbbreviation == "UTA":
        homeString = f"{home} {config.utah_hockey_club_emoji}"
    elif homeAbbreviation == "VAN":
        homeString = f"{home} {config.vancouver_canucks_emoji}"
    elif homeAbbreviation == "VGK":
        homeString = f"{home} {config.vegas_golden_knights_emoji}"
    elif homeAbbreviation == "WSH":
        homeString = f"{home} {config.washington_capitals_emoji}"
    elif homeAbbreviation == "WPG":
        homeString = f"{home} {config.winnipeg_jets_emoji}"
    else:
        homeString = f"{home}"
    
    return awayString, homeString

class playoffs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `playoffs.py`")
    
    @app_commands.command(name="brackets", description="Get the current NHL playoff brackets")
    async def brackets(self, interaction: discord.Interaction):
        try:
            if config.command_log_bool:
                command_log_channel = self.bot.get_channel(config.command_log)
                await command_log_channel.send(
                    f"`/brackets` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.datetime.now()}`\n---"
                )

            url = "https://api-web.nhle.com/v1/playoff-series/carousel/20242025/"
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"NHL API returned status {response.status_code}")
            data = response.json()

            season = url.split("/")[-2]
            rounds = data.get("rounds", [])
            embeds = []
            
            for rnd in rounds:
                round_label = rnd.get("roundLabel", f"Round {rnd.get('roundNumber', '?')}")
                embed = discord.Embed(
                    title=f"{round_label} – NHL {season[:4]}–{season[4:]}",
                    color=discord.Color.blurple(),
                    url="https://www.nhl.com/playoffs/2025/bracket"
                )

                for series in rnd.get("series", []):
                    top = series.get("topSeed", {})
                    bottom = series.get("bottomSeed", {})
                    needed = series.get("neededToWin", 4)

                    top_abbr = top.get("abbrev", "???")
                    bottom_abbr = bottom.get("abbrev", "???")
                    top_wins = top.get("wins", 0)
                    bottom_wins = bottom.get("wins", 0)

                    try:
                        bottom_string, top_string = strings(bottom_abbr, top_abbr, bottom_abbr, top_abbr)
                    except:
                        bottom_string, top_string = bottom_abbr, top_abbr

                    if top_wins >= needed or bottom_wins >= needed:
                        status = "✅ Completed"
                    elif top_wins > 0 or bottom_wins > 0:
                        status = "🟡 In Progress"
                    else:
                        status = "🕓 Scheduled"

                    if "logo" in top and not embed.thumbnail.url:
                        embed.set_thumbnail(url=top["logo"])

                    raw_link = series.get("seriesLink")
                    link = f"https://www.nhl.com{raw_link}" if raw_link else "https://www.nhl.com/playoffs/"
                    letter = series.get("seriesLetter", "?")

                    matchup = f"{bottom_string} ({bottom_wins}) vs {top_string} ({top_wins})"
                    series_status = f"{matchup} — *{status}*\n[View Series {letter}]({link})"

                    embed.add_field(
                        name=f"Series {letter}",
                        value=series_status,
                        inline=False
                    )

                embed.set_footer(text=config.footer)
                embeds.append(embed)

            if not embeds:
                await interaction.response.send_message("The playoff bracket has not been finalized yet.")
                return

            view = BracketPaginator(embeds, interaction.user)
            await interaction.response.send_message(embed=embeds[0], view=view)

        except Exception:
            error_channel = self.bot.get_channel(920797181034778655)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message("Error with command. Message has been sent to Bot Developers.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(playoffs(bot), guilds=[discord.Object(id=config.hockey_discord_server)])