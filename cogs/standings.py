import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import requests
import json
import config


class standings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `standings.py`")

    
    @app_commands.command(name="standings", description="Gets the standings of a team!")
    async def standings(self, interaction: discord.Interaction, team: str=None):
        url = "https://statsapi.web.nhl.com/api/v1/standings"
        if team == None:
            try:
                response = requests.get(url)
                x = json.loads(response.text)
                y = 0
                at = 0
                me = 0
                ce = 0
                pa = 0
                records = x['records']
                atlantic = []
                metropolitan = []
                central = []
                pacific = []
                await interaction.response.send_message("Searching for standings..", ephemeral=True)
                for i in records:
                    for j in records[y]['teamRecords']:
                        metroString = ""
                        metroWins = records[y]['teamRecords'][me]['leagueRecord']['wins']
                        metroLosses = records[y]['teamRecords'][me]['leagueRecord']['losses']
                        metroOT = records[y]['teamRecords'][me]['leagueRecord']['ot']
                        metroPoints = records[y]['teamRecords'][me]['points']
                        metroString += records[y]['teamRecords'][me]['team']['name']
                        metroString += f" ({metroWins}-{metroLosses}-{metroOT}) {metroPoints} points"
                        metropolitan.append(metroString)
                        me += 1
                    y += 1
                    for k in records[y]['teamRecords']:
                        atlanticString = ""
                        atlanticWins = records[y]['teamRecords'][at]['leagueRecord']['wins']
                        atlanticLosses = records[y]['teamRecords'][at]['leagueRecord']['losses']
                        atlanticOT = records[y]['teamRecords'][at]['leagueRecord']['ot']
                        atlanticPoints = records[y]['teamRecords'][at]['points']
                        atlanticString += records[y]['teamRecords'][at]['team']['name']
                        atlanticString += f" ({atlanticWins}-{atlanticLosses}-{atlanticOT}) {atlanticPoints} points"
                        atlantic.append(atlanticString)
                        at += 1
                    y += 1
                    for l in records[y]['teamRecords']:
                        centralString = ""
                        centralWins = records[y]['teamRecords'][ce]['leagueRecord']['wins']
                        centralLosses = records[y]['teamRecords'][ce]['leagueRecord']['losses']
                        centralOT = records[y]['teamRecords'][ce]['leagueRecord']['ot']
                        centralPoints = records[y]['teamRecords'][ce]['points']
                        centralString += records[y]['teamRecords'][ce]['team']['name']
                        centralString += f" ({centralWins}-{centralLosses}-{centralOT}) {centralPoints} points"
                        central.append(centralString)
                        ce += 1
                    y += 1
                    for m in records[y]['teamRecords']:
                        pacificString = ""
                        pacificWins = records[y]['teamRecords'][pa]['leagueRecord']['wins']
                        pacificLosses = records[y]['teamRecords'][pa]['leagueRecord']['losses']
                        pacificOT = records[y]['teamRecords'][pa]['leagueRecord']['ot']
                        pacificPoints = records[y]['teamRecords'][pa]['points']
                        pacificString += records[y]['teamRecords'][pa]['team']['name']
                        pacificString += f" ({pacificWins}-{pacificLosses}-{pacificOT}) {pacificPoints} points"
                        pacific.append(pacificString)
                        pa += 1
                    break
                
                embed = discord.Embed(title="NHL Standings", color=config.color)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Standings")
                embed.add_field(name="Atlantic Division", value=f"1. {atlantic[0]}\n2. {atlantic[1]}\n3. {atlantic[2]}\n4. {atlantic[3]}\n5. {atlantic[4]}\n6. {atlantic[5]}\n7. {atlantic[6]}\n8. {atlantic[7]}", inline=False)
                embed.add_field(name="Metropolitan Division", value=f"1. {metropolitan[0]}\n2. {metropolitan[1]}\n3. {metropolitan[2]}\n4. {metropolitan[3]}\n5. {metropolitan[4]}\n6. {metropolitan[5]}\n7. {metropolitan[6]}\n8. {metropolitan[7]}", inline=False)
                embed.add_field(name="Central Division", value=f"1. {central[0]}\n2. {central[1]}\n3. {central[2]}\n4. {central[3]}\n5. {central[4]}\n6. {central[5]}\n7. {central[6]}\n8. {central[7]}", inline=False)
                embed.add_field(name="Pacific Division", value=f"1. {pacific[0]}\n2. {pacific[1]}\n3. {pacific[2]}\n4. {pacific[3]}\n5. {pacific[4]}\n6. {pacific[5]}\n7. {pacific[6]}\n8. {pacific[7]}", inline=False)
                embed.set_footer(text="Standings are updated every 5 minutes.")
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                await interaction.followup.send("Error getting schedule! THERE IS CURRENTLY AN ERROR WITH THE NHL API ALL HOCKEY BOTS DO NOT WORK!!!", ephemeral=True)
                #await interaction.followup.send("Error getting standings! Message has been sent to Bot Developers", ephemeral=True)
                embed = discord.Embed(title="Error with `/standings`", description=f"```{e}```", color=config.color)
        else:
            try:
                response = requests.get(url)
                x = json.loads(response.text)
                y = 0
                at = 0
                me = 0
                ce = 0
                pa = 0
                records = x['records']
                atlantic = []
                metropolitan = []
                central = []
                pacific = []
                await interaction.response.send_message("Searching for standings..", ephemeral=True)
                teamName = config.checkForTeamName(team)
                try:
                    for i in records:
                        for j in records[y]['teamRecords']:
                            if teamName == records[y]['teamRecords'][me]['team']['name']:
                                team = records[y]['teamRecords'][me]['team']['name']
                                wins = records[y]['teamRecords'][me]['leagueRecord']['wins']
                                losses = records[y]['teamRecords'][me]['leagueRecord']['losses']
                                ot = records[y]['teamRecords'][me]['leagueRecord']['ot']
                                points = records[y]['teamRecords'][me]['points']
                                row = records[y]['teamRecords'][me]['row']
                                gamesPlayed = records[y]['teamRecords'][at]['gamesPlayed']
                                goalsAgainst = records[y]['teamRecords'][me]['goalsAgainst']
                                goalsScored = records[y]['teamRecords'][me]['goalsScored']
                                embed = discord.Embed(title=f"{team}", color=config.color)
                                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Standings")
                                embed.add_field(name="Wins", value=f"{wins}", inline=True)
                                embed.add_field(name="Losses", value=f"{losses}", inline=True)
                                embed.add_field(name="OT", value=f"{ot}", inline=True)
                                embed.add_field(name="Points", value=f"{points}", inline=True)
                                embed.add_field(name="ROW", value=f"{row}", inline=True)
                                embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                                embed.add_field(name="Goals Scored", value=f"{goalsScored}", inline=True)
                                embed.add_field(name="Goals Against", value=f"{goalsAgainst}", inline=True)
                                embed.set_footer(text="Standings are updated every 5 minutes.")
                                return await interaction.followup.send(embed=embed, ephemeral=True)
                            me += 1
                        y += 1
                        for k in records[y]['teamRecords']:
                            if teamName == records[y]['teamRecords'][at]['team']['name']:
                                team = records[y]['teamRecords'][at]['team']['name']
                                wins = records[y]['teamRecords'][at]['leagueRecord']['wins']
                                losses = records[y]['teamRecords'][at]['leagueRecord']['losses']
                                ot = records[y]['teamRecords'][at]['leagueRecord']['ot']
                                points = records[y]['teamRecords'][at]['points']
                                row = records[y]['teamRecords'][at]['row']
                                gamesPlayed = records[y]['teamRecords'][at]['gamesPlayed']
                                goalsAgainst = records[y]['teamRecords'][at]['goalsAgainst']
                                goalsScored = records[y]['teamRecords'][at]['goalsScored']
                                embed = discord.Embed(title=f"{team}", color=config.color)
                                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Standings")
                                embed.add_field(name="Wins", value=f"{wins}", inline=True)
                                embed.add_field(name="Losses", value=f"{losses}", inline=True)
                                embed.add_field(name="OT", value=f"{ot}", inline=True)
                                embed.add_field(name="Points", value=f"{points}", inline=True)
                                embed.add_field(name="ROW", value=f"{row}", inline=True)
                                embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                                embed.add_field(name="Goals Scored", value=f"{goalsScored}", inline=True)
                                embed.add_field(name="Goals Against", value=f"{goalsAgainst}", inline=True)
                                embed.set_footer(text="Standings are updated every 5 minutes.")
                                return await interaction.followup.send(embed=embed, ephemeral=True)
                            at += 1
                        y += 1
                        for l in records[y]['teamRecords']:
                            if teamName == records[y]['teamRecords'][ce]['team']['name']:
                                team = records[y]['teamRecords'][ce]['team']['name']
                                wins = records[y]['teamRecords'][ce]['leagueRecord']['wins']
                                losses = records[y]['teamRecords'][ce]['leagueRecord']['losses']
                                ot = records[y]['teamRecords'][ce]['leagueRecord']['ot']
                                points = records[y]['teamRecords'][ce]['points']
                                row = records[y]['teamRecords'][ce]['row']
                                gamesPlayed = records[y]['teamRecords'][ce]['gamesPlayed']
                                goalsAgainst = records[y]['teamRecords'][ce]['goalsAgainst']
                                goalsScored = records[y]['teamRecords'][ce]['goalsScored']
                                embed = discord.Embed(title=f"{team}", color=config.color)
                                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Standings")
                                embed.add_field(name="Wins", value=f"{wins}", inline=True)
                                embed.add_field(name="Losses", value=f"{losses}", inline=True)
                                embed.add_field(name="OT", value=f"{ot}", inline=True)
                                embed.add_field(name="Points", value=f"{points}", inline=True)
                                embed.add_field(name="ROW", value=f"{row}", inline=True)
                                embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                                embed.add_field(name="Goals Scored", value=f"{goalsScored}", inline=True)
                                embed.add_field(name="Goals Against", value=f"{goalsAgainst}", inline=True)
                                embed.set_footer(text="Standings are updated every 5 minutes.")
                                return await interaction.followup.send(embed=embed, ephemeral=True)
                            ce += 1
                        y += 1
                        for m in records[y]['teamRecords']:
                            if teamName == records[y]['teamRecords'][pa]['team']['name']:
                                team = records[y]['teamRecords'][pa]['team']['name']
                                wins = records[y]['teamRecords'][pa]['leagueRecord']['wins']
                                losses = records[y]['teamRecords'][pa]['leagueRecord']['losses']
                                ot = records[y]['teamRecords'][pa]['leagueRecord']['ot']
                                points = records[y]['teamRecords'][pa]['points']
                                row = records[y]['teamRecords'][pa]['row']
                                gamesPlayed = records[y]['teamRecords'][pa]['gamesPlayed']
                                goalsAgainst = records[y]['teamRecords'][pa]['goalsAgainst']
                                goalsScored = records[y]['teamRecords'][pa]['goalsScored']
                                embed = discord.Embed(title=f"{team}", color=config.color)
                                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Standings")
                                embed.add_field(name="Wins", value=f"{wins}", inline=True)
                                embed.add_field(name="Losses", value=f"{losses}", inline=True)
                                embed.add_field(name="OT", value=f"{ot}", inline=True)
                                embed.add_field(name="Points", value=f"{points}", inline=True)
                                embed.add_field(name="ROW", value=f"{row}", inline=True)
                                embed.add_field(name="Games Played", value=f"{gamesPlayed}", inline=True)
                                embed.add_field(name="Goals Scored", value=f"{goalsScored}", inline=True)
                                embed.add_field(name="Goals Against", value=f"{goalsAgainst}", inline=True)
                                embed.set_footer(text="Standings are updated every 5 minutes.")
                                return await interaction.followup.send(embed=embed, ephemeral=True)
                            pa += 1
                        break
                    else:
                        return await interaction.followup.send("Team not found!")
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    embed = discord.Embed(title="Error with `/standings`", description=f"```{e}```", color=config.color)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                embed = discord.Embed(title="Error with `/standings`", description=f"```{e}```", color=config.color)
                embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Error")
                embed.add_field(name="Team", value=team)
                embed.add_field(name="User", value=interaction.user.mention)
                embed.add_field(name="Server", value=interaction.guild.name)
                embed.add_field(name="Channel", value=interaction.channel.mention)
                embed.set_footer(text=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                await interaction.followup.send("Error getting schedule! THERE IS CURRENTLY AN ERROR WITH THE NHL API ALL HOCKEY BOTS DO NOT WORK!!!", ephemeral=True)
                #await interaction.followup.send("Error getting standings! Message has been sent to Bot Developers", ephemeral=True)
                await error_channel.send(embed=embed)



async def setup(bot):
    await bot.add_cog(standings(bot))