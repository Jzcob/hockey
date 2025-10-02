import discord
import asyncio
from discord.ext import commands
import os
import config
import mysql.connector.pooling
from dotenv import load_dotenv
from datetime import datetime
import topgg
import traceback

# --- Initial Setup ---
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.auto_moderation_configuration = True
intents.reactions = True
status = discord.Status.online

# --- Database Pool Setup ---
db_pool = None  # Initialize pool as None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="bot_pool",
        pool_size=5,
        host=os.getenv("db_host"),
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        database=os.getenv("db_name")
    )
    print("✅ Successfully created database connection pool.")
except mysql.connector.Error as err:
    print(f"❌ FAILED to create database connection pool: {err}")
    exit() # Exit if the bot can't connect to the database on start

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = db_pool
        self.topggpy = None

bot = MyBot(command_prefix=';;', intents=intents, help_command=None)

# --- Bot Admin Commands & Events ---
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
async def triviaquestions(ctx):
    if ctx.author.id == config.jacob:
        await ctx.send(file=discord.File("trivia.json"))
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner, used to get the trivia questions.", color=0xff0000)
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
                with open(file_path, "w", encoding="utf-8") as file: # Added encoding for safety
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
            embed = discord.Embed(title="Error", description="This command can only be used in specified channels or DMs.", color=0xff0000)
            return await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner.", color=0xff0000)
        return await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")
    print(f"Bot is ready and connected to {len(bot.guilds)} servers.")
    # Initialize top.gg client and attach it to the bot instance
    bot.topggpy = topgg.DBLClient(bot, os.getenv("topgg-token"), autopost=True, post_shard_count=True)

@bot.event
async def on_guild_join(guild):
    join_leave_channel = bot.get_channel(1168939285274177627)
    try:
        embed = discord.Embed(title="Joined Server", description=f"Name: {guild.name}\nMembers: {guild.member_count}\n", color=0x00ff00)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await join_leave_channel.send(embed=embed)
    except Exception as e:
        await join_leave_channel.send(f"Joined a server but couldn't get server information. Error: {e}")


    try:
        guilds = bot.guilds
        members = sum(g.member_count for g in guilds)
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await vc.edit(name=f"Servers: {len(guilds)}")
        await membersVC.edit(name=f"Members: {int(members):,}")
        if len(guilds) % 100 == 0:
            await join_leave_channel.send(f"<@920797181034778655> Bot has reached a milestone of `{len(guilds)}` servers!")
    except Exception as e:
        print(f"Error updating stats on guild join: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title="Cooldown", description=f"This command is on cooldown. Try again in {round(error.retry_after, 1)} seconds.", color=0xffa500)
        await ctx.send(embed=embed, ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Permissions Error", description="You do not have the required permissions to use this command.", color=0xff0000)
        await ctx.send(embed=embed, ephemeral=True)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(title="Bot Permissions Error", description="I do not have the required permissions to execute this command.", color=0xff0000)
        await ctx.send(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Error", description="An unexpected error occurred while processing your command.", color=0xff0000)
        await ctx.send(embed=embed, ephemeral=True)
        error_channel = bot.get_channel(config.error_channel)
        string = f"{ctx.author} in {ctx.guild} (ID: {ctx.guild.id})\nCommand: {ctx.command}\nError: {traceback.format_exc()}"
        await error_channel.send(f"```{string}```")
@bot.event
async def on_guild_remove(guild):
    join_leave_channel = bot.get_channel(1168939285274177627)
    try:
        embed = discord.Embed(title="Left Server", description=f"Name: {guild.name}\nMembers: {guild.member_count}\n", color=0xff0000)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await join_leave_channel.send(embed=embed)
    except Exception as e:
        await join_leave_channel.send(f"Left a server but couldn't get server information. Error: {e}")


    try:
        guilds = bot.guilds
        members = sum(g.member_count for g in guilds)
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await vc.edit(name=f"Servers: {len(guilds)}")
        await membersVC.edit(name=f"Members: {int(members):,}")
    except Exception as e:
        print(f"Error updating stats on guild remove: {e}")

async def load_cogs():
    print("--- Loading Cogs ---")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Loaded: `{filename}`')
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")
    print("--------------------")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("token"))

# --- NEW: Graceful Shutdown Function ---
async def shutdown(bot_instance: MyBot):
    print("Bot is shutting down.")
    owner = bot_instance.get_user(config.jacob)
    if owner:
        try:
            await owner.send(f"Bot is shutting down now. ({datetime.now()})")
        except discord.errors.Forbidden:
            print("Could not send shutdown DM. Owner may have DMs disabled.")
    
    # Close the database pool before closing the bot
    if bot_instance.db_pool:
        bot_instance.db_pool.close()
        print("Database connection pool closed.")
        
    await bot_instance.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # When Ctrl+C is pressed, run the shutdown coroutine
        print("Shutdown signal received.")
        asyncio.run(shutdown(bot))
