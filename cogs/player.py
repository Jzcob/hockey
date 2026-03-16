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
        await interaction.response.defer()

        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                if command_log_channel:
                    await command_log_channel.send(
                        f"`/player` used by `{interaction.user.name}` in `{guild_name}` for player `{name}` at `{datetime.now()}`\n---"
                    )
            except: pass

        try:
            with open("teams.json", "r") as f:
                teams = json.load(f)

            session = self.bot.http_session 

            for team_abbr, team_name in teams.items():
                url = f"https://api-web.nhle.com/v1/roster/{team_abbr}/current"
                
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    roster_data = await resp.json()

                for position_group in ["forwards", "defensemen", "goalies"]:
                    players = roster_data.get(position_group, [])
                    for p_data in players:
                        f_name = p_data["firstName"]["default"]
                        l_name = p_data["lastName"]["default"]
                        full_name = f"{f_name} {l_name}"

                        if full_name.lower() == name.lower():
                            p_id = p_data["id"]
                            p_url = f"https://api-web.nhle.com/v1/player/{p_id}/landing"
                            
                            async with session.get(p_url) as p_resp:
                                if p_resp.status != 200:
                                    continue
                                player_info = await p_resp.json()

                            embed = self._create_player_embed(player_info, full_name, team_name)
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
            player_id = player_data.get('id') # Get player ID

            position_map = {
                "G": "Goalie", "D": "Defenseman", "C": "Center",
                "L": "Left Wing", "R": "Right Wing"
            }
            position_full = position_map.get(position, position)

            player_name_slug = full_name.lower().replace(" ", "-")
            
            team_slug = player_data.get("currentTeam", {}).get("teamSlug")

            if team_slug and player_id:
                player_url = f"https://www.nhl.com/{team_slug}/player/{player_name_slug}-{player_id}"
            else:
                player_url = f"https://www.nhl.com/player/{player_id}"
        

            embed = discord.Embed(
                title=f"{full_name}",
                description=f"{position_full} for the {team_name} #{sweater_number}",
                color=config.color,
                url=player_url
            )
            embed.set_thumbnail(url=headshot)
            embed.add_field(name="Birth Date", value=birth_date, inline=True)
            embed.add_field(name="Birth City", value=birth_city, inline=True)
            embed.add_field(name="Birth Country", value=birth_country, inline=True)
            embed.add_field(name="Games Played", value=games_played, inline=True)
            embed.add_field(name="Goals", value=goals, inline=True)
            embed.add_field(name="Assists", value=assists, inline=True)
            embed.add_field(name="Points", value=points, inline=True)
            embed.set_footer(text=f"Player ID: {player_id}")
            return embed
        except Exception as e:
            print(f"Error creating embed: {e}")
            raise

async def setup(bot):
    await bot.add_cog(player(bot))