# admin_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import os
from dotenv import load_dotenv
import random
import traceback
import config
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# --- Helper function for simulation ---
def get_nhl_teams():
    """Returns a list of all NHL team names."""
    # The Coyotes franchise became the Utah Hockey Club for the 2024-25 season.
    # This list is updated to reflect that change.
    return [
        "Anaheim Ducks", "Boston Bruins", "Buffalo Sabres", "Calgary Flames",
        "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
        "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings",
        "Edmonton Oilers", "Florida Panthers", "Los Angeles Kings",
        "Minnesota Wild", "Montreal Canadiens", "Nashville Predators",
        "New Jersey Devils", "New York Islanders", "New York Rangers",
        "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins",
        "San Jose Sharks", "Seattle Kraken", "St. Louis Blues",
        "Tampa Bay Lightning", "Toronto Maple Leafs", "Utah Hockey Club",
        "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals", "Winnipeg Jets"
    ]

# --- Mock NHL API Function ---
def fetch_weekly_results():
    """
    (MOCK FUNCTION) Fetches a dictionary of game results for the week.
    REPLACE THIS with a real API call.
    Returns a dict like: {'Team Name': 'win' | 'ot_loss' | 'loss'}
    """
    print("MOCK API: Fetching weekly game results...")
    nhl_teams = get_nhl_teams()
    results = {}
    # Simulate that about 20-28 teams play in a given week
    participating_teams = random.sample(nhl_teams, k=random.randint(20, 28))
    for team in participating_teams:
        outcome = random.choice(['win', 'win', 'win', 'ot_loss', 'loss', 'loss'])
        results[team] = outcome
    print(f"MOCK API: Generated {len(results)} results.")
    return results

