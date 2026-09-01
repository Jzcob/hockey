import discord
from discord import app_commands
from discord.ext import commands
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

    async def _log_command(self, interaction: discord.Interaction):
        if not config.command_log_bool:
            return
        try:
            log_channel = self.bot.get_channel(config.command_log)
            if not log_channel:
                return
            location = f"`{interaction.guild.name}`" if interaction.guild else "DMs"
            await log_channel.send(f"`/{interaction.command.name}` used by `{interaction.user.name}` in {location} at `{datetime.now()}`\n---")
        except Exception as e:
            print(f"Command logging failed: {e}")

    @app_commands.command(name="teams", description="Get the teams and their abbreviations!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def teams_cmd(self, interaction: discord.Interaction):
        await self._log_command(interaction)
        await interaction.response.defer(ephemeral=True)

        try:
            # Map JSON names to your config.py variable names
            name_corrections = {
                "Anaheim Ducks": "anahiem_ducks_emoji",
                "USA": "usa_emoji",
                "Canada": "canada_emoji",
                "Czechia": "czech_republic_emoji"
            }

            with open("teams.json", "r", encoding="utf-8") as f:
                teams_data = json.load(f)

            description_lines = []
            for abbr, name in teams_data.items():
                if name in name_corrections:
                    emoji_attr_name = name_corrections[name]
                else:
                    # Logic: "New York Rangers" -> "new_york_rangers_emoji"
                    emoji_attr_name = f"{name.lower().replace(' ', '_').replace('.', '')}_emoji"
                
                emoji = getattr(config, emoji_attr_name, "")
                description_lines.append(f"**{abbr}** - {name} {emoji}")

            # Split into two columns if the list is too long for one embed field
            embed = discord.Embed(
                title="League & Olympic Teams",
                description="Use these abbreviations with `/game` or `/schedule`!\n\n" + "\n".join(description_lines),
                color=discord.Color.green()
            )
            embed.set_footer(text=config.footer)
            
            await interaction.followup.send(embed=embed, ephemeral=True)

        except FileNotFoundError:
            await interaction.followup.send("❌ `teams.json` not found.", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel:
                await error_channel.send(f"**Error in /teams:**\n```{traceback.format_exc()}```")
            await interaction.followup.send("❌ An error occurred.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(teams(bot))