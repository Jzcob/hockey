import discord
import asyncio
from discord.ext import commands
import os
import config
import aiomysql
from dotenv import load_dotenv
from datetime import datetime
import topgg
import traceback

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.auto_moderation_configuration = True
intents.reactions = True
intents.members = False 
status = discord.Status.online

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = None 
        self.topggpy = None

    async def setup_hook(self):
        print("Creating database connection pool...")
        try:
            self.db_pool = await aiomysql.create_pool(
                host=os.getenv("db_host"),
                port=3306,
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                db=os.getenv("db_name"),
                autocommit=True,
                loop=asyncio.get_event_loop(),
                pool_recycle=3600
            )
            print("✅ Successfully created database connection pool.")
        except Exception as e:
            print(f"❌ FAILED to create database connection pool: {e}")
            await self.close()
            return

        print("--- Loading Cogs ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded: `{filename}`')
                except Exception as e:
                    print(f"❌ Failed to load cog {filename}: {e}")
                    traceback.print_exc()
        print("--------------------")

bot = MyBot(command_prefix=';;', intents=intents, help_command=None)

# --- Helper Function for Premium Logging ---
async def log_premium_event(bot, title, entity_id, is_guild, color):
    try:
        log_channel = bot.get_channel(config.premium_logs)
        if log_channel:
            type_str = "Server" if is_guild else "User"
            embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
            embed.add_field(name="Type", value=type_str, inline=True)
            embed.add_field(name="ID", value=f"`{entity_id}`", inline=True)
            
            name = "Unknown"
            if is_guild:
                guild = bot.get_guild(entity_id)
                if guild: name = guild.name
            else:
                try:
                    user = await bot.fetch_user(entity_id)
                    if user: name = user.name
                except: pass
            
            embed.add_field(name="Name", value=name, inline=False)
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"Error logging premium event: {e}")

# --- Entitlement Events ---

@bot.event
async def on_entitlement_create(entitlement: discord.Entitlement):
    entity_id = entitlement.guild_id if entitlement.guild_id else entitlement.user_id
    async with bot.db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql = """
                INSERT INTO premium_status (entity_id, is_premium, tier) 
                VALUES (%s, 1, 'referee') 
                ON DUPLICATE KEY UPDATE is_premium = 1, tier = 'referee'
            """
            await cursor.execute(sql, (entity_id,))
    await log_premium_event(bot, "🆕 New Subscription Created", entity_id, bool(entitlement.guild_id), 0x00ff00)

@bot.event
async def on_entitlement_update(entitlement: discord.Entitlement):
    entity_id = entitlement.guild_id if entitlement.guild_id else entitlement.user_id
    async with bot.db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql = "UPDATE premium_status SET is_premium = 1 WHERE entity_id = %s"
            await cursor.execute(sql, (entity_id,))
    await log_premium_event(bot, "🔄 Subscription Renewed/Updated", entity_id, bool(entitlement.guild_id), 0x3498db)

@bot.event
async def on_entitlement_delete(entitlement: discord.Entitlement):
    entity_id = entitlement.guild_id if entitlement.guild_id else entitlement.user_id
    async with bot.db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            sql = "UPDATE premium_status SET is_premium = 0 WHERE entity_id = %s"
            await cursor.execute(sql, (entity_id,))
    await log_premium_event(bot, "❌ Subscription Expired", entity_id, bool(entitlement.guild_id), 0xff0000)

# --- Standard Commands ---

