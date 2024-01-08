### This is a private Cog for the Hockey Bot and is not for public use. ###
# Purpose: Create tickets for users to ask questions in.
# No other server can use this Cog, other than the Hockey Bot server.


import discord
from discord import app_commands, utils
from discord.ext import commands
import config

#### Roles ####
management = 1165854746863751168
admin =1165854745177640990
moderator = 1165854748604383243
staff = 1165854744577855509
developer = 1170802776859750421
tester = 1171967165843386519

class SelectMenu(discord.ui.Select):
    def __init__(self):
        print("1")
        menu = [
            discord.SelectOption(label="Management", description="Management related questions"),
            discord.SelectOption(label="Development", description="Development related questions"),
            discord.SelectOption(label="General", description="General questions")
        ]
        print("2")
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=menu)
        print("3")
    
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
        if self.values[0] == "Management":
            if managementTicket is None:
                await interaction.guild.create_text_channel(name=f"mgmt-{interaction.user.name.lower()}", category=ticketCategory, overwrites=overwritesManagement)
                await interaction.response.send_message(f"Hey {interaction.user.mention}, I've created a ticket for you in {managementTicket.mention}", ephemeral=True)
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
    @app_commands.checks.has_any_role(management)
    async def ticket(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("Select a ticket type.", view=SelectView(), ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error with Tickets!\n ```{e}```")
            return await interaction.response.send_message("Error creating ticket! Message has been sent to Jacob", ephemeral=True)
    
    @app_commands.command(name="close", description="Close a ticket")
    @app_commands.checks.has_any_role(management, admin, moderator, staff, developer, tester)
    async def close(self, interaction: discord.Interaction):
        try:
            if interaction.channel.name.startswith("mgmt-") or interaction.channel.name.startswith("dev-") or interaction.channel.name.startswith("gen-"):
                try:
                    messages = await interaction.channel.history(limit=1).flatten()
                    transcript = ""
                    for message in messages:
                        timestamp = message.created_at.strftime("%m/%d/%Y @ %H:%M:%S")
                        transcript += f"{message.author.name} ({timestamp}): {message.content}\n\n"
                    with open(f"transcript.txt", "w") as f:
                        f.write(transcript)
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"<@920797181034778655> Error with Tickets!\n ```{e}```")
                    return await interaction.response.send_message("Error getting transcript! Message has been sent to Jacob", ephemeral=True)
                ticketLog = self.bot.get_channel(config.ticket_log)
                await interaction.response.send_message("Ticket closed!", ephemeral=True)
                await ticketLog.send(file=discord.File("transcript.txt"), content=f"Ticket `{interaction.channel.name}` closed by `{interaction.user.name}`.") 
                await interaction.channel.delete()
            else:
                await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655> Error with Tickets!\n ```{e}```")
            return await interaction.response.send_message("Error closing ticket! Message has been sent to Jacob", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot), guilds=[discord.Object(id=config.hockey_discord_server)])