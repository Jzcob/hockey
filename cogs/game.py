import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
import requests
from datetime import datetime, timedelta
import config
import pytz
import traceback

gameIDs = {}

class GameStatsView(discord.ui.View):
    def __init__(self, boxscore_data: dict, pbp_data: dict, original_embed: discord.Embed, game_state: str):
        super().__init__(timeout=300)  # Buttons will stop working after 5 minutes
        self.boxscore_data = boxscore_data
        self.pbp_data = pbp_data
        self.original_embed = original_embed
        
        self.away_team_id = boxscore_data.get('awayTeam', {}).get('id')
        self.away_team_abbrev = boxscore_data.get('awayTeam', {}).get('abbrev', 'AWAY')
        self.home_team_id = boxscore_data.get('homeTeam', {}).get('id')
        self.home_team_abbrev = boxscore_data.get('homeTeam', {}).get('abbrev', 'HOME')

        self.player_map = {}
        for player in self.pbp_data.get('rosterSpots', []):
            try:
                first_name = player.get('firstName', {}).get('default', '')
                last_name = player.get('lastName', {}).get('default', '')
                full_name = f"{first_name} {last_name}".strip()
                if full_name:
                    self.player_map[player['playerId']] = full_name
            except (KeyError, TypeError):
                continue

        if game_state in ["FUT", "PRE"]:
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label != "Summary":
                    item.disabled = True

    def _get_player_name(self, player_id: int) -> str:
        return self.player_map.get(player_id, "Unknown Player")

    def _get_team_abbrev(self, team_id: int) -> str:
        if team_id == self.away_team_id:
            return self.away_team_abbrev
        if team_id == self.home_team_id:
            return self.home_team_abbrev
        return "TEAM"

    def _build_roster_embed(self, team_type: str) -> discord.Embed:
        if team_type == 'away':
            team_data = self.boxscore_data['awayTeam']
            stats_data = self.boxscore_data.get('playerByGameStats', {}).get('awayTeam', {})
            title = f"{team_data.get('commonName', {}).get('default', 'Away Team')} Roster"
        else: # home
            team_data = self.boxscore_data['homeTeam']
            stats_data = self.boxscore_data.get('playerByGameStats', {}).get('homeTeam', {})
            title = f"{team_data.get('commonName', {}).get('default', 'Home Team')} Roster"

        embed = discord.Embed(
            title=title, 
            color=self.original_embed.color
        )
        embed.set_thumbnail(url=team_data.get('logo'))

        try:
            def format_skater(p):
                g = p.get('goals', 0)
                a = p.get('assists', 0)
                sog = p.get('sog', 0)
                pim = p.get('pim', 0)
                return f"#{p['sweaterNumber']} {p['name']['default']} ({g}G, {a}A, {sog}SOG, {pim}PIM)"

            forwards = "\n".join([format_skater(p) for p in stats_data.get('forwards', [])])
            defense = "\n".join([format_skater(p) for p in stats_data.get('defense', [])])
            
            goalie_list = []
            for p in stats_data.get('goalies', []):
                if p.get('toi', '00:00') != '00:00':
                    saves_shots = p.get('saveShotsAgainst', '0/0')
                    save_pctg = p.get('savePctg', 0)
                    goalie_list.append(f"#{p['sweaterNumber']} {p['name']['default']} ({saves_shots}, {save_pctg:.3f} SV%)")
                else:
                    goalie_list.append(f"#{p['sweaterNumber']} {p['name']['default']} (DNP)")
            goalies = "\n".join(goalie_list)

            embed.add_field(name="Forwards", value=forwards if forwards else "N/A", inline=False)
            embed.add_field(name="Defense", value=defense if defense else "N/A", inline=False)
            embed.add_field(name="Goalies", value=goalies if goalies else "N/A", inline=False)
        
        except KeyError:
            embed.description = "Roster data is not available for this game."

        embed.set_footer(text=self.original_embed.footer.text)
        return embed

    def _build_goals_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Scoring Summary", color=self.original_embed.color)
        
        goal_descs = []
        plays = self.pbp_data.get('plays', [])
        
        if not plays:
            embed.description = "Play-by-play data is not yet available."
            return embed

        for play in plays:
            if play.get('typeDescKey') == 'goal':
                details = play.get('details', {})
                period = play.get('periodDescriptor', {}).get('number', 'P')
                period_type = play.get('periodDescriptor', {}).get('periodType', '')
                if period_type == "OT": period = "OT"
                if period_type == "SO": period = "SO"
                
                time = play.get('timeInPeriod', '00:00') 
                
                team_id = details.get('eventOwnerTeamId')
                team_abbrev = self._get_team_abbrev(team_id)
                
                scorer_id = details.get('scoringPlayerId')
                scorer_name = self._get_player_name(scorer_id)
                goal_total = details.get('scoringPlayerTotal', 0) 
                
                goal_str = f"P{period} {time} - **{scorer_name} ({goal_total})** ({team_abbrev})"

                assist_names = []
                if 'assist1PlayerId' in details:
                    p_id = details['assist1PlayerId']
                    p_name = self._get_player_name(p_id)
                    p_total = details.get('assist1PlayerTotal', 0) 
                    assist_names.append(f"{p_name} ({p_total})")
                
                if 'assist2PlayerId' in details:
                    p_id = details['assist2PlayerId']
                    p_name = self._get_player_name(p_id)
                    p_total = details.get('assist2PlayerTotal', 0)
                    assist_names.append(f"{p_name} ({p_total})")
                
                if len(assist_names) == 1:
                    goal_str += f"\n*Assisted by: {assist_names[0]}*"
                elif len(assist_names) == 2:
                    goal_str += f"\n*Assisted by: {assist_names[0]} & {assist_names[1]}*"
                
                goal_descs.append(goal_str)

        if not goal_descs:
            embed.description = "No goals have been scored yet."
        else:
            embed.description = "\n\n".join(goal_descs)
            
        embed.set_footer(text=self.original_embed.footer.text)
        return embed

    def _build_penalties_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Penalty Summary", color=self.original_embed.color)
        
        penalty_descs = []
        plays = self.pbp_data.get('plays', [])

        if not plays:
            embed.description = "Play-by-play data is not yet available."
            return embed
            
        for play in plays:
            if play.get('typeDescKey') == 'penalty':
                details = play.get('details', {})
                period = play.get('periodDescriptor', {}).get('number', 'P')
                period_type = play.get('periodDescriptor', {}).get('periodType', '')
                if period_type == "OT": period = "OT"
                
                time = play.get('timeInPeriod', '00:00')
                
                team_id = details.get('eventOwnerTeamId')
                team_abbrev = self._get_team_abbrev(team_id)
                
                player_id = details.get('committedByPlayerId') 
                player_name = self._get_player_name(player_id)
                duration = details.get('duration', 0)
                penalty_type = details.get('descKey', 'N/A').title()
                
                penalty_str = f"P{period} {time} - **{player_name}** ({team_abbrev}) - *{duration} min* for *{penalty_type}*"
                penalty_descs.append(penalty_str)

        if not penalty_descs:
            embed.description = "No penalties have been called yet."
        else:
            embed.description = "\n\n".join(penalty_descs)
            
        embed.set_footer(text=self.original_embed.footer.text)
        return embed

    
    @discord.ui.button(label="Summary", style=discord.ButtonStyle.primary, row=0)
    async def summary_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.original_embed, view=self)

    @discord.ui.button(label="Goals", style=discord.ButtonStyle.success, row=0)
    async def goals_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        goals_embed = self._build_goals_embed()
        await interaction.response.edit_message(embed=goals_embed, view=self)

    @discord.ui.button(label="Penalties", style=discord.ButtonStyle.danger, row=0)
    async def penalties_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        penalties_embed = self._build_penalties_embed()
        await interaction.response.edit_message(embed=penalties_embed, view=self)

    @discord.ui.button(label="Away Roster", style=discord.ButtonStyle.secondary, row=1)
    async def away_roster_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        roster_embed = self._build_roster_embed('away')
        await interaction.response.edit_message(embed=roster_embed, view=self)

    @discord.ui.button(label="Home Roster", style=discord.ButtonStyle.secondary, row=1)
    async def home_roster_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        roster_embed = self._build_roster_embed('home')
        await interaction.response.edit_message(embed=roster_embed, view=self)


