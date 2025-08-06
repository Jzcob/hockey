# user_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import os
from dotenv import load_dotenv
import config
from datetime import datetime
import traceback

# Load environment variables from .env file
load_dotenv()

# --- UI Modal for Bench Teams (Step 2) ---
class SetBenchModal(ui.Modal, title="Set Your Bench Teams (Step 2 of 2)"):
    bench_one = ui.TextInput(label="Bench Team 1", placeholder="Enter NHL Team Name")
    bench_two = ui.TextInput(label="Bench Team 2", placeholder="Enter NHL Team Name")
    bench_three = ui.TextInput(label="Bench Team 3", placeholder="Enter NHL Team Name")

    def __init__(self, bot, db_cursor, db_connection, active_teams: list):
        super().__init__(timeout=300)
        self.bot = bot
        self.cursor = db_cursor
        self.db = db_connection
        self.active_teams = active_teams

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bench_teams = [self.bench_one.value, self.bench_two.value, self.bench_three.value]
            all_teams = self.active_teams + bench_teams

            # --- VALIDATION: Check for duplicate teams across all 8 picks ---
            if len(set(all_teams)) != len(all_teams):
                await interaction.response.send_message("❌ You cannot select the same team more than once. Please start over with `/join_league`.", ephemeral=True)
                # Clean up the partial entry
                try:
                    self.cursor.execute("DELETE FROM rosters WHERE user_id = %s", (interaction.user.id,))
                    self.db.commit()
                except mysql.connector.Error as cleanup_err:
                    print(f"Failed to clean up partial entry for user {interaction.user.id}: {cleanup_err}")
                return

            sql = "UPDATE rosters SET bench_one = %s, bench_two = %s, bench_three = %s WHERE user_id = %s"
            val = (self.bench_one.value, self.bench_two.value, self.bench_three.value, interaction.user.id)
            
            self.cursor.execute(sql, val)
            self.db.commit()
            await interaction.response.edit_message(
                content="🎉 **Welcome to the league!** Your full roster is set. Use `/my_roster` to view it.",
                view=None
            )
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.response.is_done():
                await interaction.response.edit_message(content="❌ An error occurred. The issue has been reported.", view=None)
            else:
                await interaction.followup.send("❌ An error occurred. The issue has been reported.", ephemeral=True)


# --- UI View with Button to Trigger Step 2 ---
class SetBenchButtonView(ui.View):
    def __init__(self, bot, db_cursor, db_connection):
        super().__init__(timeout=300)
        self.bot = bot
        self.cursor = db_cursor
        self.db = db_connection

    @ui.button(label="Set Bench Teams", style=discord.ButtonStyle.success)
    async def set_bench(self, interaction: discord.Interaction, button: ui.Button):
        try:
            self.cursor.execute("SELECT team_one, team_two, team_three, team_four, team_five FROM rosters WHERE user_id = %s", (interaction.user.id,))
            roster = self.cursor.fetchone()
            if roster:
                active_teams = list(roster.values())
                modal = SetBenchModal(self.bot, self.cursor, self.db, active_teams)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Could not find your active roster. Please try `/join_league` again.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message("❌ An error occurred. The issue has been reported.", ephemeral=True)


# --- UI Modal for Active Teams (Step 1) ---
class JoinLeagueModal(ui.Modal, title="Join the League (Step 1 of 2)"):
    team_one = ui.TextInput(label="Active Team 1", placeholder="Enter NHL Team Name")
    team_two = ui.TextInput(label="Active Team 2", placeholder="Enter NHL Team Name")
    team_three = ui.TextInput(label="Active Team 3", placeholder="Enter NHL Team Name")
    team_four = ui.TextInput(label="Active Team 4", placeholder="Enter NHL Team Name")
    team_five = ui.TextInput(label="Active Team 5", placeholder="Enter NHL Team Name")

    def __init__(self, bot, db_cursor, db_connection):
        super().__init__(timeout=300)
        self.bot = bot
        self.cursor = db_cursor
        self.db = db_connection

    async def on_submit(self, interaction: discord.Interaction):
        try:
            active_teams = [self.team_one.value, self.team_two.value, self.team_three.value, self.team_four.value, self.team_five.value]

            # --- VALIDATION: Check for duplicate active teams ---
            if len(set(active_teams)) != len(active_teams):
                await interaction.response.send_message("❌ You cannot select the same active team more than once. Please try again.", ephemeral=True)
                return

            sql = "INSERT INTO rosters (user_id, team_one, team_two, team_three, team_four, team_five) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (interaction.user.id, *active_teams)
            
            self.cursor.execute(sql, val)
            self.db.commit()
            
            view = SetBenchButtonView(self.bot, self.cursor, self.db)
            await interaction.response.send_message(
                "✅ Active roster saved! Click the button below to set your bench teams.",
                view=view,
                ephemeral=True
            )
        except mysql.connector.Error as err:
            if err.errno == 1062: # Duplicate entry
                await interaction.response.send_message("❌ You are already in the league!", ephemeral=True)
            else:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.response.send_message(f"❌ An error occurred while setting your teams. The issue has been reported.", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.response.send_message(f"❌ An error occurred. The issue has been reported.", ephemeral=True)

# --- UI View for Swapping Teams ---
class SwapView(ui.View):
    def __init__(self, bot, user_id, db_cursor, db_connection, active_teams, bench_teams):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.cursor = db_cursor
        self.db = db_connection
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
            try:
                # First, get the names of the teams being swapped
                self.cursor.execute(f"SELECT {self.active_selection}, {self.bench_selection} FROM rosters WHERE user_id = {self.user_id}")
                team_names = self.cursor.fetchone()
                active_team_name = team_names[self.active_selection]
                bench_team_name = team_names[self.bench_selection]

                # Now, perform the swap
                sql = f"UPDATE rosters SET {self.active_selection} = %s, {self.bench_selection} = %s, swaps_used = swaps_used + 1 WHERE user_id = %s"
                self.cursor.execute(sql, (bench_team_name, active_team_name, self.user_id))
                self.db.commit()
                
                await interaction.followup.send(f"✅ Swap successful! **{bench_team_name}** is now active, and **{active_team_name}** is on the bench.", ephemeral=True)
                # Disable the view after a successful swap
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self)
                self.stop()

            except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                await interaction.followup.send("❌ A database error occurred. The issue has been reported.", ephemeral=True)
                self.stop()


