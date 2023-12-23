import discord
from discord.ext import commands
from discord import app_commands
import requests
import config
#import topgg

class vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `vote.py`")
    
    @app_commands.command(name="vote", description="Vote for the bot!")
    async def vote(self, interaction: discord.Interaction):
        link = "https://top.gg/bot/1156302042969677845/vote"
        embed = discord.Embed(title="Vote for the bot!", description=f"Vote for the bot [here]({link})!", color=config.color)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1156254139966292099/1156254690573557920/61487dbbd329bb0004dbd335.png?ex=65144d98&is=6512fc18&hm=a2d4ae15d46d52bdf2e15ee6feea5042323d96b706ba03586b477b262f7af48b&")
        embed.set_author(icon_url=interaction.user.avatar.url, name="NHL Bot Vote")
        embed.set_footer(text=config.footer)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    """@commands.Cog.Listener()
    async def on_dbl_vote(self, data):
        user = self.bot.get_user(data["user"])
        voterChannel = self.bot.get_channel(1187613219796291684)
        await voterChannel.send(f"`{user.name}` has voted for the bot!")
        await user.send(f"Thanks for voting for the bot! You can vote again in 12 hours [here](https://top.gg/bot/1156302042969677845/vote)!")
    
    @commands.Cog.Listener()
    async def on_dbl_test(self, data):
        user = self.bot.get_user(data["user"])
        voterChannel = self.bot.get_channel(1187613219796291684)
        await voterChannel.send(f"`{user.name}` has voted for the bot!")
        await user.send(f"Received a test upvote from {data['user']}")"""

async def setup(bot):
    await bot.add_cog(vote(bot))