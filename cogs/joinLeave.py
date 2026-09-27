import discord
from discord.ext import commands
from discord import app_commands
import config
import pymongo
import os
from dotenv import load_dotenv
load_dotenv()
import traceback

myclient = pymongo.MongoClient(os.getenv("mongodb"))
myDB = myclient["Hockey"]
mycol = myDB["user_info"]

async def add_hockey_league_role(self, member: discord.Member):
    """Give the Hockey League role to members registered in the rosters table."""
    try:
        async with self.bot.db_pool.acquire() as conn:
            await conn.ping(reconnect=True)

            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT user_id FROM rosters WHERE user_id = %s LIMIT 1",
                    (member.id,)
                )
                roster = await cursor.fetchone()

        # User is not registered in the hockey league.
        if roster is None:
            return

        role = member.guild.get_role(config.hockey_bot_league)

        if role is None:
            raise RuntimeError(
                f"Could not find hockey_bot_league role "
                f"({config.hockey_bot_league}) in guild {member.guild.id}"
            )

        # Don't make an unnecessary Discord API request if they already have it.
        if role not in member.roles:
            await member.add_roles(
                role,
                reason="Registered Hockey League member rejoined the server"
            )

    except Exception:
        error_channel = self.bot.get_channel(config.error_channel)
        if error_channel:
            await error_channel.send(
                f"<@920797181034778655>"
                f"```{traceback.format_exc()}```"
            )

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
        "levels": {
            "level": 0,
            "xp": 0
        },
        "economy": {
            "wallet": 0,
            "bank": 0
        },
        "punishments": {
            "bans": [],
            "timeouts": [],
            "warns": [],
            "notes": []
        },
    }
    mycol.insert_one(mydict)


class joinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `joinLeave.py`")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == config.hockey_discord_server:
            welcome_channel = self.bot.get_channel(1173831029295951882)
            embed = discord.Embed(title="Welcome to the Hockey Discord Server!", description=f"Welcome to the Hockey Discord Server, {member.mention}!\n\n" + 
            f":mega: Please read the rules in <#1165854571340513292>\n" + 
            f":mega: If you have any questions please ask them in <#1165873655931219968>" +
            f":mega: Have fun in the server!", color=config.color)
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"Member #{len(member.guild.members)}")
            add_db(member)
            await self.add_hockey_league_role(member)
            await welcome_channel.send(content=member.mention, embed=embed)
            try:
                await member.send(embed=embed)
            except:
                error_channel = self.bot.get_channel(config.error_channel)
                string = f"{traceback.format_exc()}"
                await error_channel.send(f"<@920797181034778655>```{string}```")
        else:
            return
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == config.hockey_discord_server:
            welcome_channel = self.bot.get_channel(1173831029295951882)
            await welcome_channel.send(f"{member.mention} has left the server.")
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB['info']['punished'] == True:
                return
            else:
                mycol.delete_one({"_id": member.id})
        else:
            return
    
    @app_commands.command(name="add-db", description="Adds a user to the database.")
    @app_commands.checks.has_any_role(config.owner)
    async def addDB(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id not in config.bot_authors:
            return await interaction.response.send_message("You cannot add a member to the database!", ephemeral=True)
        try:
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB is None:
                add_db(member)
                await interaction.response.send_message("User added to the database!", ephemeral=True)
            else:
                await interaction.response.send_message("User already exists in the database!", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")

    @app_commands.command(name="add-hockey-league-role", description="Adds the Hockey League role to users registered in the rosters table.")
    @app_commands.checks.has_any_role(config.owner)
    async def add_hockey_league_role_command(self, interaction: discord.Interaction):
        if interaction.user.id not in config.bot_authors:
            return await interaction.response.send_message("You cannot add the Hockey League role to a member!", ephemeral=True)
        else:
            members = interaction.guild.members
            for member in members:
                await self.add_hockey_league_role(member)
            await interaction.response.send_message("Hockey League role added to registered members!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(joinLeave(bot), guilds=[discord.Object(id=config.hockey_discord_server)])