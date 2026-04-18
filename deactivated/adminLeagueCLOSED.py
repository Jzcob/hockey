# admin_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import aiomysql
import aiohttp
import os
from dotenv import load_dotenv
import random
import traceback
import config
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# --- Helper function for team names ---
def get_nhl_teams():
    """Returns a list of all official NHL team names."""
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

# --- Real NHL API Function ---
async def fetch_game_results_async(session: aiohttp.ClientSession, start_date_str: str, end_date_str: str):
    """
    Fetches game results from the NHL API for a given date range ASYNCHRONOUSLY.
    Returns a dict like: {'Team Name': ['win', 'loss', 'ot_loss', ...]}
    """
    print(f"API: Fetching game results from {start_date_str} to {end_date_str}...")
    
    results = {}
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
        
        try:
            # Use 'async with' for the non-blocking request
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json() # await the json()

                for day in data.get("gameWeek", []):
                    for game in day.get("games", []):
                        if game.get("gameState") not in ["OFF", "FINAL"]:
                            continue

                        home_team_data = game.get("homeTeam", {})
                        away_team_data = game.get("awayTeam", {})
                        
                        # Fix for potential 'None' placeName (e.g., All-Star games)
                        home_place = home_team_data.get('placeName', {}).get('default') or ''
                        away_place = away_team_data.get('placeName', {}).get('default') or ''

                        home_name = f"{home_place} {home_team_data.get('commonName', {}).get('default')}".strip()
                        away_name = f"{away_place} {away_team_data.get('commonName', {}).get('default')}".strip()
                        
                        home_score = home_team_data.get("score", 0)
                        away_score = away_team_data.get("score", 0)
                        
                        last_period_type = game.get("gameOutcome", {}).get("lastPeriodType")

                        results.setdefault(home_name, [])
                        results.setdefault(away_name, [])

                        if home_score > away_score:
                            results[home_name].append('win')
                            results[away_name].append('ot_loss' if last_period_type in ["OT", "SO"] else 'loss')
                        else:
                            results[away_name].append('win')
                            results[home_name].append('ot_loss' if last_period_type in ["OT", "SO"] else 'loss')

        except aiohttp.ClientError as e: # Catch aiohttp errors
            print(f"API Error fetching data for {date_str}: {e}")
        
        current_date += timedelta(days=1)
        
    print(f"API: Fetched {sum(len(v) for v in results.values())} total game results.")
    return results

