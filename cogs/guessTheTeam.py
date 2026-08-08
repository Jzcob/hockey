from email.mime import message

import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import config
import traceback
from datetime import datetime
from thefuzz import fuzz

# --- Global Constants ---
SIMILARITY_THRESHOLD = 85 

class GuessTheTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_pool = self.bot.db_pool

    @commands.Cog.listener()
    async def on_ready(self):
        print("LOADED: `guessTheTeam.py`")

    async def log_command(self, interaction: discord.Interaction):
        if config.command_log_bool:
            try:
                command_log_channel = self.bot.get_channel(config.command_log)
                guild_name = interaction.guild.name if interaction.guild else "DMs"
                if command_log_channel:
                    await command_log_channel.send(f"`/guess-the-team` used by `{interaction.user.name}` in `{guild_name}` at `{datetime.now()}`\n---")
            except: pass

    @app_commands.command(name="guess-the-team", description="Race to unscramble the NHL team name!")
    async def guessTheTeam(self, interaction: discord.Interaction):
        await self.log_command(interaction)
        
        # --- TARGETED AUDIT FOR SERVER 1530756253754724362 ---
        target_guild_id = 1530756253754724362
        is_target_server = interaction.guild and interaction.guild.id == target_guild_id
        
        if is_target_server:
            guild = interaction.guild
            me = guild.me if guild else None
            permissions = interaction.channel.permissions_for(me) if me and interaction.channel else None
            
            audit_report = (
                f"🔍 **[GUESS-THE-TEAM AUDIT]**\n"
                f"• Server ID Match: `True` ({target_guild_id})\n"
                f"• Bot User: `{self.bot.user}` (ID: `{self.bot.user.id}`)\n"
                f"• Message Content Intent Enabled: `{self.bot.intents.message_content}`\n"
                f"• Members Intent Enabled: `{self.bot.intents.members}`\n"
                f"• Channel Type: `{interaction.channel.type}`\n"
                f"• Permissions -> View Channel: `{permissions.view_channel if permissions else 'N/A'}` | "
                f"Send Messages: `{permissions.send_messages if permissions else 'N/A'}` | "
                f"Read Message History: `{permissions.read_message_history if permissions else 'N/A'}`\n"
                f"• Total Cached Members in Guild: `{guild.member_count if guild else 'N/A'}` (Cached locally: `{len(guild.members) if guild else 'N/A'}`)"
            )
            print(audit_report.replace("**", "").replace("`", ""))
            
        await interaction.response.defer()

        try:
            teams = [
                "Anaheim Ducks", "Boston Bruins", "Buffalo Sabres", "Calgary Flames",
                "Carolina Hurricanes", "Chicago Blackhawks", "Colorado Avalanche",
                "Columbus Blue Jackets", "Dallas Stars", "Detroit Red Wings",
                "Edmonton Oilers", "Florida Panthers", "Los Angeles Kings",
                "Minnesota Wild", "Montréal Canadiens", "Nashville Predators",
                "New Jersey Devils", "New York Islanders", "New Rangers",
                "Ottawa Senators", "Philadelphia Flyers", "Pittsburgh Penguins",
                "Seattle Kraken", "San Jose Sharks", "St. Louis Blues",
                "Tampa Bay Lightning", "Toronto Maple Leafs", "Utah Hockey Club",
                "Vancouver Canucks", "Vegas Golden Knights", "Washington Capitals",
                "Winnipeg Jets"
            ]

            correct_team = random.choice(teams)
            
            scrambled_list = list(correct_team.replace(" ", "").upper())
            random.shuffle(scrambled_list)
            scrambled_team = ' '.join(scrambled_list)

            embed = discord.Embed(
                title="🏁 Guess The Team RACE!",
                description=f"Unscramble the NHL team name! You have 30 seconds.\n\n# `{scrambled_team}`",
                color=config.color
            )
            embed.set_footer(text="Anyone in the channel can guess!")
            msg_sent = await interaction.followup.send(embed=embed)
            
            # Send audit report to channel if it's the target server so you can read it easily in Discord
            if is_target_server:
                await interaction.channel.send(audit_report)

            start_time = datetime.now()

            def check(message):
                is_match = message.channel.id == interaction.channel.id and not message.author.bot
                if is_target_server and not message.author.bot:
                    print(f"DEBUG AUDIT [Team Check]: Heard message from {message.author} content: '{message.content}' -> Valid Match: {is_match}")
                return is_match

            while True:
                elapsed = (datetime.now() - start_time).total_seconds()
                remaining = 30.0 - elapsed

                if remaining <= 0:
                    await interaction.followup.send(f"⏱️ Time's up! No one guessed it. The correct answer was **{correct_team}**.")
                    break

                try:
                    msg = await self.bot.wait_for('message', timeout=remaining, check=check)
                    user_ans = msg.content.strip().lower()
                    
                    if user_ans == correct_team.lower() or fuzz.ratio(user_ans, correct_team.lower()) >= SIMILARITY_THRESHOLD:
                        await msg.reply(f"🏆 **{msg.author.display_name}** got it! The team was **{correct_team}**!")
                        break
                    else:
                        try: await msg.add_reaction("❌")
                        except: pass

                except asyncio.TimeoutError:
                    await interaction.followup.send(f"⏱️ Time's up! The correct answer was **{correct_team}**.")
                    break

        except Exception as e:
            error_channel = self.bot.get_channel(config.error_channel)
            if error_channel:
                await error_channel.send(f"<@920797181034778655> Error in `/guess-the-team`:\n```{traceback.format_exc()}```")
                
            await interaction.followup.send("An error occurred. The issue has been reported.", ephemeral=True)

    @guessTheTeam.error
    async def guessTheTeam_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"⌛ Command on cooldown! Try again in {error.retry_after:.2f} seconds.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GuessTheTeam(bot))