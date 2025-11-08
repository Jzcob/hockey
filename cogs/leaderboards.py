import discord
from discord.ext import commands
from discord import app_commands
import aiomysql
import os
from dotenv import load_dotenv
import config
import traceback
from datetime import datetime
import math

load_dotenv()

class FantasyLeaderboardView(discord.ui.View):
    def __init__(self, leaders: list, bot: commands.Bot, timeout=180):
        super().__init__(timeout=timeout)
        self.leaders = leaders
        self.bot = bot
        self.current_page = 1
        self.per_page = 10
        self.total_pages = math.ceil(len(self.leaders) / self.per_page)
        self.message = None
        self.update_buttons()

    async def create_embed(self) -> discord.Embed:
        """Creates the embed for the current page."""
        embed = discord.Embed(title="🏆 Fantasy League Leaderboard", color=discord.Color.gold())
        
        start_index = (self.current_page - 1) * self.per_page
        end_index = self.current_page * self.per_page
        page_leaders = self.leaders[start_index:end_index]
        
        description = []
        for i, leader in enumerate(page_leaders, start=start_index):
            rank = i + 1  # Global rank
            try:
                user = await self.bot.fetch_user(leader['user_id'])
                user_name = user.display_name
            except discord.errors.NotFound:
                user_name = f"Unknown User ({leader['user_id']})"
            
            rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
            description.append(f"{rank_emoji} {user_name} - **{leader['points']}** points")
        
        if not description:
            embed.description = "No players on this page."
        else:
            embed.description = "\n".join(description)
            
        embed.set_footer(text=f"Page {self.current_page} of {self.total_pages}")
        return embed

    def update_buttons(self):
        """Enables or disables buttons based on the current page."""
        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page >= self.total_pages

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.blurple, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.blurple, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    async def on_timeout(self):
        """Disables all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.errors.NotFound:
                pass


class Leaderboards(commands.Cog, name="Leaderboards"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = self.bot.db_pool 
        print("Leaderboards Cog: Database pool is accessible.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `leaderboards.py`")

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    # For grouped commands, the full name is needed
                    full_command_name = f"{interaction.command.parent.name} {interaction.command.name}"
                    await command_log_channel.send(f"`/{full_command_name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /{interaction.command.name}: {e}")

    leaderboard = app_commands.Group(name="leaderboard", description="Commands for viewing game leaderboards and stats.")

    @leaderboard.command(name="fantasy", description="Displays the fantasy league leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fantasy_leaderboard(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer()
            leaders = []
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # MODIFIED: Select ALL rosters, not just top 10
                    await cursor.execute("SELECT user_id, points FROM rosters ORDER BY points DESC")
                    leaders = await cursor.fetchall()

            if not leaders:
                if not interaction.is_expired():
                    await interaction.followup.send("There are no players on the fantasy leaderboard yet!")
                return

            view = FantasyLeaderboardView(leaders=leaders, bot=self.bot)
            
            initial_embed = await view.create_embed()
            
            if not interaction.is_expired():
                message = await interaction.followup.send(embed=initial_embed, view=view)
                view.message = message

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @leaderboard.command(name="trivia", description="View the trivia leaderboards!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def trivia_leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        await self.log_command(interaction)
        try:
            await interaction.response.defer()
            myresult = []
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if global_view:
                        await cursor.execute("""
                            SELECT ts.user_id, SUM(ts.points) AS total_points
                            FROM trivia_scores ts
                            JOIN trivia_users tu ON ts.user_id = tu.user_id
                            WHERE tu.allow_leaderboard = 1
                            GROUP BY ts.user_id
                            ORDER BY total_points DESC
                            LIMIT 10
                        """)
                    else:
                        await cursor.execute("""
                            SELECT ts.user_id, ts.points
                            FROM trivia_scores ts
                            JOIN trivia_users tu ON ts.user_id = tu.user_id
                            WHERE ts.guild_id = %s AND tu.allow_leaderboard = 1
                            ORDER BY ts.points DESC
                            LIMIT 10
                        """, (interaction.guild.id,))
                    
                    myresult = await cursor.fetchall()
            
            title = "🌐 Global Trivia Leaderboard" if global_view else f"Trivia Leaderboard for {interaction.guild.name}"
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_footer(text=config.footer)
            
            description = []
            for i, row in enumerate(myresult, start=1):
                user_id = row['user_id']
                points = row.get('total_points') or row.get('points', 0)
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except discord.errors.NotFound:
                    name = "Unknown User"
                description.append(f"{i}. `{name}` - `{points:,}` point{'s' if points != 1 else ''}")

            embed.description = "\n".join(description) if description else "No entries yet!"
            if not interaction.is_expired():
                await interaction.followup.send(embed=embed)

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.follow_up.send("An error occurred. The issue has been reported.", ephemeral=True) # Note: Changed to follow_up as it's likely a typo in original

    @leaderboard.command(name="gtp", description="View the Guess The Player leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(global_view="Show global leaderboard instead of just this server.")
    async def gtp_leaderboard(self, interaction: discord.Interaction, global_view: bool = False):
        await self.log_command(interaction)
        try:
            await interaction.response.defer()
            rows = []
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    if global_view:
                        await cursor.execute("""
                            SELECT gs.user_id, SUM(gs.points) AS total_points
                            FROM gtp_scores gs
                            JOIN gtp_users gu ON gs.user_id = gu.user_id
                            WHERE gu.allow_leaderboard = 1
                            GROUP BY gs.user_id
                            ORDER BY total_points DESC
                            LIMIT 10
                        """)
                    else:
                        await cursor.execute("""
                            SELECT gs.user_id, gs.points
                            FROM gtp_scores gs
                            JOIN gtp_users gu ON gs.user_id = gu.user_id
                            WHERE gs.guild_id = %s AND gu.allow_leaderboard = 1
                            ORDER BY gs.points DESC
                            LIMIT 10
                        """, (interaction.guild.id,))
                    
                    rows = await cursor.fetchall()
            
            title = "🌐 Global Guess The Player Leaderboard" if global_view else f"GTP Leaderboard for {interaction.guild.name}"
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_footer(text=config.footer)

            description = []
            for i, row in enumerate(rows, start=1):
                user_id = row['user_id']
                points = row.get('total_points') or row.get('points', 0)
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except discord.errors.NotFound:
                    name = "Unknown User"
                description.append(f"{i}. `{name}` - `{points:,}` point{'s' if points != 1 else ''}")

            embed.description = "\n".join(description) if description else "No entries yet!"
            if not interaction.is_expired():
                await interaction.followup.send(embed=embed)

        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @leaderboard.command(name="trivia-status", description="Toggles if you are displayed on the trivia leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(allow="Choose 'on' to be shown (default), or 'off' to be hidden.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def trivia_leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            allow_bool = allow.value == 't'
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO trivia_users (user_id, allow_leaderboard)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE allow_leaderboard = %s
                    """, (interaction.user.id, allow_bool, allow_bool))
            
            if not interaction.is_expired():
                await interaction.followup.send(f"Your trivia leaderboard visibility has been set to `{allow.name}`.", ephemeral=True)
        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @leaderboard.command(name="gtp-status", description="Toggles if you are displayed on the Guess The Player leaderboard.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(allow="Choose 'on' to be shown (default), or 'off' to be hidden.")
    @app_commands.choices(allow=[
        app_commands.Choice(name='on', value='t'),
        app_commands.Choice(name='off', value='f')
    ])
    async def gtp_leaderboard_status(self, interaction: discord.Interaction, allow: discord.app_commands.Choice[str]):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            allow_bool = allow.value == 't'
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO gtp_users (user_id, allow_leaderboard)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE allow_leaderboard = %s
                    """, (interaction.user.id, allow_bool, allow_bool))
            
            if not interaction.is_expired():
                await interaction.followup.send(f"Your Guess The Player leaderboard visibility has been set to `{allow.name}`.", ephemeral=True)
        except Exception as e:
            if not interaction.is_expired():
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Leaderboards(bot))