import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import requests
import json
import config

class player(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `player.py`")
    
    """@app_commands.command(name="player", description="Gets the information of a team!")
    async def player(self, interaction : discord.Interaction, name: str):
        try: 
            teamsURL = "https://statsapi.web.nhl.com/api/v1/teams"
            teamsGet = requests.get(teamsURL)
            y = json.loads(teamsGet.text)
            await interaction.response.send_message("Searching for player..", ephemeral=True)
            u = 1
            a = 1
            while u < 56:
                teamRosterURL = f"https://statsapi.web.nhl.com/api/v1/teams/{u}/roster"
                teamRosterGet = requests.get(teamRosterURL)
                t = json.loads(teamRosterGet.text)
                try:
                    messageNumber = teamRosterGet.json()['messageNumber']
                except:
                    messageNumber = None
                if messageNumber == None:
                    for x in t['roster']:
                        playerName = teamRosterGet.json()['roster'][a]['person']['fullName']
                        if playerName.lower() == name.lower():
                            playerID = teamRosterGet.json()['roster'][a]['person']['id']
                            playerURL = f"https://statsapi.web.nhl.com/api/v1/people/{playerID}"
                            playerGet = requests.get(playerURL)
                            playerFullName = playerGet.json()['people'][0]['fullName']
                            playerBirthDate = playerGet.json()['people'][0]['birthDate']
                            playerAge = playerGet.json()['people'][0]['currentAge']
                            playerBirthCountry = playerGet.json()['people'][0]['birthCountry']
                            playerPosition = playerGet.json()['people'][0]['primaryPosition']['name']
                            playerNumber = playerGet.json()['people'][0]['primaryNumber']
                            playerShoots = playerGet.json()['people'][0]['shootsCatches']
                            playerTeam = playerGet.json()['people'][0]['currentTeam']['name']
                            playerActive = playerGet.json()['people'][0]['active']
                            playerRookie = playerGet.json()['people'][0]['rookie']
                            playerCaptain = playerGet.json()['people'][0]['captain']
                            playerAlternateCaptain = playerGet.json()['people'][0]['alternateCaptain']
                            playerLink = playerGet.json()['people'][0]['link']
                            embed = discord.Embed(title=f"{playerFullName}", color=config.color, url=f"https://www.nhl.com/player/{playerID}")
                            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Player Information")
                            if playerRookie == True:
                                embed.description = f"**Rookie** for the {playerTeam}\n{playerPosition}"
                            elif playerCaptain == True:
                                embed.description = f"**Captain** for the {playerTeam}\n{playerPosition}"
                            elif playerAlternateCaptain == True:
                                embed.description = f"**Alternate Captain** for the {playerTeam}\n{playerPosition}"
                            else:
                                embed.description = f"{playerPosition} for the {playerTeam}"
                            embed.add_field(name="Number", value=f"{playerNumber}", inline=True)
                            embed.add_field(name="Age", value=f"{playerAge}", inline=True)
                            embed.add_field(name="Birth Country", value=f"{playerBirthCountry}", inline=True)
                            embed.add_field(name="Birth Date", value=f"{playerBirthDate}", inline=True)
                            embed.add_field(name="Shoots", value=f"{playerShoots}", inline=True)
                            embed.add_field(name="Active", value=f"{playerActive}", inline=True)
                            embed.set_footer(text=f"Player ID: {playerID}")

                            await interaction.followup.send(embed=embed)
                            return

                        else:
                            pl = len(t['roster']) - 1
                            if pl == a:
                                u += 1
                                a = 0
                                break
                            else:
                                a += 1
                                
                    else:
                        u += 1
                else:
                    u += 1
                    
            else:
                await interaction.followup.send("Player not found!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error", description=f"```{e}```", color=config.color)
            embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
            embed.add_field(name="Player Name", value=name)
            embed.add_field(name="User", value=interaction.user.mention)
            embed.add_field(name="Server", value=interaction.guild.name)
            embed.add_field(name="Channel", value=interaction.channel.mention)
            embed.set_footer(text=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            await interaction.followup.send("Error getting schedule! THERE IS CURRENTLY AN ERROR WITH THE NHL API ALL HOCKEY BOTS DO NOT WORK!!!", ephemeral=True)
            #await interaction.followup.send("Error getting player! Message has been sent to Bot Developers", ephemeral=True)
            await error_channel.send(f"Something went wrong `{e}`")"""

async def setup(bot):
    await bot.add_cog(player(bot))