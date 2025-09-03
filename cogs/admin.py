import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import config
import traceback

watching = discord.CustomActivity(name="👀 New Feature Coming?")


class admin(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LOADED: `admin.py`")
        await self.bot.change_presence(activity=discord.CustomActivity(name="👀 New Feature Coming?"))
    
    @app_commands.command(name="dev-mode", description="Toggles dev mode!")
    async def dev_mode(self, interaction: discord.Interaction):
        if config.command_log_bool == True:
            command_log_channel = self.bot.get_channel(config.command_log)
            await command_log_channel.send(f"`/dev-mode` used by `{interaction.user.name}` in `{interaction.guild.name}` at `{datetime.now()}` \n---")
        try:
            if interaction.user.id == 920797181034778655:
                if config.dev_mode == False:
                    config.dev_mode = True
                    return await interaction.response.send_message("Dev mode is now enabled!")
                else:
                    config.dev_mode = False
                    return await interaction.response.send_message("Dev mode is now disabled!")
            else:
                return await interaction.response.send_message("You are not the bot owner!", ephemeral=True)
        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"<@920797181034778655>```{string}```")

    @app_commands.command(name="send", description="Make the bot say something.")
    @app_commands.checks.has_any_role(config.admin, config.owner)
    async def say(self, interaction: discord.Interaction, *, message: str, channel: discord.TextChannel = None):
        try:
            if channel == None:
                channel = interaction.channel
                await channel.send(message)
                await interaction.response.send_message(f"Sent message to {channel.mention}", ephemeral=True)
            else:
                await channel.send(message)
                await interaction.response.send_message(f"Sent message to {channel.mention}", ephemeral=True)
        except:
            error_channel = self.bot.get_channel(config.error_channel)
            string = f"{traceback.format_exc()}"
            await error_channel.send(f"```{string}```")
    
    """@app_commands.command(name="announce_league", description="Posts the fantasy league announcement embed.")
    @app_commands.default_permissions(administrator=True)
    async def announce_league(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="🏒 Announcing the First Annual Hockey Bot League! 🏒",
                description=(
                    "Get ready to put your hockey knowledge to the test! I am thrilled to launch a brand-new, discord-wide "
                    "**NHL Fantasy League**, a season-long competition where you can prove you're the best armchair GM.\n\n"
                    "This is all about the love of the game, bragging rights, and friendly competition. "
                    "There are no prizes—just the glory of finishing at the top!\n\n"
                    "This league is inspired by MyAnimeList's Fantasy Anime League."
                ),
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📜 How It Works: The Basics",
                value=(
                    "The league is simple to join and play. Here’s everything you need to know to build your team and start earning points.\n\n"
                    "**1. Build Your Roster (`/join_league`)**\n"
                    "- Every player will draft a roster of **8 NHL teams**.\n"
                    "- **5 Active Teams:** These are your starters. Only teams in your active roster will earn you points each week.\n"
                    "- **3 Bench Teams:** These are your reserves. They don't earn points, but you can swap them with your active teams.\n\n"
                    "**2. Make Strategic Swaps (`/swap_teams`)**\n"
                    "- You have **10 swaps** to use for the entire season. Use them wisely!\n"
                    "- You can swap any active team with any bench team to adapt to matchups, hot streaks, or injuries.\n\n"
                    "**3. Ace Your Pick (`/ace_team`)**\n"
                    "- Each week, you can select **one team** from your active roster to be your \"Aced\" team.\n"
                    "- This Aced team will earn a **massive x3 point multiplier** for all of its games that week!\n"
                    "- Ace selections are reset every week, so be sure to make your pick!\n"
                    "- Once selected, you cannot change your Aced team until the next week."
                ),
                inline=False
            )

            embed.add_field(
                name="📊 The Scoring System",
                value=(
                    "Points are awarded automatically based on how your **5 active teams** perform in their real-world games.\n\n"
                    "- **Win:** `+4 Points`\n"
                    "- **Overtime / Shootout Loss:** `+2 Points`\n"
                    "- **Regulation Loss:** `-2 Points`\n\n"
                    "**Aced Team Multiplier:**\n"
                    "- Aced Win: `+12 Points` (4 x 3)\n"
                    "- Aced OT / SO Loss: `+6 Points` (2 x 3)\n"
                    "- Aced Regulation Loss: `-6 Points` (-2 x 3)"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🚀 How to Get Started",
                value=(
                    "Ready to build your dynasty? Here are the commands you'll need:\n\n"
                    "- `/join-league` - **Start here!** A two-step process to pick your 5 active and 3 bench teams.\n"
                    "- `/my-roster` - View your current team selections, total points, and remaining swaps.\n"
                    "- `/swap-teams` - Use one of your 10 seasonal swaps.\n"
                    "- `/ace-team` - Choose your weekly x3 points multiplier team.\n"
                    "- `/leaderboard fantasy` - See how you stack up against the competition!\n\n"
                    "The puck drops soon! Draft your teams, make your picks, and may the best fan win!"
                ),
                inline=False
            )

            embed.add_field(
                name="⚠️ Important Notes",
                value=(
                    "The NHL season kicks off on October 7th. Please ensure your rosters are set before then as you won't be able to join after that!\n"
                    "I REPEAT: **SET YOUR ROSTERS BEFORE OCTOBER 7TH!**\n"
                    "You will not be able to join the league after the season starts!\n\n"
                    "Please remember that this is a friendly competition, and I want everyone to have fun!"
                )
            )

            embed.set_footer(text="For any questions, please join the bots discord server in `/info`")
            
            embed.set_thumbnail(url="https://www-league.nhlstatic.com/images/logos/league-dark/133-flat.svg")
            guilds = self.bot.guilds
            successful_sends = 0
            failed_sends = 0

            for guild in guilds:
                # First, try to get the public updates channel, otherwise fall back to the system channel
                target_channel = guild.public_updates_channel or guild.system_channel

                # Check if we actually found a channel to send to
                if target_channel:
                    try:
                        await target_channel.send(embed=embed)
                        print(f"✅ Successfully sent announcement to '{guild.name}'")
                        successful_sends += 1
                    except discord.Forbidden:
                        # This handles the "Missing Permissions" error specifically
                        print(f"❌ Failed to send to '{guild.name}' in #{target_channel.name} due to missing permissions.")
                        failed_sends += 1
                    except Exception as e:
                        # Catch any other unexpected errors
                        print(f"❌ An unexpected error occurred for '{guild.name}': {e}")
                        failed_sends += 1
                else:
                    # This handles servers with no suitable channel found
                    print(f"⚠️ Could not find a suitable announcement channel in '{guild.name}'.")
                    failed_sends += 1

            # Send a final status back to the user who ran the command
            await interaction.response.send_message(
                f"Announcement process complete.\n"
                f"✅ Sent successfully to **{successful_sends}** servers.\n"
                f"❌ Failed for **{failed_sends}** servers. (Check console for details)"
            )
        except Exception as e:
                error_channel = self.bot.get_channel(config.error_channel)
                string = f"{traceback.format_exc()}"
                await error_channel.send(f"<@920797181034778655>```{string}```")"""

async def setup(bot):
    await bot.add_cog(admin(bot), guilds=[discord.Object(id=config.hockey_discord_server)])
