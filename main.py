import os
import asyncio
import time
import uuid
import subprocess
import json
import requests
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)

# ================= ENV =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
APP_URL = os.environ.get("APP_URL", "")
PORT = int(os.environ.get("PORT", 8000))
RD_KEY = os.getenv("REAL_DEBRID_API_KEY")
AUTHORIZED_USERS = list(map(int, os.environ.get("AUTHORIZED_USERS", "").split(","))) if os.environ.get("AUTHORIZED_USERS") else []

# Validate required env vars
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not API_ID:
    raise ValueError("API_ID environment variable is required")
if not API_HASH:
    raise ValueError("API_HASH environment variable is required")

# ================= BOT =================
bot = Client(
    "anydl",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ================= STATE =================
USERS = {}
PENDING_RENAME = {}
ACTIVE = None
_LAST = {}

def get_user(uid):
    return USERS.setdefault(uid, {
        "streamable": False,
        "thumbnail": None,
        "quality": "best",
        "screenshots": True
    })

def is_authorized(uid):
    if not AUTHORIZED_USERS:
        return True
    return uid in AUTHORIZED_USERS

def busy(): 
    return ACTIVE is not None

def cancel_task(): 
    global ACTIVE
    if ACTIVE: 
        ACTIVE["stop"] = True

# ================= HELPER FUNCTIONS =================
def human(x):
    """Convert bytes to human readable format"""
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if x < 1024:
            return f"{x:.2f} {u}"
        x /= 1024
    return f"{x:.2f} PB"

async def progress(msg, jid, phase, cur, total):
    """Update progress message with current status"""
    now = time.time()
    
    if jid not in _LAST:
        _LAST[jid] = now
    if now - _LAST[jid] < 4:
        return
    
    _LAST[jid] = now
    pct = (cur / total) * 100 if total else 0
    filled = int(pct / 10)
    bar = "▰" * filled + "▱" * (10 - filled)
    
    text = (
        f"⏳ **{phase}**\n"
        f"`{bar}` {pct:.1f}%\n"
        f"📦 {human(cur)} / {human(total)}"
    )
    
    try:
        await msg.edit(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]]))
    except:
        pass

async def close_kb(msg):
    """Remove inline keyboard from message"""
    try:
        await msg.edit_reply_markup(None)
    except:
        pass

def is_streamable(path):
    """Check if file is a streamable video format"""
    ext = os.path.splitext(path)[1].lower()
    return ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]

def screenshots(video):
    """Generate screenshots from video at specific timestamps"""
    shots = []
    timestamps = ["00:00:05", "00:10:00"]
    
    for t in timestamps:
        out = f"/tmp/{uuid.uuid4().hex}.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", t, "-i", video, "-vframes", "1", "-q:v", "2", out],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30
            )
            if os.path.exists(out) and os.path.getsize(out) > 0:
                shots.append(out)
        except:
            if os.path.exists(out):
                os.remove(out)
    return shots

def yt_formats(url):
    """Get available YouTube formats with file sizes"""
    try:
        cmd = ["yt-dlp", "-J", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return []
        
        info = json.loads(result.stdout)
        formats = []
        
        for f in info.get('formats', []):
            if not f.get('height'):
                continue
            
            filesize = f.get('filesize') or f.get('filesize_approx')
            if not filesize:
                continue
            
            formats.append((
                f['format_id'],
                f['format_id'],
                f"{f.get('height', 'audio')}p",
                round(filesize / 1e6, 1)
            ))
        
        formats.sort(key=lambda x: int(x[2].replace('p', '')), reverse=True)
        
        seen = set()
        unique_formats = []
        for fmt in formats:
            if fmt[2] not in seen:
                seen.add(fmt[2])
                unique_formats.append(fmt)
        
        return unique_formats[:10]
    except Exception as e:
        print(f"Error getting formats: {e}")
        return []

async def http_dl(url, path, msg, jid):
    """Download file from direct URL with progress tracking"""
    await msg.edit("⏳ **Starting download...**")
    
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    
    total = int(r.headers.get('content-length', 0))
    cur = 0
    
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*512):
            if ACTIVE and ACTIVE.get("stop"):
                raise Exception("Cancelled by user")
            
            if chunk:
                f.write(chunk)
                cur += len(chunk)
                await progress(msg, jid, "Downloading", cur, total)

