import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback
import json
from datetime import datetime

class teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `teams.py`")

    # Helper function to handle command logging consistently
    async def _log_command(self, interaction: discord.Interaction):
        if not config.command_log_bool:
            return
        
        try:
            log_channel = self.bot.get_channel(config.command_log)
            if not log_channel:
                return

            location = "DMs"
            if interaction.guild:
                location = f"`{interaction.guild.name}`"

            await log_channel.send(f"`/{interaction.command.name}` used by `{interaction.user.name}` in {location} at `{datetime.now()}`\n---")
        except Exception as e:
            print(f"Command logging failed for /{interaction.command.name}: {e}")

    @app_commands.command(name="teams", description="Get the teams in the league!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def teams(self, interaction: discord.Interaction):
        await self._log_command(interaction)
        await interaction.response.defer(ephemeral=True)

        try:
            # A dictionary to manually correct any mismatches between JSON names and config variable names.
            name_corrections = {
                "Anaheim Ducks": "anahiem_ducks_emoji", # Corrects for the "anahiem" typo
            }

            with open("teams.json", "r", encoding="utf-8") as f:
                teams_data = json.load(f)

            description_lines = []
            for abbr, name in teams_data.items():
                if name in name_corrections:
                    emoji_attr_name = name_corrections[name]
                else:
                    emoji_attr_name = f"{name.lower().replace(' ', '_').replace('.', '')}_emoji"
                
                emoji = getattr(config, emoji_attr_name, "")
                description_lines.append(f"**{abbr}** - {name} {emoji}")

            embed = discord.Embed(
                title="League Teams",
                description="Here are all the teams in the league!\n\n" + "\n".join(description_lines),
                color=discord.Color.green()
            )
            embed.set_footer(text=config.footer)
            
            await interaction.followup.send(embed=embed, ephemeral=True)

        except FileNotFoundError:
            await interaction.followup.send("❌ `teams.json` file not found. Please contact an admin.", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel:
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            
            if not interaction.is_expired():
                await interaction.followup.send("❌ An error occurred. The issue has been reported.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(teams(bot))