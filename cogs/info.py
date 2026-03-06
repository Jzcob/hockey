import discord
from discord.ext import commands
from discord import app_commands
import config
import traceback
from datetime import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_pool = self.bot.db_pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `info.py`")

    async def is_guild_premium(self, guild_id):
        """Checks if the current guild is a Referee Tier subscriber."""
        if not guild_id: return False
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT is_premium FROM premium_status WHERE entity_id = %s", (guild_id,))
                res = await cursor.fetchone()
                return bool(res[0]) if res else False
    
    @app_commands.command(name="info", description="Shows the info menu and bot policies!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def info(self, interaction: discord.Interaction):
        # Logging Logic
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = interaction.guild.name if interaction.guild else "DMs"
            await command_log_channel.send(f"`/info` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")

        # Check Premium Status
        is_premium = await self.is_guild_premium(interaction.guild_id)
        
        embed = discord.Embed(
            title="Hockey Bot Information", 
            description=(
                "**The 2nd largest Hockey bot on Discord!**\n"
                "Providing NHL stats, live updates, and advanced moderation tools."
            ), 
            color=0x00ff00
        )

        # Referee Tier Section
        premium_value = (
            "✅ **Status: Active**\nThis server has persistent storage enabled!" if is_premium 
            else "❌ **Status: Inactive**\nUpgrade to the **Referee Tier** for permanent logs and data exports!"
        )
        embed.add_field(name="💎 Referee Tier", value=premium_value, inline=False)

        # 📊 Data & Policy Summary
        embed.add_field(
            name="📊 Data & Policy Summary", 
            value=(
                "• **Free Tier:** Moderation logs are kept for **90 days**.\n"
                "• **Referee Tier:** Logs are stored permanently.\n"
                "• **Policy Notice:** Terms and Privacy policies may be updated at any time without notice."
            ), 
            inline=False
        )

        # Links & Timestamps
        embed.add_field(name="Policy Links", value=(
            f"[Privacy Policy](https://github.com/Jzcob/hockey/blob/main/SECURITY.md)\n"
            f"[Terms of Service](https://github.com/Jzcob/hockey/wiki/Terms-of-Service-for-Hockey-Bot)\n"
            "*Last Updated: March 06, 2026*"
        ), inline=True)
        
        embed.add_field(name="Community", value=(
            f"[Support Server]({config.discord_link if hasattr(config, 'discord_link') else 'https://discord.gg/WGQYdzvn8y'})\n"
            f"[GitHub Repo](https://github.com/Jzcob/hockey)\n"
            f"[Patreon](https://www.patreon.com/jzcob)"
        ), inline=True)

        embed.set_footer(text=config.footer)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))