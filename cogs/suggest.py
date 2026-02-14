import discord
from discord import app_commands, ui
from discord.ext import commands
import config
from datetime import datetime
import traceback

# This is the pop-up window (Modal)
class SuggestionModal(ui.Modal, title='Bot Suggestion'):
    # Input fields
    suggestion_title = ui.TextInput(
        label='Suggestion Title',
        placeholder='Give your idea a short name...',
        required=True,
        max_length=100
    )
    
    suggestion_description = ui.TextInput(
        label='Description',
        style=discord.TextStyle.paragraph,
        placeholder='Describe the feature or change in detail...',
        required=True,
        max_length=1000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            suggestion_channel = self.bot.get_channel(config.suggestion_channel)
            
            embed = discord.Embed(
                title="New Bot Suggestion",
                description=(
                    f"**Title:** {self.suggestion_title.value}\n"
                    f"**Details:** {self.suggestion_description.value}\n\n"
                    f"**Suggested by:** {interaction.user.name} ({interaction.user.id})\n"
                    f"**Suggested at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                color=config.color
            )
            embed.set_footer(text=f"User ID: {interaction.user.id}")
            
            if suggestion_channel:
                await suggestion_channel.send(embed=embed)
                await interaction.response.send_message("✅ Your suggestion has been sent to the developers! Thanks for helping out.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Suggestion channel not found. Please contact an admin.", ephemeral=True)

        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel:
                await error_channel.send(f"<@920797181034778655> Error in Suggestion Modal:\n```{traceback.format_exc()}```")
            await interaction.response.send_message("An error occurred while sending your suggestion.", ephemeral=True)

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `suggest.py`")
    
    @app_commands.command(name="suggest", description="Suggest a new feature or improvement for the bot!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def suggest(self, interaction: discord.Interaction):
        # Log the command usage
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                if command_log_channel:
                    await command_log_channel.send(
                        f"`/suggest` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---"
                    )
            except Exception as e:
                print(f"Logging failed: {e}")

        # Send the Modal to the user
        await interaction.response.send_modal(SuggestionModal(self.bot))

async def setup(bot):
    await bot.add_cog(Suggest(bot))