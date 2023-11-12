import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import config

class team(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `team.py`")
    
    @app_commands.command(name="team", description="Gets the information of a team!")
    async def team(self, interaction : discord.Interaction, team: str):
        #teams url "https://statsapi.web.nhl.com/api/v1/teams"
        #https://statsapi.web.nhl.com/api/v1/teams/6
        try:

            teamID = config.checkForTeam(team)
            if teamID == None:
                await interaction.response.send_message("Team not found!")
                return
            
            teamURL = f"https://statsapi.web.nhl.com/api/v1/teams/{teamID}"
            teamGet = requests.get(teamURL)
            teamFullName = teamGet.json()['teams'][0]['name']
            teamNickname = teamGet.json()['teams'][0]['teamName']
            teamAbbreviation = teamGet.json()['teams'][0]['abbreviation']
            teamDivision = teamGet.json()['teams'][0]['division']['name']
            teamConference = teamGet.json()['teams'][0]['conference']['name']
            teamVenue = teamGet.json()['teams'][0]['venue']['name']
            teamLocation = teamGet.json()['teams'][0]['locationName']
            teamFirstYear = teamGet.json()['teams'][0]['firstYearOfPlay']
            teamOfficialSite = teamGet.json()['teams'][0]['officialSiteUrl']

            embed = discord.Embed(title=f"{teamFullName}", description=f"{teamNickname}", color=config.color, url=f"{teamOfficialSite}")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Team Information")
            embed.add_field(name="Abbreviation", value=f"{teamAbbreviation}", inline=True)
            embed.add_field(name="Division", value=f"{teamDivision}", inline=True)
            embed.add_field(name="Conference", value=f"{teamConference}", inline=True)
            embed.add_field(name="Venue", value=f"{teamVenue}", inline=True)
            embed.add_field(name="Location", value=f"{teamLocation}", inline=True)
            embed.add_field(name="First Year of Play", value=f"{teamFirstYear}", inline=True)
            embed.set_footer(text=f"Team ID: {teamID}")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await interaction.followup.send("Error getting schedule! THERE IS CURRENTLY AN ERROR WITH THE NHL API ALL HOCKEY BOTS DO NOT WORK!!!", ephemeral=True)
            #await interaction.response.send_message("Error getting team! Message has been sent to Bot Developers", ephemeral=True)
            embed = discord.Embed(title="Error with `/team`", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Team", value=team)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.mention)
            await error_channel.send(embed=embed)


    
async def setup(bot):
    await bot.add_cog(team(bot))