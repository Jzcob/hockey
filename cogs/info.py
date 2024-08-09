import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `info.py`")
    
    @app_commands.command(name="info", description="Shows the info menu!")
    async def info(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            from datetime import datetime
            await command_log_channel.send(f"`/info` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}`\n---")
        embed = discord.Embed(title="Info Menu", description="Here is the info for this bot!\nAll updates to the bot except for important changes are sent in my discord server.", color=0x00ff00)
        embed.add_field(name="My Privacy Policy", value="https://github.com/Jzcob/hockey/blob/main/SECURITY.md", inline=False)
        embed.add_field(name="My Terms of Service", value="https://github.com/Jzcob/hockey/wiki/Terms-of-Service-for-Hockey-Bot", inline=False)
        embed.add_field(name="NHL Privacy Policy", value="https://www.nhl.com/info/privacy-policy", inline=False)
        embed.add_field(name="NHL Terms of Service", value="https://www.nhl.com/info/terms-of-service", inline=False)
        embed.add_field(name="NHL API", value="https://gitlab.com/dword4/nhlapi/-/blob/master/new-api.md?ref_type=heads", inline=False)
        if interaction.guild.id == config.hockey_discord_server:
            embed.add_field(name="OpenWeather Privacy Policy", value="https://openweathermap.org/privacy-policy", inline=False)
            embed.add_field(name="OpenWeather Terms of Service", value="https://openweathermap.org/terms", inline=False)
        embed.add_field(name="Discord Privacy Policy", value="https://discord.com/privacy", inline=False)
        embed.add_field(name="Discord Terms of Service", value="https://discord.com/terms", inline=False)
        embed.add_field(name="My GitHub", value="https://github.com/Jzcob/hockey", inline=False)
        embed.add_field(name="My Discord", value="https://discord.gg/W5Jx5QSZCb", inline=False)
        embed.add_field(name="My Patreon", value="https://www.patreon.com/jzcob", inline=False)
        embed.set_footer(text=config.footer)
        await interaction.response.send_message(embed=embed, ephemeral=True)
async def setup(bot):
    await bot.add_cog(Info(bot))