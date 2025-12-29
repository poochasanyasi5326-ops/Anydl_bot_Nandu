Here is a **clean, honest, production-ready README.md** that matches **exactly what your bot does today**, enforces your owner ID, and does **not overpromise** anything.

You can **copy-paste this as `README.md`** in your GitHub repo.

---

# AnyDL – Personal Telegram Downloader Bot

AnyDL is a **private, owner-restricted Telegram bot** designed for **personal use** to download content from YouTube, direct links, and torrents (via Seedr), with full control over thumbnails, screenshots, formats, and upload behavior.

This bot is **not public**, **not multi-user**, and **not intended for resale or distribution**.

---

## 🔒 Access Control (Strict)

* **Owner ID enforced:** `519459195`
* Only the owner can:

  * Start downloads
  * Use buttons
  * Trigger jobs
* Unauthorized users:

  * See an access-denied message
  * Can view their Telegram ID
  * Get a “Contact Owner” button

There is **no bypass**.

---

## ✅ Features

### 📥 Supported Sources

* **YouTube**

  * Video formats (multiple resolutions)
  * Audio-only formats (multiple bitrates)
* **Magnet / Torrent**

  * Handled via **Seedr**
  * Auto cleanup after completion
* **Direct HTTP/HTTPS links**

---

### 🎞 Streamable vs Non-Streamable

* Toggle between:

  * **Streamable** (Telegram video player)
  * **Non-streamable** (document upload)
* Preference is **remembered per user**

---

### 🖼 Thumbnail Management

* `/setcustomthumbnail`

  * Upload an image to set a custom thumbnail
* Thumbnail is:

  * Remembered per user
  * Applied to all future uploads
* Clear / View options available via buttons

---

### 📸 Screenshot Generation

* Optional **3 automatic screenshots** using FFmpeg
* Timestamps:

  * 3s, 8s, 15s
* Behavior:

  * **Streamable ON** → first screenshot used as thumbnail
  * **Streamable OFF** → screenshots sent as preview album
* Screenshot generation can be toggled ON/OFF

---

### ✏️ Rename System

* Rename flow before upload:

  * Use default filename
  * Or provide a custom name
* Rules:

  * `@channel_name.mkv` is valid
  * No spaces added or removed automatically
  * Extension auto-added if missing
  * Invalid characters rejected
* Cancel available at all stages

---

### 📊 Progress Tracking

Text-based real-time updates via message edits:

* Downloaded size
* Total size
* Speed
* ETA
* Upload progress
* Cancel button available during:

  * Download
  * Upload

*(Telegram does not support native progress bars; this is the standard method used by all bots.)*

---

### 🧠 Preferences Memory

The bot remembers:

* Streamable / Non-streamable choice
* Screenshot toggle state
* Custom thumbnail

*(Memory is in-process; resets on container restart.)*

---

### 🛠 Owner Controls

Available via `/start` buttons:

* 📊 Disk Health (container disk usage)
* ❓ Help & Commands
* 🆔 Show Telegram ID
* 🔄 Reboot Bot (safe container restart)

---

## 🧩 Project Structure

```
Anydl_bot_Nandu-main/
├── Dockerfile
├── requirements.txt
├── run.sh
├── main.py
├── README.md
├── helper_funcs/
│   ├── display.py      # Progress & UI updates
│   └── ffmpeg.py       # Screenshots & streamable helpers
└── plugins/
    ├── command.py      # Telegram UI, buttons, commands
    └── task_manager.py # Download engine & job control
```

---

## 🚀 Deployment (Koyeb)

### Environment Variables (Required)

```
BOT_TOKEN=your_telegram_bot_token
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
SEEDR_TOKEN=your_seedr_bearer_token
```

> ⚠️ Never commit tokens to GitHub.

---

### Seedr Token Setup (Important)

Seedr does **not** provide an official API key.

You must:

1. Log in to [https://www.seedr.cc](https://www.seedr.cc)
2. Open Chrome DevTools → Network tab
3. Refresh the page
4. Click any `/api/*` request
5. Copy the value after:

   ```
   Authorization: Bearer <TOKEN>
   ```
6. Use that value as `SEEDR_TOKEN`

Tokens may expire and need manual refresh.

---

## ⚠️ Limitations (By Design)

* Single active job at a time
* No parallel downloads
* No persistent database
* Preferences reset on restart
* Seedr token is session-based
* Personal use only

These choices keep the bot:

* Stable
* Predictable
* Easy to maintain

---

## 🧠 Why This Bot Exists

This project is built for:

* Learning
* Personal automation
* Full control without public exposure
* Avoiding shady public bots

It prioritizes **clarity, safety, and correctness** over hype.

---

## 📜 Disclaimer

* You are responsible for the content you download
* Respect copyright laws in your jurisdiction
* This project is provided **as-is**, without warranty

---

## ✅ Status

✔ Feature-complete
✔ Owner-locked
✔ Stable for personal use
✔ Ready for deployment

-