class game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `game.py`")
    
    @app_commands.command(name="game", description="Check the information for a game today! (e.g. BOS, NYR, etc.)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def game(self, interaction: discord.Interaction, abbreviation: str):
        if config.command_log_bool:
            command_log_channel = self.bot.get_channel(config.command_log)
            guild_name = interaction.guild.name if interaction.guild else "DMs"
            await command_log_channel.send(
                f"`/game` used by `{interaction.user.name}` in `{guild_name}` team `{abbreviation}` at `{datetime.now()}`\n---"
            )
        try:
            await interaction.response.defer()
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
                "USA": "Team USA", "CAN": "Team Canada", "SWE": "Team Sweden", "FIN": "Team Finland" }

            abbreviation = abbreviation.upper()
            if abbreviation not in teams:
                await interaction.followup.send(
                    "Invalid team abbreviation. Use `/teams` to see all of the abbreviations!" 
                )
                return

            team_name = teams[abbreviation]
            hawaii = pytz.timezone('US/Hawaii')
            today = datetime.now(hawaii).strftime('%Y-%m-%d')
            url = f'https://api-web.nhle.com/v1/club-schedule/{abbreviation}/week/{today}'
            
            response = requests.get(url)
            if response.status_code != 200:
                await interaction.followup.send(f"Failed to fetch schedule data for `{team_name}`.")
                return

            data = response.json()
            games = data.get('games', [])
            if not games:
                await interaction.followup.send(f"**{team_name}** do not play today!")
                return

            game = next((g for g in games if g.get('gameDate') == today), None)
            if not game:
                await interaction.followup.send(f"**{team_name}** do not play today!")
                return

            gameID = game.get('id')
            game_state = game.get('gameState', 'FUT')
            if not gameID:
                await interaction.followup.send("Could not retrieve game details. Please try again later.")
                return

            url2 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
            response2 = requests.get(url2)
            if response2.status_code != 200:
                await interaction.followup.send("Failed to fetch game details (boxscore). Please try again later.")
                return
            data2 = response2.json()

            url3 = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/play-by-play"
            response3 = requests.get(url3)
            if response3.status_code != 200:
                await interaction.followup.send("Failed to fetch game details (play-by-play). Please try again later.")
                return
            data3 = response3.json()

            home = data2.get('homeTeam', {}).get('commonName', {}).get('default', 'Unknown Team')
            away = data2.get('awayTeam', {}).get('commonName', {}).get('default', 'Unknown Team')
            tvBroadcasts = data2.get('tvBroadcasts', [])
            networks = "\n".join(
                f"{b['network']} ({b.get('countryCode', 'Unknown')})"
                for b in tvBroadcasts
                if not (interaction.guild and interaction.guild.id in config.bruins_servers and b['network'] != "NESN")
            )

            if game_state in ["FUT", "PRE"]:
                startTime = datetime.strptime(
                    data2.get("startTimeUTC", ""), '%Y-%m-%dT%H:%M:%SZ'
                ) - timedelta(hours=5)
                startTimeFormatted = startTime.strftime('%I:%M %p')
                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"Game is scheduled for {startTimeFormatted}",
                    color=config.color
                )
            elif game_state in ["FINAL", "OFF"]:
                homeScore = data2.get('homeTeam', {}).get('score', 0)
                awayScore = data2.get('awayTeam', {}).get('score', 0)
                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"Final!\nScore: {awayScore} | {homeScore}",
                    color=config.color
                )
                
                three_stars_data = data2.get('summary', {}).get('threeStars', [])
                if three_stars_data:
                    star_strings = []
                    for star in three_stars_data:
                        name = star.get('name', 'Unknown')
                        team = star.get('teamAbbrev', 'TEAM')
                        star_num = star.get('star', 0)
                        star_strings.append(f"{star_num}. **{name}** ({team})")
                    
                    if star_strings:
                        embed.add_field(name="Three Stars", value="\n".join(star_strings), inline=False)

            else:
                homeScore = data2.get('homeTeam', {}).get('score', 0)
                awayScore = data2.get('awayTeam', {}).get('score', 0)
                homeShots = data2.get('homeTeam', {}).get('sog', 0)
                awayShots = data2.get('awayTeam', {}).get('sog', 0)
                clock = data2.get('clock', {}).get('timeRemaining', 'Unknown Time')
                clockRunning = data2.get('clock', {}).get('running', False)
                clockIntermission = data2.get('clock', {}).get('inIntermission', False)

                situation = data2.get('situation', {})
                situation_str = ""
                if situation:
                    home_sit = situation.get('homeTeam', {}).get('situationDescriptions', [])
                    away_sit = situation.get('awayTeam', {}).get('situationDescriptions', [])
                    time_rem = situation.get('timeRemaining', '0:00')
                    home_strength = situation.get('homeTeam', {}).get('strength', 5)
                    away_strength = situation.get('awayTeam', {}).get('strength', 5)
                    strength_str = f"({home_strength} on {away_strength})"
                    
                    if "PP" in home_sit:
                        home_abbrev = data2.get('homeTeam', {}).get('abbrev', 'HOME')
                        situation_str = f"\n\n**{home_abbrev} Power Play {strength_str}**\n*Time Remaining: {time_rem}*"
                    elif "PP" in away_sit:
                        away_abbrev = data2.get('awayTeam', {}).get('abbrev', 'AWAY')
                        situation_str = f"\n\n**{away_abbrev} Power Play {strength_str}**\n*Time Remaining: {time_rem}*"

                embed = discord.Embed(
                    title=f"{away} @ {home}",
                    description=f"GAME IS LIVE!!!\n\nScore: {awayScore} - {homeScore}\nShots: {awayShots} - {homeShots}{situation_str}",
                    color=config.color
                )
                
                period = game.get('periodDescriptor', {}).get('number')
                period_type = game.get('periodDescriptor', {}).get('periodType')
                
                if period_type == "OT":
                    period_str = "Overtime"
                elif period_type == "SO":
                    period_str = "Shootout"
                elif period:
                    period_str = f"Period {period}"
                else:
                    period_str = "" 

                clock_val = "Intermission" if clockIntermission else f"{clock}\n{period_str}".strip()
                embed.add_field(name="Clock", value=clock_val, inline=False)

            embed.add_field(name="TV Broadcast", value=networks if networks else "N/A", inline=False)
            embed.add_field(name="Game ID", value=gameID, inline=False)
            embed.set_footer(text=config.footer)

            # --- Create and send the View ---
            view = GameStatsView(data2, data3, embed, game_state)
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")


    @game.error
    async def game_error(self, interaction: discord.Interaction, error):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Error with command, Message has been sent to Bot Developers", ephemeral=True)
            else:
                await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send("Error with command, Message has been sent to Bot Developers", ephemeral=True)
            
        error_channel = self.bot.get_channel(config.error_channel)
        await error_channel.send(f"<@9Services_Bot>```{error}```")

async def setup(bot):
    await bot.add_cog(game(bot))