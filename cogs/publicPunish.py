import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiomysql
import os
import config
import traceback
from datetime import datetime, timedelta

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.bot_authors: 
            return True
        await interaction.response.send_message("❌ This command is restricted to bot owners.", ephemeral=True)
        return False
    return app_commands.check(predicate)

class PunishPublic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = self.bot.db_pool
        self.retention_days = 90
        self.enc_key = os.getenv("db_encryption_key") 
        self.prune_task.start()

    def cog_unload(self):
        self.prune_task.cancel()

    async def check_released(self, interaction: discord.Interaction) -> bool:
        if getattr(config, "released", False):
            return True
        
        await interaction.followup.send(
            "🚧 **This feature is coming soon!**\n"
            "Join my discord server found in `/info` for more information and updates.", 
            ephemeral=True
        )
        return False

    @tasks.loop(hours=24)
    async def prune_task(self):
        """Wipes data older than 90 days for non-premium guilds."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    tables = ["warns", "timeouts", "kicks", "bans", "staff_notes"]
                    for table in tables:
                        query = f"""
                        DELETE t FROM {table} t
                        LEFT JOIN premium_status p ON t.guild_id = p.entity_id
                        WHERE (p.is_premium = FALSE OR p.is_premium IS NULL)
                        AND t.created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                        """
                        await cursor.execute(query, (self.retention_days,))
                    await conn.commit()
        except Exception:
            print(f"Error in prune_task:\n{traceback.format_exc()}")

    async def is_guild_premium(self, guild_id):
        """Checks MySQL to see if the guild has active Referee Tier benefits."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT is_premium FROM premium_status WHERE entity_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return bool(res['is_premium']) if res else False

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `publicPunish.py`")

    # --- Punishment History & Management ---

    @app_commands.command(name="punishments", description="View punishment history.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def punishments(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer() # Immediate defer to stop timeout
        if not await self.check_released(interaction):
            return

        premium = await self.is_guild_premium(interaction.guild.id)
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    limit = 1000 if premium else 10
                    
                    query = f"""
                        (SELECT 'Warn' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at 
                        FROM warns WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Timeout' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at 
                        FROM timeouts WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Kick' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at 
                        FROM kicks WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Ban' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at 
                        FROM bans WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        ORDER BY created_at DESC
                    """
                    await cursor.execute(query, (
                        self.enc_key, user.id, interaction.guild.id, 
                        self.enc_key, user.id, interaction.guild.id,
                        self.enc_key, user.id, interaction.guild.id,
                        self.enc_key, user.id, interaction.guild.id
                    ))
                    history = await cursor.fetchall()

            embed = discord.Embed(title=f"Punishments for {user.name}", color=discord.Color.orange())
            
            if not history:
                embed.description = "This user has a clean record."
            else:
                for item in history:
                    date_str = item['created_at'].strftime('%Y-%m-%d')
                    raw_reason = item['reason']
                    reason = raw_reason.decode('utf-8') if isinstance(raw_reason, bytes) else str(raw_reason or "No reason provided.")

                    embed.add_field(
                        name=f"{item['type']} on {date_str}", 
                        value=f"**Reason:** {reason[:100]}\n**Staff:** <@{item['staff_id']}>", 
                        inline=False
                    )

            footer = "💎 Referee Tier: Persistent storage enabled." if premium else f"⏳ Free Tier: Records limited to 10 and deleted after {self.retention_days} days."
            embed.set_footer(text=footer)
            await interaction.followup.send(embed=embed)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("An error occurred while fetching punishment history. The issue has been reported.", ephemeral=True)


    # --- Moderation Commands ---

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return
        
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO warns (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been warned.")
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("❌ Error logging warning. Check database columns.", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            await user.timeout(timedelta(minutes=duration), reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO timeouts (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been timed out for {duration} minutes.")
        except discord.Forbidden:
            await interaction.followup.send("❌ I lack permissions to timeout this user.")
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("❌ An error occurred during timeout.")
    
    @timeout.error
    async def timeout_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        else:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("An error occurred while processing the command. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a user.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            await user.kick(reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO kicks (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been kicked.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Permission denied. My role must be higher than the target's role.")
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("❌ Kick failed. Check bot permissions and database.")
    


    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            await user.ban(reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO bans (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been banned.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Permission denied. Cannot ban this user.")
        except Exception:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ Ban failed.")

    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        else:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("An error occurred while processing the command. The issue has been reported.", ephemeral=True)
    # --- Configuration Commands ---

    @app_commands.command(name="set-logs", description="Set the channel where moderation logs are sent.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        if not await self.check_released(interaction):
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO guild_settings (guild_id, log_channel_id) 
                        VALUES (%s, %s) 
                        ON DUPLICATE KEY UPDATE log_channel_id = VALUES(log_channel_id)
                    """
                    await cursor.execute(sql, (interaction.guild.id, channel.id))
                    await conn.commit()
            
            await interaction.followup.send(f"✅ Logging channel has been set to {channel.mention}", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.followup.send("An error occurred while setting the logging channel. The issue has been reported.", ephemeral=True)

    @set_logs.error
    async def set_logs_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        else:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")
            await interaction.response.send_message("An error occurred while processing the command. The issue has been reported.", ephemeral=True)

    # --- Helpers ---

    async def get_logging_channel(self, guild_id):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT log_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return res['log_channel_id'] if res else None

    async def send_mod_log(self, guild, embed):
        channel_id = await self.get_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(PunishPublic(bot))