# --- UI View for Reset Confirmation ---
class ConfirmResetView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.db_pool = bot.db_pool

    @ui.button(label="Confirm & Reset Season", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            async with self.db_pool.acquire() as db_conn:
                async with db_conn.cursor() as cursor:
                    await cursor.execute("TRUNCATE TABLE rosters")
                    # No commit needed (autocommit)
            await interaction.response.edit_message(content="✅ **The league has been reset!** All rosters and points are cleared.", view=None)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.edit_message(content="❌ An error occurred during the reset. The issue has been reported.", view=None)
        # No 'finally' block needed
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Reset cancelled.", view=None)
        self.stop()

# --- Admin Cog ---
class adminLeague(commands.Cog, name="adminLeague"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = bot.db_pool  # Get the pool from the bot
        self.http_session = aiohttp.ClientSession() # Create the session for API calls
        if self.db_pool:
            print("Admin Cog: Database pool is accessible.")
        else:
            print("❌ Admin Cog: Database pool is NOT accessible.")
        print("Grabbing a Dunkin' iced coffee for the admin... ☕")
    
    async def cog_unload(self):
        """Called when the cog is unloaded."""
        await self.http_session.close()

    async def on_ready(self):
        print(f"LOADED: `admin_cog.py`")
        # Call the new async create_table method
        if self.db_pool:
            await self.create_table_async()

    async def create_table_async(self):
        try:
            async with self.db_pool.acquire() as db_conn:
                async with db_conn.cursor() as cursor:
                    await cursor.execute("""
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
        except Exception as err: # Catch generic Exception
            print(f"Admin Cog: Failed to create table: {err}")
    
    async def log_command(self, interaction: discord.Interaction):
        # Your logging logic here
        pass

    @app_commands.command(name="remove_user", description="Removes a user from the fantasy league.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(user="The user to remove from the league.")
    async def remove_user(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        try:
            rowcount = 0
            async with self.db_pool.acquire() as db_conn:
                async with db_conn.cursor() as cursor:
                    await cursor.execute("DELETE FROM rosters WHERE user_id = %s", (user.id,))
                    rowcount = cursor.rowcount # Get rowcount before connection closes

            if rowcount > 0:
                await interaction.followup.send(f"✅ Successfully removed **{user.display_name}** from the league.", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️ **{user.display_name}** was not found in the league.", ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
            

    @app_commands.command(name="calculate_points", description="Backs up data, then calculates points for a specified date range.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        start_date="The start date for the calculation period (Format: YYYY-MM-DD).",
        end_date="The end date for the calculation period (Format: YYYY-MM-DD)."
    )
    async def calculate_points(self, interaction: discord.Interaction, start_date: str, end_date: str):
        await interaction.response.defer(ephemeral=True)
        # --- 1. BACKUP DATABASE ---
        try:
            all_rosters_backup = []
            async with self.db_pool.acquire() as db_conn_backup:
                async with db_conn_backup.cursor(aiomysql.DictCursor) as cursor_backup:
                    await cursor_backup.execute("SELECT * FROM rosters")
                    all_rosters_backup = await cursor_backup.fetchall()
            
            if all_rosters_backup:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_filename = f"rosters_backup_{timestamp}.sql"
                with open(backup_filename, "w", encoding="utf-8") as f:
                    f.write(f"-- NHL Fantasy League Roster Backup -- {timestamp}\n")
                    for row in all_rosters_backup:
                        values = [f"'{str(v).replace("'", "''")}'" if isinstance(v, str) else str(v) if v is not None else "NULL" for v in row.values()]
                        columns = ", ".join([f"`{col}`" for col in row.keys()])
                        values_str = ", ".join(values)
                        f.write(f"INSERT INTO rosters ({columns}) VALUES ({values_str});\n")
                
                if not interaction.is_expired(): await interaction.followup.send(f"✅ Database backup created successfully.", file=discord.File(backup_filename), ephemeral=True)
                os.remove(backup_filename)
            else:
                if not interaction.is_expired(): await interaction.followup.send("ℹ️ No data to back up. Proceeding...", ephemeral=True)
        except Exception:
            if not interaction.is_expired(): await interaction.followup.send(f"❌ **CRITICAL: Database backup failed.** Point calculation aborted.", ephemeral=True)
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            return

        # --- 2. PROCEED WITH POINT CALCULATION ---
        try:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                if not interaction.is_expired(): await interaction.followup.send("❌ Invalid date format. Please use `YYYY-MM-DD` for both start and end dates.", ephemeral=True)
                return

            WIN_POINTS, OT_LOSS_POINTS, LOSS_POINTS, ACE_MULTIPLIER = 4, 2, -2, 3
            
            # --- Awaited async API call ---
            game_results = await fetch_game_results_async(self.http_session, start_date, end_date)
            
            if not game_results:
                if not interaction.is_expired(): await interaction.followup.send(f"No completed game results found for the period `{start_date}` to `{end_date}`.", ephemeral=True)
                return

            all_rosters = []
            total_points_awarded, players_updated = 0, 0
            async with self.db_pool.acquire() as db_conn_calc:
                async with db_conn_calc.cursor(aiomysql.DictCursor) as cursor_calc:
                    await cursor_calc.execute("SELECT * FROM rosters")
                    all_rosters = await cursor_calc.fetchall()

                    if not all_rosters:
                        if not interaction.is_expired(): await interaction.followup.send("No rosters found to calculate points for.", ephemeral=True)
                        return

                    for roster in all_rosters:
                        period_points = 0
                        active_teams = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
                        for slot in active_teams:
                            team_name = roster.get(slot)
                            if team_name and team_name in game_results:
                                for result in game_results[team_name]:
                                    points_for_game = {'win': WIN_POINTS, 'ot_loss': OT_LOSS_POINTS, 'loss': LOSS_POINTS}.get(result, 0)
                                    if roster.get('aced_team_slot') == slot:
                                        points_for_game *= ACE_MULTIPLIER
                                    period_points += points_for_game
                        
                        if period_points != 0:
                            await cursor_calc.execute("UPDATE rosters SET points = points + %s WHERE user_id = %s", (period_points, roster['user_id']))
                            total_points_awarded += period_points
                            players_updated += 1
                    # autocommit handles the commit
            
            view = ui.View(timeout=180)
            reset_aces_button = ui.Button(label="Reset Weekly Aces", style=discord.ButtonStyle.primary, emoji="✨")
            
            # --- This nested callback also needs conversion ---
            async def reset_aces_callback(callback_interaction: discord.Interaction):
                try:
                    async with self.db_pool.acquire() as db_conn_inner:
                        async with db_conn_inner.cursor() as cursor_inner:
                            await cursor_inner.execute("UPDATE rosters SET aced_team_slot = NULL")
                    await callback_interaction.response.send_message("✅ All player aces have been reset.", ephemeral=True)
                except Exception:
                    await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            
            reset_aces_button.callback = reset_aces_callback
            view.add_item(reset_aces_button)

            embed = discord.Embed(title=f"✅ Point Calculation Complete for {start_date} to {end_date}", color=discord.Color.green())
            embed.add_field(name="Players Updated", value=str(players_updated))
            embed.add_field(name="Net Points Awarded", value=str(total_points_awarded))
            embed.set_footer(text="Use /league_admin to reset aces for the next week or click the button!")
            if not interaction.is_expired(): await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred during point calculation. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="league_admin", description="Manage the global hockey league.")
    @app_commands.default_permissions(administrator=True)
    async def admin_league(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            view = ui.View(timeout=180)

            """reset_button = ui.Button(label="Reset League Season", style=discord.ButtonStyle.danger, emoji="🔄")
            async def reset_callback(callback_interaction: discord.Interaction):
                confirm_view = ConfirmResetView(self.bot)
                await callback_interaction.response.send_message(
                    "⚠️ **Are you sure?** This deletes all rosters and points.", view=confirm_view, ephemeral=True)
            reset_button.callback = reset_callback
            view.add_item(reset_button)"""

            reset_aces_button = ui.Button(label="Reset Weekly Aces", style=discord.ButtonStyle.primary, emoji="✨")
            async def reset_aces_callback(callback_interaction: discord.Interaction):
                try:
                    async with self.db_pool.acquire() as db_conn:
                        async with db_conn.cursor() as cursor:
                            await cursor.execute("UPDATE rosters SET aced_team_slot = NULL")
                    await callback_interaction.response.send_message("✅ All player aces have been reset.", ephemeral=True)
                except Exception:
                    await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            
            reset_aces_button.callback = reset_aces_callback
            view.add_item(reset_aces_button)

            stats_button = ui.Button(label="League Stats", style=discord.ButtonStyle.secondary, emoji="📊")

            async def stats_callback(callback_interaction: discord.Interaction):
                try:
                    player_count = 0
                    async with self.db_pool.acquire() as db_conn:
                        async with db_conn.cursor(aiomysql.DictCursor) as cursor:
                            await cursor.execute("SELECT COUNT(user_id) AS count FROM rosters")
                            player_count_data = await cursor.fetchone()
                            player_count = player_count_data['count']
                    embed = discord.Embed(title="🏒 Global League Stats", color=discord.Color.blue())
                    embed.add_field(name="Total Players", value=str(player_count))
                    await callback_interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception:
                    await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            
            stats_button.callback = stats_callback
            view.add_item(stats_button)

            await interaction.followup.send("League Admin Panel:", view=view, ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
    
    alert = app_commands.Group(name="alert", description="Send alerts to league members.")

    @alert.command(name="custom", description="Sends a custom message to all league members.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(message="The message to send.")
    async def alert_custom(self, interaction: discord.Interaction, message: str):
        await self.log_command(interaction)
        await interaction.response.defer(ephemeral=True)
        try:
            user_ids = []
            async with self.db_pool.acquire() as db_conn:
                async with db_conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT user_id FROM rosters")
                    user_ids = [row['user_id'] for row in await cursor.fetchall()]

            if not user_ids:
                if not interaction.is_expired(): await interaction.followup.send("There are no users in the league to alert.", ephemeral=True)
                return

            success_count, fail_count = 0, 0
            failed_users = []
            for user_id in user_ids:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await user.send(f"📢 **League Alert:**\n\n{message}")
                    success_count += 1
                except (discord.errors.NotFound, discord.errors.Forbidden):
                    fail_count += 1
                    failed_users.append(user_id)

            
            if not interaction.is_expired(): await interaction.followup.send(f"✅ Alert sent to **{success_count}** users.\n❌ Failed to send to **{fail_count}** users.", ephemeral=True)
            if fail_count is not 0:
                jacob_id = await self.bot.fetch_user(920797181034778655)
                failed_usernames = []
                for user_id in failed_users:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        failed_usernames.append(user.name)
                    except discord.errors.NotFound:
                        failed_usernames.append(f"Unknown User (ID: {user_id})")

                await jacob_id.send(f"Failed to send alert to the following users: {', '.join(failed_usernames)}")

        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(adminLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])