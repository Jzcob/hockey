# 🏒 Hockey

A feature-rich Discord bot for hockey communities, with live league information, games, trivia, fantasy competition, moderation tools, and configurable daily schedules.

Hockey currently supports **NHL** and **PWHL** data through a shared league-command system and is built with Python and `discord.py`.

> Thank you to every server and community that has supported Hockey since its launch in 2023.

## ✨ Features

### 🏒 NHL & PWHL

Hockey provides a common set of slash commands for supported leagues:

- `/today` — today's schedule and scores
- `/tomorrow` — tomorrow's schedule
- `/yesterday` — yesterday's results
- `/standings` — league standings
- `/schedule` — schedule for a specific team
- `/game` — live or past game information
- `/player` — player information
- `/teams` — team names, codes, and abbreviations

Commands that require a league allow you to select **NHL** or **PWHL**.

Server managers can also configure automatic schedule channels independently for each league with `/set-schedule-channel` and `/clear-schedule-channel`.

### 🎮 Hockey Games

Hockey includes several community games and leaderboards:

- **Hockey Trivia**
- **Guess the Player**
- **Guess the Team**
- **Guess the Player Race**
- Trivia, GTP, fantasy, and fantasy-history leaderboards
- Personal point tracking

Have a trivia question you think should be added? Use `/suggest-trivia`.

### 🏆 Hockey Bot Fantasy League

The bot also contains its own fantasy hockey league system, including:

- Eight-team rosters
- Five active teams and three bench teams
- Seasonal team swaps
- Weekly **Ace Team** selection for a points multiplier
- Fantasy points and leaderboards
- Historical fantasy standings
- Administrative roster and scoring tools

Fantasy registration availability is controlled by the bot and may be closed outside the registration period.

### 🛡️ Moderation

Hockey includes server moderation functionality alongside its hockey features, including warnings, timeouts, kicks, bans, punishment history, and configurable moderation logs. **Staff Notes**, **Permanent Storage**, **Full Punishment History**, and **Punishment History Exports** are available as paid features through the **Referee Tier**.

Use `/help moderation` in Discord for the currently available moderation commands and permission requirements.

## 🤖 Adding Hockey

Hockey can be found through Discord's **App Discovery**. Search for **Hockey** and add the app to your server.

For support, questions, suggestions, and community updates, join the Hockey Discord server:

**https://discord.gg/WGQYdzvn8y**

## 📖 Help

Use `/help` in Discord. The help system includes menus for **General**, **NHL**, **PWHL**, **Games**, **Hockey Bot League**, and **Moderation**.

Because Hockey continues to evolve, the in-bot `/help` command is the best place to check currently available user-facing commands.

## 🧱 Project Structure

```text
hockey/
├── cogs/          # Core commands, games, fantasy league, moderation, etc.
├── cogsv2/        # Shared league commands and automatic scheduling
├── strategies/    # League-specific NHL/PWHL implementations
├── utils/         # Supporting utilities
├── main.py        # Startup, database pool, events, and extension loading
├── config.py      # Bot configuration
├── teams.json     # NHL team information
└── trivia.json    # Trivia question data
```

The newer league system uses a strategy-based design so common commands can work across multiple leagues while league-specific API and formatting logic remains separated.

## 🛠️ Development

Hockey is written primarily in **Python** using `discord.py`. The current application also uses a MySQL-compatible database through `aiomysql` and loads secrets/database configuration from environment variables.

The project is open source. Contributions, bug fixes, and feature ideas are welcome through pull requests.

Please do not commit bot tokens, database credentials, API keys, or other secrets.

## 🔒 Security & Terms

See `SECURITY.md` for security-related information and `TOS.md` for the project's terms of service.

## 🗓️ Milestones

| Milestone | Date |
|---|---:|
| 🚀 Released | November 1, 2023 |
| ✅ Verified | January 5, 2024 |
| 🎉 100 servers | January 20, 2024 |
| 🎉 200 servers | March 26, 2024 |
| 🎉 300 servers | May 8, 2024 |
| 🎉 400 servers | July 30, 2024 |
| 🎉 500 servers | October 5, 2024 |
| 🎉 600 servers | November 22, 2024 |
| 🎉 700 servers | February 8, 2025 |
| 🎉 800 servers | April 20, 2025 |
| 🎉 900 servers | October 7, 2025 |
| 🏆 **1,000 servers** | **January 6, 2026** |

## ❤️ Thank You

Thank you to everyone who has added Hockey, played the games, submitted trivia, competed in the fantasy league, reported bugs, suggested features, or contributed to the project.

Reaching **1,000 servers** would not have happened without the communities using the bot.

### Want to help improve Hockey?

Open an issue, submit an idea, or make a pull request. Contributions are welcome.
