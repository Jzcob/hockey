import discord
from discord.ext import commands
from discord import app_commands
import config
from config import logs
import traceback


class logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `logs.py`")
        
### MESSAGE LOGS ###
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        channel = self.bot.get_channel(1168944556927103067)
        if message.guild.id == config.hockey_discord_server:
            if message.author.bot:
                return
            else:
                try:
                    embed = discord.Embed(color=config.color)
                    embed.set_author(name=message.author, icon_url=message.author.avatar.url)
                    embed.add_field(name=f"Message Deleted in <#{message.channel.id}>", value=message.content)
                    embed.set_footer(text=f"ID: {message.author.id}")
                    return await channel.send(embed=embed)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
        else:
            return
    
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if messages.guild.id == config.hockey_discord_server:
            channel = self.bot.get_channel(1168944556927103067)
            if messages.author.bot:
                return
            else:
                try:
                    embed = discord.Embed(color=config.color)
                    embed.add_field(name=f'Messaged Deleted', value=len(messages))
                    return await channel.send(embed=embed)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
        else:
            return
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild.id == config.hockey_discord_server:
            if before.author.bot:
                return
            else:
                try:
                    embed = discord.Embed(title=f'Messaged edited in #{before.channel.name}',color=config.color, description=f"**Before:** {before.content}\n**+After:** {after.content}")
                    embed.set_author(name=before.author, icon_url=before.author.avatar)
                    embed.set_footer(text=f"ID: {before.author.id}")
                    channel = self.bot.get_channel(1168944556927103067)
                    await channel.send(embed=embed)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
        else:
            return

### MEMBER LOGS ###
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.guild.id == config.hockey_discord_server:
            if before.bot:
                return
            else:
                try:
                    channel = self.bot.get_channel(1168944556927103067)
                    if before.nick != after.nick:
                        embed = discord.Embed(title=f"Nickname Changed", color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.add_field(name="Before", value=before.nick, inline=False)
                        embed.add_field(name="After", value=after.nick, inline=False)
                        await channel.send(embed=embed)
                    elif len(before.roles) < len(after.roles):
                        newRole = next(role for role in after.roles if role not in before.roles)
                        embed = discord.Embed(title=f"Role Added",description=newRole.mention, color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.set_footer(text=f"ID: {before.id}")
                        await channel.send(embed=embed)
                    elif len(before.roles) > len(after.roles):
                        oldRole = next(role for role in before.roles if role not in after.roles)
                        embed = discord.Embed(title=f"Role Removed",description=oldRole.mention, color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.set_footer(text=f"ID: {before.id}")
                        await channel.send(embed=embed)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
        else:
            return
    
    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if before.guild.id == config.hockey_discord_server:
            channel = self.bot.get_channel(1168944556927103067)
            if before.bot:
                return
            else:
                try:
                    if before.name != after.name:
                        embed = discord.Embed(title=f"Username Changed", color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.add_field(name="Before", value=before.name, inline=False)
                        embed.add_field(name="After", value=after.name, inline=False)
                        return await channel.send(embed=embed)
                    elif before.discriminator != after.discriminator:
                        embed = discord.Embed(title=f"Discriminator Changed", color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.add_field(name="Before", value=before.discriminator, inline=False)
                        embed.add_field(name="After", value=after.discriminator, inline=False)
                        return await channel.send(embed=embed)
                    elif before.avatar != after.avatar:
                        embed = discord.Embed(title=f"Avatar Changed", color=config.color)
                        embed.set_author(name=before, icon_url=before.avatar.url)
                        embed.set_thumbnail(url=after.avatar_url)
                        return await channel.send(embed=embed)
                except:
                    error_channel = self.bot.get_channel(config.error_channel)
                    string = f"{traceback.format_exc()}"
                    await error_channel.send(f"```{string}```")
        else:
            return

async def setup(bot):
    await bot.add_cog(logs(bot))