import discord
from discord.ext import commands
from discord import app_commands, ui
import mysql.connector
import config # Your config file with DB credentials

# --- UI Modal for Joining the League ---
class JoinLeagueModal(ui.Modal, title="Join the Hockey League"):
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
        # This is a simplified version. A real implementation should have 3 more fields
        # for bench teams, but modals are limited to 5 inputs.
        # A multi-step view or separate command would be needed for the bench.
        sql = """
            INSERT INTO rosters (user_id, team_one, team_two, team_three, team_four, team_five)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        val = (interaction.user.id, self.team_one.value, self.team_two.value, self.team_three.value, self.team_four.value, self.team_five.value)
        try:
            self.cursor.execute(sql, val)
            self.db.commit()
            await interaction.response.send_message("🎉 Welcome to the league! Your active roster is set. Use `/set_bench` to add your bench teams.", ephemeral=True)
        except mysql.connector.Error as err:
            await interaction.response.send_message(f"❌ An error occurred: {err}", ephemeral=True)


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
                active_team_name, bench_team_name = team_names[0], team_names[1]

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
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        self.cursor = self.db.cursor(dictionary=True, buffered=True) # Use dictionary cursor for easy data access
        print("User Cog: Database connection established.")

    def get_user_roster(self, user_id: int):
        """Fetches a user's full roster from the database."""
        self.cursor.execute("SELECT * FROM rosters WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    @app_commands.command(name="join_league", description="Sign up for the fantasy league and set your active teams.")
    async def join_league(self, interaction: discord.Interaction):
        roster = self.get_user_roster(interaction.user.id)
        if roster:
            await interaction.response.send_message("You are already in the league! Use `/my_roster` to see your teams.", ephemeral=True)
            return
        # Note: Modals are limited to 5 fields. A proper solution for 8 teams would be a multi-step view.
        # This modal will just set the first 5.
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
        for i in range(1, 6):
            slot_name = f"team_{'one' if i==1 else 'two' if i==2 else 'three' if i==3 else 'four' if i==4 else 'five'}"
            team_name = roster.get(slot_name, "Empty")
            ace_emoji = " ✨" if roster.get('aced_team_slot') == slot_name else ""
            active_teams.append(f"**{i}.** {team_name}{ace_emoji}")

        bench_teams = []
        for i in range(1, 4):
            slot_name = f"bench_{'one' if i==1 else 'two' if i==2 else 'three'}"
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

    @app_commands.command(name="ace_team", description="Select one active team to earn double points for the week.")
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
        await interaction.response.send_message("Select your ace team. This team will earn double points from all games this week.", view=view, ephemeral=True)

# The setup function to load the cog
async def setup(bot):
    await bot.add_cog(userLeague(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
