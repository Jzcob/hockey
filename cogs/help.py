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
        try:
            embed = discord.Embed(title="Help Menu", description="Here are the commands you can use with this bot!\n\n<> = Required\n() = Not Required\n\nHave any questions?\nhttps://discord.gg/H6ePukhwJZ", color=config.color)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
            embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
            #embed.add_field(name="`/player <name>`", value="Gets the information of a player!", inline=False)
            #embed.add_field(name="`/guess-the-player`", value="Guess the player!", inline=False)
            embed.add_field(name="`/guess-the-team`", value="Guess the team!", inline=False)
            embed.add_field(name="`/team <name>`", value="Gets the information of a team!", inline=False)
            embed.add_field(name="`/teams`", value="Gets the all teams in the NHL!", inline=False)
            embed.add_field(name="`/standings`", value="Gets the standings of the NHL!", inline=False)
            embed.add_field(name="`/schedule <abbreviation>`", value="Gets the schedule of a NHL Team!", inline=False)
            embed.add_field(name="`/game <abbreviation>`", value="Gets the information of a game!", inline=False)
            embed.add_field(name="`/today`", value="Gets the games of today!", inline=False)
            embed.add_field(name="`/vote`", value="Vote for the bot!", inline=False)
            embed.add_field(name="`/info`", value="Shows the info menu!", inline=False)
            embed.add_field(name="`/help`", value="Shows this help menu!", inline=False)
            embed.set_footer(text=config.footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            embed = discord.Embed(title="Error with `/help`", description=f"```{e}```", color=config.color)
            embed.add_field(name="User", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="Server", value=f"{interaction.guild.name}", inline=False)
            await error_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
