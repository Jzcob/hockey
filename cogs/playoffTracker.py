import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import traceback
import config
from datetime import datetime

# Reusing your existing TEAM_EMOJIS or the logic from the previous bracket
TEAM_MAP = {
    "ANA": "anahiem_ducks_emoji", "BOS": "boston_bruins_emoji", "BUF": "buffalo_sabres_emoji",
    "CGY": "calgary_flames_emoji", "CAR": "carolina_hurricanes_emoji", "CHI": "chicago_blackhawks_emoji",
    "COL": "colorado_avalanche_emoji", "CBJ": "columbus_blue_jackets_emoji", "DAL": "dallas_stars_emoji",
    "DET": "detroit_red_wings_emoji", "EDM": "edmonton_oilers_emoji", "FLA": "florida_panthers_emoji",
    "LAK": "los_angeles_kings_emoji", "MIN": "minnesota_wild_emoji", "MTL": "montreal_canadiens_emoji",
    "NSH": "nashville_predators_emoji", "NJD": "new_jersey_devils_emoji", "NYI": "new_york_islanders_emoji",
    "NYR": "new_york_rangers_emoji", "OTT": "ottawa_senators_emoji", "PHI": "philadelphia_flyers_emoji",
    "PIT": "pittsburgh_penguins_emoji", "SJS": "san_jose_sharks_emoji", "SEA": "seattle_kraken_emoji",
    "STL": "st_louis_blues_emoji", "TBL": "tampa_bay_lightning_emoji", "TOR": "toronto_maple_leafs_emoji",
    "UTA": "utah_hockey_club_emoji", "VAN": "vancouver_canucks_emoji", "VGK": "vegas_golden_knights_emoji",
    "WSH": "washington_capitals_emoji", "WPG": "winnipeg_jets_emoji"
}

class PlayoffTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_pool = bot.db_pool
        self.http_session = aiohttp.ClientSession()
        self.auto_update_brackets.start()

    def cog_unload(self):
        self.auto_update_brackets.cancel()

    def get_team_string(self, abbr):
        emoji_attr = TEAM_MAP.get(abbr)
        emoji = getattr(config, emoji_attr, "") if emoji_attr else ""
        return f"{emoji} {abbr}".strip()

    async def build_playoff_embeds(self):
        """Fetches API data and builds the list of embeds (one per round)."""
        now = datetime.now()
        season = f"{now.year}{now.year + 1}" if now.month >= 7 else f"{now.year - 1}{now.year}"
        url = f"https://api-web.nhle.com/v1/playoff-series/carousel/{season}/"
        
        async with self.http_session.get(url) as r:
            if r.status != 200: return []
            data = await r.json()

        rounds = data.get("rounds", [])
        embeds = []
        for rnd in rounds:
            label = rnd.get("roundLabel", f"Round {rnd.get('roundNumber')}")
            embed = discord.Embed(
                title=f"🏆 {label} - {season[:4]}/{season[4:]} Playoffs",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            for series in rnd.get("series", []):
                top = series.get("topSeed", {})
                bottom = series.get("bottomSeed", {})
                t_wins, b_wins = top.get("wins", 0), bottom.get("wins", 0)
                
                status = "✅ Final" if (t_wins >= 4 or b_wins >= 4) else "🏒 In Progress" if (t_wins > 0 or b_wins > 0) else "🕓 Scheduled"
                
                matchup = f"{self.get_team_string(bottom.get('abbrev', 'TBD'))} ({b_wins}) vs {self.get_team_string(top.get('abbrev', 'TBD'))} ({t_wins})"
                embed.add_field(
                    name=f"Series {series.get('seriesLetter', '?')}",
                    value=f"{matchup}\n*{status}*",
                    inline=False
                )
            embeds.append(embed)
        return embeds

    @tasks.loop(minutes=30)
    async def auto_update_brackets(self):
        """Loop that finds all active tracker messages and edits them."""
        await self.bot.wait_until_ready()
        try:
            embeds = await self.build_playoff_embeds()
            if not embeds: return

            # In this 'Static' mode, we'll just display the LATEST round (the most relevant one)
            # or you could combine them. For a single message, we'll show the current active round.
            current_embed = embeds[-1] 

            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT guild_id, channel_id, message_id FROM playoff_trackers")
                    records = await cursor.fetchall()

            for guild_id, channel_id, message_id in records:
                channel = self.bot.get_channel(channel_id)
                if not channel: continue
                try:
                    msg = await channel.fetch_message(message_id)
                    await msg.edit(embed=current_embed)
                except discord.NotFound:
                    # Message deleted, clean up DB?
                    pass
                except Exception:
                    continue
        except Exception:
            print(f"Playoff Update Error: {traceback.format_exc()}")

    @app_commands.command(name="setup-playoff-tracker", description="Set a channel for a live-updating playoff bracket.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_tracker(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        embeds = await self.build_playoff_embeds()
        if not embeds:
            return await interaction.followup.send("No playoff data available yet.")

        # Send the message
        msg = await channel.send(embed=embeds[-1]) # Sends the most recent round

        # Save to DB
        now = datetime.now()
        season = f"{now.year}{now.year + 1}" if now.month >= 7 else f"{now.year - 1}{now.year}"
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO playoff_trackers (guild_id, channel_id, message_id, season)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE channel_id=%s, message_id=%s, season=%s
                """, (interaction.guild.id, channel.id, msg.id, season, channel.id, msg.id, season))
                await conn.commit()

        await interaction.followup.send(f"✅ Live playoff tracker established in {channel.mention}!")
    
    @app_commands.command(name="remove-playoff-tracker", description="Remove the channel for the live-updating playoff bracket.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_tracker(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT channel_id, message_id FROM playoff_trackers WHERE guild_id = %s", (interaction.guild.id,))
                record = await cursor.fetchone()
                if not record:
                    return await interaction.followup.send("No active playoff tracker found for this server.")
                
                channel_id, message_id = record
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.delete()
                    except:
                        pass  # Message might already be deleted

                await cursor.execute("DELETE FROM playoff_trackers WHERE guild_id = %s", (interaction.guild.id,))
                await conn.commit()

        await interaction.followup.send("✅ Playoff tracker removed.")

async def setup(bot):
    await bot.add_cog(PlayoffTracker(bot))