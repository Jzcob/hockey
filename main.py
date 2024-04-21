import discord
import asyncio
from discord.ext import commands
import os
import config
from dotenv import load_dotenv
import traceback
import requests
from datetime import datetime, timedelta
import pytz

import topgg
load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
intents.auto_moderation_configuration = True
intents.reactions = True
bot = commands.Bot(command_prefix=';;', intents=intents, help_command=None)
status = discord.Status.online

def strings(awayAbbreviation, homeAbbreviation, home, away):
    if awayAbbreviation == "ANA":
        awayString = f"{config.anahiem_ducks_emoji} {away}"
    elif awayAbbreviation == "ARI":
        awayString = f"{config.arizona_coyotes_emoji} {away}"
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
    elif homeAbbreviation == "ARI":
        homeString = f"{home} {config.arizona_coyotes_emoji}"
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

@bot.command()
async def sync(ctx) -> None:
    if ctx.author.id == config.jacob:
        try:
            fmt = await ctx.bot.tree.sync()
            print(f"Synced {len(fmt)} commands.")
            embed = discord.Embed(title="Synced", description=f"Synced {len(fmt)} commands.", color=0x00ff00)
            await ctx.send(embed=embed)
            return
        except Exception as e:
            print(e)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner, used to sync the global commands with the discord api.", color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
async def syncserver(ctx) -> None:
    if ctx.author.id == config.jacob:
        try:
            fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            print(f"Synced {len(fmt)} commands.")
            embed = discord.Embed(title="Synced", description=f"Synced {len(fmt)} commands.", color=0x00ff00)
            await ctx.send(embed=embed)
            return
        except Exception as e:
            print(e)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner, used to sync the server commands with the discord api.", color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
async def servers(ctx):
    if ctx.author.id == config.jacob:
        if ctx.channel.type == discord.ChannelType.private or ctx.channel.id in config.allowed_channels:   
            guilds = bot.guilds
            try:
                desc = ""
                members = 0
                desc += f"Total Servers: {len(guilds)}\n" 
                for guild in guilds:
                    members += guild.member_count
                    try:
                        desc += f"ID: {guild.id}, Members: {guild.member_count}, Name: {guild.name}\n"
                    except:
                        desc += ("---Error getting server information---\n")
                file_path = "server_info.txt"
                with open(file_path, "w") as file:
                    file.write(desc)
                await ctx.send(file=discord.File(file_path))
                os.remove(file_path)
                vc = bot.get_channel(1173304351872253952)
                membersVC = bot.get_channel(1186445778043031722)
                await vc.edit(name=f"Servers: {len(bot.guilds)}")
                await membersVC.edit(name=f"Members: {int(members):,}")
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"Something went wrong. `{e}`", color=0xff0000)
                return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="This command can only be used in DMs.", color=0xff0000)
            return await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner, used to sync the servers the bot is in.", color=0xff0000)
        return await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")
    while True:
        bot.topggpy = topgg.DBLClient(bot, os.getenv("topgg-token"), autopost=True, post_shard_count=True)
        await asyncio.sleep(1800)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'FOUND: `{filename}`')

async def main():
    #await update_stats.start()
    await load()
    await bot.start(token=os.getenv("token"))

@bot.event
async def on_guild_join(guild):
    join_leave_channel = bot.get_channel(1168939285274177627)
    try:
        embed = discord.Embed(title="Joined Server", description=f"Name: {guild.name}\n" +
                                            f"Members: {guild.member_count}\n", color=0x00ff00)
        embed.set_thumbnail(url=f"{guild.icon}")
        await join_leave_channel.send(embed=embed)
    except:
        await join_leave_channel.send("Joined a server but couldn't get server information")
    try:
        guilds = bot.guilds
        members = 0
        for guild in guilds:
            members += guild.member_count
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await membersVC.edit(name=f"Members: {int(members):,}")
        await vc.edit(name=f"Servers: {len(bot.guilds)}")
        #await bot.topggpy.post_guild_count()
    except Exception as e:
        print(e)


@bot.event
async def on_guild_remove(guild):
    join_leave_channel = bot.get_channel(1168939285274177627)
    try:
        embed = discord.Embed(title="Left Server", description=f"Name: {guild.name}\n" +
                                        f"Members: {guild.member_count}\n", color=0xff0000)
        embed.set_thumbnail(url=f"{guild.icon}")
        await join_leave_channel.send(embed=embed)
    except:
        await join_leave_channel.send("Left a server but couldn't get server information")
    try:
        guilds = bot.guilds
        members = 0
        for guild in guilds:
            members += guild.member_count
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await membersVC.edit(name=f"Members: {int(members):,}")
        await vc.edit(name=f"Servers: {len(bot.guilds)}")
        #await bot.topggpy.post_guild_count()
    except Exception as e:
        print(e)

@bot.tree.context_menu(name="today")
async def today(interaction: discord.Interaction, user: discord.User):
    try:
        print("1")
        hawaii = pytz.timezone('US/Hawaii')
        dt = datetime.now(hawaii)
        today = dt.strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/schedule/{today}"
        await interaction.response.defer()
        msg = await interaction.original_response()
        r = requests.get(url)
        global data
        data = r.json()
        print("2")
        games = data["gameWeek"][0]["games"]
        embed = discord.Embed(title=f"Today's Games", description=f"Total games today: {len(games)}", color=config.color)
        embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
        embed.set_footer(text=config.footer)
        print("3")
        for i in range(len(games)):
            print("loop")
            try:
                game = data["gameWeek"][0]["games"][i]
                gameState = game["gameState"]
                gameID = game['id']
                url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
                r2 = requests.get(url2)
                game2 = r2.json()
                startTime = game["startTimeUTC"]
                startTime = datetime.strptime(startTime, '%Y-%m-%dT%H:%M:%SZ')
                startTime = startTime - timedelta(hours=4)
                startTime = startTime.strftime('%I:%M %p')
                if gameState == "FUT":
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
                elif gameState == "FINAL" or gameState == "OFF":
                    homeScore = game2['homeTeam']['score']
                    awayScore = game2['awayTeam']['score']
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"Final!", value=f"\n{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\n", inline=False)
                    embed.set_footer(text=f"ID: {gameID}")
                elif gameState == "LIVE" or gameState == "CRIT":
                    homeScore = game2['homeTeam']['score']
                    awayScore = game2['awayTeam']['score']
                    clock = game2['clock']['timeRemaining']
                    clockRunning = game2['clock']['running']
                    clockIntermission = game2['clock']['inIntermission']
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    if clockRunning == True:
                        embed.add_field(name=f"LIVE", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\nTime: {clock}", inline=False)
                    if clockIntermission == True:
                        embed.add_field(name=f"Intermission!", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}", inline=False)
                else:
                    home = game2["homeTeam"]["name"]["default"]
                    away = game2["awayTeam"]["name"]["default"]
                    homeAbbreviation = game2["homeTeam"]["abbrev"]
                    awayAbbreviation = game2["awayTeam"]["abbrev"]
                    awayString, homeString = strings(awayAbbreviation, homeAbbreviation, home, away)
                    embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
            except Exception as e:
                print(e)
        print("4")
        return await msg.edit(embed=embed)
    except:
        error_channel = bot.get_channel(error_channel)
        string = f"{traceback.format_exc()}"
        await error_channel.send(f"<@920797181034778655>```{string}```")
        await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)


asyncio.run(main())

