import discord
from discord.ext import commands
from discord import app_commands
import config
from datetime import datetime
import traceback


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `help.py`")
    
    @app_commands.command(name="help", description="Shows the help menu!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.choices(menu=[
        app_commands.Choice(name="general", value="general"),
        app_commands.Choice(name="nhl", value="nhl"),
        app_commands.Choice(name="games", value="games"),
        app_commands.Choice(name="hockey-bot-league", value="hockey-bot-league")
    ])
    async def help(self, interaction: discord.Interaction, menu: app_commands.Choice[str]):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(
                    f"`/help {menu.value}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                )
            except Exception as e:
                print(f"Logging failed: {e}")

        try:
            embed = discord.Embed(
                title="Help Menu",
                description=(
                    "Here are the commands you can use with this bot!\n\n"
                    "<> = Required\n() = Optional\n\n"
                    "Have any questions?\nhttps://discord.gg/W5Jx5QSZCb"
                ),
                color=config.color
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png")
            
            if menu.value == "general":
                embed.add_field(name="`/help <menu>`", value="Shows the help menu's!", inline=False)
                embed.add_field(name="`/info`", value="Shows the info menu!", inline=False)
                embed.add_field(name="`/avatar`", value="Get the avatar of the bot or a user!", inline=False)
                if interaction.guild and interaction.guild.id == config.hockey_discord_server:
                    embed.add_field(name="`/weather <city> (state) (country)`", value="Get the weather of a city!", inline=False)
                    embed.add_field(name="`/f-to-c <fahrenheit>`", value="Convert Fahrenheit to Celsius!", inline=False)
                    embed.add_field(name="`/c-to-f <celsius>`", value="Convert Celsius to Fahrenheit!", inline=False)
            
            elif menu.value == "nhl":
                #embed.add_field(name="`/bracket`", value="Get the NHL Playoff bracket!", inline=False)
                embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
                embed.add_field(name="`/team <abbreviation>`", value="Gets the information of a team!", inline=False)
                embed.add_field(name="`/teams`", value="Lists all NHL teams!", inline=False)
                embed.add_field(name="`/standings`", value="Get the NHL standings!", inline=False)
                embed.add_field(name="`/schedule <abbreviation>`", value="Get the schedule of an NHL team!", inline=False)
                embed.add_field(name="`/game <abbreviation>`", value="Get information about a game!", inline=False)
                embed.add_field(name="`/today`", value="List today's games!", inline=False)
                embed.add_field(name="`/tomorrow`", value="List tomorrow's games!", inline=False)
                embed.add_field(name="`/yesterday`", value="List yesterday's games!", inline=False)
            
            elif menu.value == "games":
                embed.add_field(name="`/guess-the-player`", value="Guess a random NHL player!", inline=False)
                embed.add_field(name="`/trivia`", value="Answer trivia questions to earn points!", inline=False)
                embed.add_field(name="`/leaderboard <subcommand>`", value="View leaderboards (`trivia`, `gtp`, `fantasy`) or manage your visibility (`trivia-status`, `gtp-status`).", inline=False)
                embed.add_field(name="`/mypoints <subcommand>`", value="Check your points for a specific game (`trivia`, `gtp`, `fantasy`).", inline=False)
                embed.add_field(name="`/suggest-trivia <question> <answer>`", value="Suggest a trivia question!", inline=False)

            elif menu.value == "hockey-bot-league":
                #embed.add_field(name="`/join-league` ACTIVE UNTIL OCTOBER 7th", value="Start here! A two-step process to pick your 5 active and 3 bench teams.", inline=False)
                embed.add_field(name="`/my-roster`", value="View your current team selections, total points, and remaining swaps.", inline=False)
                embed.add_field(name="`/swap-teams`", value="Use one of your 10 seasonal swaps.", inline=False)
                embed.add_field(name="`/ace-team`", value="Choose your weekly x3 points multiplier team.", inline=False)
                embed.add_field(name="`/leaderboard fantasy`", value="See how you stack up against the competition!", inline=False)
                embed.add_field(name="`/mypoints fantasy`", value="Check your current point total in the fantasy league.", inline=False)


            embed.set_footer(text=config.footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message(
                "An error occurred while displaying the help menu. The issue has been reported.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Help(bot))
