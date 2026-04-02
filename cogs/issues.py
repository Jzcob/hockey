import discord
from discord import app_commands, ui
from discord.ext import commands
import config
from datetime import datetime
import traceback

class IssueModal(ui.Modal, title='Report an Issue'):
    issue_title = ui.TextInput(
        label='Issue Title',
        placeholder='Give a brief title for the issue...',
        required=True,
        max_length=100
    )
    
    issue_description = ui.TextInput(
        label='Description',
        style=discord.TextStyle.paragraph,
        placeholder='Describe the issue in detail, including steps to reproduce if possible...',
        required=True,
        max_length=1000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            error_channel = self.bot.get_channel(config.error_channel)
            
            embed = discord.Embed(
                title="New Issue Reported",
                description=(
                    f"**Title:** {self.issue_title.value}\n"
                    f"**Details:** {self.issue_description.value}\n\n"
                    f"**Reported by:** {interaction.user.name} ({interaction.user.id})\n"
                    f"**Reported at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                color=config.color
            )
            embed.set_footer(text=f"User ID: {interaction.user.id}")
            
            if error_channel:
                await error_channel.send(embed=embed)
                await interaction.response.send_message("✅ Your issue has been reported to the developers! Thanks for helping improve the bot.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Error channel not found. Please contact an admin.", ephemeral=True)

        except Exception:
            if error_channel:
                await error_channel.send(f"<@920797181034778655> Error in Issue Modal:\n```{traceback.format_exc()}```")
            await interaction.response.send_message("An error occurred while reporting your issue.", ephemeral=True)

class Issues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="report", description="Report an issue with the bot to the developers.")
    async def report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(IssueModal(self.bot))
async def setup(bot):
    await bot.add_cog(Issues(bot))