# admin_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import config # Your config file with DB credentials
import random # Used for the mock API data
import os
from dotenv import load_dotenv
load_dotenv() 

# --- Helper function for simulation ---
def get_nhl_teams():
    """Returns a list of all NHL team names."""
    return [
        "Anaheim Ducks", "Boston Bruins", "Buffalo Sabres", "Calgary Flames",
        "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
        "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings",
        "Edmonton Oilers", "Florida Panthers", "Los Angeles Kings",
        "Minnesota Wild", "Montreal Canadiens", "Nashville Predators",
        "New Jersey Devils", "New York Islanders", "New York Rangers",
        "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins",
        "San Jose Sharks", "Seattle Kraken", "St. Louis Blues",
        "Tampa Bay Lightning", "Toronto Maple Leafs", "Vancouver Canucks",
        "Vegas Golden Knights", "Washington Capitals", "Winnipeg Jets", "Arizona Coyotes"
    ]

# --- Mock NHL API Function ---
# This function now returns a dictionary with game outcomes for each team.
def fetch_weekly_results():
    """
    (MOCK FUNCTION) Fetches a dictionary of game results for the week.
    REPLACE THIS with a real API call.
    Returns a dict like: {'Team Name': 'win' | 'ot_loss' | 'loss'}
    """
    print("MOCK API: Fetching weekly game results...")
    nhl_teams = get_nhl_teams()
    
    results = {}
    # Simulate results for a random number of teams
    participating_teams = random.sample(nhl_teams, k=random.randint(20, 28))
    
    for team in participating_teams:
        outcome = random.choice(['win', 'win', 'win', 'ot_loss', 'loss', 'loss']) # Skew towards wins/losses
        results[team] = outcome
        
    print(f"MOCK API: Results are {results}")
    return results

# --- UI View for Reset Confirmation ---
# This view asks the admin for a final confirmation before deleting all data.
class ConfirmResetView(ui.View):
    def __init__(self, db_cursor, db_connection):
        super().__init__(timeout=60)
        self.cursor = db_cursor
        self.db = db_connection

    @ui.button(label="Confirm & Reset Season", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        """Wipes the rosters table to start a new season."""
        try:
            self.cursor.execute("TRUNCATE TABLE rosters")
            self.db.commit()
            await interaction.response.edit_message(content="✅ **The league has been reset!** All rosters and points are cleared.", view=None)
        except mysql.connector.Error as err:
            await interaction.response.edit_message(content=f"❌ A database error occurred: {err}", view=None)
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="Reset cancelled.", view=None)
        self.stop()

