import discord
from discord.ext import commands
from discord import app_commands
import requests
from datetime import datetime, timedelta
import config
import pytz
import traceback

class GameStatsView(discord.ui.View):
    def __init__(self, boxscore_data, pbp_data, original_embed, game_state):
        super().__init__(timeout=300)
        self.boxscore_data = boxscore_data
        self.pbp_data = pbp_data
        self.original_embed = original_embed
        
        # FIX: Fallback for team names in buttons
        self.away_team_abbrev = boxscore_data.get('awayTeam', {}).get('abbrev', 'AWAY')
        self.home_team_abbrev = boxscore_data.get('homeTeam', {}).get('abbrev', 'HOME')

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        team_data = self.boxscore_data['awayTeam'] if team_type == 'away' else self.boxscore_data['homeTeam']
        stats_data = self.boxscore_data.get('playerByGameStats', {}).get(f'{team_type}Team', {})
        
        # FIX: Universal name check
        display_name = team_data.get('commonName', {}).get('default') or team_data.get('placeName', {}).get('default', 'Team')
        
        embed = discord.Embed(title=f"{display_name} Roster", color=self.original_embed.color)
        embed.set_thumbnail(url=team_data.get('logo'))

        try:
            def fmt(p): return f"#{p['sweaterNumber']} {p['name']['default']} ({p.get('goals',0)}G, {p.get('assists',0)}A)"
            fwd = "\n".join([fmt(p) for p in stats_data.get('forwards', [])])
            dfe = "\n".join([fmt(p) for p in stats_data.get('defense', [])])
            embed.add_field(name="Forwards", value=fwd[:1024] if fwd else "N/A", inline=False)
            embed.add_field(name="Defense", value=dfe[:1024] if dfe else "N/A", inline=False)
        except Exception: embed.description = "Stats not available."
        return embed

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.primary)
    async def summary_button(self, interaction, button): await interaction.response.edit_message(embed=self.original_embed)

    @discord.ui.button(label="Away Roster", style=discord.ButtonStyle.secondary)
    async def away_roster_button(self, interaction, button): await interaction.response.edit_message(embed=self._build_roster_embed('away'))

    @discord.ui.button(label="Home Roster", style=discord.ButtonStyle.secondary)
    async def home_roster_button(self, interaction, button): await interaction.response.edit_message(embed=self._build_roster_embed('home'))

class game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="game", description="Check game info for a team (NHL or Intl codes)")
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await interaction.response.defer()
        abbrev = abbreviation.upper()
        
        # ADDED INTL CODES TO MAPPING
        teams = {
            "ANA": "Anaheim Ducks", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres",
            "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes", "CHI": "Chicago Blackhawks",
            "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets", "DAL": "Dallas Stars",
            "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers",
            "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "MTL": "Montreal Canadiens",
            "NSH": "Nashville Predators", "NJD": "New Jersey Devils", "NYI": "New York Islanders",
            "NYR": "New York Rangers", "OTT": "Ottawa Senators", "PHI": "Philadelphia Flyers",
            "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks", "SEA": "Seattle Kraken",
            "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs",
            "UTA": "Utah Hockey Club", "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights",
            "WSH": "Washington Capitals", "WPG": "Winnipeg Jets",
            "USA": "USA", "CAN": "Canada", "SWE": "Sweden", "FIN": "Finland", 
            "SVK": "Slovakia", "LAT": "Latvia", "GER": "Germany", "ITA": "Italy",
            "CZE": "Czechia", "SUI": "Switzerland", "DEN": "Denmark", "FRA": "France"
        }

        if abbrev not in teams:
            await interaction.followup.send("Invalid team. Use NHL or Olympic codes.")
            return

        hawaii = pytz.timezone('US/Hawaii')
        today = datetime.now(hawaii).strftime('%Y-%m-%d')
        url = f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/{today}'
        
        r = requests.get(url)
        data = r.json()
        games = data.get('games', [])
        game_data = next((g for g in games if g.get('gameDate') == today), None)

        if not game_data:
            await interaction.followup.send(f"**{teams[abbrev]}** doesn't play today.")
            return

        g_id = game_data['id']
        b_url = f"https://api-web.nhle.com/v1/gamecenter/{g_id}/boxscore"
        p_url = f"https://api-web.nhle.com/v1/gamecenter/{g_id}/play-by-play"
        
        b_data = requests.get(b_url).json()
        p_data = requests.get(p_url).json()

        # FIX: Use universal name logic
        h_t, a_t = b_data['homeTeam'], b_data['awayTeam']
        h_n = h_t.get('commonName', {}).get('default') or h_t.get('placeName', {}).get('default', 'Home')
        a_n = a_t.get('commonName', {}).get('default') or a_t.get('placeName', {}).get('default', 'Away')

        embed = discord.Embed(title=f"{a_n} @ {h_n}", color=config.color)
        embed.add_field(name="Status", value=b_data.get('gameState', 'FUT'))
        embed.add_field(name="Score", value=f"{a_t.get('score',0)} - {h_t.get('score',0)}")
        
        view = GameStatsView(b_data, p_data, embed, b_data.get('gameState'))
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(game(bot))