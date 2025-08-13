import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv
import random
import traceback
import config
from datetime import datetime, timedelta
import requests

load_dotenv()

def get_nhl_teams():
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

def fetch_game_results(start_date_str: str, end_date_str: str):
    print(f"API: Fetching game results from {start_date_str} to {end_date_str}...")
    
    results = {}
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for day in data.get("gameWeek", []):
                for game in day.get("games", []):
                    if game.get("gameState") not in ["OFF", "FINAL"]:
                        continue

                    home_team_data = game.get("homeTeam", {})
                    away_team_data = game.get("awayTeam", {})
                    
                    home_name = f"{home_team_data.get('placeName', {}).get('default')} {home_team_data.get('commonName', {}).get('default')}"
                    away_name = f"{away_team_data.get('placeName', {}).get('default')} {away_team_data.get('commonName', {}).get('default')}"
                    
                    home_score = home_team_data.get("score", 0)
                    away_score = away_team_data.get("score", 0)
                    
                    last_period_type = game.get("gameOutcome", {}).get("lastPeriodType")

                    if home_name not in results: results[home_name] = []
                    if away_name not in results: results[away_name] = []

                    if home_score > away_score:
                        results[home_name].append('win')
                        results[away_name].append('ot_loss' if last_period_type in ["OT", "SO"] else 'loss')
                    else:
                        results[away_name].append('win')
                        results[home_name].append('ot_loss' if last_period_type in ["OT", "SO"] else 'loss')

        except requests.exceptions.RequestException as e:
            print(f"API Error fetching data for {date_str}: {e}")
        
        current_date += timedelta(days=1)
        
    print(f"API: Fetched {sum(len(v) for v in results.values())} total game results.")
    return results

class ConfirmResetView(ui.View):
    pass

