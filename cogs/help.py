import discord
from discord.ext import commands
from discord import app_commands
import config

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
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            if interaction.guild == None:
                await command_log_channel.send(f"`/help` used by `{interaction.user.name}` in DMs at `{datetime.now()}`\n---")
            elif interaction.guild.name == "":
                await command_log_channel.send(f"`/help` used by `{interaction.user.name}` in an unknown server at `{datetime.now()}`\n---")
            else: 
                await command_log_channel.send(f"`/help` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        embed = discord.Embed(title="Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required\n\nHave any questions?\nhttps://discord.gg/W5Jx5QSZCb", color=config.color)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
        embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
        embed.add_field(name="`/guess-the-player`", value="Guess the player!", inline=False)
        embed.add_field(name="`/guess-the-team`", value="Guess the team!", inline=False)
        embed.add_field(name="`/team <abbreviation>`", value="Gets the information of a team!", inline=False)
        embed.add_field(name="`/teams`", value="Gets the all teams in the NHL!", inline=False)
        embed.add_field(name="`/leaderboard`", value="View the leaderboards!", inline=False)
        embed.add_field(name="`/leaderboard-status`", value="Toggles if you want to be displayed on the leaderboard!", inline=False)
        embed.add_field(name="`/my-points`", value="Checks how many points you have!", inline=False)
        #embed.add_field(name="`/standings`", value="Gets the standings of the NHL!", inline=False)
        #embed.add_field(name="`/series`", value="Gets the playoff series!", inline=False)
        embed.add_field(name="`/schedule <abbreviation>`", value="Gets the schedule of a NHL Team!", inline=False)
        #embed.add_field(name="`/game <abbreviation>`", value="Gets the information of a game!", inline=False)
        #embed.add_field(name="`/today`", value="Gets the games of today!", inline=False)
        #embed.add_field(name="`/yesterday`", value="Gets the games of yesterday!", inline=False)
        embed.add_field(name="`/avatar`", value="Gets the avatar of the bot or a user!", inline=False)
        embed.add_field(name="`/info`", value="Shows the info menu!", inline=False)
        embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
        if interaction.guild.id == config.hockey_discord_server:
            embed.add_field(name="`/weather <city> (state) (country)`", value="Gets the weather/tempature of a city!", inline=False)
            embed.add_field(name="`/f-to-c <fahrenheit>`", value="Converts fahrenheit to celsius!", inline=False)
            embed.add_field(name="`/c-to-f <celsius>`", value="Converts celsius to fahrenheit!", inline=False)
        embed.set_footer(text=config.footer)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Help(bot))
