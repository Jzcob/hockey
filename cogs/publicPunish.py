import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiomysql
import os
import io
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

    # --- Release Check Helper ---

    async def check_released(self, interaction: discord.Interaction) -> bool:
        if getattr(config, "released", False):
            return True
        
        await interaction.response.send_message(
            "🚧 **This feature is coming soon!**\n"
            "Join my discord server found in `/info` for more information and updates.", 
            ephemeral=True
        )
        return False

    @tasks.loop(hours=24)
    async def prune_task(self):
        """Wipes data older than 90 days for non-premium guilds."""
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
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        premium = await self.is_guild_premium(interaction.guild.id)
        
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
                if raw_reason:
                    reason = raw_reason.decode('utf-8') if isinstance(raw_reason, bytes) else str(raw_reason)
                else:
                    reason = "No reason provided or decryption failed."

                embed.add_field(
                    name=f"{item['type']} on {date_str}", 
                    value=f"**Reason:** {reason[:100]}\n**Staff:** <@{item['staff_id']}>", 
                    inline=False
                )

        if premium:
            embed.set_footer(text="💎 Referee Tier: Persistent storage enabled.")
        else:
            embed.set_footer(text=f"⏳ Free Tier: Records limited to 10 per type and deleted after {self.retention_days} days.")
        
        await interaction.followup.send(embed=embed)

    # --- Moderation Commands ---

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "INSERT INTO warns (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been warned.")
    
    @app_commands.command(name="timeout", description="Timeout a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str, evidence: discord.Attachment = None):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "INSERT INTO timeouts (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been timed out for {duration} minutes.")
        await user.timeout(timedelta(minutes=duration), reason=reason)

    @app_commands.command(name="kick", description="Kick a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "INSERT INTO kicks (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been kicked.")
        await user.kick(reason=reason)
    
    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "INSERT INTO bans (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s), %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, self.enc_key, evidence.url if evidence else None))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been banned.")
        await user.ban(reason=reason)
    
    @app_commands.command(name="unban", description="Unban a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unban(self, interaction: discord.Interaction, user: discord.User):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "DELETE FROM bans WHERE guild_id = %s AND user_id = %s"
                await cursor.execute(sql, (interaction.guild.id, user.id))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been unbanned.")
        await interaction.guild.unban(user)
    
    @app_commands.command(name="clear-punishments", description="Clear all punishments for a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clear_punishments(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                tables = ["warns", "timeouts", "kicks", "bans", "staff_notes"]
                for table in tables:
                    sql = f"DELETE FROM {table} WHERE guild_id = %s AND user_id = %s"
                    await cursor.execute(sql, (interaction.guild.id, user.id))
                await conn.commit()
        await interaction.followup.send(f"✅ All punishments for **{user.name}** have been cleared.")
    
    @app_commands.command(name="delete-punishment", description="Delete a specific punishment by ID.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def delete_punishment(self, interaction: discord.Interaction, punishment_id: int):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                tables = ["warns", "timeouts", "kicks", "bans", "staff_notes"]
                for table in tables:
                    sql = f"DELETE FROM {table} WHERE id = %s AND guild_id = %s"
                    await cursor.execute(sql, (punishment_id, interaction.guild.id))
                await conn.commit()
        await interaction.followup.send(f"✅ Punishment with ID **{punishment_id}** has been deleted.")
    
    @app_commands.command(name="add-note", description="Add an internal staff note.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def add_note(self, interaction: discord.Interaction, user: discord.Member, note: str):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        premium = await self.is_guild_premium(interaction.guild.id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if not premium:
                    await cursor.execute("SELECT COUNT(*) FROM staff_notes WHERE user_id = %s AND guild_id = %s", (user.id, interaction.guild.id))
                    res = await cursor.fetchone()
                    if res and res[0] >= 3:
                        return await interaction.followup.send("❌ **Free Tier** is limited to 3 notes per user. Upgrade to **Referee** for unlimited notes!")

                sql = "INSERT INTO staff_notes (guild_id, user_id, staff_id, note_content) VALUES (%s, %s, %s, AES_ENCRYPT(%s, %s))"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, note, self.enc_key))
                await conn.commit()
        await interaction.followup.send(f"✅ Note added for {user.name}.")
    
    # --- New Configuration Commands ---

    @app_commands.command(name="set-logs", description="Set the channel where moderation logs are sent.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.check_released(interaction):
            return

        await interaction.response.defer()
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = """
                    INSERT INTO guild_settings (guild_id, logging_channel_id) 
                    VALUES (%s, %s) 
                    ON DUPLICATE KEY UPDATE logging_channel_id = VALUES(logging_channel_id)
                """
                await cursor.execute(sql, (interaction.guild.id, channel.id))
                await conn.commit()
        
        await interaction.followup.send(f"✅ Logging channel has been set to {channel.mention}")

    async def get_logging_channel(self, guild_id):
        """Helper to fetch the log channel ID from the database"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT logging_channel_id FROM guild_settings WHERE guild_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return res['logging_channel_id'] if res else None

    async def send_mod_log(self, guild, embed):
        """Helper to send logs to the configured channel"""
        channel_id = await self.get_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PunishPublic(bot))