class adminLeague(commands.Cog, name="adminLeague"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        try:
            self.db_pool = pooling.MySQLConnectionPool(
                pool_name="hockey_league_pool",
                pool_size=5,
                host=os.getenv("db_host"),
                user=os.getenv("db_user"),
                password=os.getenv("db_password"),
                database=os.getenv("db_name")
            )
            print("Admin Cog: Database connection pool established.")
            self.create_table()
        except mysql.connector.Error as err:
            print(f"FAILED to create database pool in Admin Cog: {err}")
        print("Grabbing a Dunkin' iced coffee for the admin... ☕")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `admin_cog.py`")

    def create_table(self):
        pass

    @app_commands.command(name="calculate_points", description="Backs up data, then calculates points for a specified date range.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    @app_commands.describe(
        start_date="The start date for the calculation period (Format: YYYY-MM-DD).",
        end_date="The end date for the calculation period (Format: YYYY-MM-DD)."
    )
    async def calculate_points(self, interaction: discord.Interaction, start_date: str, end_date: str):
        if config.command_log_bool:
            pass
        
        await interaction.response.defer(ephemeral=True)

        # --- 1. BACKUP DATABASE ---
        db_conn_backup, cursor_backup = None, None
        try:
            db_conn_backup = self.db_pool.get_connection()
            cursor_backup = db_conn_backup.cursor(dictionary=True)
            cursor_backup.execute("SELECT * FROM rosters")
            all_rosters_backup = cursor_backup.fetchall()

            if all_rosters_backup:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_filename = f"rosters_backup_{timestamp}.sql"
                
                with open(backup_filename, "w", encoding="utf-8") as f:
                    f.write(f"-- NHL Fantasy League Roster Backup -- {timestamp}\n")
                    for row in all_rosters_backup:
                        values = []
                        for val in row.values():
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                escaped_val = str(val).replace("'", "''")
                                values.append(f"'{escaped_val}'")
                        
                        columns = ", ".join([f"`{col}`" for col in row.keys()])
                        values_str = ", ".join(values)
                        insert_statement = f"INSERT INTO rosters ({columns}) VALUES ({values_str});\n"
                        f.write(insert_statement)
                
                await interaction.followup.send(f"✅ Database backup created successfully. Proceeding with point calculation.", file=discord.File(backup_filename), ephemeral=True)
                os.remove(backup_filename)
            else:
                await interaction.followup.send("ℹ️ No data in rosters table to back up. Proceeding with point calculation.", ephemeral=True)

        except Exception as backup_error:
            await interaction.followup.send(f"❌ **CRITICAL: Database backup failed.** Point calculation has been aborted. Please check the error logs.", ephemeral=True)
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            return
        finally:
            if cursor_backup: cursor_backup.close()
            if db_conn_backup: db_conn_backup.close()

        # --- 2. PROCEED WITH POINT CALCULATION ---
        db_conn_calc, cursor_calc = None, None
        try:
            # --- Date Validation ---
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                await interaction.followup.send("❌ Invalid date format. Please use `YYYY-MM-DD` for both start and end dates.", ephemeral=True)
                return

            WIN_POINTS, OT_LOSS_POINTS, LOSS_POINTS, ACE_MULTIPLIER = 4, 2, -2, 3
            game_results = fetch_game_results(start_date, end_date)
            
            if not game_results:
                await interaction.followup.send(f"No completed game results found for the period `{start_date}` to `{end_date}`.", ephemeral=True)
                return

            db_conn_calc = self.db_pool.get_connection()
            cursor_calc = db_conn_calc.cursor(dictionary=True)
            cursor_calc.execute("SELECT * FROM rosters")
            all_rosters = cursor_calc.fetchall()

            if not all_rosters:
                await interaction.followup.send("No rosters found to calculate points for.", ephemeral=True)
                return

            total_points_awarded, players_updated = 0, 0
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
                    cursor_calc.execute("UPDATE rosters SET points = points + %s WHERE user_id = %s", (period_points, roster['user_id']))
                    total_points_awarded += period_points
                    players_updated += 1
            
            db_conn_calc.commit()

            embed = discord.Embed(title=f"✅ Point Calculation Complete for {start_date} to {end_date}", color=discord.Color.green())
            embed.add_field(name="Players Updated", value=str(players_updated))
            embed.add_field(name="Net Points Awarded", value=str(total_points_awarded))
            embed.set_footer(text="Use /league_admin to reset aces for the next week.")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred during point calculation. The issue has been reported.", ephemeral=True)
        finally:
            if cursor_calc: cursor_calc.close()
            if db_conn_calc: db_conn_calc.close()

    @app_commands.command(name="league_admin", description="Manage the global hockey league.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True)
    async def admin_league(self, interaction: discord.Interaction):
        if config.command_log_bool:
            pass

        view = ui.View(timeout=180)

        reset_button = ui.Button(label="Reset League Season", style=discord.ButtonStyle.danger, emoji="🔄")
        async def reset_callback(callback_interaction: discord.Interaction):
            confirm_view = ConfirmResetView(self.bot)
            await callback_interaction.response.send_message(
                "⚠️ **Are you sure?** This deletes all rosters and points.", view=confirm_view, ephemeral=True)
        reset_button.callback = reset_callback
        view.add_item(reset_button)

        reset_aces_button = ui.Button(label="Reset Weekly Aces", style=discord.ButtonStyle.primary, emoji="✨")
        async def reset_aces_callback(callback_interaction: discord.Interaction):
            db_conn = None
            cursor = None
            try:
                db_conn = self.db_pool.get_connection()
                cursor = db_conn.cursor()
                cursor.execute("UPDATE rosters SET aced_team_slot = NULL")
                db_conn.commit()
                await callback_interaction.response.send_message("✅ All player aces have been reset.", ephemeral=True)
            except Exception as e:
                await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            finally:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
        reset_aces_button.callback = reset_aces_callback
        view.add_item(reset_aces_button)

        stats_button = ui.Button(label="League Stats", style=discord.ButtonStyle.secondary, emoji="📊")
        async def stats_callback(callback_interaction: discord.Interaction):
            db_conn = None
            cursor = None
            try:
                db_conn = self.db_pool.get_connection()
                cursor = db_conn.cursor(dictionary=True)
                cursor.execute("SELECT COUNT(user_id) AS count FROM rosters")
                player_count = cursor.fetchone()['count']
                embed = discord.Embed(title="🏒 Global League Stats", color=discord.Color.blue())
                embed.add_field(name="Total Players", value=str(player_count))
                await callback_interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await callback_interaction.response.send_message("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            finally:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
        stats_button.callback = stats_callback
        view.add_item(stats_button)

        await interaction.response.send_message("League Admin Panel:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(adminLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
