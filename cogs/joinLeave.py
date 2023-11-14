import discord
from discord.ext import commands
from discord import app_commands
import config
import TOKEN
import pymongo

myclient = pymongo.MongoClient(TOKEN.mongoDB)
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
            await welcome_channel.send(content=member.mention, embed=embed)
            try:
                await member.send(embed=embed)
            except:
                return
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
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            return await error_channel.send(f"Something went wrong with `/add-db` `{e}`")

async def setup(bot):
    await bot.add_cog(joinLeave(bot), guilds=[discord.Object(id=config.hockey_discord_server)])