async def run_task(job, mode, fmt, prefs, msg, fname):
    """Main task runner for downloads"""
    global ACTIVE
    jid = str(uuid.uuid4())
    ACTIVE = {"stop": False}
    out = f"/tmp/{fname}"
    
    try:
        if mode == "youtube":
            await msg.edit(f"⏳ **Downloading YouTube video...**\n`{fname}`")
            
            cmd = ["yt-dlp", "-f", fmt, "-o", out, job]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            while proc.returncode is None:
                if ACTIVE["stop"]:
                    proc.kill()
                    raise Exception("Cancelled by user")
                await asyncio.sleep(1)
                await proc.wait()
            
            if proc.returncode != 0:
                raise Exception("Download failed")
        
        elif mode == "torrent":
            await msg.edit(f"⏳ **Processing torrent...**\n`{fname}`")
            
            if not RD_KEY:
                raise Exception("Real-Debrid API key not configured")
            
            h = {"Authorization": f"Bearer {RD_KEY}"}
            
            r = requests.post(
                "https://api.real-debrid.com/rest/1.0/torrents/addMagnet",
                headers=h,
                data={"magnet": job},
                timeout=30
            )
            r.raise_for_status()
            tid = r.json()['id']
            
            requests.post(
                f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{tid}",
                headers=h,
                data={"files": "all"},
                timeout=30
            )
            
            await msg.edit("⏳ **Waiting for torrent to be ready...**")
            for _ in range(60):
                if ACTIVE["stop"]:
                    raise Exception("Cancelled by user")
                
                info = requests.get(
                    f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}",
                    headers=h,
                    timeout=30
                ).json()
                
                if info['status'] == 'downloaded':
                    break
                
                await asyncio.sleep(5)
            else:
                raise Exception("Torrent download timeout")
            
            if not info.get('links'):
                raise Exception("No files in torrent")
            
            link = info['links'][0]
            unrestrict = requests.post(
                "https://api.real-debrid.com/rest/1.0/unrestrict/link",
                headers=h,
                data={"link": link},
                timeout=30
            ).json()
            
            await http_dl(unrestrict['download'], out, msg, jid)
        
        elif mode == "file":
            await msg.edit(f"⏳ **Downloading file...**\n`{fname}`")
            await job.download(file_name=out)
        
        else:
            await http_dl(job, out, msg, jid)
        
        if not os.path.exists(out):
            raise Exception("Download failed - file not found")
        
        shots = []
        if prefs.get("shots") and is_streamable(out):
            await msg.edit("📸 **Generating screenshots...**")
            shots = screenshots(out)
        
        await msg.edit("📤 **Uploading to Telegram...**")
        
        file_size = os.path.getsize(out)
        caption = f"✅ **{fname}**\n📦 Size: {human(file_size)}"
        
        thumb = prefs.get("thumb") or (shots[0] if shots else None)
        
        await msg.reply_document(
            out,
            thumb=thumb,
            supports_streaming=prefs.get("stream", False),
            caption=caption,
            progress=lambda c, t: progress(msg, jid, "Uploading", c, t)
        )
        
        await close_kb(msg)
        await msg.edit("✅ **Upload complete!**")
        
        for shot in shots:
            try:
                os.remove(shot)
            except:
                pass
    
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{str(e)}`")
    
    finally:
        if os.path.exists(out):
            try:
                os.remove(out)
            except:
                pass
        ACTIVE = None

# ================= UI =================
def main_menu(authorized=True):
    if not authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Unauthorized", callback_data="unauth")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Download", callback_data="dl")],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎞 Streamable", callback_data="set_stream"),
            InlineKeyboardButton("📄 Normal", callback_data="set_file"),
        ],
        [
            InlineKeyboardButton("🎚 Quality", callback_data="quality"),
            InlineKeyboardButton("📸 Screenshots", callback_data="toggle_screenshots"),
        ],
        [
            InlineKeyboardButton("💾 Disk Reboot", callback_data="reboot"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")]
    ])

def thumbnail_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Set", callback_data="thumb_set"),
            InlineKeyboardButton("👁 View", callback_data="thumb_view"),
            InlineKeyboardButton("🗑 Clear", callback_data="thumb_clear")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")]
    ])

def quality_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("144p", callback_data="q_144"),
            InlineKeyboardButton("360p", callback_data="q_360")
        ],
        [
            InlineKeyboardButton("480p", callback_data="q_480"),
            InlineKeyboardButton("720p", callback_data="q_720")
        ],
        [
            InlineKeyboardButton("1080p", callback_data="q_1080"),
            InlineKeyboardButton("Best", callback_data="q_best")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings")]
    ])

# ================= HANDLERS =================
@bot.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    uid = m.from_user.id
    get_user(uid)
    authorized = is_authorized(uid)
    
    welcome_text = f"✅ **AnyDL Bot Ready**\n\n"
    if authorized:
        welcome_text += "👋 Welcome! Send me a link to get started."
    else:
        welcome_text += "❌ You are not authorized to use this bot."
    
    await m.reply(welcome_text, reply_markup=main_menu(authorized))

@bot.on_callback_query()
async def callbacks(_, q: CallbackQuery):
    uid = q.from_user.id
    user = get_user(uid)
    authorized = is_authorized(uid)

    if q.data == "unauth":
        await q.answer("You are not authorized!", show_alert=True)
        return

    if not authorized and q.data != "help":
        await q.answer("Unauthorized access!", show_alert=True)
        return

    if q.data == "back":
        await q.message.edit("📋 **Main Menu**", reply_markup=main_menu(authorized))

    elif q.data == "dl":
        await q.message.edit("📥 Send me a link:\n• YouTube URL\n• Magnet Link\n• Direct URL", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]))

    elif q.data == "settings":
        stream_status = "✅" if user["streamable"] else "❌"
        shots_status = "✅" if user["screenshots"] else "❌"
        await q.message.edit(
            f"⚙️ **Settings**\n\n"
            f"🎞 Streamable: {stream_status}\n"
            f"📸 Screenshots: {shots_status}\n"
            f"🎚 Quality: {user['quality']}",
            reply_markup=settings_menu()
        )

    elif q.data == "set_stream":
        user["streamable"] = True
        await q.answer("✅ Streamable mode enabled", show_alert=True)

    elif q.data == "set_file":
        user["streamable"] = False
        await q.answer("✅ Normal file mode enabled", show_alert=True)

    elif q.data == "toggle_screenshots":
        user["screenshots"] = not user["screenshots"]
        status = "ON" if user["screenshots"] else "OFF"
        await q.answer(f"📸 Screenshots: {status}", show_alert=True)

    elif q.data == "quality":
        await q.message.edit("🎚 **Select YouTube Quality**", reply_markup=quality_menu())

    elif q.data.startswith("q_"):
        quality = q.data.replace("q_", "")
        user["quality"] = quality
        await q.answer(f"✅ Quality set to: {quality}", show_alert=True)

    elif q.data == "thumb":
        await q.message.edit("🖼 **Thumbnail Manager**", reply_markup=thumbnail_menu())

    elif q.data == "thumb_set":
        await q.message.reply("📤 Send me a photo to set as thumbnail")

    elif q.data == "thumb_clear":
        user["thumbnail"] = None
        await q.answer("✅ Thumbnail cleared", show_alert=True)

    elif q.data == "thumb_view":
        if user["thumbnail"]:
            await q.message.reply_photo(user["thumbnail"], caption="🖼 Current Thumbnail")
        else:
            await q.answer("❌ No thumbnail set", show_alert=True)

    elif q.data == "reboot":
        global ACTIVE
        ACTIVE = None
        await q.answer("✅ Disk rebooted successfully", show_alert=True)

    elif q.data == "help":
        help_text = (
            "📌 **AnyDL Bot Help**\n\n"
            "**Supported:**\n"
            "• YouTube (multiple qualities)\n"
            "• Torrent/Magnet links (via Real-Debrid)\n"
            "• Direct download links\n"
            "• Streamable/Normal file options\n"
            "• Custom thumbnails\n"
            "• Progress tracking (speed, ETA, size)\n"
            "• Screenshot generation\n"
            "• Rename files\n"
            "• Cancel downloads\n\n"
            "**Usage:**\n"
            "1. Set your preferences in Settings\n"
            "2. Send any supported link\n"
            "3. Choose quality (for YouTube)\n"
            "4. Wait for download & upload\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/cancel - Cancel current task"
        )
        await q.message.reply(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]]))

    elif q.data == "cancel":
        cancel_task()
        await q.message.edit("❌ **Task cancelled**")
        await q.answer("Task cancelled")

    elif q.data.startswith("fmt_"):
        if not authorized:
            await q.answer("Unauthorized!", show_alert=True)
            return
        
        fmt_id = q.data.replace("fmt_", "")
        url = q.message.reply_to_message.text
        user = get_user(uid)
        
        status = await q.message.edit("⏳ **Starting download...**")
        
        prefs = {
            "stream": user["streamable"],
            "thumb": user["thumbnail"],
            "shots": user["screenshots"]
        }
        
        fname = f"video_{uuid.uuid4().hex[:8]}.mp4"
        asyncio.create_task(run_task(url, "youtube", fmt_id, prefs, status, fname))

@bot.on_message(filters.photo & filters.private)
async def set_thumb(_, m: Message):
    uid = m.from_user.id
    if not is_authorized(uid):
        await m.reply("❌ Unauthorized")
        return
    
    USERS[uid]["thumbnail"] = m.photo.file_id
    await m.reply("✅ Thumbnail saved successfully!")

@bot.on_message(filters.text & filters.private & ~filters.command(["start", "cancel"]))
async def handle_text(_, m: Message):
    uid = m.from_user.id
    
    if not is_authorized(uid):
        await m.reply("❌ You are not authorized to use this bot.", reply_markup=main_menu(False))
        return
    
    if uid in PENDING_RENAME:
        new_name = m.text.strip()
        del PENDING_RENAME[uid]
        await m.reply(f"✅ Filename will be: `{new_name}`")
        return
    
    text = m.text.strip()
    if text.startswith("http") or text.startswith("magnet:"):
        await handle_link(_, m)
    else:
        await m.reply("ℹ️ Send me a valid link (YouTube, Magnet, or Direct URL)")

async def handle_link(_, m: Message):
    uid = m.from_user.id
    user = get_user(uid)
    
    if not is_authorized(uid):
        await m.reply("❌ Unauthorized")
        return
    
    if busy():
        await m.reply("⚠️ A task is already running. Please wait.")
        return
    
    url = m.text.strip()
    
    if "youtube.com" in url or "youtu.be" in url:
        try:
            formats = yt_formats(url)
            if not formats:
                await m.reply("❌ Could not fetch video formats")
                return
            
            buttons = []
            for fmt_id, _, res, size in formats[:9]:
                buttons.append(InlineKeyboardButton(f"{res} ({size}MB)", callback_data=f"fmt_{fmt_id}"))
            
            kb = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
            kb.append([InlineKeyboardButton("❌ Cancel", callback_data="back")])
            
            await m.reply("🎚 **Select Quality:**", reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            await m.reply(f"❌ Error: {e}")
    
    elif url.startswith("magnet:"):
        fname = f"torrent_{uuid.uuid4().hex[:8]}.mkv"
        status = await m.reply(f"⏳ **Starting torrent download...**\n`{fname}`")
        
        prefs = {
            "stream": user["streamable"],
            "thumb": user["thumbnail"],
            "shots": user["screenshots"]
        }
        
        asyncio.create_task(run_task(url, "torrent", None, prefs, status, fname))
    
    else:
        fname = f"file_{uuid.uuid4().hex[:8]}.mp4"
        status = await m.reply(f"⏳ **Starting download...**\n`{fname}`")
        
        prefs = {
            "stream": user["streamable"],
            "thumb": user["thumbnail"],
            "shots": user["screenshots"]
        }
        
        asyncio.create_task(run_task(url, "direct", None, prefs, status, fname))

@bot.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(_, m: Message):
    if not is_authorized(m.from_user.id):
        await m.reply("❌ Unauthorized")
        return
    
    if busy():
        cancel_task()
        await m.reply("✅ Current task cancelled")
    else:
        await m.reply("ℹ️ No active task to cancel")

# ================= WEBHOOK =================
async def health(_):
    return web.Response(text="OK")

async def webhook(request):
    from pyrogram.types import Update
    update = Update(**await request.json())
    await bot.invoke(update)
    return web.Response(text="OK")

async def web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post("/webhook", webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# ================= MAIN =================
async def main():
    await bot.start()
    
    if APP_URL:
        webhook_url = f"{APP_URL}/webhook"
        await bot.set_webhook(webhook_url)
        print(f"✅ Bot started! Webhook set to: {webhook_url}")
        await web_server()
    else:
        print("✅ Bot started in polling mode")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
