import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiomysql
import os
import io
import config
from datetime import datetime, timedelta

# Custom check for Bot Owner since app_commands doesn't have one built-in
def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.bot_authors: # Uses your existing config list
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

    # --- Punishment Commands ---

    @app_commands.command(name="punishments", description="View punishment history.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def punishments(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        premium = await self.is_guild_premium(interaction.guild.id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                limit = 25 if premium else 10
                await cursor.execute(
                    "SELECT reason, staff_id, created_at FROM warns WHERE user_id = %s AND guild_id = %s ORDER BY created_at DESC LIMIT %s", 
                    (user.id, interaction.guild.id, limit)
                )
                warns = await cursor.fetchall()

        embed = discord.Embed(title=f"Punishments for {user.name}", color=discord.Color.orange())
        if not warns:
            embed.description = "This user has a clean record."
        else:
            for w in warns:
                date_str = w['created_at'].strftime('%Y-%m-%d')
                embed.add_field(
                    name=f"Warned on {date_str}", 
                    value=f"**Reason:** {w['reason'][:100]}\n**Staff:** <@{w['staff_id']}>", 
                    inline=False
                )

        if premium:
            embed.set_footer(text="💎 Referee Tier: Persistent storage enabled.")
        else:
            embed.set_footer(text=f"⏳ Free Tier: Records older than {self.retention_days} days are automatically deleted.")
        
        await interaction.followup.send(embed=embed)

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

    # --- Standard Moderation ---

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

async def setup(bot):
    await bot.add_cog(PunishPublic(bot))