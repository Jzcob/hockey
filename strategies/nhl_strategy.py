import discord
from discord import app_commands
from discord.ext import commands
import config
from datetime import datetime, timedelta
import requests
import pytz
import traceback
import strategies.base_strategy as base_strategy

TEAM_EMOJIS = {
    "ANA": config.anahiem_ducks_emoji, "BOS": config.boston_bruins_emoji, "BUF": config.buffalo_sabres_emoji,
    "CGY": config.calgary_flames_emoji, "CAR": config.carolina_hurricanes_emoji, "CHI": config.chicago_blackhawks_emoji,
    "COL": config.colorado_avalanche_emoji, "CBJ": config.columbus_blue_jackets_emoji, "DAL": config.dallas_stars_emoji,
    "DET": config.detroit_red_wings_emoji, "EDM": config.edmonton_oilers_emoji, "FLA": config.florida_panthers_emoji,
    "LAK": config.los_angeles_kings_emoji, "MIN": config.minnesota_wild_emoji, "MTL": config.montreal_canadiens_emoji,
    "NSH": config.nashville_predators_emoji, "NJD": config.new_jersey_devils_emoji, "NYI": config.new_york_islanders_emoji,
    "NYR": config.new_york_rangers_emoji, "OTT": config.ottawa_senators_emoji, "PHI": config.philadelphia_flyers_emoji,
    "PIT": config.pittsburgh_penguins_emoji, "SJS": config.san_jose_sharks_emoji, "SEA": config.seattle_kraken_emoji,
    "STL": config.st_louis_blues_emoji, "TBL": config.tampa_bay_lightning_emoji, "TOR": config.toronto_maple_leafs_emoji,
    "UTA": config.utah_hockey_club_emoji, "VAN": config.vancouver_canucks_emoji, "VGK": config.vegas_golden_knights_emoji,
    "WSH": config.washington_capitals_emoji, "WPG": config.winnipeg_jets_emoji,
}

def strings(awayAbbrev, homeAbbrev, home, away):
    a_emoji = TEAM_EMOJIS.get(awayAbbrev, "")
    h_emoji = TEAM_EMOJIS.get(homeAbbrev, "")
    return f"{a_emoji} {away}".lstrip(), f"{home} {h_emoji}".rstrip()

