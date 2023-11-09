import discord
from discord.ext import commands
from discord import app_commands
import requests
import config

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `help.py`")
    
    @app_commands.command(name="help", description="Shows the help menu!")
    async def help(self, interaction: discord.Interaction):
        if interaction.guild.id != 1156254139966292096:
            try:
                embed = discord.Embed(title="Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
                embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
                embed.add_field(name="`/guess-the-player`", value="Guess the player!", inline=False)
                embed.add_field(name="`/guess-the-team`", value="Guess the team!", inline=False)
                embed.add_field(name="`/team <name>`", value="Gets the information of a team!", inline=False)
                embed.add_field(name="`/standings (team)`", value="Gets the standings of the NHL!", inline=False)
                embed.add_field(name="`/schedule <length> <team>`", value="Gets the schedule of the NHL!", inline=False)
                embed.add_field(name="`/game <team>`", value="Gets the information of a game!", inline=False)
                embed.add_field(name="`/today (team)`", value="Gets the games of today!", inline=False)
                embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
                embed.set_footer(text="Made by @jzcob")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                embed = discord.Embed(title="Error with `/help`", description=f"```{e}```", color=config.color)
                embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
                embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
                embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
                await error_channel.send(embed=embed)
        else:
            #TEMPORARY
            try:
                embed = discord.Embed(title="Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
                embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
                embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
                embed.add_field(name="`/guess-the-player`", value="Guess the player!", inline=False)
                embed.add_field(name="`/guess-the-team`", value="Guess the team!", inline=False)
                embed.add_field(name="`/team <name>`", value="Gets the information of a team!", inline=False)
                embed.add_field(name="`/standings (team)`", value="Gets the standings of the NHL!", inline=False)
                embed.add_field(name="`/schedule <length> <team>`", value="Gets the schedule of the NHL!", inline=False)
                embed.add_field(name="`/game <team>`", value="Gets the information of a game!", inline=False)
                embed.add_field(name="`/today (team)`", value="Gets the games of today!", inline=False)
                embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
                embed.set_footer(text="Made by @jzcob")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                embed = discord.Embed(title="Error with `/help`", description=f"```{e}```", color=config.color)
                embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
                embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
                embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
                await error_channel.send(embed=embed)
    
    @app_commands.command(name="staff-help", description="Shows the help menu!")
    @app_commands.checks.has_any_role("Staff")
    @app_commands.choices(role=[
        app_commands.OptionChoice(name="Helper", value="helper"),
        app_commands.OptionChoice(name="Moderator", value="moderator"),
        app_commands.OptionChoice(name="Administrator", value="administrator"),
        app_commands.OptionChoice(name="Manager", value="manager")
    ], description="The role you want to see the help menu for!")
    async def staffHelp(self, interaction: discord.Interaction, role: discord.app_commands.Choice[str]):
        try:
            member = interaction.user
            def is_helper(member):
                return discord.utils.get(member.roles, name="Helper") is not None
            def is_moderator(member):
                return discord.utils.get(member.roles, name="Moderator") is not None
            def is_administrator(member):
                return discord.utils.get(member.roles, name="Administrator") is not None
            def is_manager(member):
                return discord.utils.get(member.roles, name="Manager") is not None
            def is_owner(member):
                return discord.utils.get(member.roles, name="Server Owner") is not None
            if role.value == "helper":
                if is_helper(member) or is_manager(member) or is_owner(member):
                    embed = discord.Embed(title="Helper Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                    embed.add_field(name="`/staff-help helper`", value="Shows this help menu!", inline=False)
                    embed.add_field(name="`/warn <member> <reason> <evidence>`", value="Warns a member of the discord server.", inline=False)
                    embed.add_field(name="`/punishments <member>`", value="Shows the punishments of a member.", inline=False)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("You are not a helper!", ephemeral=True)
                
            elif role.value == "moderator":
                if is_moderator(member) or is_manager(member) or is_owner(member):
                    embed = discord.Embed(title="Moderator Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                    embed.add_field(name="`/staff-help moderator`", value="Shows this help menu!", inline=False)
                    embed.add_field(name="`/warn <member> <reason> <evidence>`", value="Warns a member of the discord server.", inline=False)
                    embed.add_field(name="`/timeout <member> <duration> <reason> <evidence>`", value="Timeouts a member of the discord server.", inline=False)
                    embed.add_field(name="`/ban <member> <reason> <evidence>`", value="Bans a member of the discord server.", inline=False)
                    embed.add_field(name="`/set-note <member> <note>`", value="Sets a note for a member of the discord server.", inline=False)
                    embed.add_field(name="`/purge <amount> (member)`", value="Purges a certain amount of messages.", inline=False)
                    embed.add_field(name="`/punishments <member>`", value="Shows the punishments of a member.", inline=False)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("You are not a moderator!", ephemeral=True)
            elif role.value == "administrator":
                if is_administrator(member) or is_manager(member) or is_owner(member):
                    embed = discord.Embed(title="Administrator Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                    embed.add_field(name="`/staff-help administrator`", value="Shows this help menu!", inline=False)
                    embed.add_field(name="`/warn <member> <reason> <evidence>`", value="Warns a member of the discord server.", inline=False)
                    embed.add_field(name="`/timeout <member> <duration> <reason> <evidence>`", value="Timeouts a member of the discord server.", inline=False)
                    embed.add_field(name="`/ban <member> <reason> <evidence>`", value="Bans a member of the discord server.", inline=False)
                    embed.add_field(name="`/set-note <member> <note>`", value="Sets a note for a member of the discord server.", inline=False)
                    embed.add_field(name="`/remove-note <member> <note number>`", value="Removes a note for a member of the discord server.", inline=False)
                    embed.add_field(name="`/cancel-timeout <member>`", value="Cancels a timeout for a member of the discord server.", inline=False)
                    embed.add_field(name="`/remove-warn <member> <warning number>`", value="Removes a warning for a member of the discord server.", inline=False)
                    embed.add_field(name="`/remove-timeout <member> <timeout number>`", value="Removes a timeout for a member of the discord server.", inline=False)
                    embed.add_field(name="`/remove-ban <member> <ban number>`", value="Removes a ban for a member of the discord server.", inline=False)
                    embed.add_field(name="`/fix-punishment <member> <type> <punishment> <reason>", description="Fixes a punishment for a member of the discord server.", inline=False)
                    embed.add_field(name="`/purge <amount> (member)`", value="Purges a certain amount of messages.", inline=False)
                    embed.add_field(name="`/punishments <member>`", value="Shows the punishments of a member.", inline=False)
                    embed.add_field(name="`/set-warns <member> <amount>`", value="Sets the amount of warns for a member.", inline=False)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("You are not an administrator!", ephemeral=True)
            elif role.value == "manager":
                if is_manager(member) or is_owner(member):
                    embed=discord.Embed(title="Manager Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required", color=config.color)
                    embed.add_field(name="`/staff-help manager`", value="Shows this help menu!", inline=False)
                    embed.add_field(name="Use `/staff-help administrator`", value="You get the same commands :)", inline=False)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("You are not a manager!", ephemeral=True)
            else:
                await interaction.response.send_message("Role not found!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/help`", description=f"```{e}```", color=config.color)
            embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
            embed.add_field(name="Channel", value=f"{interaction.channel.name}", inline=False)
            await interaction.response.send_message("Error with `/help`! Message has been sent to Jacob, but feel free to ping him in <#1168943619886035066> I give you permission. :)\n Tell him to look at #bot-errors", ephemeral=True)
            await error_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
