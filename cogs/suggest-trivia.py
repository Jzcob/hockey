import re
import discord
from discord.ext import commands
from discord import app_commands
import config
from datetime import datetime
import traceback

class SuggestTrivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `suggest-trivia.py`")
    
    @app_commands.command(name="suggest-trivia", description="Suggest a trivia question!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def suggest_trivia(self, interaction: discord.Interaction, question: str, answer: str):
        banned_users = ['gamernum21', 'jace0920']
        if interaction.user.name in banned_users:
            await interaction.response.send_message("You have been blacklisted from using this command due to inappropriate behavior.", ephemeral=True)
            return
        BLACKLIST_REGEX = re.compile(
            r'\b(f[a@4]g{1,2}(s|ot)?|n[i!1]g{2,}[e3a@4]r(s|z)?|c[u*]nt|wh[o0]re|tr[a@]nny|r[e3]t[a@]rd|kys|kill\s*your\s*self)\b',
            re.IGNORECASE
        )
        if BLACKLIST_REGEX.search(question) or BLACKLIST_REGEX.search(answer):
            await interaction.response.send_message("Your suggestion contains inappropriate content.", ephemeral=True)
            return
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(
                    f"`/suggest-trivia` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                )
            except Exception as e:
                print(f"Logging failed: {e}")
        try:
            suggestion_channel = self.bot.get_channel(config.suggestion_channel)
            embed = discord.Embed(
                title="Trivia Suggestion",
                description=(
                    f"**Question:** {question}\n"
                    f"**Answer:** {answer}\n"
                    f"**Suggested by:** {interaction.user.name}\n"
                    f"**Suggested at:** {datetime.now()}"
                ),
                color=config.color
            )
            await suggestion_channel.send(embed=embed)
            await interaction.response.send_message("Your suggestion has been sent to the Bot Developerl!")
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")

async def setup(bot):
    await bot.add_cog(SuggestTrivia(bot))