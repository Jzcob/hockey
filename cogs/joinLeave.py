import discord
from discord.ext import commands
from discord import app_commands
import config
import TOKEN
import pymongo


class joinLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `joinLeave.py`")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == config.hockey_discord_server:
            welcome_channel = self.bot.get_channel(1165858822183735316)
            await welcome_channel.send(f"Welcome to the server, {member.mention}!")
            await member.send(f"Welcome to the server, {member.mention}!")
        else:
            return
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == config.hockey_discord_server:
            welcome_channel = self.bot.get_channel(1165858822183735316)
            await welcome_channel.send(f"{member.mention} has left the server.")
        else:
            return
    
    @app_commands.command(name="add-db", description="Adds a user to the database.")
    @app_commands.checks.has_any_role(config.owner)
    async def addDB(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id not in config.bot_authors:
            return await interaction.response.send_message("You cannot add a member to the database!", ephemeral=True)
        try:
            myclient = pymongo.MongoClient(TOKEN.mongoDB)
            myDB = myclient["Hockey"]
            mycol = myDB["user_info"]
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB is None:
                mydict = { 
                            "_id": member.id,
                            "info": {
                                "name": member.name,
                                "tag": member.discriminator,
                                "joined": member.joined_at.strftime("%b %d, %Y"),
                                "applied": False,
                                "appealed": False,
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
                await interaction.response.send_message("User added to the database!", ephemeral=True)
            else:
                await interaction.response.send_message("User already exists in the database!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            return await error_channel.send(f"Something went wrong with `/add-db` `{e}`")

async def setup(bot):
    await bot.add_cog(joinLeave(bot), guilds=[discord.Object(id=config.hockey_discord_server)])