import discord
import requests
import config
import pytz
import asyncio
from datetime import datetime
from thefuzz import fuzz
import strategies.base_strategy as base_strategy

class PWHLStrategy(base_strategy.LeagueStrategy):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://lscluster.hockeytech.com/feed/index.php"
        self.base_params = {
            "key": "446521baf8c38984",
            "client_code": "pwhl",
            "fmt": "json"
        }

    # --- INTERFACE EXECUTIONS ---

    async def get_today_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "/league today pwhl")
        try:
            params = {**self.base_params, "feed": "modulekit", "view": "scorebar"}
            data = requests.get(self.base_url, params=params).json()
            games = data.get('SiteKit', {}).get('Scorebar', [])

            if not games:
                return await interaction.followup.send("No PWHL items flagged on the tracking schedule today.")

            embed = discord.Embed(title="PWHL Scoreboard Today", color=0x5D3FD3)
            for g in games:
                status = g.get('period_name', 'Scheduled')
                embed.add_field(
                    name=f"Status: {status}",
                    value=f"{g['visiting_team_name']} ({g['visiting_goal_count']}) @ {g['home_team_name']} ({g['home_goal_count']})",
                    inline=False
                )
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error collecting PWHL feed layers.")

    async def get_standings(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        try:
            params = {**self.base_params, "feed": "modulekit", "view": "statviewtype", "stat": "conference", "type": "standings", "season_id": "5"}
            data = requests.get(self.base_url, params=params).json()
            
            # Extract standings lines out of HockeyTech matrix rows
            records = data.get('SiteKit', {}).get('Statviewtype', [])
            embed = discord.Embed(title="PWHL Standings Overview", color=0x5D3FD3)
            
            lines = []
            for team in records:
                if 'team_name' in team:
                    lines.append(f"**{team['team_name']}** - {team.get('points', 0)}pts ({team.get('wins', 0)}W-{team.get('losses', 0)}L)")

            embed.description = "\n".join(lines) if lines else "Roster details unpopulated for selected season target context."
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Failed to capture standings layer.")

    # --- GAMES LOGIC ATTACHMENTS ---

    async def run_gtp_game(self, interaction: discord.Interaction):
        # PWHL Roster database parsing stub matching strategy pattern blueprint
        params = {**self.base_params, "feed": "modulekit", "view": "roster", "team_id": "3", "season_id": "5"}
        try:
            data = requests.get(self.base_url, params=params).json()
            players = data.get('SiteKit', {}).get('Roster', [])
            if not players: return await interaction.followup.send("Roster parsing context returned empty configuration values.")
            
            p = random.choice(players)
            full_name = f"{p['first_name']} {p['last_name']}"
            
            embed = discord.Embed(title="🎯 PWHL Guess The Player!", description=f"Guess the player from the roster files! Name begins with `{p['first_name'][0]}`", color=0x5D3FD3)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Game generation loop failure.")

    # --- REFRESH STUBS TO SATISFY MANAGER TASKS ---
    async def post_daily_schedule(self, channel): pass
    async def update_live_scores(self): pass
    async def get_schedule(self, interaction, abbrev): pass
    async def get_game_info(self, interaction, abbrev): pass
    async def get_player_info(self, interaction, name): pass
    async def get_all_teams(self, interaction): pass