# --- Admin Cog ---
class adminLeague(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mysql.connector.connect(
            host=os.getenv("db_host"),
            user=os.getenv("db_user"),
            password=os.getenv("db_password"),
            database=os.getenv("db_name")
        )
        # Use dictionary cursor for easier access to columns by name
        self.cursor = self.db.cursor(dictionary=True, buffered=True)
        print("Admin Cog: Database connection established.")
        self.create_table()

    def create_table(self):
        """Creates the rosters table if it doesn't already exist."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS rosters (
                    user_id BIGINT PRIMARY KEY,
                    team_one VARCHAR(255),
                    team_two VARCHAR(255),
                    team_three VARCHAR(255),
                    team_four VARCHAR(255),
                    team_five VARCHAR(255),
                    bench_one VARCHAR(255),
                    bench_two VARCHAR(255),
                    bench_three VARCHAR(255),
                    points INT DEFAULT 0,
                    swaps_used TINYINT DEFAULT 0,
                    aced_team_slot VARCHAR(50) NULL
                )
            """)
            print("Admin Cog: Rosters table is ready.")
        except mysql.connector.Error as err:
            print(f"Admin Cog: Failed to create table: {err}")

    @app_commands.command(name="simulate_users", description="[TESTING] Populates the league with fake users.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(count="The number of fake users to create (e.g., 50)")
    async def simulate_users(self, interaction: discord.Interaction, count: int):
        """Creates a specified number of fake users with random data for testing."""
        await interaction.response.defer(ephemeral=True)
        
        if count <= 0:
            await interaction.followup.send("Please enter a positive number of users to simulate.", ephemeral=True)
            return
            
        try:
            nhl_teams = get_nhl_teams()
            created_count = 0
            for _ in range(count):
                user_id = random.randint(10**17, 10**18 - 1) # Fake Discord ID
                
                # Assign 8 unique random teams
                random_roster = random.sample(nhl_teams, 8)
                
                points = random.randint(0, 150)
                swaps_used = random.randint(0, 10)
                
                # Randomly assign an aced team or leave it null
                aced_team_slot = random.choice([None, 'team_one', 'team_two', 'team_three', 'team_four', 'team_five'])

                sql = """
                    INSERT INTO rosters (user_id, team_one, team_two, team_three, team_four, team_five, bench_one, bench_two, bench_three, points, swaps_used, aced_team_slot)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    team_one=VALUES(team_one), team_two=VALUES(team_two), team_three=VALUES(team_three), team_four=VALUES(team_four), team_five=VALUES(team_five),
                    bench_one=VALUES(bench_one), bench_two=VALUES(bench_two), bench_three=VALUES(bench_three),
                    points=VALUES(points), swaps_used=VALUES(swaps_used), aced_team_slot=VALUES(aced_team_slot)
                """
                val = (user_id, *random_roster, points, swaps_used, aced_team_slot)
                self.cursor.execute(sql, val)
                created_count += 1
                
            self.db.commit()
            await interaction.followup.send(f"✅ Successfully created or updated **{created_count}** simulated users in the database.", ephemeral=True)

        except mysql.connector.Error as err:
            await interaction.followup.send(f"❌ A database error occurred during simulation: {err}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)


    @app_commands.command(name="calculate_points", description="Calculates and awards points based on weekly results.")
    @app_commands.default_permissions(administrator=True)
    async def calculate_points(self, interaction: discord.Interaction):
        """
        This command fetches weekly winners, calculates points for each player,
        and updates the database.
        """
        await interaction.response.defer(ephemeral=True)

        # --- Point Values ---
        WIN_POINTS = 4
        OT_LOSS_POINTS = 2
        LOSS_POINTS = -2
        ACE_MULTIPLIER = 3

        try:
            # 1. Fetch game results from the (mock) API
            weekly_results = fetch_weekly_results()
            if not weekly_results:
                await interaction.followup.send("Could not fetch weekly results. Aborting.", ephemeral=True)
                return

            # 2. Get all player rosters from the database
            self.cursor.execute("SELECT * FROM rosters")
            all_rosters = self.cursor.fetchall()

            if not all_rosters:
                await interaction.followup.send("There are no players in the league to calculate points for.", ephemeral=True)
                return

            total_points_awarded = 0
            players_updated = 0

            # 3. Iterate through each player and calculate their points
            for roster in all_rosters:
                weekly_points = 0
                user_id = roster['user_id']
                active_team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']

                for slot in active_team_slots:
                    player_team = roster.get(slot)
                    
                    # Check if the player's team has a result this week
                    if player_team and player_team in weekly_results:
                        result = weekly_results[player_team]
                        points_for_game = 0
                        is_aced = roster.get('aced_team_slot') == slot

                        # Determine base points from the game outcome
                        if result == 'win':
                            points_for_game = WIN_POINTS
                        elif result == 'ot_loss':
                            points_for_game = OT_LOSS_POINTS
                        elif result == 'loss':
                            points_for_game = LOSS_POINTS
                        
                        # Apply the ace multiplier if the team was aced
                        if is_aced:
                            points_for_game *= ACE_MULTIPLIER
                        
                        weekly_points += points_for_game
                
                # 4. Update the player's score in the database if their point total changed
                if weekly_points != 0:
                    update_sql = "UPDATE rosters SET points = points + %s WHERE user_id = %s"
                    self.cursor.execute(update_sql, (weekly_points, user_id))
                    total_points_awarded += weekly_points
                    players_updated += 1
            
            self.db.commit()

            # 5. Send a summary report to the admin
            embed = discord.Embed(
                title="✅ Weekly Point Calculation Complete",
                description="Player scores have been updated based on this week's game results.",
                color=discord.Color.green()
            )
            embed.add_field(name="Players with Score Changes", value=str(players_updated))
            embed.add_field(name="Net Points Awarded/Deducted", value=str(total_points_awarded))
            embed.set_footer(text="Remember to use /admin_league to reset aces for next week.")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except mysql.connector.Error as err:
            await interaction.followup.send(f"❌ A database error occurred during point calculation: {err}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)


    @app_commands.command(name="league_admin", description="Manage the global hockey league.")
    @app_commands.default_permissions(administrator=True)
    async def admin_league(self, interaction: discord.Interaction):
        """Provides a control panel for league administrators."""
        view = ui.View(timeout=180)

        # --- Button to Reset the Season ---
        reset_button = ui.Button(label="Reset League Season", style=discord.ButtonStyle.danger, emoji="🔄")
        async def reset_callback(interaction: discord.Interaction):
            confirm_view = ConfirmResetView(self.cursor, self.db)
            await interaction.response.send_message(
                "⚠️ **Are you absolutely sure?** This will delete all user rosters and points permanently.",
                view=confirm_view,
                ephemeral=True
            )
        reset_button.callback = reset_callback
        view.add_item(reset_button)

        # --- Button to Reset Weekly Aces ---
        reset_aces_button = ui.Button(label="Reset Weekly Aces", style=discord.ButtonStyle.primary, emoji="✨")
        async def reset_aces_callback(interaction: discord.Interaction):
            try:
                self.cursor.execute("UPDATE rosters SET aced_team_slot = NULL")
                self.db.commit()
                await interaction.response.send_message("✅ All player aces have been reset for the week.", ephemeral=True)
            except mysql.connector.Error as err:
                await interaction.response.send_message(f"❌ A database error occurred: {err}", ephemeral=True)
        reset_aces_button.callback = reset_aces_callback
        view.add_item(reset_aces_button)

        # --- Button to View League Stats ---
        stats_button = ui.Button(label="League Stats", style=discord.ButtonStyle.secondary, emoji="📊")
        async def stats_callback(interaction: discord.Interaction):
            try:
                self.cursor.execute("SELECT COUNT(user_id) FROM rosters")
                player_count = self.cursor.fetchone()['COUNT(user_id)']
                embed = discord.Embed(title="🏒 Global League Stats", color=discord.Color.blue())
                embed.add_field(name="Total Players", value=str(player_count))
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except mysql.connector.Error as err:
                await interaction.response.send_message(f"❌ A database error occurred: {err}", ephemeral=True)
        stats_button.callback = stats_callback
        view.add_item(stats_button)

        await interaction.response.send_message("League Admin Panel:", view=view, ephemeral=True)

# The setup function to load the cog
async def setup(bot):
    await bot.add_cog(adminLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
