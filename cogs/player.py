import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import requests
import config
import traceback
import json

class player(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `player.py`")
    
    @app_commands.command(name="player", description="Gets the information of a player!")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def player(self, interaction: discord.Interaction, name: str):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                await command_log_channel.send(
                    f"`/player` used by `{interaction.user.name}` in `{guild_name}` for player `{name}` at `{datetime.now()}`\n---"
                )
            except Exception as e:
                print(f"Command logging failed: {e}")

        try:
            await interaction.response.defer()
            with open("teams.json", "r") as f:
                teams = json.load(f)

            for team_abbr, team_name in teams.items():
                url = f"https://api-web.nhle.com/v1/roster/{team_abbr}/current"
                response = requests.get(url)
                if response.status_code != 200:
                    continue
                roster_data = response.json()

                for position_group in ["forwards", "defensemen", "goalies"]:
                    players = roster_data.get(position_group, [])
                    for player in players:
                        first_name = player["firstName"]["default"]
                        last_name = player["lastName"]["default"]
                        full_name = f"{first_name} {last_name}"

                        if full_name.lower() == name.lower():
                            player_id = player["id"]
                            player_data_url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
                            player_response = requests.get(player_data_url)
                            if player_response.status_code != 200:
                                continue
                            player_data = player_response.json()

                            embed = self._create_player_embed(player_data, full_name, team_name)
                            await interaction.followup.send(embed=embed)
                            return

            await interaction.followup.send("Player not found!", ephemeral=True)

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            await error_channel.send(f"<@920797181034778655>```{traceback.format_exc()}```")
            await interaction.followup.send(
                "An error occurred while fetching player data. The issue has been reported.",
                ephemeral=True
            )

    def _create_player_embed(self, player_data, full_name, team_name):
        try:
            headshot = player_data.get("headshot", "")
            position = player_data.get("position", "")
            birth_date = player_data.get("birthDate", "Unknown")
            birth_city = player_data.get("birthCity", {}).get("default", "Unknown")
            birth_country = player_data.get("birthCountry", "Unknown")
            sweater_number = player_data.get("sweaterNumber", "N/A")
            stats = player_data.get("featuredStats", {}).get("regularSeason", {}).get("career", {})
            games_played = stats.get("gamesPlayed", "N/A")
            goals = stats.get("goals", "N/A")
            assists = stats.get("assists", "N/A")
            points = stats.get("points", "N/A")

            position_map = {
                "G": "Goalie", "D": "Defenseman", "C": "Center",
                "L": "Left Wing", "R": "Right Wing"
            }
            position_full = position_map.get(position, position)

            embed = discord.Embed(
                title=f"{full_name}",
                description=f"{position_full} for the {team_name} #{sweater_number}",
                color=config.color,
                url=f"https://www.nhl.com/player/{player_data.get('id')}"
            )
            embed.set_thumbnail(url=headshot)
            embed.add_field(name="Birth Date", value=birth_date, inline=True)
            embed.add_field(name="Birth City", value=birth_city, inline=True)
            embed.add_field(name="Birth Country", value=birth_country, inline=True)
            embed.add_field(name="Games Played", value=games_played, inline=True)
            embed.add_field(name="Goals", value=goals, inline=True)
            embed.add_field(name="Assists", value=assists, inline=True)
            embed.add_field(name="Points", value=points, inline=True)
            embed.set_footer(text=f"Player ID: {player_data.get('id')}")
            return embed
        except Exception as e:
            print(f"Error creating embed: {e}")
            raise

async def setup(bot):
    await bot.add_cog(player(bot))