# --- UI View for Reset Confirmation ---
class ConfirmResetView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        # This view will use the bot's db connection from the cog
        self.cursor = self.bot.get_cog("adminLeague").cursor
        self.db = self.bot.get_cog("adminLeague").db

    @ui.button(label="Confirm & Reset Season", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            self.cursor.execute("TRUNCATE TABLE rosters")
            self.db.commit()
            await interaction.response.edit_message(content="✅ **The league has been reset!** All rosters and points are cleared.", view=None)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.edit_message(content="❌ An error occurred during the reset. The issue has been reported.", view=None)
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Reset cancelled.", view=None)
        self.stop()

# --- Admin Cog ---
class adminLeague(commands.Cog, name="adminLeague"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.db = mysql.connector.connect(
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            self.cursor = self.db.cursor(dictionary=True, buffered=True)
            print("Admin Cog: Database connection established.")
            self.create_table()
        except mysql.connector.Error as err:
            print(f"FAILED to connect to database in Admin Cog: {err}")
        # And the most important feature...
        print("Grabbing a Dunkin' iced coffee for the admin... ☕")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `admin_cog.py`")

    def create_table(self):
        """Creates the rosters table if it doesn't already exist."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS rosters (
                    user_id BIGINT PRIMARY KEY,
                    team_one VARCHAR(255), team_two VARCHAR(255), team_three VARCHAR(255),
                    team_four VARCHAR(255), team_five VARCHAR(255),
                    bench_one VARCHAR(255), bench_two VARCHAR(255), bench_three VARCHAR(255),
                    points INT DEFAULT 0, swaps_used TINYINT DEFAULT 0,
                    aced_team_slot VARCHAR(50) NULL
                )
            """)
            print("Admin Cog: Rosters table is ready.")
        except mysql.connector.Error as err:
            print(f"Admin Cog: Failed to create table: {err}")

    @app_commands.command(name="remove_user", description="Removes a user from the fantasy league.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    @app_commands.describe(user="The user to remove from the league.")
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        if config.command_log_bool:
            try:
                log_channel = self.bot.get_channel(config.command_log)
                await log_channel.send(f"`/remove_user` used by `{interaction.user.name}` for user `{user.name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /remove_user: {e}")

        try:
            await interaction.response.defer(ephemeral=True)
            self.cursor.execute("DELETE FROM rosters WHERE user_id = %s", (user.id,))
            self.db.commit()

            if self.cursor.rowcount > 0:
                await interaction.followup.send(f"✅ Successfully removed **{user.display_name}** from the league.", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ **{user.display_name}** was not found in the league.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)


    @app_commands.command(name="notify_all", description="Sends a DM to all league members with their rank and points.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    async def notify_all(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                log_channel = self.bot.get_channel(config.command_log)
                await log_channel.send(f"`/notify_all` used by `{interaction.user.name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /notify_all: {e}")

        try:
            await interaction.response.defer(ephemeral=True)
            self.cursor.execute("SELECT user_id, points FROM rosters ORDER BY points DESC")
            all_rosters = self.cursor.fetchall()

            if not all_rosters:
                await interaction.followup.send("There are no players in the league to notify.", ephemeral=True)
                return

            success_count, fail_count = 0, 0
            for rank, roster in enumerate(all_rosters, 1):
                try:
                    user = await self.bot.fetch_user(roster['user_id'])
                    embed = discord.Embed(title="🏒 Weekly League Update!", color=discord.Color.blue())
                    embed.add_field(name="Your Rank", value=f"**#{rank}** of {len(all_rosters)}", inline=True)
                    embed.add_field(name="Your Points", value=f"**{roster['points']}** 🏆", inline=True)
                    embed.set_footer(text="Good luck next week!")
                    await user.send(embed=embed)
                    success_count += 1
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    fail_count += 1
            
            await interaction.followup.send(f"✅ Notification process complete.\n- DMs sent: **{success_count}**\n- DMs failed: **{fail_count}**", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="calculate_points", description="Calculates and awards points based on weekly results.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    async def calculate_points(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                log_channel = self.bot.get_channel(config.command_log)
                await log_channel.send(f"`/calculate_points` used by `{interaction.user.name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /calculate_points: {e}")
        
        try:
            await interaction.response.defer(ephemeral=True)

            WIN_POINTS, OT_LOSS_POINTS, LOSS_POINTS, ACE_MULTIPLIER = 4, 2, -2, 3
            
            weekly_results = fetch_weekly_results()
            self.cursor.execute("SELECT * FROM rosters")
            all_rosters = self.cursor.fetchall()

            if not all_rosters:
                await interaction.followup.send("No rosters found to calculate points for.", ephemeral=True)
                return

            total_points_awarded, players_updated = 0, 0
            for roster in all_rosters:
                weekly_points = 0
                active_teams = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
                for slot in active_teams:
                    team_name = roster.get(slot)
                    if team_name and team_name in weekly_results:
                        result = weekly_results[team_name]
                        points_for_game = {'win': WIN_POINTS, 'ot_loss': OT_LOSS_POINTS, 'loss': LOSS_POINTS}.get(result, 0)
                        if roster.get('aced_team_slot') == slot:
                            points_for_game *= ACE_MULTIPLIER
                        weekly_points += points_for_game
                
                if weekly_points != 0:
                    self.cursor.execute("UPDATE rosters SET points = points + %s WHERE user_id = %s", (weekly_points, roster['user_id']))
                    total_points_awarded += weekly_points
                    players_updated += 1
            
            self.db.commit()

            embed = discord.Embed(title="✅ Weekly Point Calculation Complete", color=discord.Color.green())
            embed.add_field(name="Players Updated", value=str(players_updated))
            embed.add_field(name="Net Points Awarded", value=str(total_points_awarded))
            embed.set_footer(text="Use /league_admin to reset aces for the next week.")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="league_admin", description="Manage the global hockey league.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    async def admin_league(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                log_channel = self.bot.get_channel(config.command_log)
                await log_channel.send(f"`/league_admin` used by `{interaction.user.name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /league_admin: {e}")

        try:
            view = ui.View(timeout=180)

            # --- Reset Season Button ---
            reset_button = ui.Button(label="Reset League Season", style=discord.ButtonStyle.danger, emoji="🔄")
            async def reset_callback(callback_interaction: discord.Interaction):
                confirm_view = ConfirmResetView(self.bot)
                await callback_interaction.response.send_message(
                    "⚠️ **Are you sure?** This deletes all rosters and points.", view=confirm_view, ephemeral=True)
            reset_button.callback = reset_callback
            view.add_item(reset_button)

            # --- Reset Aces Button ---
            reset_aces_button = ui.Button(label="Reset Weekly Aces", style=discord.ButtonStyle.primary, emoji="✨")
            async def reset_aces_callback(callback_interaction: discord.Interaction):
                try:
                    self.cursor.execute("UPDATE rosters SET aced_team_slot = NULL")
                    self.db.commit()
                    await callback_interaction.response.send_message("✅ All player aces have been reset.", ephemeral=True)
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                    await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            reset_aces_button.callback = reset_aces_callback
            view.add_item(reset_aces_button)

            # --- League Stats Button ---
            stats_button = ui.Button(label="League Stats", style=discord.ButtonStyle.secondary, emoji="📊")
            async def stats_callback(callback_interaction: discord.Interaction):
                try:
                    self.cursor.execute("SELECT COUNT(user_id) AS count FROM rosters")
                    player_count = self.cursor.fetchone()['count']
                    embed = discord.Embed(title="🏒 Global League Stats", color=discord.Color.blue())
                    embed.add_field(name="Total Players", value=str(player_count))
                    await callback_interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                    await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            stats_button.callback = stats_callback
            view.add_item(stats_button)

            await interaction.response.send_message("League Admin Panel:", view=view, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred. The issue has been reported.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)


# The setup function to load the cog
async def setup(bot):
    await bot.add_cog(adminLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
