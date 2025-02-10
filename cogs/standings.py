import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import config
import traceback

def strings(name):
    if name == "Anaheim Ducks":
        string = f"{config.anahiem_ducks_emoji} {name}"
    elif name == "Boston Bruins":
        string = f"{config.boston_bruins_emoji} {name}"
    elif name == "Buffalo Sabres":
        string = f"{config.buffalo_sabres_emoji} {name}"
    elif name == "Calgary Flames":
        string = f"{config.calgary_flames_emoji} {name}"
    elif name == "Carolina Hurricanes":
        string = f"{config.carolina_hurricanes_emoji} {name}"
    elif name == "Chicago Blackhawks":
        string = f"{config.chicago_blackhawks_emoji} {name}"
    elif name == "Colorado Avalanche":
        string = f"{config.colorado_avalanche_emoji} {name}"
    elif name == "Columbus Blue Jackets":
        string = f"{config.columbus_blue_jackets_emoji} {name}"
    elif name == "Dallas Stars":
        string = f"{config.dallas_stars_emoji} {name}"
    elif name == "Detroit Red Wings":
        string = f"{config.detroit_red_wings_emoji} {name}"
    elif name == "Edmonton Oilers":
        string = f"{config.edmonton_oilers_emoji} {name}"
    elif name == "Florida Panthers":
        string = f"{config.florida_panthers_emoji} {name}"
    elif name == "Los Angeles Kings":
        string = f"{config.los_angeles_kings_emoji} {name}"
    elif name == "Minnesota Wild":
        string = f"{config.minnesota_wild_emoji} {name}"
    elif name == "Montréal Canadiens":
        string = f"{config.montreal_canadiens_emoji} {name}"
    elif name == "Nashville Predators":
        string = f"{config.nashville_predators_emoji} {name}"
    elif name == "New Jersey Devils":
        string = f"{config.new_jersey_devils_emoji} {name}"
    elif name == "New York Islanders":
        string = f"{config.new_york_islanders_emoji} {name}"
    elif name == "New York Rangers":
        string = f"{config.new_york_rangers_emoji} {name}"
    elif name == "Ottawa Senators":
        string = f"{config.ottawa_senators_emoji} {name}"
    elif name == "Philadelphia Flyers":
        string = f"{config.philadelphia_flyers_emoji} {name}"
    elif name == "Pittsburgh Penguins":
        string = f"{config.pittsburgh_penguins_emoji} {name}"
    elif name == "San Jose Sharks":
        string = f"{config.san_jose_sharks_emoji} {name}"
    elif name == "St. Louis Blues":
        string = f"{config.st_louis_blues_emoji} {name}"
    elif name == "Tampa Bay Lightning":
        string = f"{config.tampa_bay_lightning_emoji} {name}"
    elif name == "Toronto Maple Leafs":
        string = f"{config.toronto_maple_leafs_emoji} {name}"
    elif name == "Vancouver Canucks":
        string = f"{config.vancouver_canucks_emoji} {name}"
    elif name == "Vegas Golden Knights":
        string = f"{config.vegas_golden_knights_emoji} {name}"
    elif name == "Washington Capitals":
        string = f"{config.washington_capitals_emoji} {name}"
    elif name == "Winnipeg Jets":
        string = f"{config.winnipeg_jets_emoji} {name}"
    elif name == "Seattle Kraken":
        string = f"{config.seattle_kraken_emoji} {name}"
    elif name == "Utah Hockey Club":
        string = f"{config.utah_hockey_club_emoji} {name}"
    else:
        string = name

    return string



class standings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `standings.py`")
    
    @app_commands.command(name="standings", description="Get the standings!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def standings(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            if interaction.guild == None:
                await command_log_channel.send(f"`/standings` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/standings` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else:
                await command_log_channel.send(f"`/standings` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        today = datetime.today().strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/standings/{today}"
        r = requests.get(url)
        data = r.json()
        await interaction.response.defer()
        msg = await interaction.original_response()
        standings = data["standings"]
        atlantic = []
        metropolitan = []
        central = []
        pacific = []
        try:
            for i in range(len(standings)):
                divisionName = data["standings"][i]["divisionName"]
                if divisionName == "Atlantic":
                    atlanticString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    name = data['standings'][i]['teamName']['default']
                    wildcardSequence = data["standings"][i]["wildcardSequence"]
                    if wildcardSequence == 1 or wildcardSequence == 2:
                        wildcardSequence = ":wc:"
                    else:
                        wildcardSequence = ""
                    new_name = strings(name)
                    atlanticString += f"{new_name} ({wins}-{losses}-{otLosses}) {points}pts {wildcardSequence}"
                    atlantic.append(atlanticString)
                elif divisionName == "Metropolitan":
                    metropolitanString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    name = data['standings'][i]['teamName']['default']
                    wildcardSequence = data["standings"][i]["wildcardSequence"]
                    if wildcardSequence == 1 or wildcardSequence == 2:
                        wildcardSequence = ":wc:"
                    else:
                        wildcardSequence = ""
                    new_name = strings(name)
                    metropolitanString += f"{new_name} ({wins}-{losses}-{otLosses}) {points}pts {wildcardSequence}"
                    metropolitan.append(metropolitanString)
                elif divisionName == "Central":
                    centralString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    name = data['standings'][i]['teamName']['default']
                    wildcardSequence = data["standings"][i]["wildcardSequence"]
                    if wildcardSequence == 1 or wildcardSequence == 2:
                        wildcardSequence = ":joker:"
                    else:
                        wildcardSequence = ""
                    new_name = strings(name)
                    centralString += f"{new_name} ({wins}-{losses}-{otLosses}) {points}pts {wildcardSequence}"
                    central.append(centralString)
                elif divisionName == "Pacific":
                    pacificString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    name = data['standings'][i]['teamName']['default']
                    wildcardSequence = data["standings"][i]["wildcardSequence"]
                    if wildcardSequence == 1 or wildcardSequence == 2:
                        wildcardSequence = ":wc:"
                    else:
                        wildcardSequence = ""
                    new_name = strings(name)
                    pacificString += f"{new_name} ({wins}-{losses}-{otLosses}) {points}pts {wildcardSequence}"
                    pacific.append(pacificString)
            embed = discord.Embed(title="Standings", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)
            embed.add_field(name="Atlantic", value="\n".join(atlantic), inline=False)
            embed.add_field(name="Metropolitan", value="\n".join(metropolitan), inline=False)
            embed.add_field(name="Central", value="\n".join(central), inline=False)
            embed.add_field(name="Pacific", value="\n".join(pacific), inline=False)
            await msg.edit(embed=embed)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)


async def setup(bot):
    await bot.add_cog(standings(bot))