# By inheriting from GroupCog, all commands in this class start with /nhl
class NHL(commands.GroupCog, base_strategy.LeagueStrategy, name="nhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # --- DISCORD COMMANDS ---

    @app_commands.command(name="today", description="Get today's NHL schedule and scores")
    async def today_cmd(self, interaction: discord.Interaction):
        await self.get_today_games(interaction)

    @app_commands.command(name="yesterday", description="Get yesterday's NHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)
    
    @app_commands.command(name="standings", description="Get the NHL standings")
    async def standings_cmd(self, interaction: discord.Interaction):
        await self.get_standings(interaction)
    
    @app_commands.command(name="schedule", description="Get the schedule for the week for an NHL team! (e.g. BOS, NYR, etc.)")
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_schedule(interaction, abbreviation)
    
    @app_commands.command(name="game", description="Get information about an NHL game for a team (use NHL or Intl codes)")
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_game_info(interaction, abbreviation)
    
    @app_commands.command(name="player", description="Get information about an NHL player")
    async def player_cmd(self, interaction: discord.Interaction, name: str):
        await self.get_player_info(interaction, name)
    
    @app_commands.command(name="team", description="Get information about an NHL team")
    async def team_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_team_info(interaction, abbreviation)
    
    @app_commands.command(name="teams", description="Get a list of all NHL teams and their abbreviations")
    async def teams_cmd(self, interaction: discord.Interaction):
        await self.get_all_teams(interaction)
    
    

    # --- STRATEGY LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction):
        base_strategy.log_command(self.bot, interaction, "nhl today")
        await interaction.response.defer()
        try:
            hawaii = pytz.timezone('US/Hawaii')
            t_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{t_str}"
            
            r = requests.get(url)
            data = r.json()
            
            if not data["gameWeek"] or not data["gameWeek"][0]["games"]:
                embed = discord.Embed(title="Today's Games", description="No games scheduled for today.", color=config.color)
                embed.set_footer(text=config.footer)
                await interaction.followup.send(embed=embed)
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Today's Games", description=f"Total games today: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            for game in games:
                gs = game["gameState"]
                h_t, a_t = game["homeTeam"], game["awayTeam"]
                
                h_name = h_t.get("placeName", {}).get("default") or h_t.get("commonName", {}).get("default", "TBD")
                a_name = a_t.get("placeName", {}).get("default") or a_t.get("commonName", {}).get("default", "TBD")
                
                a_str, h_str = strings(a_t["abbrev"], h_t["abbrev"], h_name, a_name)
                utc_start = datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                ts = int(utc_start.timestamp())

                if gs in ("FUT", "PRE"):
                    embed.add_field(name=f"<t:{ts}:t>", value=f"{a_str} @ {h_str}\nGame is scheduled!", inline=False)
                
                elif gs in ("FINAL", "OFF"):
                    outcome = game.get("gameOutcome", {}).get("lastPeriodType", "REG")
                    status = "Final"
                    if outcome == "OT": status = "Final (OT)"
                    elif outcome == "SO": status = "Final (SO)"
                    embed.add_field(name=status, value=f"{a_str} @ {h_str}\nScore: {a_t.get('score',0)} | {h_t.get('score',0)}", inline=False)

                elif gs in ("LIVE", "CRIT"):
                    try:
                        r2 = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game['id']}/boxscore")
                        g2 = r2.json()
                        clock = g2.get('clock', {})
                        period = game.get('periodDescriptor', {}).get('number')
                        period_ord = {1: "1st", 2: "2nd", 3: "3rd", 4: "OT"}.get(period, f"P{period}")
                        
                        if clock.get('inIntermission'):
                            status = "Intermission"
                        else:
                            time_rem = clock.get('timeRemaining', '00:00')
                            status = f"🔴 LIVE - {period_ord}"
                            a_str = f"{a_str}\nScore: {a_t.get('score',0)} | {h_t.get('score',0)}\n`{time_rem}`"
                        
                        embed.add_field(name=status, value=f"{a_str} @ {h_str}" if "LIVE" not in status else a_str, inline=False)
                    except:
                        embed.add_field(name="🔴 LIVE", value=f"{a_str} @ {h_str}\nScore: {a_t.get('score',0)} | {h_t.get('score',0)}", inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("Error fetching schedule.")

    async def get_yesterday_games(self, interaction: discord.Interaction):
        base_strategy.log_command(self.bot, interaction, "nhl yesterday")
        await interaction.response.defer()
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            y_date = (datetime.now(hawaii_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://api-web.nhle.com/v1/schedule/{y_date}"
            
            r = requests.get(url)
            data = r.json()

            if not data.get("gameWeek") or not data["gameWeek"][0].get("games"):
                await interaction.followup.send(embed=discord.Embed(title="Yesterday's Games", description="No games yesterday.", color=config.color))
                return

            games = data["gameWeek"][0]["games"]
            embed = discord.Embed(title=f"Yesterday's Games ({y_date})", description=f"Total games: {len(games)}", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            embed.set_footer(text=config.footer)

            for game in games:
                h_t, a_t = game["homeTeam"], game["awayTeam"]
                h_name = h_t.get("placeName", {}).get("default") or h_t.get("commonName", {}).get("default", "TBD")
                a_name = a_t.get("placeName", {}).get("default") or a_t.get("commonName", {}).get("default", "TBD")
                
                a_str, h_str = strings(a_t["abbrev"], h_t["abbrev"], h_name, a_name)
                
                outcome = game.get("gameOutcome", {}).get("lastPeriodType", "REG")
                status = "Final"
                if outcome == "OT": status = "Final (OT)"
                elif outcome == "SO": status = "Final (SO)"

                embed.add_field(
                    name=status,
                    value=f"{a_str} @ {h_str}\nScore: {a_t.get('score',0)} | {h_t.get('score',0)}",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
        except Exception:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send("Error occurred.", ephemeral=True)

    # --- Abstract Method Implementations ---
    async def get_standings(self, interaction: discord.Interaction): pass
    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_player_info(self, interaction: discord.Interaction, player_name: str): pass
    async def get_team_info(self, interaction: discord.Interaction, team_abbreviation: str): pass
    async def get_all_teams(self, interaction: discord.Interaction): pass
    async def get_tomorrow_games(self, interaction: discord.Interaction): pass
    async def set_schedule_channel(self, interaction: discord.Interaction, channel_id: int): pass
    async def remove_schedule_channel(self, interaction: discord.Interaction): pass
    async def post_daily_schedule(self): pass
    async def get_playoff_bracket(self, interaction: discord.Interaction): pass

async def setup(bot):
    await bot.add_cog(NHL(bot))