import discord
import requests
import config
import strategies.base_strategy as base_strategy

class PWHLStrategy(base_strategy.LeagueStrategy):
    def __init__(self, bot):
        self.bot = bot
        # PWHL LeagueStat/HockeyTech Base URL
        self.base_url = "https://lscluster.hockeytech.com/feed/index.php"
        self.params = {
            "feed": "modulekit",
            "view": "scorebar", # For today's games
            "key": "6917a1f2e052cc7a", # Example PWHL Key
            "fmt": "json",
            "client_code": "pwhl"
        }

    async def get_today_games(self, interaction: discord.Interaction):
        # 1. Log the command using your base_strategy utility
        base_strategy.log_command(self.bot, interaction, "/league today pwhl")
        await interaction.response.defer()

        try:
            # 2. Fetch data from HockeyTech Scorebar
            r = requests.get(self.base_url, params=self.params)
            data = r.json()
            
            # The PWHL API returns games in a slightly different structure
            games = data.get('SiteKit', {}).get('Scorebar', [])

            if not games:
                return await interaction.followup.send("No PWHL games scheduled for today.")

            embed = discord.Embed(title="Today's PWHL Games", color=0x5D3FD3) # Purple for PWHL
            
            for game in games:
                home = game['home_team_name']
                away = game['visiting_team_name']
                h_score = game['home_goal_count']
                a_score = game['visiting_goal_count']
                status = game['period_name'] # e.g., "1st", "Final"
                
                embed.add_field(
                    name=f"{status}",
                    value=f"{away} ({a_score}) @ {home} ({h_score})",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send("Error fetching PWHL data.")

    # Implement other abstract methods (standings, player, etc.)
    async def get_standings(self, interaction): pass
    async def get_schedule(self, interaction, abbrev): pass
    async def get_game_info(self, interaction, abbrev): pass
    async def get_player_info(self, interaction, name): pass
    async def get_team_info(self, interaction, abbrev): pass
    async def get_all_teams(self, interaction): pass
    async def get_tomorrow_games(self, interaction): pass
    async def get_yesterday_games(self, interaction): pass
    async def set_schedule_channel(self, interaction, channel_id): pass
    async def remove_schedule_channel(self, interaction): pass
    async def post_daily_schedule(self): pass
    async def get_playoff_bracket(self, interaction): pass