# --- User Commands Cog ---
class userLeague(commands.Cog):
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
            print("User Cog: Database connection established.")
        except mysql.connector.Error as err:
            print(f"FAILED to connect to database in User Cog: {err}")
            
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `user_cog.py`")

    def get_user_roster(self, user_id: int):
        """Fetches a user's full roster from the database."""
        self.cursor.execute("SELECT * FROM rosters WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    @app_commands.command(name="league_leaderboard", description="Displays the top 10 players in the league.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def leaderboard(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/league_leaderboard` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /league_leaderboard: {e}")
        
        try:
            await interaction.response.defer()
            self.cursor.execute("SELECT user_id, points FROM rosters ORDER BY points DESC LIMIT 10")
            leaders = self.cursor.fetchall()

            if not leaders:
                await interaction.followup.send("There are no players on the leaderboard yet!")
                return

            embed = discord.Embed(title="🏆 League Leaderboard", color=discord.Color.gold())
            description = []
            for rank, leader in enumerate(leaders, 1):
                try:
                    user = await self.bot.fetch_user(leader['user_id'])
                    user_name = user.display_name
                except discord.errors.NotFound:
                    user_name = f"Unknown User ({leader['user_id']})"
                
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                description.append(f"{rank_emoji} {user_name} - **{leader['points']}** points")
            
            embed.description = "\n".join(description)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)


    @app_commands.command(name="join_league", description="Sign up for the fantasy league and set your roster.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def join_league(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/join_league` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /join_league: {e}")

        try:
            roster = self.get_user_roster(interaction.user.id)
            if roster:
                await interaction.response.send_message("You are already in the league! Use `/my_roster` to see your teams.", ephemeral=True)
                return
            
            modal = JoinLeagueModal(self.bot, self.cursor, self.db)
            await interaction.response.send_modal(modal)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred. The issue has been reported.", ephemeral=True)
            else:
                await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="my_roster", description="View your current team roster, points, and swaps.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def my_roster(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/my_roster` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /my_roster: {e}")

        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet! Use `/join_league` to get started.", ephemeral=True)
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

    @app_commands.command(name="swap_teams", description="Swap an active team with a bench team.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def swap_teams(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/swap_teams` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /swap_teams: {e}")

        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return
            if roster.get('swaps_used', 0) >= 10:
                await interaction.followup.send("❌ You have used all 10 of your swaps for the season!", ephemeral=True)
                return

            active_teams = [('team_one', roster['team_one']), ('team_two', roster['team_two']), ('team_three', roster['team_three']), ('team_four', roster['team_four']), ('team_five', roster['team_five'])]
            bench_teams = [('bench_one', roster['bench_one']), ('bench_two', roster['bench_two']), ('bench_three', roster['bench_three'])]
            
            view = SwapView(self.bot, interaction.user.id, self.cursor, self.db, active_teams, bench_teams)
            await interaction.followup.send("Select one active team and one bench team to swap:", view=view, ephemeral=True)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="ace_team", description="Select one active team to earn triple points for the week.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ace_team(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(f"`/ace_team` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /ace_team: {e}")

        try:
            await interaction.response.defer(ephemeral=True)
            roster = self.get_user_roster(interaction.user.id)
            if not roster:
                await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return

            team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
            options = [discord.SelectOption(label=roster[slot], value=slot) for slot in team_slots if roster.get(slot)]
            
            if not options:
                await interaction.followup.send("You don't have any active teams to ace!", ephemeral=True)
                return

            select = ui.Select(placeholder="Choose a team to make your ace...", options=options)

            async def select_callback(callback_interaction: discord.Interaction):
                chosen_slot = select.values[0]
                try:
                    self.cursor.execute("UPDATE rosters SET aced_team_slot = %s WHERE user_id = %s", (chosen_slot, callback_interaction.user.id))
                    self.db.commit()
                    team_name = roster[chosen_slot]
                    await callback_interaction.response.edit_message(content=f"✅ **{team_name}** is now your aced team for the week!", view=None)
                except Exception as e:
                    error_channel = self.bot.get_channel(config.error_channel)
                    await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                    await callback_interaction.response.edit_message(content="❌ A database error occurred. The issue has been reported.", view=None)

            select.callback = select_callback
            view = ui.View(timeout=180)
            view.add_item(select)
            await interaction.followup.send("Select your ace team. This team will earn triple points from all games this week.", view=view, ephemeral=True)
        
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

# The setup function to load the cog
async def setup(bot):
    await bot.add_cog(userLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
