### This is a private Cog for the Hockey Bot and is not for public use. ###
# Purpose: Create tickets for users to ask questions in.
# No other server can use this Cog, other than the Hockey Bot server.


import discord
from discord import app_commands, utils
from discord.ext import commands
import config
import traceback

#### Roles ####
management = 1165854746863751168
admin =1165854745177640990
moderator = 1165854748604383243
staff = 1165854744577855509
developer = 1170802776859750421
tester = 1171967165843386519

class SelectMenu(discord.ui.Select):
    def __init__(self):
        menu = [
            discord.SelectOption(label="Management", description="Management related questions"),
            discord.SelectOption(label="Development", description="Development related questions such as bugs, in-depth suggestions, etc."),
            discord.SelectOption(label="General", description="General questions")
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=menu)
    
    async def callback(self, interaction: discord.Interaction):
        managementTicket = utils.get(interaction.guild.text_channels, name=f"mgmt-{interaction.user.name.lower()}")
        developmentTicket = utils.get(interaction.guild.text_channels, name=f"dev-{interaction.user.name.lower()}")
        generalTicket = utils.get(interaction.guild.text_channels, name=f"gen-{interaction.user.name.lower()}")
        overwritesManagement = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.get_role(management): discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        overwritesDevelopment = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.get_role(developer): discord.PermissionOverwrite(read_messages=True),
            interaction.guild.get_role(tester): discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        overwritesGeneral = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.get_role(staff): discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        ticketCategory = utils.get(interaction.guild.categories, name="Tickets")
        if managementTicket is None and developmentTicket is None and generalTicket is None:
            if self.values[0] == "Management":
                if managementTicket is None:
                    try:
                        ticket = await interaction.guild.create_text_channel(name=f"mgmt-{interaction.user.name.lower()}", category=ticketCategory, overwrites=overwritesManagement)
                        await interaction.response.send_message(f"Hey {interaction.user.mention}, I've created a ticket for you in {managementTicket.mention}", ephemeral=True)
                        await ticket.send(f"<@{interaction.user.id}> please specify below this what your issue is.")
                    except Exception as e:
                        error_channel = self.bot.get_channel(config.error_channel)
                        await error_channel.send(f"<@920797181034778655> Error with Tickets!\n ```{e}```")
                else: await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {managementTicket.mention}", ephemeral=True)
            elif self.values[0] == "Development":
                if developmentTicket is None:
                    await interaction.guild.create_text_channel(name=f"dev-{interaction.user.name.lower()}", category=ticketCategory, overwrites=overwritesDevelopment)
                    await interaction.response.send_message(f"Hey {interaction.user.mention}, I've created a ticket for you in {developmentTicket.mention}", ephemeral=True)
                else: await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {developmentTicket.mention}", ephemeral=True)
            elif self.values[0] == "General":
                if generalTicket is None:
                    await interaction.guild.create_text_channel(name=f"gen-{interaction.user.name.lower()}", category=ticketCategory, overwrites=overwritesGeneral)
                    await interaction.response.send_message(f"Hey {interaction.user.mention}, I've created a ticket for you in {generalTicket.mention}", ephemeral=True)
                else: await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {generalTicket.mention}", ephemeral=True)
        elif managementTicket is not None or developmentTicket is not None or generalTicket is not None:
            try:
                return await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {managementTicket.mention}", ephemeral=True)
            except:
                pass
            try:
                return await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {developmentTicket.mention}", ephemeral=True)
            except:
                pass
            try:
                return await interaction.response.send_message(f"Hey {interaction.user.mention}, you already have a ticket in {generalTicket.mention}", ephemeral=True)
            except:
                pass    
            
class SelectView(discord.ui.View):
    try:
        def __init__(self, *, timeout = 60):
            super().__init__(timeout=timeout)
            self.add_item(SelectMenu())
    except Exception as e:
            print(e)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `tickets.py`")
    
    @app_commands.command(name="ticket", description="Create a ticket")
    async def ticket(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("Select a ticket type.", view=SelectView(), ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
    
    @app_commands.command(name="close", description="Close a ticket")
    @app_commands.checks.has_any_role(management, admin, moderator, staff, developer, tester)
    async def close(self, interaction: discord.Interaction):
        try:
            if interaction.channel.name.startswith("mgmt-") or interaction.channel.name.startswith("dev-") or interaction.channel.name.startswith("gen-"):
                await interaction.response.send_message("Closing the ticket", ephemeral=True)
                try:
                    messages = interaction.channel.history(limit=None)
                    transcript = ""
                    
                    async for message in messages:
                        timestamp = message.created_at.strftime("%m/%d/%Y @ %H:%M:%S")
                        transcript += f"{message.author.name} ({timestamp}): {message.content}\n\n"
                    with open("transcript.txt", "w", encoding="utf-8") as file:
                        file.write(transcript)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
                    await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
                ticketLog = interaction.client.get_channel(config.ticketLog)
                await ticketLog.send(file=discord.File("transcript.txt"), content=f"`{interaction.channel.name}` Ticket closed by {interaction.user.name}")
                await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            else:
                await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot), guilds=[discord.Object(id=config.hockey_discord_server)])