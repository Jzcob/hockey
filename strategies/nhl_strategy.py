import discord
from discord import app_commands
from discord.ext import commands
import config
from datetime import datetime, timedelta
import requests
import pytz
import traceback
import json
import asyncio
from thefuzz import fuzz
import strategies.base_strategy as base_strategy
import random

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

async def nhl_team_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = []
    try:
        with open("teams.json", "r", encoding="utf-8") as f:
            teams_data = json.load(f)
        for abbr, name in teams_data.items():
            if current.lower() in name.lower() or current.lower() in abbr.lower():
                choices.append(app_commands.Choice(name=f"{name} ({abbr})", value=abbr))
    except Exception:
        pass
    return choices[:25]


class GameStatsView(discord.ui.View):
    def __init__(self, boxscore_data, original_embed):
        super().__init__(timeout=300)
        self.boxscore_data = boxscore_data
        self.original_embed = original_embed
        self.away_team_abbrev = boxscore_data.get('awayTeam', {}).get('abbrev', 'AWAY')
        self.home_team_abbrev = boxscore_data.get('homeTeam', {}).get('abbrev', 'HOME')

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        team_data = self.boxscore_data['awayTeam'] if team_type == 'away' else self.boxscore_data['homeTeam']
        stats_data = self.boxscore_data.get('playerByGameStats', {}).get(f'{team_type}Team', {})
        display_name = team_data.get('commonName', {}).get('default') or team_data.get('placeName', {}).get('default', 'Team')

        embed = discord.Embed(title=f"{display_name} Roster Stats", color=self.original_embed.color)
        embed.set_thumbnail(url=team_data.get('logo'))

        try:
            def fmt(p): return f"#{p['sweaterNumber']} {p['name']['default']} ({(p.get('goals') or 0)}G, {(p.get('assists') or 0)}A)"
            fwd = "\n".join([fmt(p) for p in stats_data.get('forwards', [])])
            dfe = "\n".join([fmt(p) for p in stats_data.get('defense', [])])
            def goalies_fmt(p):
                name = p.get('name', {}).get('default', 'Unknown')
                number = p.get('sweaterNumber', '?')
                toi = p.get('toi', '00:00')
                try:
                    minutes, seconds = map(int, toi.split(':'))
                    total_seconds = minutes * 60 + seconds
                except (ValueError, TypeError, AttributeError):
                    total_seconds = 0
                if total_seconds > 0:
                    goals_against = p.get('goalsAgainst', 0)
                    gaa = f"{goals_against * 3600 / total_seconds:.2f}"
                    save_pct = p.get('savePctg')
                    sv_pct = f"{save_pct:.3f}" if save_pct is not None else 'N/A'
                    saves = p.get('saves', 'N/A')
                    shots = p.get('shotsAgainst', 'N/A')
                    return f"#{number} {name} (GAA: {gaa}, SV%: {sv_pct}, Saves: {saves}/{shots})"
                return f"#{number} {name} (GAA: N/A, SV%: N/A, Saves: N/A)"
            goalies = "\n".join([goalies_fmt(p) for p in stats_data.get('goalies', [])])
            embed.add_field(name="Forwards", value=fwd[:1024] if fwd else "N/A", inline=False)
            embed.add_field(name="Defense", value=dfe[:1024] if dfe else "N/A", inline=False)
            embed.add_field(name="Goalies", value=goalies[:1024] if goalies else "N/A", inline=False)
        except Exception: 
            embed.description = "Stats temporarily unavailable."
        return embed

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.primary)
    async def summary_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self.original_embed)

    @discord.ui.button(label="Away Roster", style=discord.ButtonStyle.secondary)
    async def away_roster_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('away'))

    @discord.ui.button(label="Home Roster", style=discord.ButtonStyle.secondary)
    async def home_roster_button(self, interaction, button): 
        await interaction.response.edit_message(embed=self._build_roster_embed('home'))