@bot.command()
async def sync(ctx) -> None:
    if ctx.author.id == config.jacob:
        try:
            fmt = await ctx.bot.tree.sync()
            print(f"Synced {len(fmt)} commands.")
            embed = discord.Embed(title="Synced", description=f"Synced {len(fmt)} commands.", color=0x00ff00)
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner.", color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
async def syncserver(ctx) -> None:
    if ctx.author.id == config.jacob:
        try:
            fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            print(f"Synced {len(fmt)} commands.")
            embed = discord.Embed(title="Synced", description=f"Synced {len(fmt)} commands to this server.", color=0x00ff00)
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to only the bot owner.", color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
async def triviaquestions(ctx):
    if ctx.author.id == config.jacob:
        await ctx.send(file=discord.File("trivia.json"))
    else:
        embed = discord.Embed(title="Error", description="This is a bot admin command restricted to the bot owner.", color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
async def servers(ctx):
    if ctx.author.id == config.jacob:
        if ctx.channel.type == discord.ChannelType.private or ctx.channel.id in config.allowed_channels:
            guilds = bot.guilds
            try:
                desc = f"Total Servers: {len(guilds)}\n"
                members = sum(g.member_count for g in guilds)
                for guild in guilds:
                    desc += f"ID: {guild.id}, Members: {guild.member_count}, Name: {guild.name}\n"
                
                file_path = "server_info.txt"
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(desc)
                await ctx.send(file=discord.File(file_path))
                os.remove(file_path)
                
                vc = bot.get_channel(1173304351872253952)
                membersVC = bot.get_channel(1186445778043031722)
                await vc.edit(name=f"Servers: {len(bot.guilds)}")
                await membersVC.edit(name=f"Members: {int(members):,}")
            except Exception as e:
                await ctx.send(embed=discord.Embed(title="Error", description=f"Something went wrong: `{e}`", color=0xff0000))
        else:
            await ctx.send(embed=discord.Embed(title="Error", description="Use this in specified channels or DMs.", color=0xff0000))
    else:
        await ctx.send(embed=discord.Embed(title="Error", description="Unauthorized: Bot owner only.", color=0xff0000))

# --- Events ---

@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")
    print(f"Bot is ready and connected to {len(bot.guilds)} servers.")
    bot.topggpy = topgg.DBLClient(bot, os.getenv("topgg-token"), autopost=True, post_shard_count=True)

@bot.event
async def on_guild_join(guild):
    join_leave_channel = bot.get_channel(1168939285274177627)
    try:
        guilds = bot.guilds
        members = sum(g.member_count for g in guilds)
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await vc.edit(name=f"Servers: {len(guilds)}")
        await membersVC.edit(name=f"Members: {int(members):,}")
        if len(guilds) % 100 == 0:
            await join_leave_channel.send(f"<@920797181034778655> Milestone: `{len(guilds)}` servers!")
    except Exception as e:
        print(f"Join update error: {e}")

@bot.event
async def on_guild_remove(guild):
    try:
        guilds = bot.guilds
        members = sum(g.member_count for g in guilds)
        vc = bot.get_channel(1173304351872253952)
        membersVC = bot.get_channel(1186445778043031722)
        await vc.edit(name=f"Servers: {len(guilds)}")
        await membersVC.edit(name=f"Members: {int(members):,}")
    except Exception as e:
        print(f"Remove update error: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=discord.Embed(title="Cooldown", description=f"Try again in {round(error.retry_after, 1)}s.", color=0xffa500), ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(title="Permissions", description="Missing permissions.", color=0xff0000), ephemeral=True)
    else:
        error_channel = bot.get_channel(config.error_channel)
        string = f"{ctx.author} in {ctx.guild}\nCommand: {ctx.command}\nError: {traceback.format_exc()}"
        await error_channel.send(f"```{string}```")

# --- Shutdown logic ---

async def main():
    async with bot:
        await bot.start(os.getenv("token"))

async def shutdown(bot_instance: MyBot):
    print("Bot is shutting down.")
    owner = bot_instance.get_user(config.jacob)
    if owner:
        try: await owner.send(f"Bot shutting down. ({datetime.now()})")
        except: pass
    if bot_instance.db_pool:
        bot_instance.db_pool.close()
        await bot_instance.db_pool.wait_closed()
    await bot_instance.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown(bot))