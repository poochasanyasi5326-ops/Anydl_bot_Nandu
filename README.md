---
title: AnyDL Owner Only
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 8000
---

# 🚀 AnyDL Mastery Bot

A private, high-performance Telegram bot built for **YouTube Mastery**, **Smart Renaming**, and **Magnet Downloads**, optimized for **16GB storage** environments.

## ✨ Key Features
* **YouTube Mastery**: Real-time extraction of video/audio dimensions with merged high-quality output.
* **Smart Rename**: Automatic extension protection (e.g., adds `.mp4` if you forget).
* **Owner Only**: Strict security ensures only the authorized user can trigger downloads.
* **Auto-Cleanup**: Wipes the disk after every task to prevent storage crashes.
* **Live Progress**: Visual progress bars and ETA tracking for all uploads.

## 🛠️ Configuration
Ensure you set the following **Environment Variables** in your dashboard:
* `API_ID`: Your Telegram API ID.
* `API_HASH`: Your Telegram API Hash.
* `BOT_TOKEN`: Your Bot Token from @BotFather.

## 📦 Deployment Note
This bot uses **Aria2** for magnets and **FFmpeg** for YouTube merging. The `app_port` is set to **8000** to match the `aiohttp` server in `main.py`.
