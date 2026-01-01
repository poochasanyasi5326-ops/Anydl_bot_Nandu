# AnyDL Bot

A powerful Telegram bot for downloading content from YouTube, torrents, and direct links.

## Features
✅ YouTube quality selector with file sizes
✅ Torrent/Magnet support (Real-Debrid)
✅ Thumbnail management
✅ Progress tracking
✅ Screenshot generation
✅ Authorization system

## Quick Start

1. Copy .env.example to .env and add your credentials
2. Run: `docker-compose up -d`
3. View logs: `docker-compose logs -f`

## Environment Variables

Required:
- BOT_TOKEN
- API_ID
- API_HASH

Optional:
- APP_URL (for webhook)
- AUTHORIZED_USERS (comma-separated IDs)
- REAL_DEBRID_API_KEY (for torrents)

## Commands

/start - Start the bot
/cancel - Cancel current task
