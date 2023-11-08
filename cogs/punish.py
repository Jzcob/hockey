import discord
import pymongo
from discord.ext import commands
from discord import app_commands
import config
import TOKEN
from datetime import datetime as dt
from datetime import timedelta as td

currTime = dt.now()
timeFormat = currTime.strftime("%b %d, %Y")
dt_string = currTime.strftime("%d/%m/%Y %H:%M:%S")

myclient = pymongo.MongoClient(TOKEN.mongoDB)
myDB = myclient["Hockey"]
mycol = myDB["user_info"]

###### Roles ########
staff = 1165854744577855509
helper = 1165854743894179930
mod = 1165854748604383243
admin = 1165854745177640990
manager = 1165854746863751168
owner = 1165854743281799218
##### Channels ########


class punish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `punish.py`")

### Warn ###
    @app_commands.command(name="warn", description="Warns a user!")
    @app_commands.checks.has_role(staff)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str, evidence: discord.Attachment):
        try:
            def is_staff(member):
                return discord.utils.get(member.roles, name="Staff") is not None
            staff = interaction.user.id
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            if is_staff(member):
                mgr_channel = self.bot.get_channel(config.mgr_channel)
                embed = discord.Embed(title="Attempted Warn", description=f"{interaction.user.mention} tried to warn {member.mention} for `{reason}`", color=config.color)
                embed.set_image(url=f"{evidence.url}")
                await mgr_channel.send(embed=embed)
                return await interaction.response.send_message("You cannot warn a staff member!", ephemeral=True)
            elif staff == member:
                return await interaction.response.send_message("You cannot warn yourself!", ephemeral=True)
            elif member.id == 1156302042969677845:
                return await interaction.response.send_message("You cannot warn me!", ephemeral=True)
            warnList = playerDB['punishments']["warns"]
            warnList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}"})
            embed = discord.Embed(title=f"{member} was warned", color=config.color)
            embed.add_field(name="Punished By", value=f"{interaction.user.name}", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.add_field(name="Time", value=f"{dt_string}", inline=False)
            embed.set_image(url=f"{evidence.url}")
            userEmbed = discord.Embed(title=f"You have been warned in `{interaction.guild.name}`", color=config.color)
            userEmbed.add_field(name="Reason", value=f"{reason}", inline=False)
            userEmbed.add_field(name="Time", value=f"{dt_string}", inline=False)
            userEmbed.set_image(url=f"{evidence.url}")
            userEmbed.set_footer(text="If you feel this was a mistake, please contact a staff member by making a ticket.")
            print(warnList)
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.warns": warnList}})
            await interaction.response.send_message(embed=embed)
            try:
                await member.send(embed=userEmbed)
            except:
                await mod_logs.send(f"Unable to DM {member.mention} about their warn.")
            await mod_logs.send(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `warn` command:\n{e}")

### Timeout ###
    @app_commands.command(name="timeout", description="Timeouts a user!")
    @app_commands.describe(duration="How long should the timeout be?")
    @app_commands.choices(duration=[
        discord.app_commands.Choice(name='6 hours', value='6h'),
        discord.app_commands.Choice(name='1 day', value='1d'),
        discord.app_commands.Choice(name='3 days', value='3d'),
        discord.app_commands.Choice(name='1 week', value='1w'),
        discord.app_commands.Choice(name='2 weeks', value='2w'),
        discord.app_commands.Choice(name='3 weeks', value='3w'),
        discord.app_commands.Choice(name='1 month', value='1m'),
        ])
    @app_commands.checks.has_any_role(mod, admin, manager, owner)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: discord.app_commands.Choice[str], reason: str, evidence: discord.Attachment):
        try:
            if member.is_timed_out() is True:
                return await interaction.response.send_message("This user is already timed out!", ephemeral=True)
            staff = interaction.user.id
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            def is_staff(member):
                return discord.utils.get(member.roles, name="Staff") is not None
            if is_staff(member):
                mgr = self.bot.get_channel(config.mgr_channel)
                embed = discord.Embed(title="Attempted Timeout", description=f"{interaction.user.mention} tried to timeout {member.mention} for `{reason}`", color=config.color)
                embed.set_image(url=f"{evidence.url}")
                await mgr.send(embed=embed)
                return await interaction.response.send_message("You cannot timeout a staff member!", ephemeral=True)
            elif staff == member:
                return await interaction.response.send_message("You cannot timeout yourself!", ephemeral=True)
            elif member.id == 1156302042969677845:
                return await interaction.response.send_message("You cannot timeout me!", ephemeral=True)
            
            embed = discord.Embed(title=f"`{member.name}` was timed out", color=config.color)
            embed.add_field(name="Punished By", value=f"{interaction.user.name}", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.add_field(name="Duration", value=f"{duration.name}", inline=False)
            embed.add_field(name="Time", value=f"{dt_string}", inline=False)
            embed.set_image(url=f"{evidence.url}")

            userEmbed = discord.Embed(title=f"You have been timed out in `{interaction.guild.name}`", color=config.color)
            userEmbed.add_field(name="Reason", value=f"{reason}", inline=False)
            userEmbed.add_field(name="Duration", value=f"{duration.name}", inline=False)
            userEmbed.add_field(name="Time", value=f"{dt_string}", inline=False)
            userEmbed.set_image(url=f"{evidence.url}")

            timeoutList = playerDB['punishments']["timeouts"]
            if duration.value == "6h":
                punishment_duration = td(hours=6)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "1d":
                punishment_duration = td(days=1)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "3d":
                punishment_duration = td(days=3)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "1w":
                punishment_duration = td(weeks=1)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "2w":
                punishment_duration = td(weeks=2)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "3w":
                punishment_duration = td(weeks=3)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            elif duration.value == "1m":
                punishment_duration = td(weeks=4)
                timeoutList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}", "duration": f"{duration.name}"})
            else:
                return await interaction.response.send_message("Invalid duration!", ephemeral=True)
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.timeouts": timeoutList}})
            await member.timeout(punishment_duration, reason=reason)
            await interaction.response.send_message(embed=embed)
            try:
                await member.send(embed=userEmbed)
            except:
                await mod_logs.send(f"Unable to DM {member.mention} about their timeout.")
            await mod_logs.send(embed=embed)

        
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `timeout` command:\n{e}")
    
    @app_commands.command(name="test-user", description="Test user command")
    async def test_user(self, interaction: discord.Interaction, member: discord.Member):
        def is_staff(member):
            return discord.utils.get(member.roles, name="Staff") is not None
        print(is_staff(member))
        await interaction.response.send_message(f"User Roles: {member.roles}")


async def setup(bot):
    await bot.add_cog(punish(bot), guilds=[discord.Object(id=config.hockey_discord_server)])