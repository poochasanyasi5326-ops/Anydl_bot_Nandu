# AnyDL Bot - Complete Deployment Guide

A powerful Telegram bot for downloading content from YouTube, torrents, and direct links with full feature set.

## ✨ Features

1. ✅ Thumbnail management (Set, View, Clear)
2. ✅ YouTube quality selector with file sizes
3. ✅ Torrent/Magnet support (Real-Debrid)
4. ✅ Rename & Cancel buttons
5. ✅ Streamable vs Normal file option
6. ✅ Progress tracker (speed, ETA, size)
7. ✅ File preference memory
8. ✅ Thumbnail remembrance
9. ✅ Start command with interactive buttons
10. ✅ Disk reboot functionality
11. ✅ Screenshot generation from videos
12. ✅ Authorization system

## 📋 Requirements

- Python 3.10+
- FFmpeg
- Docker (optional)
- Telegram Bot Token
- Real-Debrid API Key (optional, for torrents)

## 🚀 Deployment Options

### Option 1: Docker (Recommended)

1. **Clone and setup:**
```bash
git clone <your-repo>
cd anydl-bot
```

2. **Create .env file:**
```bash
cp .env.example .env
# Edit .env with your credentials
nano .env
```

3. **Build and run:**
```bash
docker-compose up -d
```

4. **View logs:**
```bash
docker-compose logs -f
```

5. **Stop bot:**
```bash
docker-compose down
```

### Option 2: Koyeb Deployment

1. **Prepare files:**
   - Keep only `main.py` and `requirements.txt`
   - Delete `command.py`, `task_manager.py`, and helper folders

2. **Create Koyeb app:**
   - Go to [Koyeb Dashboard](https://app.koyeb.com)
   - Create new service from GitHub
   - Select your repository

3. **Set Environment Variables:**
   ```
   BOT_TOKEN=your_bot_token
   API_ID=your_api_id
   API_HASH=your_api_hash
   APP_URL=https://your-app-name.koyeb.app
   AUTHORIZED_USERS=123456789,987654321  (optional)
   REAL_DEBRID_API_KEY=your_key          (optional)
   ```

4. **Configure Build:**
   - Builder: Docker
   - Dockerfile: Use provided Dockerfile
   - Port: 8000
   - Health check: `/`

5. **Deploy!**

### Option 3: VPS/Server

1. **Install dependencies:**
```bash
sudo apt update
sudo apt install python3.10 python3-pip ffmpeg wget -y
```

2. **Install yt-dlp:**
```bash
sudo wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

3. **Setup bot:**
```bash
git clone <your-repo>
cd anydl-bot
pip3 install -r requirements.txt
```

4. **Configure environment:**
```bash
export BOT_TOKEN="your_token"
export API_ID="your_id"
export API_HASH="your_hash"
export APP_URL="https://your-domain.com"
```

5. **Run bot:**
```bash
python3 main.py
```

6. **Run with systemd (optional):**
```bash
sudo nano /etc/systemd/system/anydl-bot.service
```

Add:
```ini
[Unit]
Description=AnyDL Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/anydl-bot
Environment="BOT_TOKEN=your_token"
Environment="API_ID=your_id"
Environment="API_HASH=your_hash"
Environment="APP_URL=https://your-domain.com"
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable anydl-bot
sudo systemctl start anydl-bot
sudo systemctl status anydl-bot
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | `123456:ABC-DEF...` |
| `API_ID` | Telegram API ID from my.telegram.org | `12345678` |
| `API_HASH` | Telegram API hash from my.telegram.org | `abcdef123456...` |

### Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_URL` | Public URL for webhook (required for Koyeb) | `https://your-app.koyeb.app` |
| `PORT` | Server port | `8000` |
| `AUTHORIZED_USERS` | Comma-separated user IDs | `123456789,987654321` |
| `REAL_DEBRID_API_KEY` | Real-Debrid key for torrent support | `ABC123...` |

## 📱 Usage

1. Start the bot: `/start`
2. Set your preferences in Settings
3. Send any supported link:
   - YouTube: `https://youtube.com/watch?v=...`
   - Magnet: `magnet:?xt=urn:btih:...`
   - Direct: `https://example.com/file.mp4`
4. For YouTube, select quality from menu
5. Wait for download and upload

## 🎯 Commands

- `/start` - Start the bot and show menu
- `/cancel` - Cancel current download task

## 🔒 Authorization

To restrict bot access to specific users:

1. Get your Telegram user ID (send /start to @userinfobot)
2. Set `AUTHORIZED_USERS` environment variable:
   ```
   AUTHORIZED_USERS=123456789,987654321
   ```
3. Restart the bot

If `AUTHORIZED_USERS` is not set, the bot is public.

## 🐛 Troubleshooting

### Bot not responding
- Check if webhook is set correctly: `APP_URL` must match your public URL
- Verify environment variables are set
- Check logs: `docker-compose logs -f` or `systemctl status anydl-bot`

### Download fails
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check yt-dlp is installed: `yt-dlp --version`
- Verify disk space: `df -h`

### Torrent download fails
- Verify `REAL_DEBRID_API_KEY` is set correctly
- Check Real-Debrid account has active subscription
- Ensure magnet link is valid

## 📊 Resource Requirements

- **RAM**: Minimum 512MB, Recommended 1GB
- **CPU**: 1 core minimum
- **Storage**: 2GB for system + space for temporary downloads
- **Bandwidth**: Depends on usage

## 🔄 Updates

To update the bot:

**Docker:**
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Manual:**
```bash
git pull
pip3 install -r requirements.txt --upgrade
sudo systemctl restart anydl-bot
```

## 📝 License

This project is for educational purposes. Respect copyright laws and content creators.

## 🆘 Support

For issues and feature requests, please open an issue on GitHub.

---

Made with ❤️ for the community
