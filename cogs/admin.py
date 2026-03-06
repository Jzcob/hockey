import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import config
import traceback
import aiomysql

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in config.bot_authors:
            return True
        await interaction.response.send_message("❌ This command is restricted to bot owners.", ephemeral=True)
        return False
    return app_commands.check(predicate)

class admin(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.db_pool = self.bot.db_pool
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `admin.py`")
        await self.bot.change_presence(activity=discord.CustomActivity(name="🏒 HOCKEY HOCKEY 🏒"))
    
    # --- New Manual Premium Management ---

    @app_commands.command(name="give-referee", description="Manually grant Referee Tier to a server (Owner Only).")
    @is_owner()
    @app_commands.describe(guild_id="The ID of the server to grant premium to.")
    async def give_referee(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO premium_status (entity_id, is_premium, tier) 
                        VALUES (%s, 1, 'referee') 
                        ON DUPLICATE KEY UPDATE is_premium = 1, tier = 'referee'
                    """
                    await cursor.execute(sql, (int(guild_id),))
                    await conn.commit()
            await interaction.followup.send(f"✅ Server `{guild_id}` has been manually upgraded to **Referee Tier**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Database error: {e}")

    @app_commands.command(name="remove-referee", description="Manually remove Referee Tier from a server (Owner Only).")
    @is_owner()
    @app_commands.describe(guild_id="The ID of the server to remove premium from.")
    async def remove_referee(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    sql = "DELETE FROM premium_status WHERE entity_id = %s"
                    await cursor.execute(sql, (int(guild_id),))
                    await conn.commit()
            await interaction.followup.send(f"✅ Server `{guild_id}` has been downgraded to **Free Tier**.")
        except Exception as e:
            await interaction.followup.send(f"❌ Database error: {e}")

    # --- Existing Admin Commands ---

    @app_commands.command(name="dev-mode", description="Toggles dev mode!")
    async def dev_mode(self, interaction: discord.Interaction):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/dev-mode` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}` \n---")
        try:
            if interaction.user.id in config.bot_authors:
                config.dev_mode = not config.dev_mode
                status = "enabled" if config.dev_mode else "disabled"
                return await interaction.response.send_message(f"Dev mode is now {status}!")
            else:
                return await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")

    @app_commands.command(name="send", description="Make the bot say something.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def say(self, interaction: discord.Interaction, *, message: str, channel: discord.TextChannel = None):
        try:
            target_channel = channel or interaction.channel
            await target_channel.send(message)
            await interaction.response.send_message(f"Sent message to {target_channel.mention}", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"```{traceback.format_exc()}```")

async def setup(bot):
    await bot.add_cog(admin(bot), guilds=[discord.Object(id=config.hockey_discord_server)])