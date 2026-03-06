import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiomysql
import os
import io
import config
import traceback
from datetime import datetime, timedelta

# Custom check for Bot Owner since app_commands doesn't have one built-in
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
        self.prune_task.start()

    def cog_unload(self):
        self.prune_task.cancel()

    @tasks.loop(hours=24)
    async def prune_task(self):
        """Wipes data older than 90 days for non-premium guilds."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                tables = ["warns", "timeouts", "bans", "staff_notes"]
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
        await interaction.response.defer()
        premium = await self.is_guild_premium(interaction.guild.id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Determine limit per category based on premium status
                limit = 1000 if premium else 10
                
                # Use subqueries to limit each type individually before joining them
                query = f"""
                    (SELECT 'Warn' as type, reason, staff_id, created_at 
                     FROM warns 
                     WHERE user_id = %s AND guild_id = %s 
                     ORDER BY created_at DESC LIMIT {limit})
                    UNION ALL
                    (SELECT 'Timeout' as type, reason, staff_id, created_at 
                     FROM timeouts 
                     WHERE user_id = %s AND guild_id = %s 
                     ORDER BY created_at DESC LIMIT {limit})
                    UNION ALL
                    (SELECT 'Kick' as type, reason, staff_id, created_at 
                     FROM kicks 
                     WHERE user_id = %s AND guild_id = %s 
                     ORDER BY created_at DESC LIMIT {limit})
                    UNION ALL
                    (SELECT 'Ban' as type, reason, staff_id, created_at 
                     FROM bans 
                     WHERE user_id = %s AND guild_id = %s 
                     ORDER BY created_at DESC LIMIT {limit})
                    ORDER BY created_at DESC
                """
                
                await cursor.execute(query, (
                    user.id, interaction.guild.id, 
                    user.id, interaction.guild.id,
                    user.id, interaction.guild.id,
                    user.id, interaction.guild.id
                ))
                history = await cursor.fetchall()

        embed = discord.Embed(title=f"Punishments for {user.name}", color=discord.Color.orange())
        
        if not history:
            embed.description = "This user has a clean record."
        else:
            for item in history:
                date_str = item['created_at'].strftime('%Y-%m-%d')
                embed.add_field(
                    name=f"{item['type']} on {date_str}", 
                    value=f"**Reason:** {item['reason'][:100]}\n**Staff:** <@{item['staff_id']}>", 
                    inline=False
                )

        if premium:
            embed.set_footer(text="💎 Referee Tier: Persistent storage enabled.")
        else:
            embed.set_footer(text=f"⏳ Free Tier: Records older than {self.retention_days} days are automatically deleted.")
        
        await interaction.followup.send(embed=embed)

    # --- Moderation Commands ---

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: discord.Attachment = None):
        await interaction.response.defer()
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = "INSERT INTO warns (guild_id, user_id, staff_id, reason, evidence_url) VALUES (%s, %s, %s, %s, %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, evidence.url if evidence else None))
                await conn.commit()
        await interaction.followup.send(f"✅ **{user.name}** has been warned.")

    @app_commands.command(name="timeout", description="Timeout a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.choices(duration=[
        app_commands.Choice(name="60 Seconds", value=60),
        app_commands.Choice(name="5 Minutes", value=300),
        app_commands.Choice(name="10 Minutes", value=600),
        app_commands.Choice(name="1 Hour", value=3600),
        app_commands.Choice(name="1 Day", value=86400),
        app_commands.Choice(name="1 Week", value=604800)
    ])
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: app_commands.Choice[int], reason: str):
        await interaction.response.defer()
        try:
            until = timedelta(seconds=duration.value)
            await user.timeout(until, reason=reason)
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO timeouts (guild_id, user_id, staff_id, reason, duration_seconds) VALUES (%s, %s, %s, %s, %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason, duration.value))
                    await conn.commit()
            
            await interaction.followup.send(f"✅ **{user.name}** has been timed out for {duration.name}.")
        except Exception:
            await interaction.followup.send("❌ Failed to timeout user. Check hierarchy/permissions.")

    @app_commands.command(name="untimeout", description="Remove timeout from a user.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()
        try:
            await user.timeout(None, reason=reason)
            await interaction.followup.send(f"✅ Timeout removed from **{user.name}**.")
        except Exception:
            await interaction.followup.send("❌ Failed to remove timeout.")

    @app_commands.command(name="kick", description="Kick a user.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await interaction.response.defer()
        try:
            await user.kick(reason=reason)
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO kicks (guild_id, user_id, staff_id, reason) VALUES (%s, %s, %s, %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been kicked.")
        except Exception:
            await interaction.followup.send("❌ Failed to kick user.")

    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str, delete_messages: bool = False):
        await interaction.response.defer()
        try:
            delete_sec = 604800 if delete_messages else 0
            await interaction.guild.ban(user, reason=reason, delete_message_seconds=delete_sec)
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "INSERT INTO bans (guild_id, user_id, staff_id, reason) VALUES (%s, %s, %s, %s)"
                    await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, reason))
                    await conn.commit()
            await interaction.followup.send(f"✅ **{user.name}** has been banned.")
        except Exception:
            await interaction.followup.send("❌ Failed to ban user.")

    @app_commands.command(name="unban", description="Unban a user by ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        await interaction.response.defer()
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await interaction.followup.send(f"✅ **{user.name}** has been unbanned.")
        except Exception:
            await interaction.followup.send("❌ Failed to unban user. Ensure the ID is correct.")

    # --- Staff Notes & Exports ---

    @app_commands.command(name="export-logs", description="REFEREE ONLY: Export all server logs to a text file.")
    @app_commands.checks.has_permissions(administrator=True)
    async def export_logs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not await self.is_guild_premium(interaction.guild.id):
            return await interaction.followup.send("❌ Upgrade to **Referee** to export server logs.")

        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM warns WHERE guild_id = %s", (interaction.guild.id,))
                results = await cursor.fetchall()

        if not results:
            return await interaction.followup.send("No logs found to export.")

        output = "ID | User ID | Staff ID | Date | Reason\n" + "-"*60 + "\n"
        for r in results:
            output += f"{r['warn_id']} | {r['user_id']} | {r['staff_id']} | {r['created_at']} | {r['reason']}\n"

        file = discord.File(io.BytesIO(output.encode()), filename=f"history_{interaction.guild.id}.txt")
        await interaction.followup.send("✅ Server history export:", file=file)

    @app_commands.command(name="add-note", description="Add an internal staff note.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def add_note(self, interaction: discord.Interaction, user: discord.Member, note: str):
        await interaction.response.defer(ephemeral=True)
        premium = await self.is_guild_premium(interaction.guild.id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if not premium:
                    await cursor.execute("SELECT COUNT(*) FROM staff_notes WHERE user_id = %s AND guild_id = %s", (user.id, interaction.guild.id))
                    res = await cursor.fetchone()
                    if res and res[0] >= 3:
                        return await interaction.followup.send("❌ **Free Tier** is limited to 3 notes per user. Upgrade to **Referee** for unlimited notes!")

                sql = "INSERT INTO staff_notes (guild_id, user_id, staff_id, note_content) VALUES (%s, %s, %s, %s)"
                await cursor.execute(sql, (interaction.guild.id, user.id, interaction.user.id, note))
                await conn.commit()
        await interaction.followup.send(f"✅ Note added for {user.name}.")

async def setup(bot):
    await bot.add_cog(PunishPublic(bot))