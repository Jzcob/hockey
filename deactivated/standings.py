import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime
import config
import traceback

class standings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `standings.py`")
    
    @app_commands.command(name="standings", description="Get the standings!")
    async def standings(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
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
                    atlanticString += data['standings'][i]['teamName']['default']
                    atlanticString += f" ({wins}-{losses}-{otLosses}) {points}pts"
                    atlantic.append(atlanticString)
                elif divisionName == "Metropolitan":
                    metropolitanString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    metropolitanString += data['standings'][i]['teamName']['default']
                    metropolitanString += f" ({wins}-{losses}-{otLosses}) {points}pts"
                    metropolitan.append(metropolitanString)
                elif divisionName == "Central":
                    centralString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    centralString += data['standings'][i]['teamName']['default']
                    centralString += f" ({wins}-{losses}-{otLosses}) {points}pts"
                    central.append(centralString)
                elif divisionName == "Pacific":
                    pacificString = ""
                    wins = data['standings'][i]['wins']
                    losses = data['standings'][i]['losses']
                    otLosses = data['standings'][i]['otLosses']
                    points = data['standings'][i]['points']
                    pacificString += data['standings'][i]['teamName']['default']
                    pacificString += f" ({wins}-{losses}-{otLosses}) {points}pts"
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
    await bot.add_cog(standings(bot), guilds=[discord.Object(id=config.hockey_discord_server)])