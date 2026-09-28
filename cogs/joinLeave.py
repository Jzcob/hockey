import discord
from discord.ext import commands
from discord import app_commands
import config
import pymongo
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

myclient = pymongo.MongoClient(os.getenv("mongodb"))
myDB = myclient["Hockey"]
mycol = myDB["user_info"]


def add_db(member: discord.Member):
    mydict = {
        "_id": member.id,
        "info": {
            "name": member.name,
            "tag": member.discriminator,
            "joined": member.joined_at.strftime("%b %d, %Y"),
            "applied": False,
            "appealed": False,
            "punished": False,
            "currently_banned": False
        },
        "levels": {"level": 0, "xp": 0},
        "economy": {"wallet": 0, "bank": 0},
        "punishments": {"bans": [], "timeouts": [], "warns": [], "notes": []},
    }
    mycol.insert_one(mydict)


class joinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def report_error(self):
        error_channel = self.bot.get_channel(config.error_channel)
        if error_channel:
            await error_channel.send(
                f"<@920797181034778655>```{traceback.format_exc()}```"
            )

    async def add_hockey_league_role(self, member: discord.Member):
        """Give the league role if this Discord user has a roster."""
        try:
            async with self.bot.db_pool.acquire() as conn:
                await conn.ping(reconnect=True)
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT user_id FROM rosters WHERE user_id = %s LIMIT 1",
                        (member.id,)
                    )
                    roster = await cursor.fetchone()

            if roster is None:
                return False

            role = member.guild.get_role(config.hockey_bot_league)
            if role is None:
                raise RuntimeError(
                    f"Could not find hockey_bot_league role "
                    f"({config.hockey_bot_league}) in guild {member.guild.id}"
                )

            if role not in member.roles:
                await member.add_roles(
                    role,
                    reason="Registered Hockey League member joined/rejoined the server"
                )

            return True
        except Exception:
            await self.report_error()
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `joinLeave.py`")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != config.hockey_discord_server:
            return

        welcome_channel = self.bot.get_channel(1173831029295951882)
        embed = discord.Embed(
            title="Welcome to the Hockey Discord Server!",
            description=(
                f"Welcome to the Hockey Discord Server, {member.mention}!\\n\\n"
                f":mega: Please read the rules in <#1165854571340513292>\\n"
                f":mega: If you have any questions please ask them in "
                f"<#1165873655931219968>\\n"
                f":mega: Have fun in the server!"
            ),
            color=config.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)}")

        try:
            # Avoid duplicate MongoDB _id errors when a preserved member rejoins.
            if mycol.find_one({"_id": member.id}) is None:
                add_db(member)
        except Exception:
            await self.report_error()

        await self.add_hockey_league_role(member)

        if welcome_channel:
            try:
                await welcome_channel.send(content=member.mention, embed=embed)
            except Exception:
                await self.report_error()

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            # Closed DMs are normal and do not need an error report.
            pass
        except Exception:
            await self.report_error()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != config.hockey_discord_server:
            return

        welcome_channel = self.bot.get_channel(1173831029295951882)
        if welcome_channel:
            try:
                await welcome_channel.send(f"{member.mention} has left the server.")
            except Exception:
                await self.report_error()

        try:
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB is None:
                return

            if playerDB.get("info", {}).get("punished", False):
                return

            mycol.delete_one({"_id": member.id})
        except Exception:
            await self.report_error()

    @app_commands.command(
        name="sync-league-roles",
        description="Give the Hockey League role to all registered league members."
    )
    @app_commands.checks.has_any_role(config.owner)
    async def sync_league_roles(self, interaction: discord.Interaction):
        # A guild-wide sync may take time, so acknowledge Discord immediately.
        await interaction.response.defer(ephemeral=True, thinking=True)

        if interaction.guild is None or interaction.guild.id != config.hockey_discord_server:
            await interaction.followup.send(
                "This command can only be used in the Hockey Discord server.",
                ephemeral=True
            )
            return

        if interaction.user.id not in config.bot_authors:
            await interaction.followup.send(
                "You cannot sync Hockey League roles!",
                ephemeral=True
            )
            return

        try:
            role = interaction.guild.get_role(config.hockey_bot_league)
            if role is None:
                await interaction.followup.send(
                    f"Could not find the Hockey League role with ID `{config.hockey_bot_league}`.",
                    ephemeral=True
                )
                return

            # Fetch the roster once instead of doing one SQL query per member.
            async with self.bot.db_pool.acquire() as conn:
                await conn.ping(reconnect=True)
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT user_id FROM rosters")
                    rows = await cursor.fetchall()

            roster_user_ids = {int(row[0]) for row in rows}

            checked = registered = added = already_had = failed = 0

            for member in interaction.guild.members:
                if member.bot:
                    continue

                checked += 1
                if member.id not in roster_user_ids:
                    continue

                registered += 1
                if role in member.roles:
                    already_had += 1
                    continue

                try:
                    await member.add_roles(
                        role,
                        reason=f"Hockey League role sync requested by {interaction.user}"
                    )
                    added += 1
                except (discord.Forbidden, discord.HTTPException):
                    failed += 1

            await interaction.followup.send(
                "✅ **Hockey League role sync complete.**\\n\\n"
                f"Members checked: **{checked:,}**\\n"
                f"Registered league members in server: **{registered:,}**\\n"
                f"Roles added: **{added:,}**\\n"
                f"Already had role: **{already_had:,}**\\n"
                f"Failed: **{failed:,}**",
                ephemeral=True
            )
        except Exception:
            await self.report_error()
            if not interaction.is_expired():
                await interaction.followup.send(
                    "❌ An error occurred while syncing league roles. The issue has been reported.",
                    ephemeral=True
                )

    @app_commands.command(name="add-db", description="Adds a user to the database.")
    @app_commands.checks.has_any_role(config.owner)
    async def addDB(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id not in config.bot_authors:
            return await interaction.response.send_message(
                "You cannot add a member to the database!",
                ephemeral=True
            )

        try:
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB is None:
                add_db(member)
                await interaction.response.send_message(
                    "User added to the database!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "User already exists in the database!", ephemeral=True
                )
        except Exception:
            await self.report_error()
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred. The issue has been reported.",
                    ephemeral=True
                )
            elif not interaction.is_expired():
                await interaction.followup.send(
                    "❌ An error occurred. The issue has been reported.",
                    ephemeral=True
                )


async def setup(bot):
    await bot.add_cog(
        joinLeave(bot),
        guilds=[discord.Object(id=config.hockey_discord_server)]
    )
