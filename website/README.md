# HockeyBot Website

A modern, cyan-themed NHL dashboard website for the HockeyBot Discord bot.

## Features

- **Landing page** – animated cyan bubble background, hero section, features grid, premium upsell
- **Commands page** – tabbed view of all bot commands
- **Server Dashboard** – server admins can configure schedule channel, mod log, mute role, welcome messages, language, and prefix
- **Owner Panel** – bot owner can view all servers in the database, grant/revoke Referee premium tier, and refresh live stats

## Running locally

```bash
cd website
pip install -r requirements.txt
cp .env.example ../.env   # edit values
python app.py
```

Visit `http://localhost:5000`.

## Discord OAuth2 setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → your application → OAuth2
2. Add redirect URI: `http://localhost:5000/callback` (or your production URL)
3. Copy **Client ID** and **Client Secret** into `.env`

## Database

The website shares the same MySQL database as the bot. It expects:

- `guild_settings` table: `guild_id`, `schedule_channel_id`, `mod_log_channel_id`, `mute_role_id`, `welcome_channel_id`, `welcome_message`, `language`, `prefix`
- `premium_status` table: `entity_id`, `is_premium`, `tier`

## Deployment

For production, run with `gunicorn`:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Set `FLASK_SECRET` to a strong random string and update `DISCORD_REDIRECT_URI` to your production domain.
