# user_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import config
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- UI Modal for Bench Teams (Step 2) ---
# This modal appears after the user submits their active roster.
class SetBenchModal(ui.Modal, title="Set Your Bench Teams (Step 2 of 2)"):
    bench_one = ui.TextInput(label="Bench Team 1", placeholder="Enter NHL Team Name")
    bench_two = ui.TextInput(label="Bench Team 2", placeholder="Enter NHL Team Name")
    bench_three = ui.TextInput(label="Bench Team 3", placeholder="Enter NHL Team Name")

    def __init__(self, db_cursor, db_connection, active_teams: list):
        super().__init__(timeout=300)
        self.cursor = db_cursor
        self.db = db_connection
        self.active_teams = active_teams

    async def on_submit(self, interaction: discord.Interaction):
        """This is the final step. It inserts the complete 8-team roster into the database."""
        bench_teams = [self.bench_one.value, self.bench_two.value, self.bench_three.value]
        
        # Combine active and bench teams for the final database insert
        all_teams = self.active_teams + bench_teams
        
        sql = """
            INSERT INTO rosters (user_id, team_one, team_two, team_three, team_four, team_five, bench_one, bench_two, bench_three)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # The user_id is the first value, followed by all 8 team names
        val = (interaction.user.id, *all_teams)
        
        try:
            self.cursor.execute(sql, val)
            self.db.commit()
            await interaction.response.send_message(
                "🎉 **Welcome to the league!** Your full roster is set. Use `/my_roster` to view it.",
                ephemeral=True
            )
        except mysql.connector.Error as err:
            # Provide a more specific error if a user tries to join twice
            if err.errno == 1062: # Error code for duplicate primary key
                await interaction.response.send_message("❌ You are already in the league!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ A database error occurred: {err}", ephemeral=True)


# --- UI Modal for Active Teams (Step 1) ---
class JoinLeagueModal(ui.Modal, title="Join the League (Step 1 of 2)"):
    team_one = ui.TextInput(label="Active Team 1", placeholder="Enter NHL Team Name")
    team_two = ui.TextInput(label="Active Team 2", placeholder="Enter NHL Team Name")
    team_three = ui.TextInput(label="Active Team 3", placeholder="Enter NHL Team Name")
    team_four = ui.TextInput(label="Active Team 4", placeholder="Enter NHL Team Name")
    team_five = ui.TextInput(label="Active Team 5", placeholder="Enter NHL Team Name")

    def __init__(self, db_cursor, db_connection):
        super().__init__(timeout=300)
        self.cursor = db_cursor
        self.db = db_connection

    async def on_submit(self, interaction: discord.Interaction):
        """This method now transitions to the second modal for bench teams."""
        active_teams = [
            self.team_one.value,
            self.team_two.value,
            self.team_three.value,
            self.team_four.value,
            self.team_five.value
        ]
        
        # Create an instance of the second modal, passing the active teams and DB info
        bench_modal = SetBenchModal(self.cursor, self.db, active_teams)
        
        # Send the second modal to the user
        await interaction.response.send_modal(bench_modal)


# --- UI View for Swapping Teams ---
class SwapView(ui.View):
    def __init__(self, user_id, db_cursor, db_connection, active_teams, bench_teams):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.cursor = db_cursor
        self.db = db_connection
        self.active_selection = None
        self.bench_selection = None

        # Create dropdown for active teams
        active_options = [discord.SelectOption(label=team[1], value=team[0]) for team in active_teams if team[1]]
        self.active_dropdown = ui.Select(placeholder="Choose an active team to swap out...", options=active_options)

        # Create dropdown for bench teams
        bench_options = [discord.SelectOption(label=team[1], value=team[0]) for team in bench_teams if team[1]]
        self.bench_dropdown = ui.Select(placeholder="Choose a bench team to swap in...", options=bench_options)
        
        # Add callbacks
        self.active_dropdown.callback = self.on_active_select
        self.bench_dropdown.callback = self.on_bench_select

        self.add_item(self.active_dropdown)
        self.add_item(self.bench_dropdown)

    async def on_active_select(self, interaction: discord.Interaction):
        self.active_selection = self.active_dropdown.values[0]
        await interaction.response.defer()
        await self.check_and_execute_swap(interaction)

    async def on_bench_select(self, interaction: discord.Interaction):
        self.bench_selection = self.bench_dropdown.values[0]
        await interaction.response.defer()
        await self.check_and_execute_swap(interaction)

    async def check_and_execute_swap(self, interaction: discord.Interaction):
        if self.active_selection and self.bench_selection:
            try:
                # Get the actual team names from the database
                self.cursor.execute(f"SELECT {self.active_selection}, {self.bench_selection} FROM rosters WHERE user_id = {self.user_id}")
                team_names = self.cursor.fetchone()
                active_team_name, bench_team_name = team_names[self.active_selection], team_names[self.bench_selection]

                # Perform the swap and increment swaps_used
                sql = f"""
                    UPDATE rosters
                    SET {self.active_selection} = %s, {self.bench_selection} = %s, swaps_used = swaps_used + 1
                    WHERE user_id = %s
                """
                self.cursor.execute(sql, (bench_team_name, active_team_name, self.user_id))
                self.db.commit()
                
                await interaction.followup.send(f"✅ Swap successful! **{bench_team_name}** is now active, and **{active_team_name}** is on the bench.", ephemeral=True)
                self.stop()

            except mysql.connector.Error as err:
                await interaction.followup.send(f"❌ A database error occurred: {err}", ephemeral=True)
                self.stop()


# --- User Commands Cog ---
class userLeague(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        self.cursor = self.db.cursor(dictionary=True, buffered=True)
        print("User Cog: Database connection established.")

    def get_user_roster(self, user_id: int):
        """Fetches a user's full roster from the database."""
        self.cursor.execute("SELECT * FROM rosters WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    @app_commands.command(name="join_league", description="Sign up for the fantasy league and set your roster.")
    async def join_league(self, interaction: discord.Interaction):
        roster = self.get_user_roster(interaction.user.id)
        if roster:
            await interaction.response.send_message("You are already in the league! Use `/my_roster` to see your teams.", ephemeral=True)
            return
        
        # Start the two-step modal process
        modal = JoinLeagueModal(self.cursor, self.db)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="my_roster", description="View your current team roster, points, and swaps.")
    async def my_roster(self, interaction: discord.Interaction):
        roster = self.get_user_roster(interaction.user.id)
        if not roster:
            await interaction.response.send_message("You haven't joined the league yet! Use `/join_league` to get started.", ephemeral=True)
            return

        embed = discord.Embed(title=f"{interaction.user.display_name}'s Roster", color=discord.Color.green())
        
        active_teams = []
        team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
        for i, slot_name in enumerate(team_slots, 1):
            team_name = roster.get(slot_name, "Empty")
            ace_emoji = " ✨" if roster.get('aced_team_slot') == slot_name else ""
            active_teams.append(f"**{i}.** {team_name}{ace_emoji}")

        bench_teams = []
        bench_slots = ['bench_one', 'bench_two', 'bench_three']
        for i, slot_name in enumerate(bench_slots, 1):
            team_name = roster.get(slot_name, "Empty")
            bench_teams.append(f"**{i}.** {team_name}")

        embed.add_field(name="Active Teams", value="\n".join(active_teams), inline=True)
        embed.add_field(name="Bench Teams", value="\n".join(bench_teams), inline=True)
        embed.add_field(name="League Points", value=f"🏆 {roster.get('points', 0)}", inline=False)
        embed.add_field(name="Swaps Remaining", value=f"🔄 {10 - roster.get('swaps_used', 0)} / 10", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="swap_teams", description="Swap an active team with a bench team.")
    async def swap_teams(self, interaction: discord.Interaction):
        roster = self.get_user_roster(interaction.user.id)
        if not roster:
            await interaction.response.send_message("You haven't joined the league yet!", ephemeral=True)
            return
        if roster['swaps_used'] >= 10:
            await interaction.response.send_message("❌ You have used all 10 of your swaps for the season!", ephemeral=True)
            return

        active_teams = [('team_one', roster['team_one']), ('team_two', roster['team_two']), ('team_three', roster['team_three']), ('team_four', roster['team_four']), ('team_five', roster['team_five'])]
        bench_teams = [('bench_one', roster['bench_one']), ('bench_two', roster['bench_two']), ('bench_three', roster['bench_three'])]
        
        view = SwapView(interaction.user.id, self.cursor, self.db, active_teams, bench_teams)
        await interaction.response.send_message("Select one active team and one bench team to swap:", view=view, ephemeral=True)

    @app_commands.command(name="ace_team", description="Select one active team to earn triple points for the week.")
    async def ace_team(self, interaction: discord.Interaction):
        roster = self.get_user_roster(interaction.user.id)
        if not roster:
            await interaction.response.send_message("You haven't joined the league yet!", ephemeral=True)
            return

        options = []
        team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
        for slot in team_slots:
            if roster.get(slot): # Only show if the slot is not empty
                options.append(discord.SelectOption(label=roster[slot], value=slot))
        
        if not options:
            await interaction.response.send_message("You don't have any active teams set!", ephemeral=True)
            return

        select = ui.Select(placeholder="Choose a team to make your ace...", options=options)

        async def select_callback(interaction: discord.Interaction):
            chosen_slot = select.values[0]
            try:
                self.cursor.execute("UPDATE rosters SET aced_team_slot = %s WHERE user_id = %s", (chosen_slot, interaction.user.id))
                self.db.commit()
                team_name = roster[chosen_slot]
                await interaction.response.edit_message(content=f"✅ **{team_name}** is now your aced team for the week!", view=None)
            except mysql.connector.Error as err:
                await interaction.response.edit_message(content=f"❌ A database error occurred: {err}", view=None)

        select.callback = select_callback
        view = ui.View(timeout=180)
        view.add_item(select)
        await interaction.response.send_message("Select your ace team. This team will earn triple points from all games this week.", view=view, ephemeral=True)

# The setup function to load the cog
async def setup(bot):
    await bot.add_cog(userLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
