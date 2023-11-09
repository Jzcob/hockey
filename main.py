import discord
import asyncio
from TOKEN import token as TOKEN
from discord.ext import commands
from discord import app_commands
import os
import config

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
intents.auto_moderation_configuration = True
intents.reactions = True
bot = commands.Bot(command_prefix=';', intents=intents, help_command=None)
status = discord.Status.online

@bot.command()
async def sync(ctx) -> None:
    if ctx.author.id in config.bot_authors:
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
    if ctx.author.id in config.bot_authors:
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
    if ctx.author.id in config.bot_authors:
        if ctx.channel.type == discord.ChannelType.private or ctx.channel.id in config.allowed_channels:   
            guilds = bot.guilds
            print(guilds)
            try:
                for guild in guilds:
                    try:
                        embed = discord.Embed(description=f"Name: {guild.name}\n" +
                                            f"Owner: {guild.owner.name} ID: {guild.owner_id}\n" +
                                            f"Members: {guild.member_count}\n" +
                                            f"Created: {guild.created_at}\n" +
                                            f"Verification Level: {guild.verification_level}", color=0x00ff00)
                        embed.set_thumbnail(url=f"{guild.icon}")
                        await ctx.send(embed=embed)
                    except:
                        await ctx.send("Error getting server information")
                    
            except Exception as e:
                print(e)
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
    

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'FOUND: `{filename}`')
async def main():
    await load()
    await bot.start(token=TOKEN)

@bot.event
async def on_guild_join(guild):
    embed = discord.Embed(title="Joined Server", description=f"Name: {guild.name}\n" +
                                        f"Owner: {guild.owner.name} ID: {guild.owner_id}\n" +
                                        f"Members: {guild.member_count}\n" +
                                        f"Created: {guild.created_at}\n" +
                                        f"Verification Level: {guild.verification_level}", color=0x00ff00)
    embed.set_thumbnail(url=f"{guild.icon}")
    await bot.get_channel(1168939285274177627).send(embed=embed)

asyncio.run(main())