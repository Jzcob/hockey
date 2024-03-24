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

#import topgg
load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
intents.auto_moderation_configuration = True
intents.reactions = True
bot = commands.Bot(command_prefix=';', intents=intents, help_command=None)
status = discord.Status.online
#bot.topggpy = topgg.DBLClient(bot=bot,token=os.getenv("topgg-token"), autopost=True, post_shard_count=True)

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
                        desc += f"ID: {guild.id}, Name: {guild.name}\n"
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
                #await bot.topggpy.post_guild_count()
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"Something went wrong. `{e}`", color=0xff0000)
                return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="This command can only be used in DMs.", color=0xff0000)
            return await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner, used to sync the servers the bot is in.", color=0xff0000)
        return await ctx.send(embed=embed)

@bot.tree.context_menu(name="today")
async def today(interaction: discord.Interaction, member: discord.Member):
    try:
        hawaii = pytz.timezone('US/Hawaii')
        dt = datetime.now(hawaii)
        today = dt.strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/schedule/{today}"
        await interaction.response.defer()
        msg = await interaction.original_response()
        r = requests.get(url)
        global data
        data = r.json()
        games = data["gameWeek"][0]["games"]
        embed = discord.Embed(title=f"Today's Games", description=f"Total games today: {len(games)}", color=config.color)
        embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
        embed.set_footer(text=config.footer)
        for i in range(len(games)):
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
                awayString, homeString = config.strings(awayAbbreviation, homeAbbreviation, home, away)
                embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
            elif gameState == "FINAL" or gameState == "OFF":
                homeScore = game2['homeTeam']['score']
                awayScore = game2['awayTeam']['score']
                home = game2["homeTeam"]["name"]["default"]
                away = game2["awayTeam"]["name"]["default"]
                homeAbbreviation = game2["homeTeam"]["abbrev"]
                awayAbbreviation = game2["awayTeam"]["abbrev"]
                awayString, homeString = config.strings(awayAbbreviation, homeAbbreviation, home, away)
                embed.add_field(name=f"Final!", value=f"\n{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\n", inline=False)
                embed.set_footer(text=f"ID: {gameID}")
            elif gameState == "LIVE":
                homeScore = game2['homeTeam']['score']
                awayScore = game2['awayTeam']['score']
                clock = game2['clock']['timeRemaining']
                clockRunning = game2['clock']['running']
                clockIntermission = game2['clock']['inIntermission']
                home = game2["homeTeam"]["name"]["default"]
                away = game2["awayTeam"]["name"]["default"]
                homeAbbreviation = game2["homeTeam"]["abbrev"]
                awayAbbreviation = game2["awayTeam"]["abbrev"]
                awayString, homeString = config.strings(awayAbbreviation, homeAbbreviation, home, away)
                if clockRunning == True:
                    embed.add_field(name=f"LIVE", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}\nTime: {clock}", inline=False)
                if clockIntermission == True:
                    embed.add_field(name=f"Intermission!", value=f"{awayString} @ {homeString}\nScore: {awayScore} | {homeScore}", inline=False)
            else:
                home = game2["homeTeam"]["name"]["default"]
                away = game2["awayTeam"]["name"]["default"]
                homeAbbreviation = game2["homeTeam"]["abbrev"]
                awayAbbreviation = game2["awayTeam"]["abbrev"]
                awayString, homeString = config.strings(awayAbbreviation, homeAbbreviation, home, away)
                embed.add_field(name=f"{startTime}", value=f"{awayString} @ {homeString}\nGame is scheduled!", inline=False)
        return await msg.edit(embed=embed)
    except:
        error_channel = bot.get_channel(config.error_channel)
        string = f"{traceback.format_exc()}"
        await error_channel.send(f"```{string}```")
        await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)












@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")
    

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





asyncio.run(main())