import discord
from discord import app_commands
from discord.ext import commands
import traceback
import config
import requests
import datetime
from discord.ui import View, Button
from discord import Embed, Interaction, ButtonStyle

# --- Helper for Team Data ---
TEAM_MAP = {
    "ANA": ("anahiem_ducks_emoji", "Ducks"),
    "BOS": ("boston_bruins_emoji", "Bruins"),
    "BUF": ("buffalo_sabres_emoji", "Sabres"),
    "CGY": ("calgary_flames_emoji", "Flames"),
    "CAR": ("carolina_hurricanes_emoji", "Hurricanes"),
    "CHI": ("chicago_blackhawks_emoji", "Blackhawks"),
    "COL": ("colorado_avalanche_emoji", "Avalanche"),
    "CBJ": ("columbus_blue_jackets_emoji", "Blue Jackets"),
    "DAL": ("dallas_stars_emoji", "Stars"),
    "DET": ("detroit_red_wings_emoji", "Red Wings"),
    "EDM": ("edmonton_oilers_emoji", "Oilers"),
    "FLA": ("florida_panthers_emoji", "Panthers"),
    "LAK": ("los_angeles_kings_emoji", "Kings"),
    "MIN": ("minnesota_wild_emoji", "Wild"),
    "MTL": ("montreal_canadiens_emoji", "Canadiens"),
    "NSH": ("nashville_predators_emoji", "Predators"),
    "NJD": ("new_jersey_devils_emoji", "Devils"),
    "NYI": ("new_york_islanders_emoji", "Islanders"),
    "NYR": ("new_york_rangers_emoji", "Rangers"),
    "OTT": ("ottawa_senators_emoji", "Senators"),
    "PHI": ("philadelphia_flyers_emoji", "Flyers"),
    "PIT": ("pittsburgh_penguins_emoji", "Penguins"),
    "SJS": ("san_jose_sharks_emoji", "Sharks"),
    "SEA": ("seattle_kraken_emoji", "Kraken"),
    "STL": ("st_louis_blues_emoji", "Blues"),
    "TBL": ("tampa_bay_lightning_emoji", "Lightning"),
    "TOR": ("toronto_maple_leafs_emoji", "Maple Leafs"),
    "UTA": ("utah_hockey_club_emoji", "Utah HC"),
    "VAN": ("vancouver_canucks_emoji", "Canucks"),
    "VGK": ("vegas_golden_knights_emoji", "Golden Knights"),
    "WSH": ("washington_capitals_emoji", "Capitals"),
    "WPG": ("winnipeg_jets_emoji", "Jets"),
}

def get_team_string(abbr, is_home=True):
    data = TEAM_MAP.get(abbr)
    if not data:
        return abbr
    
    emoji_attr, _ = data
    emoji = getattr(config, emoji_attr, "")
    
    return f"{abbr} {emoji}" if is_home else f"{emoji} {abbr}"

class BracketPaginator(View):
    def __init__(self, embeds, user):
        super().__init__(timeout=120) 
        self.embeds = embeds
        self.user = user
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.embeds) - 1

    @discord.ui.button(label="Previous", style=ButtonStyle.gray)
    async def prev_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("This isn't your menu!", ephemeral=True)
        
        self.index -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="Next", style=ButtonStyle.gray)
    async def next_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            
        self.index += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        # Note: You'd need a reference to the message to edit it here, 
        # or just let the buttons sit disabled.

class playoffs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `playoffs.py`")

    def get_current_season(self):
        now = datetime.datetime.now()
        # If we are in July or later, the "current" season is the upcoming one
        if now.month >= 7:
            return f"{now.year}{now.year + 1}"
        else:
            return f"{now.year - 1}{now.year}"
    
    @app_commands.command(name="brackets", description="Get the current NHL playoff brackets")
    async def brackets(self, interaction: discord.Interaction):
        try:
            # Logging logic
            if config.command_log_bool:
                log_chan = self.bot.get_channel(config.command_log)
                if log_chan:
                    await log_chan.send(f"`/brackets` by `{interaction.user}` in `{interaction.guild}`")

            season = self.get_current_season()
            url = f"https://api-web.nhle.com/v1/playoff-series/carousel/{season}/"
            
            response = requests.get(url)
            if response.status_code != 200:
                return await interaction.response.send_message("NHL API is currently unavailable.", ephemeral=True)
            
            data = response.json()
            rounds = data.get("rounds", [])
            embeds = []
            
            for rnd in rounds:
                label = rnd.get("roundLabel", f"Round {rnd.get('roundNumber')}")
                embed = discord.Embed(
                    title=f"{label} – {season[:4]}-{season[4:]} NHL Playoffs",
                    color=discord.Color.blurple(),
                    url="https://www.nhl.com/playoffs/bracket"
                )

                for series in rnd.get("series", []):
                    top = series.get("topSeed", {})
                    bottom = series.get("bottomSeed", {})
                    
                    t_abbr, b_abbr = top.get("abbrev", "TBD"), bottom.get("abbrev", "TBD")
                    t_wins, b_wins = top.get("wins", 0), bottom.get("wins", 0)
                    needed = series.get("neededToWin", 4)

                    # Determine status icon
                    if t_wins >= needed or b_wins >= needed:
                        status = "✅ Final"
                    elif t_wins > 0 or b_wins > 0:
                        status = "🟡 In Progress"
                    else:
                        status = "🕓 Scheduled"

                    top_str = get_team_string(t_abbr, is_home=True)
                    bot_str = get_team_string(b_abbr, is_home=False)

                    raw_link = series.get("seriesLink")
                    link = f"https://www.nhl.com{raw_link}" if raw_link else "https://www.nhl.com/playoffs/"
                    
                    field_val = (
                        f"{bot_str} ({b_wins}) vs {top_str} ({t_wins})\n"
                        f"Status: *{status}* — [Series Link]({link})"
                    )

                    embed.add_field(
                        name=f"Series {series.get('seriesLetter', '?')}",
                        value=field_val,
                        inline=False
                    )

                embed.set_footer(text=config.footer)
                embeds.append(embed)

            if not embeds:
                return await interaction.response.send_message("No playoff data found for this season.")

            view = BracketPaginator(embeds, interaction.user)
            await interaction.response.send_message(embed=embeds[0], view=view)

        except Exception:
            err_chan = self.bot.get_channel(920797181034778655)
            if err_chan:
                await err_chan.send(f"Error in `/brackets`:\n```{traceback.format_exc()}```")
            await interaction.response.send_message("An internal error occurred.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(playoffs(bot))