class NHL(commands.GroupCog, name="nhl"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @staticmethod
    def format_team_strings(awayAbbrev, homeAbbrev, home, away):
        a_emoji = TEAM_EMOJIS.get(awayAbbrev, "")
        h_emoji = TEAM_EMOJIS.get(homeAbbrev, "")
        return f"{a_emoji} {away}".lstrip(), f"{home} {h_emoji}".rstrip()

    @staticmethod
    def get_division_string(name):
        return TEAM_EMOJIS.get(name[:3].upper(), "") + f" {name}"

    # --- DISCORD COMMAND INTERFACES ---

    @app_commands.command(name="today", description="Get today's NHL schedule and scores")
    async def today_cmd(self, interaction: discord.Interaction):
        await self.get_today_games(interaction, date_str=None)

    @app_commands.command(name="yesterday", description="Get yesterday's NHL scores")
    async def yesterday_cmd(self, interaction: discord.Interaction):
        await self.get_yesterday_games(interaction)

    @app_commands.command(name="standings", description="Get the NHL standings")
    async def standings_cmd(self, interaction: discord.Interaction):
        await self.get_standings(interaction, date_str=None)

    @app_commands.command(name="schedule", description="Get the schedule for the week for an NHL team")
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list")
    @app_commands.autocomplete(abbreviation=nhl_team_autocomplete)
    async def schedule_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_schedule(interaction, abbreviation, date_str=None)

    @app_commands.command(name="game", description="Check live or past game stats for an NHL team")
    @app_commands.describe(abbreviation="Type or pick a team from the drop-down list")
    @app_commands.autocomplete(abbreviation=nhl_team_autocomplete)
    async def game_cmd(self, interaction: discord.Interaction, abbreviation: str):
        await self.get_game_info(interaction, abbreviation, date_str=None)

    @app_commands.command(name="player", description="Gets the complete career overview of an NHL player")
    async def player_cmd(self, interaction: discord.Interaction, name: str):
        await self.get_player_info(interaction, name)

    @app_commands.command(name="teams", description="Get all available NHL team codes and abbreviations")
    async def teams_cmd(self, interaction: discord.Interaction):
        await self.get_all_teams(interaction)

    # --- SHARED STRATEGY ARCHITECTURE LOGIC ---

    async def get_today_games(self, interaction: discord.Interaction, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl today")
        try:
            embed = await self.build_schedule_embed(date_str=date_str)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing schedule request.")

    async def get_yesterday_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl yesterday")
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            y_date = (datetime.now(hawaii_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
            embed = await self.build_schedule_embed(date_str=y_date)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing retrospective scores.")

    async def get_standings(self, interaction: discord.Interaction, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "nhl standings")
        try:
            if not date_str:
                hawaii = pytz.timezone('US/Hawaii')
                date_str = datetime.now(hawaii).strftime('%Y-%m-%d')
            data = requests.get(f"https://api-web.nhle.com/v1/standings/{date_str}").json()

            divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for record in data.get("standings", []):
                div = record.get("divisionName")
                if div in divisions:
                    team_name = record["teamName"]["default"]
                    team_abbrev = record.get("teamAbbrev", {}).get("default", "").upper()
                    team_emoji = TEAM_EMOJIS.get(team_abbrev, "")
                    emoji_name = f"{team_emoji} {team_name}".strip()
                    wildcard = "🃏" if record.get("wildcardSequence") in [1, 2] else ""
                    wins = record.get('wins') or 0
                    losses = record.get('losses') or 0
                    ot_losses = record.get('otLosses') or 0
                    points = record.get('points') or 0
                    divisions[div].append(f"{emoji_name} ({wins}-{losses}-{ot_losses}) {points}pts {wildcard}")

            embed = discord.Embed(title=f"NHL Standings Overview ({date_str})", color=config.color)
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            for div_name, lines in divisions.items():
                embed.add_field(name=f"{div_name} Division", value="\n".join(lines) if lines else "No data", inline=False)
            embed.set_footer(text=config.footer)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Error processing standings.")

    async def get_schedule(self, interaction: discord.Interaction, team_abbreviation: str, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl schedule {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            with open("teams.json", "r") as f: teams = json.load(f)
            if abbrev not in teams:
                return await interaction.followup.send("Invalid team identifier. Try matching format via `/nhl teams`.")

            endpoint = f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/{date_str}' if date_str else f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/now'
            data = requests.get(endpoint).json()
            embed = discord.Embed(title=f"{teams[abbrev]} Weekly Outlook", color=config.color)

            for game in data.get('games', []):
                b_data = requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game['id']}/boxscore").json()
                home = b_data["homeTeam"]["commonName"]["default"]
                away = b_data["awayTeam"]["commonName"]["default"]
                utc_start = datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                embed.add_field(name=f"<t:{int(utc_start.timestamp())}:F>", value=f"{away} @ {home}", inline=False)

            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Failed to extract look-ahead week schedules.")

    async def get_game_info(self, interaction: discord.Interaction, team_abbreviation: str, date_str: str = None):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl game {team_abbreviation}")
        try:
            abbrev = team_abbreviation.upper()
            if not date_str:
                hawaii = pytz.timezone('US/Hawaii')
                date_str = datetime.now(hawaii).strftime('%Y-%m-%d')

            data = requests.get(f'https://api-web.nhle.com/v1/club-schedule/{abbrev}/week/{date_str}').json()
            game_data = next((g for g in data.get('games', []) if g.get('gameDate') == date_str), None)

            if not game_data:
                return await interaction.followup.send(
                    f"Selected team specified (`{abbrev}`) has no matches slated for `{date_str}`."
                )
            game_id = game_data['id']
            b_data = requests.get(
                f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore", timeout=15
            ).json()
            away, home = b_data['awayTeam'], b_data['homeTeam']
            away_abbr = away.get('abbrev', 'AWAY').upper()
            home_abbr = home.get('abbrev', 'HOME').upper()
            away_name = away.get('commonName', {}).get('default') or away_abbr
            home_name = home.get('commonName', {}).get('default') or home_abbr
            away_label = f"{TEAM_EMOJIS.get(away_abbr, '')} {away_name}".strip()
            home_label = f"{TEAM_EMOJIS.get(home_abbr, '')} {home_name}".strip()
            state = str(b_data.get('gameState') or game_data.get('gameState') or 'FUT').upper()
            finished = state in ('OFF', 'FINAL')
            scheduled = state in ('FUT', 'PRE')
            live = not (finished or scheduled)
            period = b_data.get('periodDescriptor') or {}
            period_type = str(period.get('periodType') or '').upper()
            period_number = period.get('number')
            if finished:
                status = 'Final / Shootout' if period_type == 'SO' else ('Final / OT' if period_type == 'OT' else 'Final')
            elif scheduled:
                status = 'Scheduled'
            else:
                status = f"Live • {'OT' if period_type == 'OT' else ('SO' if period_type == 'SO' else f'Period {period_number}' if period_number else 'In progress')}"
                clock = b_data.get('clock') or {}
                if isinstance(clock, dict) and clock.get('inIntermission'):
                    status = f"Intermission • After Period {period_number}" if period_number else 'Intermission'
                elif isinstance(clock, dict) and clock.get('timeRemaining'):
                    status += f" • {clock['timeRemaining']} remaining"
            away_score = away.get('score') or 0
            home_score = home.get('score') or 0
            embed = discord.Embed(
                title=f"{away_label} @ {home_label}",
                description=f"**{date_str}**\n**{status}**",
                color=config.color
            )
            embed.add_field(
                name='🏒 Scoreboard',
                value=(f"**{away_label}: {away_score}**\n**{home_label}: {home_score}**"
                       if not scheduled else f"{away_label} vs. {home_label}\nPuck drop pending"),
                inline=False
            )
            # NHL gamecenter landing supplies scoring events grouped by period.
            # A missing scoring feed is shown as unavailable, never as a fabricated 0.
            scoring = []
            if not scheduled:
                try:
                    landing = requests.get(
                        f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing", timeout=15
                    ).json()
                    scoring = (landing.get('summary') or {}).get('scoring') or []
                except (requests.RequestException, ValueError):
                    pass
            if scoring and isinstance(scoring, list):
                columns = []
                rows = {away_abbr: [], home_abbr: []}
                for group in scoring:
                    desc = group.get('periodDescriptor') or {}
                    number = desc.get('number')
                    ptype = str(desc.get('periodType') or '').upper()
                    label = 'SO' if ptype == 'SO' else 'OT' if ptype == 'OT' else str(number or '?')
                    columns.append(label)
                    goals = group.get('goals') or []
                    for ab in rows:
                        rows[ab].append(sum(1 for goal in goals if str((goal.get('teamAbbrev') or {}).get('default', '') if isinstance(goal.get('teamAbbrev'), dict) else (goal.get('teamAbbrev') or '')).upper() == ab))
                if columns:
                    header = f"{'Team':<5}" + ''.join(f"{col:>4}" for col in columns) + f"{'T':>5}"
                    line_a = f"{away_abbr:<5}" + ''.join(f"{v:>4}" for v in rows[away_abbr]) + f"{away_score:>5}"
                    line_h = f"{home_abbr:<5}" + ''.join(f"{v:>4}" for v in rows[home_abbr]) + f"{home_score:>5}"
                    embed.add_field(name='📊 Scoring by Period', value=f"```{header}\n{line_a}\n{line_h}```", inline=False)
            elif not scheduled:
                embed.add_field(name='📊 Scoring by Period', value='Period scoring is not available yet.', inline=False)
            if finished:
                if away_score == home_score:
                    result = 'Final result pending confirmation'
                else:
                    winner = away_name if away_score > home_score else home_name
                    suffix = ' in a shootout' if period_type == 'SO' else ' in overtime' if period_type == 'OT' else ''
                    result = f"{winner} win{suffix}"
            elif live:
                result = 'Game in progress'
            else:
                result = 'Awaiting puck drop'
            embed.add_field(name='🏆 Result', value=result, inline=True)
            embed.add_field(name='📋 Game State', value=status, inline=True)
            venue = game_data.get('venue') or {}
            venue = venue.get('default', 'Not announced') if isinstance(venue, dict) else str(venue)
            embed.add_field(name='🏟️ Venue', value=venue or 'Not announced', inline=True)
            broadcasts = [b.get('network') for b in game_data.get('tvBroadcasts', []) if b.get('network')]
            embed.add_field(name='📺 TV Broadcasts', value=', '.join(dict.fromkeys(broadcasts)) or 'Not announced', inline=False)
            start_utc = game_data.get('startTimeUTC')
            embed.add_field(name="🆔 Game ID", value=f"`{game_id}`", inline=True)
            embed.set_footer(text=config.footer)
            if start_utc and scheduled:
                try:
                    stamp = datetime.strptime(start_utc, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                    embed.add_field(name='🕒 Puck Drop', value=f"<t:{int(stamp.timestamp())}:F>", inline=False)
                except ValueError:
                    pass
            view = GameStatsView(b_data, embed)
            await interaction.followup.send(embed=embed, view=view)
        except Exception:
            await interaction.followup.send("Failed to build real-time interactive dashboard components.")

    async def get_player_info(self, interaction: discord.Interaction, player_name: str):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, f"nhl player {player_name}")
        try:
            with open("teams.json", "r") as f: teams = json.load(f)
            found_player = None

            for team_abbr in teams.keys():
                roster = requests.get(f"https://api-web.nhle.com/v1/roster/{team_abbr}/current").json()
                for group in ["forwards", "defensemen", "goalies"]:
                    for p in roster.get(group, []):
                        fn = p.get("firstName", {}).get("default", "")
                        ln = p.get("lastName", {}).get("default", "")
                        if f"{fn} {ln}".lower() == player_name.lower():
                            found_player = (p["id"], teams[team_abbr])
                            break
                    if found_player: break
                if found_player: break

            if not found_player:
                return await interaction.followup.send("Player details not resolved inside open data rosters.")

            p_data = requests.get(f"https://api-web.nhle.com/v1/player/{found_player[0]}/landing").json()
            pos_map = {"G": "Goalie", "D": "Defenseman", "C": "Center", "L": "Left Wing", "R": "Right Wing"}

            embed = discord.Embed(title=player_name, description=f"{pos_map.get(p_data.get('position'), 'Skater')} for the {found_player[1]} #{p_data.get('sweaterNumber', 'N/A')}", color=config.color)
            embed.set_thumbnail(url=p_data.get("headshot"))
            embed.add_field(name="Birth Date", value=p_data.get("birthDate", "Unknown"))
            embed.add_field(name="Place of Origin", value=f"{p_data.get('birthCity', {}).get('default', 'Unknown')}, {p_data.get('birthCountry', '')}")

            c_stats = p_data.get("featuredStats", {}).get("regularSeason", {}).get("career", {})
            gp = c_stats.get('gamesPlayed') or 'N/A'
            g = c_stats.get('goals') or 'N/A'
            a = c_stats.get('assists') or 'N/A'
            pts = c_stats.get('points') or 'N/A'
            s_stats = p_data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
            s_gp = s_stats.get('gamesPlayed') or 'N/A'
            s_g = s_stats.get('goals') or 'N/A'
            s_a = s_stats.get('assists') or 'N/A'
            s_pts = s_stats.get('points') or 'N/A'
            embed.add_field(name="Career Summary (GP/G/A/PTS)", value=f"`{gp}` GP | `{g}` G | `{a}` A | `{pts}` PTS", inline=False)
            embed.add_field(name="Season Summary (GP/G/A/PTS)", value=f"`{s_gp}` GP | `{s_g}` G | `{s_a}` A | `{s_pts}` PTS", inline=False)
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Roster parser error.")

    async def get_all_teams(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): 
            await interaction.response.defer(ephemeral=True)
        try:
            with open("teams.json", "r", encoding="utf-8") as f: 
                teams_data = json.load(f)

            lines = []
            for abbr, name in teams_data.items():
                emoji = TEAM_EMOJIS.get(abbr.upper(), "")
                lines.append(f"**{abbr}** - {name} {emoji}")

            embed = discord.Embed(
                title="Registered NHL Configurations", 
                description="\n".join(lines), 
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            await interaction.followup.send("Asset serialization read error.")

    async def build_schedule_embed(self, date_str=None):
        if not date_str:
            hawaii = pytz.timezone('US/Hawaii')
            date_str = datetime.now(hawaii).strftime('%Y-%m-%d')

        data = requests.get(f"https://api-web.nhle.com/v1/schedule/{date_str}", timeout=15).json()

        games = []
        for day in data.get("gameWeek", []):
            if day.get("date") == date_str:
                games = day.get("games", [])
                break

        embed = discord.Embed(
            title="Today's Games",
            description=f"Total games today: {len(games)}",
            color=config.color
        )
        embed.set_footer(text=config.footer)

        if not games:
            embed.add_field(name="No games scheduled", value="There are no NHL games scheduled for today.", inline=False)
            return embed

        for game in games:
            home_t, away_t = game.get("homeTeam", {}), game.get("awayTeam", {})
            home_name = home_t.get("placeName", {}).get("default") or home_t.get("commonName", {}).get("default", "TBD")
            away_name = away_t.get("placeName", {}).get("default") or away_t.get("commonName", {}).get("default", "TBD")
            away_s, home_s = self.format_team_strings(
                away_t.get("abbrev", ""), home_t.get("abbrev", ""), home_name, away_name
            )

            state = str(game.get("gameState", "FUT")).upper()
            away_score, home_score = away_t.get("score") or 0, home_t.get("score") or 0

            timestamp = None
            if game.get("startTimeUTC"):
                try:
                    start_dt = datetime.strptime(game["startTimeUTC"], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
                    timestamp = int(start_dt.timestamp())
                except (TypeError, ValueError):
                    pass

            if state in ("LIVE", "CRIT"):
                period = game.get("periodDescriptor", {}).get("number") or game.get("currentPeriod")
                if period:
                    suffix = "th" if 10 <= period % 100 <= 20 else {1:"st", 2:"nd", 3:"rd"}.get(period % 10, "th")
                    period_text = f"{period}{suffix}"
                else:
                    period_text = "LIVE"
                clock = game.get("clock", {})
                remaining = clock.get("timeRemaining") if isinstance(clock, dict) else game.get("timeRemaining")
                field_name = f"🔴 LIVE - {period_text}" + (f" - {remaining} remaining" if remaining else "")
                field_value = f"{away_s} @ {home_s}\n**{away_score} - {home_score}**"
            elif state in ("FINAL", "OFF"):
                field_name = "Final"
                field_value = f"{away_s} @ {home_s}\n**{away_score} - {home_score}**"
            else:
                field_name = f"<t:{timestamp}:t>" if timestamp else "Scheduled"
                field_value = f"{away_s} @ {home_s}\nGame is scheduled!"

            embed.add_field(name=field_name, value=field_value, inline=False)

        return embed

    async def get_tomorrow_games(self, interaction: discord.Interaction):
        if not interaction.response.is_done(): await interaction.response.defer()
        base_strategy.log_command(self.bot, interaction, "tomorrow")
        try:
            hawaii_tz = pytz.timezone('US/Hawaii')
            t_date = (datetime.now(hawaii_tz) + timedelta(days=1)).strftime('%Y-%m-%d')
            embed = await self.build_schedule_embed(date_str=t_date)
            await interaction.followup.send(embed=embed)
        except Exception:
            if DEBUG_MODE:
                traceback.print_exc()
            await interaction.followup.send("Error processing upcoming schedule.")

async def setup(bot):
    cog = NHL(bot)
    await bot.add_cog(cog)

NHLStrategy = NHL
