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
    
    @app_commands.command(name="ban", description="Bans a user!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str, evidence: discord.Attachment):
        try:
            if member.is_banned() is True:
                return await interaction.response.send_message("This user is already banned!", ephemeral=True)
            staff = interaction.user.id
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            def is_staff(member):
                return discord.utils.get(member.roles, name="Staff") is not None
            if is_staff(member):
                mgr = self.bot.get_channel(config.mgr_channel)
                embed = discord.Embed(title="Attempted Ban", description=f"{interaction.user.mention} tried to ban {member.mention} for `{reason}`", color=config.color)
                embed.set_image(url=f"{evidence.url}")
                await mgr.send(embed=embed)
                return await interaction.response.send_message("You cannot ban a staff member!", ephemeral=True)
            elif staff == member:
                return await interaction.response.send_message("You cannot ban yourself!", ephemeral=True)
            elif member.id == 1156302042969677845:
                return await interaction.response.send_message("You cannot ban me!", ephemeral=True)
            
            embed = discord.Embed(title=f"`{member.name}` was banned", color=config.color)
            embed.add_field(name="Punished By", value=f"{interaction.user.name}", inline=False)
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            embed.add_field(name="Time", value=f"{dt_string}", inline=False)
            embed.set_image(url=f"{evidence.url}")

            userEmbed = discord.Embed(title=f"You have been banned in `{interaction.guild.name}`", color=config.color)
            userEmbed.add_field(name="Reason", value=f"{reason}", inline=False)
            userEmbed.add_field(name="Time", value=f"{dt_string}", inline=False)
            userEmbed.set_image(url=f"{evidence.url}")

            banList = playerDB['punishments']["bans"]
            banList.append({"date": f"{timeFormat}", "staff": f"{staff}", "reason": f"{reason}"})
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.bans": banList}})
            await member.ban(reason=reason)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `ban` command:\n{e}")
##################################################################################################################
########################### REMOVE PUNISHMENT COMMANDS ###########################################################
##################################################################################################################            
    @app_commands.command(name="cancel-timeout", description="Cancel a user's timeout!")
    @app_commands.checks.has_any_role(mod, admin, manager, owner)
    async def cancel_timeout(self, interaction: discord.Interaction, member: discord.Member):
        if member.is_timed_out() is False:
            return await interaction.response.send_message(f"{member.mention} is not timed out!", ephemeral=True)
        try:
            await member.edit(timed_out_until=None)
            await interaction.response.send_message(f"Cancelled {member.mention}'s timeout!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `cancel-timeout` command:\n{e}")
    
    @app_commands.command(name="remove-warn", description="Remove a warn from a user's punishment history!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    async def remove_warn(self, interaction: discord.Interaction, member: discord.Member, warn: int):
        try:
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            warnList = playerDB['punishments']["warns"]
            if playerDB is None:
                return await interaction.response.send_message(f"{member.mention} has no warns!", ephemeral=True)
            if warn == 0:
                return await interaction.response.send_message(f"Invalid warn number! Warns start at 1!", ephemeral=True)
            if warn > len(warnList):
                return await interaction.response.send_message(f"Invalid warn number! {member.mention} only has {len(warnList)} warns!", ephemeral=True)
            warn -= 1
            warnList.pop(warn)
            warn += 1
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.warns": warnList}})
            await member.send(f"Your warn #{warn} has been removed in `{interaction.guild.name}` by {interaction.user.name}!")
            await interaction.response.send_message(f"Removed warn #{warn} from {member.mention}'s punishment history!")
            await mod_logs.send(f"Removed warn #{warn} from {member.mention}'s punishment history!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `remove-warn` command:\n{e}")
    
    @app_commands.command(name="remove-timeout", description="Remove a timeout from a user's punishment history!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    async def remove_timeout(self, interaction: discord.Interaction, member: discord.Member, timeout: int):
        try:
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            timeoutList = playerDB['punishments']["timeouts"]
            if playerDB is None:
                return await interaction.response.send_message(f"{member.mention} has no timeouts!", ephemeral=True)
            if timeout == 0:
                return await interaction.response.send_message(f"Invalid timeout number! Timeouts start at 1!", ephemeral=True)
            if timeout > len(timeoutList):
                return await interaction.response.send_message(f"Invalid timeout number! {member.mention} only has {len(timeoutList)} timeouts!", ephemeral=True)
            timeout -= 1
            timeoutList.pop(timeout)
            timeout += 1
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.timeouts": timeoutList}})
            await member.send(f"Your timeout #{timeout} has been removed in `{interaction.guild.name}` by {interaction.user.name}!")
            await interaction.response.send_message(f"Removed timeout #{timeout} from {member.mention}'s punishment history!")
            await mod_logs.send(f"Removed timeout #{timeout} from {member.mention}'s punishment history!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `remove-timeout` command:\n{e}")
        
    @app_commands.command(name="remove-ban", description="Remove a ban from a user's punishment history!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    async def remove_ban(self, interaction: discord.Interaction, member: discord.Member, ban: int):
        try:
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            banList = playerDB['punishments']["bans"]
            if playerDB is None:
                return await interaction.response.send_message(f"{member.mention} has no bans!", ephemeral=True)
            if ban == 0:
                return await interaction.response.send_message(f"Invalid ban number! Bans start at 1!", ephemeral=True)
            if ban > len(banList):
                return await interaction.response.send_message(f"Invalid ban number! {member.mention} only has {len(banList)} bans!", ephemeral=True)
            ban -= 1
            banList.pop(ban)
            ban += 1
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.bans": banList}})
            await member.send(f"Your ban #{ban} has been removed in `{interaction.guild.name}` by {interaction.user.name}!")
            await interaction.response.send_message(f"Removed ban #{ban} from {member.mention}'s punishment history!")
            await mod_logs.send(f"Removed ban #{ban} from {member.mention}'s punishment history!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `remove-ban` command:\n{e}")

##################################################################################################################
############################### PUNISHMENT COMMANDS ##############################################################
#################################################################################################################
    @app_commands.command(name="punishments", description="View a user's punishments!")
    async def punishments(self, interaction: discord.Interaction, member: discord.Member):
        try:
            playerDB = mycol.find_one({"_id": member.id})
            if playerDB is None:
                return await interaction.response.send_message(f"{member.mention} has no punishments!", ephemeral=True)
            warnList = playerDB['punishments']["warns"]
            timeoutList = playerDB['punishments']["timeouts"]
            banList = playerDB['punishments']["bans"]
            notelist = playerDB['punishments']["notes"]
            embed = discord.Embed(title=f"{member}'s Punishments", color=config.color)
            for warn in warnList:
                embed.add_field(name=f"Warn #{warnList.index(warn) + 1}", value=f"**Reason:** {warn['reason']}\n**Staff:** {warn['staff']}\n**Date:** {warn['date']}", inline=False)
            for timeout in timeoutList:
                embed.add_field(name=f"Timeout #{timeoutList.index(timeout) + 1}", value=f"**Reason:** {timeout['reason']}\n**Staff:** {timeout['staff']}\n**Date:** {timeout['date']}\n**Duration:** {timeout['duration']}", inline=False)
            for ban in banList:
                embed.add_field(name=f"Ban #{banList.index(ban) + 1}", value=f"**Reason:** {ban['reason']}\n**Staff:** {ban['staff']}\n**Date:** {ban['date']}", inline=False)
            for note in notelist:
                embed.add_field(name=f"Note #{notelist.index(note) + 1}", value=f"**Note:** {note['note']}\n**Staff:** {note['staff']}\n**Date:** {note['date']}", inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `punishments` command:\n{e}")

    @app_commands.command(name="fix-punishment", description="Fix a user's punishment reason!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    @app_commands.describe(type="What is the punishment?")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='Warn', value='warn'),
        discord.app_commands.Choice(name='Timeout', value='timeout'),
        discord.app_commands.Choice(name='Ban', value='ban'),
        ])
    async def fix_punishment(self, interaction: discord.Interaction, member: discord.Member, type: discord.app_commands.Choice[str], punishment: int, reason: str):
        try:
            punishment -= 1
            if type.value == "warn":
                mycol.update_one({"_id": member.id}, {"$set": {f"punishments.warns.{punishment}.reason": f"{reason}"}})
                await interaction.response.send_message(f"Updated warn #{punishment} for {member.mention}!\nNew Reason: `{reason}`")
            elif type.value == "timeout":
                mycol.update_one({"_id": member.id}, {"$set": {f"punishments.timeouts.{punishment}.reason": f"{reason}"}})
                await interaction.response.send_message(f"Updated timeout #{punishment} for {member.mention}!\nNew Reason: `{reason}`")
            elif type.value == "ban":
                mycol.update_one({"_id": member.id}, {"$set": {f"punishments.bans.{punishment}.reason": f"{reason}"}})
                await interaction.response.send_message(f"Updated ban #{punishment} for {member.mention}!\nNew Reason: `{reason}`")
            else:
                await interaction.response.send_message("Invalid punishment type!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `fix-punishment` command:\n{e}")


###############################################################################################################
################################# NOTE COMMANDS #############################################################
###############################################################################################################
    @app_commands.command(name="set-note", description="Set a note for a user!")
    @app_commands.checks.has_any_role(mod, admin, manager, owner)
    async def set_note(self, interaction: discord.Interaction, member: discord.Member, note: str):
        try:
            staff = interaction.user.id
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            noteList = playerDB['punishments']["notes"]
            noteList.append({"date": f"{timeFormat}", "staff": f"{staff}", "note": f"{note}"})
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.notes": noteList}})
            await interaction.response.send_message(f"Set a note for {member.mention}!")
            await mod_logs.send(f"Set a note for {member.mention}!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `set-note` command:\n{e}")
    
    @app_commands.command(name="remove-note", description="Remove a note from a user!")
    @app_commands.checks.has_any_role(admin, manager, owner)
    async def remove_note(self, interaction: discord.Interaction, member: discord.Member, note: int):
        try:
            mod_logs = self.bot.get_channel(config.mod_logs)
            playerDB = mycol.find_one({"_id": member.id})
            noteList = playerDB['punishments']["notes"]
            if playerDB is None:
                return await interaction.response.send_message(f"{member.mention} has no notes!", ephemeral=True)
            if note == 0:
                return await interaction.response.send_message(f"Invalid note number! Notes start at 1!", ephemeral=True)
            if note > len(noteList):
                return await interaction.response.send_message(f"Invalid note number! {member.mention} only has {len(noteList)} notes!", ephemeral=True)
            note -= 1
            noteList.pop(note)
            print(noteList)
            mycol.update_one({"_id": member.id}, {"$set": {"punishments.notes": noteList}})
            await interaction.response.send_message(f"Removed note #{note} from {member.mention}'s punishment history!")
            await mod_logs.send(f"Removed note #{note} from {member.mention}'s punishment history!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `remove-note` command:\n{e}")

##################################################################################################################
################################# TEST COMMANDS ###################################################################
##################################################################################################################

    @app_commands.command(name="purge", description="Purge a user's messages!")
    @app_commands.checks.has_any_role(mod, admin, manager, owner)
    async def purge(self, interaction: discord.Interaction, amount: int, member: discord.Member=None):
        try:
            if member is None:
                await interaction.channel.purge(limit=amount)
                await interaction.response.send_message(f"Purged {amount} messages!")
            else:
                await interaction.channel.purge(limit=amount, check=lambda m: m.author == member)
                await interaction.response.send_message(f"Purged {amount} messages from {member.mention}!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"Error in `purge` command:\n{e}")


    @app_commands.command(name="test-user", description="Test user command")
    async def test_user(self, interaction: discord.Interaction, member: discord.Member):
        def is_staff(member):
            return discord.utils.get(member.roles, name="Staff") is not None
        print(is_staff(member))
        await interaction.response.send_message(f"User Roles: {member.roles}")


async def setup(bot):
    await bot.add_cog(punish(bot), guilds=[discord.Object(id=config.hockey_discord_server)])