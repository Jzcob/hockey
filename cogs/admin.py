import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import config
import traceback
import aiomysql

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.bot_authors:
            return True
        await interaction.response.send_message("❌ This command is restricted to bot owners.", ephemeral=True)
        return False
    return app_commands.check(predicate)

class admin(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.db_pool = self.bot.db_pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `admin.py`")
        await self.bot.change_presence(activity=discord.CustomActivity(name="🚨 Playoff time /brackets 🚨"))
    
    # --- New Manual Premium Management ---

    @app_commands.command(name="give-referee", description="Manually grant Referee Tier to a server (Owner Only).")
    @is_owner()
    @app_commands.describe(guild_id="The ID of the server to grant premium to.")
    async def give_referee(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO premium_status (entity_id, is_premium, tier) 
                        VALUES (%s, 1, 'referee') 
                        ON DUPLICATE KEY UPDATE is_premium = 1, tier = 'referee'
                    """
                    await cursor.execute(sql, (int(guild_id),))
                    await conn.commit()
            await interaction.followup.send(f"✅ Server `{guild_id}` has been manually upgraded to **Referee Tier**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Database error: {e}")

    @app_commands.command(name="remove-referee", description="Manually remove Referee Tier from a server (Owner Only).")
    @is_owner()
    @app_commands.describe(guild_id="The ID of the server to remove premium from.")
    async def remove_referee(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "DELETE FROM premium_status WHERE entity_id = %s"
                    await cursor.execute(sql, (int(guild_id),))
                    await conn.commit()
            await interaction.followup.send(f"✅ Server `{guild_id}` has been downgraded to **Free Tier**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Database error: {e}")

    # --- Existing Admin Commands ---

    @app_commands.command(name="dev-mode", description="Toggles dev mode!")
    async def dev_mode(self, interaction: discord.Interaction):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/dev-mode` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}` \n---")
        try:
            if interaction.user.id in config.bot_authors:
                config.dev_mode = not config.dev_mode
                status = "enabled" if config.dev_mode else "disabled"
                return await interaction.response.send_message(f"Dev mode is now {status}!")
            else:
                return await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")

    @app_commands.command(name="send", description="Make the bot say something.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def say(self, interaction: discord.Interaction, *, message: str, channel: discord.TextChannel = None):
        try:
            target_channel = channel or interaction.channel
            await target_channel.send(message)
            await interaction.response.send_message(f"Sent message to {target_channel.mention}", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"```{traceback.format_exc()}```")

    @app_commands.command(name="bot-audit", description="Run a deep diagnostic audit for a specific server or user (Owner Only).")
    @is_owner()
    @app_commands.describe(
        guild_id="Optional: Target Server ID to audit",
        user_id="Optional: Target User ID to audit"
    )
    async def bot_audit(self, interaction: discord.Interaction, guild_id: str = None, user_id: str = None):
        await interaction.response.defer(ephemeral=True)
        
        audit_results = ["🔍 **[DEEP BOT DIAGNOSTIC AUDIT]**"]
        
        # 1. Global Core Health
        audit_results.append(
            f"**1. Core System & Intents:**\n"
            f"• Latency: `{round(self.bot.latency * 1000, 2)}ms`\n"
            f"• Connected Guilds: `{len(self.bot.guilds)}`\n"
            f"• Message Content Intent: `{self.bot.intents.message_content}`\n"
            f"• Server Members Intent: `{self.bot.intents.members}`"
        )
        
        # 2. Database Connection Check
        db_status = "❌ Disconnected / None"
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                        db_status = "✅ Connected & Responding"
            except Exception as e:
                db_status = f"❌ Error: {e}"
        audit_results.append(f"**2. Database Pool:**\n• Status: `{db_status}`")
        
        # 3. Targeted Guild Diagnostics (if provided)
        if guild_id:
            try:
                g_id = int(guild_id)
                guild = self.bot.get_guild(g_id) or await self.bot.fetch_guild(g_id)
                if guild:
                    me = guild.me or await guild.fetch_member(self.bot.user.id)
                    permissions = interaction.channel.permissions_for(me) if interaction.channel else None
                    
                    audit_results.append(
                        f"**3. Target Server Audit (`{guild.name}`):**\n"
                        f"• Server ID: `{guild.id}`\n"
                        f"• Member Count: `{guild.member_count}`\n"
                        f"• Bot Cached Members: `{len(guild.members)}`\n"
                        f"• Bot Permissions in Current Channel:\n"
                        f"  - View Channel: `{permissions.view_channel if permissions else 'N/A'}`\n"
                        f"  - Send Messages: `{permissions.send_messages if permissions else 'N/A'}`\n"
                        f"  - Read Message History: `{permissions.read_message_history if permissions else 'N/A'}`"
                    )
                else:
                    audit_results.append(f"**3. Target Server Audit:**\n• ❌ Bot is not in a guild with ID `{guild_id}` or couldn't fetch it.")
            except Exception as e:
                audit_results.append(f"**3. Target Server Audit:**\n• ❌ Failed to parse/fetch guild: `{e}`")
                
        # 4. Targeted User Diagnostics (if provided)
        if user_id:
            try:
                u_id = int(user_id)
                user = self.bot.get_user(u_id) or await self.bot.fetch_user(u_id)
                if user:
                    # Check if user has active scores/data in DB if pool is up
                    db_user_info = "Not Checked"
                    if self.db_pool:
                        async with self.db_pool.acquire() as conn:
                            async with conn.cursor() as cursor:
                                await cursor.execute("SELECT points FROM gtp_scores WHERE user_id = %s LIMIT 1", (u_id,))
                                row = await cursor.fetchone()
                                db_user_info = f"Found in GTP Scores (Points data exists)" if row else "No GTP Score entry found"
                                
                    audit_results.append(
                        f"**4. Target User Audit (`{user.name}`):**\n"
                        f"• User ID: `{user.id}`\n"
                        f"• Bot Mutuals / Cached: `{'Yes' if self.bot.get_user(u_id) else 'No (Fetched via API)'}`\n"
                        f"• Database State: `{db_user_info}`"
                    )
                else:
                    audit_results.append(f"**4. Target User Audit:**\n• ❌ Could not find user with ID `{user_id}`.")
            except Exception as e:
                audit_results.append(f"**4. Target User Audit:**\n• ❌ Failed to fetch user: `{e}`")

        # Compile and send (split if too long for one message)
        full_response = "\n\n".join(audit_results)
        if len(full_response) > 2000:
            full_response = full_response[:1990] + "..."
            
        await interaction.followup.send(full_response)

async def setup(bot):
    await bot.add_cog(admin(bot), guilds=[discord.Object(id=config.hockey_discord_server)])