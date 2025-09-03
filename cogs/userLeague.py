# user_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import os
from dotenv import load_dotenv
import config
import traceback
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# --- Helper function for team validation ---
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

def levenshtein_distance(s1, s2):
    """Calculates the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def find_closest_team(input_name: str, team_list: list):
    """Finds the closest matching team name from the official list."""
    if not input_name:
        return None
    
    scores = {team: levenshtein_distance(input_name.lower(), team.lower()) for team in team_list}
    best_match = min(scores, key=scores.get)
    best_score = scores[best_match]
    
    if best_score <= 3:
        return best_match
    return None

# --- UI Modal for Bench Teams (Step 2) ---
class SetBenchModal(ui.Modal, title="Set Your Bench Teams (Step 2 of 2)"):
    bench_one = ui.TextInput(label="Bench Team 1", placeholder="Enter NHL Team Name")
    bench_two = ui.TextInput(label="Bench Team 2", placeholder="Enter NHL Team Name")
    bench_three = ui.TextInput(label="Bench Team 3", placeholder="Enter NHL Team Name")

    def __init__(self, bot, db_pool, active_teams: list):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_pool = db_pool
        self.active_teams = active_teams

    async def on_submit(self, interaction: discord.Interaction):
        db_conn = None
        cursor = None
        try:
            bench_teams = [team.strip().title() for team in [self.bench_one.value, self.bench_two.value, self.bench_three.value]]
            all_teams = self.active_teams + bench_teams
            valid_teams = get_nhl_teams()

            for team_input in all_teams:
                if team_input not in valid_teams:
                    suggestion = find_closest_team(team_input, valid_teams)
                    msg = f"❌ Invalid team: `{team_input}`. Please use an official NHL team name. Check `/teams` for a list."
                    if suggestion:
                        msg = f"❌ Invalid team: `{team_input}`. Did you mean `{suggestion}`? Please correct it and try again."
                    await interaction.response.send_message(msg, ephemeral=True)
                    return

            if len(set(all_teams)) != len(all_teams):
                await interaction.response.send_message("❌ You cannot select the same team more than once. Please click the button to try again.", ephemeral=True)
                return

            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor()
            sql = "UPDATE rosters SET bench_one = %s, bench_two = %s, bench_three = %s WHERE user_id = %s"
            val = (*bench_teams, interaction.user.id)
            cursor.execute(sql, val)
            db_conn.commit()
            
            await interaction.response.edit_message(
                content="🎉 **Welcome to the league!** Your full roster is set. Use `/my-roster` to view it.",
                view=None
            )
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred. The issue has been reported.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

# --- UI View with Button to Trigger Step 2 ---
class SetBenchButtonView(ui.View):
    def __init__(self, bot, db_pool, user_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.db_pool = db_pool
        self.user_id = user_id

    @ui.button(label="Set Bench Teams", style=discord.ButtonStyle.success)
    async def set_bench(self, interaction: discord.Interaction, button: ui.Button):
        db_conn = None
        cursor = None
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
            
        try:
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor(dictionary=True)
            cursor.execute("SELECT team_one, team_two, team_three, team_four, team_five FROM rosters WHERE user_id = %s", (interaction.user.id,))
            roster = cursor.fetchone()
            
            if roster:
                active_teams = list(roster.values())
                modal = SetBenchModal(self.bot, self.db_pool, active_teams)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Could not find your active roster. Please try `/join-league` again.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message("❌ An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

# --- UI Modal for Active Teams (Step 1) ---
class JoinLeagueModal(ui.Modal, title="Join the League (Step 1 of 2)"):
    team_one = ui.TextInput(label="Active Team 1", placeholder="Enter NHL Team Name")
    team_two = ui.TextInput(label="Active Team 2", placeholder="Enter NHL Team Name")
    team_three = ui.TextInput(label="Active Team 3", placeholder="Enter NHL Team Name")
    team_four = ui.TextInput(label="Active Team 4", placeholder="Enter NHL Team Name")
    team_five = ui.TextInput(label="Active Team 5", placeholder="Enter NHL Team Name")

    def __init__(self, bot, db_pool):
        super().__init__(timeout=300)
        self.bot = bot
        self.db_pool = db_pool

    async def on_submit(self, interaction: discord.Interaction):
        db_conn = None
        cursor = None
        try:
            active_teams = [team.strip().title() for team in [self.team_one.value, self.team_two.value, self.team_three.value, self.team_four.value, self.team_five.value]]
            valid_teams = get_nhl_teams()

            for team_input in active_teams:
                if team_input not in valid_teams:
                    suggestion = find_closest_team(team_input, valid_teams)
                    msg = f"❌ Invalid team: `{team_input}`. Please use an official NHL team name. Check `/teams` for a list."
                    if suggestion:
                        msg = f"❌ Invalid team: `{team_input}`. Did you mean `{suggestion}`? Please correct it and try again."
                    await interaction.response.send_message(msg, ephemeral=True)
                    return

            if len(set(active_teams)) != len(active_teams):
                await interaction.response.send_message("❌ You cannot select the same active team more than once. Please try again.", ephemeral=True)
                return

            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor()
            sql = "INSERT INTO rosters (user_id, team_one, team_two, team_three, team_four, team_five) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (interaction.user.id, *active_teams)
            cursor.execute(sql, val)
            db_conn.commit()
            
            team_list_str = "\n".join([f"**{i}.** {team}" for i, team in enumerate(active_teams, 1)])
            message_content = f"✅ **Active Roster Saved!**\n{team_list_str}\n\nClick the button below to set your 3 bench teams."
            
            view = SetBenchButtonView(self.bot, self.db_pool, interaction.user.id)
            await interaction.response.send_message(
                content=message_content,
                view=view,
                ephemeral=True
            )
        except mysql.connector.Error as err:
            if err.errno == 1062:
                await interaction.response.send_message("❌ You are already in the league!", ephemeral=True)
            else:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.response.send_message(f"❌ A database error occurred. The issue has been reported.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message(f"❌ An error occurred. The issue has been reported.", ephemeral=True)
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

# --- UI View for Swapping Teams ---
class SwapView(ui.View):
    def __init__(self, bot, user_id, db_pool, active_teams, bench_teams):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.db_pool = db_pool
        self.active_selection = None
        self.bench_selection = None

        active_options = [discord.SelectOption(label=team[1], value=team[0]) for team in active_teams if team[1]]
        self.active_dropdown = ui.Select(placeholder="Choose an active team to swap out...", options=active_options)

        bench_options = [discord.SelectOption(label=team[1], value=team[0]) for team in bench_teams if team[1]]
        self.bench_dropdown = ui.Select(placeholder="Choose a bench team to swap in...", options=bench_options)
        
        self.active_dropdown.callback = self.on_active_select
        self.bench_dropdown.callback = self.on_bench_select

        self.add_item(self.active_dropdown)
        self.add_item(self.bench_dropdown)

    async def on_active_select(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.active_selection = self.active_dropdown.values[0]
        await self.check_and_execute_swap(interaction)

    async def on_bench_select(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.bench_selection = self.bench_dropdown.values[0]
        await self.check_and_execute_swap(interaction)

    async def check_and_execute_swap(self, interaction: discord.Interaction):
        if self.active_selection and self.bench_selection:
            db_conn = None
            cursor = None
            try:
                db_conn = self.db_pool.get_connection()
                cursor = db_conn.cursor(dictionary=True)
                
                cursor.execute(f"SELECT `{self.active_selection}`, `{self.bench_selection}` FROM rosters WHERE user_id = %s", (self.user_id,))
                team_names = cursor.fetchone()
                if not team_names:
                    await interaction.followup.send("❌ Could not find your roster to perform the swap.", ephemeral=True)
                    self.stop()
                    return
                    
                active_team_name = team_names[self.active_selection]
                bench_team_name = team_names[self.bench_selection]

                sql = f"UPDATE rosters SET `{self.active_selection}` = %s, `{self.bench_selection}` = %s, swaps_used = swaps_used + 1 WHERE user_id = %s"
                cursor.execute(sql, (bench_team_name, active_team_name, self.user_id))
                db_conn.commit()
                
                await interaction.followup.send(f"✅ Swap successful! **{bench_team_name}** is now active, and **{active_team_name}** is on the bench.", ephemeral=True)
                
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self)
                self.stop()

            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("❌ A database error occurred. The issue has been reported.", ephemeral=True)
                self.stop()
            finally:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()

# --- User Commands Cog ---
class userLeague(commands.Cog, name="userLeague"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = self.bot.get_cog("adminLeague").db_pool
        print("User Cog: Database pool is accessible.")
            
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `user_cog.py`")

    def get_user_roster(self, user_id: int):
        db_conn = None
        cursor = None
        try:
            db_conn = self.db_pool.get_connection()
            cursor = db_conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rosters WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error in get_user_roster for {user_id}: {err}")
            return None
        finally:
            if cursor: cursor.close()
            if db_conn: db_conn.close()

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    await command_log_channel.send(f"`/{interaction.command.name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /{interaction.command.name}: {e}")

    @app_commands.command(name="join-league", description="Sign up for the fantasy league and set your roster.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def join_league(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            modal = JoinLeagueModal(self.bot, self.db_pool)
            await interaction.response.send_modal(modal)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message("An error occurred. The issue has been reported.", ephemeral=True)
                except discord.errors.InteractionResponded:
                    await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="my-roster", description="View your current team roster, points, and swaps.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def my_roster(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet! Use `/join-league` to get started.", ephemeral=True)
                return

            if not roster.get('bench_one'):
                view = SetBenchButtonView(self.bot, self.db_pool, interaction.user.id)
                await interaction.followup.send("⚠️ Your registration is incomplete! Please set your bench teams to continue.", view=view, ephemeral=True)
                return

            embed = discord.Embed(title=f"{interaction.user.display_name}'s Roster", color=discord.Color.green())
            
            active_teams = [f"**{i}.** {roster.get(slot, 'Empty')}{' ✨' if roster.get('aced_team_slot') == slot else ''}" for i, slot in enumerate(['team_one', 'team_two', 'team_three', 'team_four', 'team_five'], 1)]
            bench_teams = [f"**{i}.** {roster.get(slot, 'Empty')}" for i, slot in enumerate(['bench_one', 'bench_two', 'bench_three'], 1)]

            embed.add_field(name="Active Teams", value="\n".join(active_teams), inline=True)
            embed.add_field(name="Bench Teams", value="\n".join(bench_teams), inline=True)
            embed.add_field(name="League Points", value=f"🏆 {roster.get('points', 0)}", inline=False)
            embed.add_field(name="Swaps Remaining", value=f"🔄 {10 - roster.get('swaps_used', 0)} / 10", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="swap-teams", description="Swap an active team with a bench team.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def swap_teams(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return
            
            if not roster.get('bench_one'):
                view = SetBenchButtonView(self.bot, self.db_pool, interaction.user.id)
                await interaction.followup.send("⚠️ Your registration is incomplete! Please set your bench teams to use this command.", view=view, ephemeral=True)
                return

            if roster.get('swaps_used', 0) >= 10:
                await interaction.followup.send("❌ You have used all 10 of your swaps for the season!", ephemeral=True)
                return

            active_teams = [('team_one', roster['team_one']), ('team_two', roster['team_two']), ('team_three', roster['team_three']), ('team_four', roster['team_four']), ('team_five', roster['team_five'])]
            bench_teams = [('bench_one', roster['bench_one']), ('bench_two', roster['bench_two']), ('bench_three', roster['bench_three'])]
            
            view = SwapView(self.bot, interaction.user.id, self.db_pool, active_teams, bench_teams)
            await interaction.followup.send("Select one active team and one bench team to swap:", view=view, ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="ace-team", description="Select one active team to earn triple points for the week.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ace_team(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return
            
            if not roster.get('bench_one'):
                view = SetBenchButtonView(self.bot, self.db_pool, interaction.user.id)
                await interaction.followup.send("⚠️ Your registration is incomplete! Please set your bench teams to use this command.", view=view, ephemeral=True)
                return
            
            if roster.get('aced_team_slot') is not None:
                aced_team_name = roster.get(roster['aced_team_slot'], "your aced team")
                await interaction.followup.send(f"❌ You have already selected **{aced_team_name}** as your ace for this week. It can be reset by an admin.", ephemeral=True)
                return

            team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
            options = [discord.SelectOption(label=roster[slot], value=slot) for slot in team_slots if roster.get(slot)]
            
            if not options:
                await interaction.followup.send("You don't have any active teams to ace!", ephemeral=True)
                return

            select = ui.Select(placeholder="Choose a team to make your ace...", options=options)

            async def select_callback(callback_interaction: discord.Interaction):
                chosen_slot = select.values[0]
                conn = None
                cur = None
                try:
                    conn = self.db_pool.get_connection()
                    cur = conn.cursor()
                    cur.execute("UPDATE rosters SET aced_team_slot = %s WHERE user_id = %s", (chosen_slot, callback_interaction.user.id))
                    conn.commit()
                    team_name = roster[chosen_slot]
                    await callback_interaction.response.edit_message(content=f"✅ **{team_name}** is now your aced team for the week!", view=None)
                except Exception as e_inner:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                    await callback_interaction.response.edit_message(content="❌ A database error occurred. The issue has been reported.", view=None)
                finally:
                    if cur: cur.close()
                    if conn: conn.close()

            select.callback = select_callback
            view = ui.View(timeout=180)
            view.add_item(select)
            await interaction.followup.send("Select your ace team. This team will earn triple points from all games this week.", view=view, ephemeral=True)
        
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(userLeague(bot))
