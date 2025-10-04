import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback
import json

class teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `teams.py`")
    
    @app_commands.command(name="teams", description="Get the teams in the league!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def teams(self, interaction: discord.Interaction):
        try:
            if config.command_log_bool == True:
                command_log_channel = self.bot.get_channel(config.command_log)
                from datetime import datetime
                if interaction.guild == None:
                    await command_log_channel.send(f"`/teams` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
                elif interaction.guild.name == "":
                    await command_log_channel.send(f"`/teams` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
                else:    
                    await command_log_channel.send(f"`/teams` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        except Exception as e:
            print(e)
        
        with open("teams.json", "r") as f:
            teams = json.load(f)

        try:
            embed = discord.Embed(title="Teams", description=f"Here are the teams in the league!\n\n", color=0x00ff00)
            for team in teams:
                if team == "ANA":
                    embed.description += f"**{team}** - {teams[team]} {config.anahiem_ducks_emoji}\n"
                elif team == "BOS":
                    embed.description += f"**{team}** - {teams[team]} {config.boston_bruins_emoji}\n"
                elif team == "BUF":
                    embed.description += f"**{team}** - {teams[team]} {config.buffalo_sabres_emoji}\n"
                elif team == "CGY":
                    embed.description += f"**{team}** - {teams[team]} {config.calgary_flames_emoji}\n"
                elif team == "CAR":
                    embed.description += f"**{team}** - {teams[team]} {config.carolina_hurricanes_emoji}\n"
                elif team == "CHI":
                    embed.description += f"**{team}** - {teams[team]} {config.chicago_blackhawks_emoji}\n"
                elif team == "COL":
                    embed.description += f"**{team}** - {teams[team]} {config.colorado_avalanche_emoji}\n"
                elif team == "CBJ":
                    embed.description += f"**{team}** - {teams[team]} {config.columbus_blue_jackets_emoji}\n"
                elif team == "DAL":
                    embed.description += f"**{team}** - {teams[team]} {config.dallas_stars_emoji}\n"
                elif team == "DET":
                    embed.description += f"**{team}** - {teams[team]} {config.detroit_red_wings_emoji}\n"
                elif team == "EDM":
                    embed.description += f"**{team}** - {teams[team]} {config.edmonton_oilers_emoji}\n"
                elif team == "FLA":
                    embed.description += f"**{team}** - {teams[team]} {config.florida_panthers_emoji}\n"
                elif team == "LAK":
                    embed.description += f"**{team}** - {teams[team]} {config.los_angeles_kings_emoji}\n"
                elif team == "MIN":
                    embed.description += f"**{team}** - {teams[team]} {config.minnesota_wild_emoji}\n"
                elif team == "MTL":
                    embed.description += f"**{team}** - {teams[team]} {config.montreal_canadiens_emoji}\n"
                elif team == "NSH":
                    embed.description += f"**{team}** - {teams[team]} {config.nashville_predators_emoji}\n"
                elif team == "NJD":
                    embed.description += f"**{team}** - {teams[team]} {config.new_jersey_devils_emoji}\n"
                elif team == "NYI":
                    embed.description += f"**{team}** - {teams[team]} {config.new_york_islanders_emoji}\n"
                elif team == "NYR":
                    embed.description += f"**{team}** - {teams[team]} {config.new_york_rangers_emoji}\n"
                elif team == "OTT":
                    embed.description += f"**{team}** - {teams[team]} {config.ottawa_senators_emoji}\n"
                elif team == "PHI":
                    embed.description += f"**{team}** - {teams[team]} {config.philadelphia_flyers_emoji}\n"
                elif team == "PIT":
                    embed.description += f"**{team}** - {teams[team]} {config.pittsburgh_penguins_emoji}\n"
                elif team == "SEA":
                    embed.description += f"**{team}** - {teams[team]} {config.seattle_kraken_emoji}\n"
                elif team == "SJS":
                    embed.description += f"**{team}** - {teams[team]} {config.san_jose_sharks_emoji}\n"
                elif team == "STL":
                    embed.description += f"**{team}** - {teams[team]} {config.st_louis_blues_emoji}\n"
                elif team == "TBL":
                    embed.description += f"**{team}** - {teams[team]} {config.tampa_bay_lightning_emoji}\n"
                elif team == "TOR":
                    embed.description += f"**{team}** - {teams[team]} {config.toronto_maple_leafs_emoji}\n"
                elif team == "UTA":
                    embed.description += f"**{team}** - {teams[team]} {config.utah_hockey_club_emoji}\n"
                elif team == "VAN":
                    embed.description += f"**{team}** - {teams[team]} {config.vancouver_canucks_emoji}\n"
                elif team == "VGK":
                    embed.description += f"**{team}** - {teams[team]} {config.vegas_golden_knights_emoji}\n"
                elif team == "WSH":
                    embed.description += f"**{team}** - {teams[team]} {config.washington_capitals_emoji}\n"
                elif team == "WPG":
                    embed.description += f"**{team}** - {teams[team]} {config.winnipeg_jets_emoji}\n"
            try:
                avatar = interaction.user.avatar.url
            except:
                avatar = self.bot.user.avatar.url
            embed.set_author(icon_url=avatar, name="NHL Bot")
            embed.set_footer(text=config.footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)

async def setup(bot):
    await bot.add_cog(teams(bot))