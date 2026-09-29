# user_cog.py
import discord
from discord.ext import commands
from discord import app_commands, ui
import aiomysql
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
        if not (self.active_selection and self.bench_selection):
            return

        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    
                    await cursor.execute(f"SELECT `{self.active_selection}`, `{self.bench_selection}` FROM rosters WHERE user_id = %s", (self.user_id,))
                    team_names = await cursor.fetchone()
                    
                    if not team_names:
                        if not interaction.is_expired(): await interaction.followup.send("❌ Could not find your roster to perform the swap.", ephemeral=True)
                        self.stop()
                        return
                        
                    active_team_name = team_names[self.active_selection]
                    bench_team_name = team_names[self.bench_selection]

                    sql = f"UPDATE rosters SET `{self.active_selection}` = %s, `{self.bench_selection}` = %s, swaps_used = swaps_used + 1 WHERE user_id = %s"
                    await cursor.execute(sql, (bench_team_name, active_team_name, self.user_id))
            
            if not interaction.is_expired(): await interaction.followup.send(f"✅ Swap successful! **{bench_team_name}** is now active, and **{active_team_name}** is on the bench.", ephemeral=True)
            
            for item in self.children:
                item.disabled = True
            if not interaction.is_expired(): await interaction.edit_original_response(view=self)
            self.stop()

        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("❌ A database error occurred. The issue has been reported.", ephemeral=True)
            self.stop()

# --- User Commands Cog ---
class userLeague(commands.Cog, name="userLeague"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_pool = bot.db_pool
        print("User Cog: Database pool is accessible.")
            
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `user_cog.py`")

    async def get_user_roster_async(self, user_id: int):
        """Asynchronously fetches a user's roster."""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT * FROM rosters WHERE user_id = %s", (user_id,))
                    return await cursor.fetchone()
        except Exception as err:
            print(f"Error in get_user_roster_async for {user_id}: {err}")
            return None

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                if command_log_channel:
                    guild_name = interaction.guild.name if interaction.guild else "DMs"
                    await command_log_channel.send(f"`/{interaction.command.name}` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except Exception as e:
                print(f"Command logging failed for /{interaction.command.name}: {e}")

    @app_commands.command(name="my-roster", description="View your current team roster, points, and swaps.")
    async def my_roster(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        await interaction.response.defer(ephemeral=True)
        try:
            roster = await self.get_user_roster_async(interaction.user.id)

            if not roster:
                if not interaction.is_expired(): await interaction.followup.send("You haven't joined the league yet! Use `/join-league` to get started.", ephemeral=True)
                return

            embed = discord.Embed(title=f"{interaction.user.display_name}'s Roster", color=discord.Color.green())
            
            active_teams = [f"**{i}.** {roster.get(slot, 'Empty')}{' ✨' if roster.get('aced_team_slot') == slot else ''}" for i, slot in enumerate(['team_one', 'team_two', 'team_three', 'team_four', 'team_five'], 1)]
            bench_teams = [f"**{i}.** {roster.get(slot, 'Empty')}" for i, slot in enumerate(['bench_one', 'bench_two', 'bench_three'], 1)]

            embed.add_field(name="Active Teams", value="\n".join(active_teams), inline=True)
            embed.add_field(name="Bench Teams", value="\n".join(bench_teams), inline=True)
            embed.add_field(name="League Points", value=f"🏆 {roster.get('points', 0)}", inline=False)
            embed.add_field(name="Swaps Remaining", value=f"🔄 {10 - roster.get('swaps_used', 0)} / 10", inline=False)

            if not interaction.is_expired(): await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="swap-teams", description="Swap an active team with a bench team.")
    async def swap_teams(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        await interaction.response.defer(ephemeral=True) # Defer immediately
        try:
            roster = await self.get_user_roster_async(interaction.user.id)
            if not roster:
                if not interaction.is_expired(): await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return
            
            if roster.get('swaps_used', 0) >= 10:
                if not interaction.is_expired(): await interaction.followup.send("❌ You have used all 10 of your swaps for the season!", ephemeral=True)
                return

            active_teams = [('team_one', roster['team_one']), ('team_two', roster['team_two']), ('team_three', roster['team_three']), ('team_four', roster['team_four']), ('team_five', roster['team_five'])]
            bench_teams = [('bench_one', roster['bench_one']), ('bench_two', roster['bench_two']), ('bench_three', roster['bench_three'])]
            
            view = SwapView(self.bot, interaction.user.id, self.db_pool, active_teams, bench_teams)
            if not interaction.is_expired(): await interaction.followup.send("Select one active team and one bench team to swap:", view=view, ephemeral=True)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @app_commands.command(name="ace-team", description="Select one active team to earn triple points for the week.")
    async def ace_team(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        await interaction.response.defer(ephemeral=True) # Defer immediately
        try:
            roster = await self.get_user_roster_async(interaction.user.id)
            if not roster:
                if not interaction.is_expired(): await interaction.followup.send("You haven't joined the league yet!", ephemeral=True)
                return
            
            if roster.get('aced_team_slot') is not None:
                aced_team_name = roster.get(roster['aced_team_slot'], "your aced team")
                if not interaction.is_expired(): await interaction.followup.send(f"❌ You have already selected **{aced_team_name}** as your ace for this week. It can be reset by a league admin.", ephemeral=True)
                return

            team_slots = ['team_one', 'team_two', 'team_three', 'team_four', 'team_five']
            options = [discord.SelectOption(label=roster[slot], value=slot) for slot in team_slots if roster.get(slot)]
            
            if not options:
                if not interaction.is_expired(): await interaction.followup.send("You don't have any active teams to ace!", ephemeral=True)
                return

            select = ui.Select(placeholder="Choose a team to make your ace...", options=options)

            async def select_callback(callback_interaction: discord.Interaction):
                chosen_slot = select.values[0]
                
                team_name = "your aced team" # Default
                for option in select.options:
                    if option.value == chosen_slot:
                        team_name = option.label
                        break

                await callback_interaction.response.defer() # Defer here

                try:
                    async with self.db_pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("UPDATE rosters SET aced_team_slot = %s WHERE user_id = %s", (chosen_slot, callback_interaction.user.id))
                    
                    await callback_interaction.edit_original_response(content=f"✅ **{team_name}** is now your aced team for the week!", view=None)
                
                except Exception:
                    error_channel = self.bot.get_channel(config.error_channel)
                    if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
                    
                    if not callback_interaction.is_expired():
                        await callback_interaction.edit_original_response(content="❌ A database error occurred. The issue has been reported.", view=None)

            select.callback = select_callback
            view = ui.View(timeout=180)
            view.add_item(select)
            if not interaction.is_expired(): await interaction.followup.send("Select your ace team. This team will earn triple points from all games this week.", view=view, ephemeral=True)
        
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel: await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            if not interaction.is_expired(): await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(userLeague(bot))

