import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiomysql
import os
import config
import traceback
import re
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

    def parse_duration(self, duration_str: str):
        """Parses a duration string like 1h, 1d, 1w into a timedelta object."""
        match = re.match(r"^(\d+)([smhdw])$", duration_str.lower())
        if not match:
            return None
        
        amount, unit = match.groups()
        amount = int(amount)
        
        units = {
            's': timedelta(seconds=amount),
            'm': timedelta(minutes=amount),
            'h': timedelta(hours=amount),
            'd': timedelta(days=amount),
            'w': timedelta(weeks=amount)
        }
        return units.get(unit)

    # --- Helpers ---

    async def check_released(self, interaction: discord.Interaction) -> bool:
        if getattr(config, "released", False):
            return True
        await interaction.followup.send(
            "🚧 **This feature is coming soon!**\nJoin my discord server found in `/info` for more information.", 
            ephemeral=True
        )
        return False

    async def get_logging_channel(self, guild_id):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT log_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return res['log_channel_id'] if res else None

    async def log_action(self, guild, message: str):
        """Safely finds the log channel and sends the message."""
        channel_id = await self.get_logging_channel(guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(message)
                except: pass

    async def send_dm_safe(self, user: discord.Member, embed: discord.Embed):
        """Safely attempts to DM a user."""
        try:
            await user.send(embed=embed)
        except: pass

    async def report_error(self, error_trace):
        error_channel = self.bot.get_channel(config.error_channel)
        if error_channel:
            await error_channel.send(f"<@920797181034778655> Error in `publicPunish`:```{error_trace}```")

    # --- Tasks ---

    @tasks.loop(hours=24)
    async def prune_task(self):
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    tables = ["warns", "timeouts", "kicks", "bans", "staff_notes"]
                    for table in tables:
                        query = f"DELETE t FROM {table} t LEFT JOIN premium_status p ON t.guild_id = p.entity_id WHERE (p.is_premium = FALSE OR p.is_premium IS NULL) AND t.created_at < DATE_SUB(NOW(), INTERVAL %s DAY)"
                        await cursor.execute(query, (self.retention_days,))
                    await conn.commit()
        except Exception as e:
            print(traceback.format_exc())
            await self.report_error(traceback.format_exc())

    async def is_guild_premium(self, guild_id):
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT is_premium FROM premium_status WHERE entity_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return bool(res['is_premium']) if res else False

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `publicPunish.py`")

    # --- Commands ---

    @app_commands.command(name="punishments", description="View punishment history.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def punishments(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            premium = await self.is_guild_premium(interaction.guild.id)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    limit = 1000 if premium else 10
                    query = f"""
                        (SELECT 'Warn' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at FROM warns WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Timeout' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at FROM timeouts WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Kick' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at FROM kicks WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        UNION ALL
                        (SELECT 'Ban' as type, CAST(AES_DECRYPT(reason, %s) AS CHAR) as reason, staff_id, created_at FROM bans WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT {limit})
                        ORDER BY created_at DESC
                    """
                    await cursor.execute(query, (self.enc_key, user.id, interaction.guild.id) * 4)
                    history = await cursor.fetchall()

            embed = discord.Embed(title=f"Punishments for {user.name}", color=discord.Color.orange())
            if not history:
                embed.description = "This user has a clean record."
            else:
                for item in history:
                    date = item['created_at'].strftime('%Y-%m-%d')
                    reason = item['reason'].decode() if isinstance(item['reason'], bytes) else str(item['reason'] or "No reason.")
                    embed.add_field(name=f"{item['type']} | {date}", value=f"**Reason:** {reason[:100]}\n**Staff:** <@{item['staff_id']}>", inline=False)
            
            embed.set_footer(text="💎 Premium" if premium else f"⏳ Free Tier (Last {self.retention_days} days)")
            await interaction.followup.send(embed=embed)
        except:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ Error fetching history.", ephemeral=True)

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

            await self.log_action(interaction.guild, f"⚠️ **{user}** was warned by **{interaction.user}**: {reason[:100]}")
            await self.send_dm_safe(user, discord.Embed(title=f"Warning: {interaction.guild.name}", description=reason, color=discord.Color.yellow()))
            await interaction.followup.send(f"✅ **{user.name}** has been warned.")
        except:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ Error logging warning.", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        # Uses the parse_duration helper to handle 1m, 1h, 1d, 1w
        delta = self.parse_duration(duration)
        if not delta:
            return await interaction.followup.send("❌ Invalid duration format. Use e.g., `15m`, `1h`, `1d`, `1w`.", ephemeral=True)
        
        # Discord maximum timeout is 28 days
        if delta > timedelta(days=28):
            return await interaction.followup.send("❌ Timeout duration cannot exceed 28 days.", ephemeral=True)

        try:
            await user.timeout(delta, reason=reason)
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO timeouts (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    # We store the duration string in the reason field so you can see it in logs later
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, f"[{duration}] {reason}", self.enc_key, evidence.url if evidence else None))
                    await conn.commit()
            
            await self.log_action(interaction.guild, f"⏱️ **{user}** timed out by **{interaction.user}** ({duration}): {reason[:100]}")
            
            dm_embed = discord.Embed(title=f"Timed out in {interaction.guild.name}", description=f"Duration: {duration}\nReason: {reason}", color=discord.Color.orange())
            await self.send_dm_safe(user, dm_embed)
            
            await interaction.followup.send(f"✅ **{user.name}** timed out for {duration}.")
            
        except discord.Forbidden: 
            await interaction.followup.send("❌ Permission Denied. I cannot timeout this user.")
        except Exception:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ An error occurred during the timeout process.")

    @app_commands.command(name="kick", description="Kick a user.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            await self.send_dm_safe(user, discord.Embed(title=f"Kicked: {interaction.guild.name}", description=reason, color=discord.Color.red()))
            await user.kick(reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO kicks (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()

            await self.log_action(interaction.guild, f"👢 **{user}** kicked by **{interaction.user}**: {reason[:100]}")
            await interaction.followup.send(f"✅ **{user.name}** kicked.")
        except discord.Forbidden: await interaction.followup.send("❌ Permission Denied.")
        except:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ Error.")

    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        if not await self.check_released(interaction): return

        try:
            await self.send_dm_safe(user, discord.Embed(title=f"Banned: {interaction.guild.name}", description=reason, color=discord.Color.red()))
            await user.ban(reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO bans (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                    await conn.commit()

            await self.log_action(interaction.guild, f"🔨 **{user}** banned by **{interaction.user}**: {reason[:100]}")
            await interaction.followup.send(f"✅ **{user.name}** banned.")
        except discord.Forbidden: await interaction.followup.send("❌ Permission Denied.")
        except:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ Error.")

    @app_commands.command(name="set-logs", description="Set log channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        if not await self.check_released(interaction): return
        
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO guild_settings (guild_id, log_channel_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE log_channel_id = VALUES(log_channel_id)"
                    await cursor.execute(sql, (interaction.guild.id, channel.id))
                    await conn.commit()
            await interaction.followup.send(f"✅ Log channel set to {channel.mention}", ephemeral=True)
        except:
            await self.report_error(traceback.format_exc())
            await interaction.followup.send("❌ DB Error.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PunishPublic(bot))