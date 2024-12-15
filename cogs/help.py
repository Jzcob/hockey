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
    async def help(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(
                    f"`/help` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
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
            embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
            embed.add_field(name="`/guess-the-player`", value="Guess the player!", inline=False)
            embed.add_field(name="`/guess-the-team`", value="Guess the team!", inline=False)
            embed.add_field(name="`/team <abbreviation>`", value="Gets the information of a team!", inline=False)
            embed.add_field(name="`/teams`", value="Lists all NHL teams!", inline=False)
            embed.add_field(name="`/leaderboard`", value="View the leaderboards!", inline=False)
            embed.add_field(name="`/leaderboard-status`", value="Toggle your visibility on the leaderboard!", inline=False)
            embed.add_field(name="`/my-points`", value="Check how many points you have!", inline=False)
            embed.add_field(name="`/standings`", value="Get the NHL standings!", inline=False)
            embed.add_field(name="`/schedule <abbreviation>`", value="Get the schedule of an NHL team!", inline=False)
            embed.add_field(name="`/game <abbreviation>`", value="Get information about a game!", inline=False)
            embed.add_field(name="`/today`", value="List today's games!", inline=False)
            embed.add_field(name="`/tomorrow`", value="List tomorrow's games!", inline=False)
            embed.add_field(name="`/yesterday`", value="List yesterday's games!", inline=False)
            embed.add_field(name="`/avatar`", value="Get the avatar of the bot or a user!", inline=False)
            embed.add_field(name="`/info`", value="Show the info menu!", inline=False)
            embed.add_field(name="`/help`", value="Show this help menu!", inline=False)

            if interaction.guild and interaction.guild.id == config.hockey_discord_server:
                embed.add_field(name="`/weather <city> (state) (country)`", value="Get the weather of a city!", inline=False)
                embed.add_field(name="`/f-to-c <fahrenheit>`", value="Convert Fahrenheit to Celsius!", inline=False)
                embed.add_field(name="`/c-to-f <celsius>`", value="Convert Celsius to Fahrenheit!", inline=False)

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
