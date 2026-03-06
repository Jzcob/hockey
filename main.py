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
intents.members = True 
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

# --- Standard Commands (sync, syncserver, etc.) ---
@bot.command()
async def sync(ctx):
    if ctx.author.id == config.jacob:
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(fmt)} commands.")

# ... (Keep your other @bot.command and @bot.event blocks here) ...

async def main():
    async with bot:
        await bot.start(os.getenv("token"))

async def shutdown(bot_instance: MyBot):
    print("Bot is shutting down.")
    if bot_instance.db_pool:
        bot_instance.db_pool.close()
        await bot_instance.db_pool.wait_closed()
    await bot_instance.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown(bot))