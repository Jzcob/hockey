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
        app_commands.Choice(name="pwhl", value="pwhl"),
        app_commands.Choice(name="games", value="games"),
        app_commands.Choice(name="hockey-bot-league", value="hockey-bot-league"),
        app_commands.Choice(name="moderation", value="moderation")
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
                    "Have any questions?\nhttps://discord.gg/WGQYdzvn8y"
                ),
                color=config.color
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png")
            
            if menu.value == "general":
                embed.add_field(name="`/help <menu>`", value="Shows the help menu's!", inline=False)
                embed.add_field(name="`/info`", value="Shows the info menu!", inline=False)
                embed.add_field(name="`/avatar`", value="Get the avatar of the bot or a user!", inline=False)
                embed.add_field(name="`/suggest`", value="Suggest a new feature or improvement for the bot!", inline=False)
            elif menu.value == "nhl":
                embed.add_field(name="`/today [league] [date]`", value="Get today's schedule and scores (supports NHL & PWHL)!", inline=False)
                embed.add_field(name="`/yesterday [league]`", value="Get yesterday's scores!", inline=False)
                embed.add_field(name="`/player <league> <name>`", value="Gets the information of a player!", inline=False)
                embed.add_field(name="`/team <league> <abbreviation>`", value="Gets the information of a team!", inline=False)
                embed.add_field(name="`/teams <league>`", value="Lists all team codes and abbreviations!", inline=False)
                embed.add_field(name="`/standings <league> [date]`", value="Get the league standings!", inline=False)
                embed.add_field(name="`/schedule <league> <abbreviation> [date]`", value="Get the schedule of a team!", inline=False)
                embed.add_field(name="`/game <league> <abbreviation> [date]`", value="Get information about a game!", inline=False)
            elif menu.value == "pwhl":
                embed.add_field(name="`/today league:PWHL`", value="Get today's PWHL schedule and scores!", inline=False)
                embed.add_field(name="`/yesterday league:PWHL`", value="Get yesterday's PWHL scores!", inline=False)
                embed.add_field(name="`/standings league:PWHL`", value="Get PWHL league standings!", inline=False)
                embed.add_field(name="`/schedule league:PWHL <abbreviation>`", value="Get the schedule for a PWHL team!", inline=False)
                embed.add_field(name="`/game league:PWHL <abbreviation>`", value="Get live or past game stats for a PWHL team!", inline=False)
                embed.add_field(name="`/teams league:PWHL`", value="Get all PWHL team codes and abbreviations!", inline=False)
            elif menu.value == "games":
                embed.add_field(name="`/guess-the-player`", value="Guess a random NHL player!", inline=False)
                embed.add_field(name="`/guess-the-team`", value="Guess a random NHL team from scrambled letters!", inline=False)
                embed.add_field(name="`/gtp-race`", value="Compete to guess a player the fastest against your server members!", inline=False)
                embed.add_field(name="`/trivia`", value="Answer trivia questions to earn points!", inline=False)
                embed.add_field(name="`/leaderboard <subcommand>`", value="View leaderboards (`trivia`, `gtp`, `fantasy`, `fantasy-history`) or manage your visibility (`trivia-status`, `gtp-status`).", inline=False)
                embed.add_field(name="`/mypoints <subcommand>`", value="Check your points for a specific game (`trivia`, `gtp`, `fantasy`).", inline=False)
                embed.add_field(name="`/suggest-trivia <question> <answer>`", value="Suggest a trivia question!", inline=False)
            elif menu.value == "hockey-bot-league":
                embed.add_field(name="`/join fantasy` ACTIVE UNTIL SEPTEMBER 29TH", value="Join the fantasy league!", inline=False)
                embed.add_field(name="`/my-roster`", value="View your current team selections, total points, and remaining swaps.", inline=False)
                embed.add_field(name="`/swap-teams`", value="Use one of your 10 seasonal swaps via interactive dropdowns.", inline=False)
                embed.add_field(name="`/ace-team`", value="Choose your weekly x3 points multiplier team.", inline=False)
                embed.add_field(name="`/leaderboard fantasy`", value="See how you stack up against the competition!", inline=False)
                embed.add_field(name="`/leaderboard fantasy-history`", value="View past fantasy league history standings.", inline=False)
                embed.add_field(name="`/mypoints fantasy`", value="Check your current point total in the fantasy league.", inline=False)
            elif menu.value == "moderation":
                embed.description = (
                    "Here are the moderation commands you can use with this bot!\n\n"
                    "<> = Required\n() = Optional\n\n"
                    "Have any questions?\nhttps://discord.gg/WGQYdzvn8y"
                )
                embed.add_field(name="`/warn <member> <reason>`", value="Warn a member of the server. *Requires `Moderate Members` permission*", inline=False)
                embed.add_field(name="`/timeout <member> <duration> <reason>`", value="Timeout a member of the server. *Requires `Moderate Members` permission*", inline=False)
                embed.add_field(name="`/kick <member> <reason>`", value="Kick a member from the server. *Requires `Kick Members` permission*", inline=False)
                embed.add_field(name="`/ban <member> <reason>`", value="Ban a member from the server. *Requires `Ban Members` permission*", inline=False)
                embed.add_field(name="`/punishments <member>`", value="View a member's history. (90-day limit for Free tier)", inline=False)
                embed.add_field(name="`/set-logs <channel>`", value="Set the logging channel for server moderation actions. *Requires `Administrator` permission*", inline=False)
                embed.add_field(name="`/add-note <member> <note>`", value="💎 **Premium:** Add a staff-only note to a user.", inline=False)
                embed.add_field(name="`/remove-note <note_id>`", value="💎 **Premium:** Remove a staff-only note by its ID.", inline=False)
                embed.add_field(name="`/view-notes <member>`", value="💎 **Premium:** View staff-only notes on a user.", inline=False)
                embed.add_field(name="`/export-history (member)`", value="💎 **Premium:** Download full punishment history to a CSV file.", inline=False)
                embed.set_footer(text="Upgrade to Premium for permanent data storage and notes!")

            if menu.value != "moderation":
                embed.set_footer(text=config.footer)
                
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel:
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message(
                "An error occurred while displaying the help menu. The issue has been reported.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Help(bot))