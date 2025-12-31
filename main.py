import os
import asyncio
import time
import uuid
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
import task_manager as tm

# ================= ENV =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
APP_URL = os.environ["APP_URL"]
PORT = int(os.environ.get("PORT", 8000))
AUTHORIZED_USERS = list(map(int, os.environ.get("AUTHORIZED_USERS", "").split(","))) if os.environ.get("AUTHORIZED_USERS") else []

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

# ================= START =================
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

# ================= CALLBACKS =================
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
        tm.ACTIVE = None
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

    elif q.data.startswith("cancel_"):
        tid = q.data.replace("cancel_", "")
        tm.cancel()
        await q.message.edit("❌ **Task cancelled**")
        await q.answer("Task cancelled")

    elif q.data.startswith("rename_"):
        tid = q.data.replace("rename_", "")
        PENDING_RENAME[uid] = tid
        await q.message.reply("✏️ Send the new filename:")

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
        await tm.run(url, "youtube", fmt_id, prefs, status, fname)

# ================= THUMBNAIL =================
@bot.on_message(filters.photo & filters.private)
async def set_thumb(_, m: Message):
    uid = m.from_user.id
    if not is_authorized(uid):
        await m.reply("❌ Unauthorized")
        return
    
    USERS[uid]["thumbnail"] = m.photo.file_id
    await m.reply("✅ Thumbnail saved successfully!")

# ================= RENAME HANDLER =================
@bot.on_message(filters.text & filters.private & ~filters.command(["start", "cancel"]))
async def handle_text(_, m: Message):
    uid = m.from_user.id
    
    if not is_authorized(uid):
        await m.reply("❌ You are not authorized to use this bot.", reply_markup=main_menu(False))
        return
    
    # Check if user is renaming
    if uid in PENDING_RENAME:
        new_name = m.text.strip()
        del PENDING_RENAME[uid]
        await m.reply(f"✅ Filename will be: `{new_name}`")
        return
    
    # Check if it's a link
    text = m.text.strip()
    if text.startswith("http") or text.startswith("magnet:"):
        await handle_link(_, m)
    else:
        await m.reply("ℹ️ Send me a valid link (YouTube, Magnet, or Direct URL)")

# ================= DOWNLOAD ENTRY =================
async def handle_link(_, m: Message):
    uid = m.from_user.id
    user = get_user(uid)
    
    if not is_authorized(uid):
        await m.reply("❌ Unauthorized")
        return
    
    if tm.busy():
        await m.reply("⚠️ A task is already running. Please wait.")
        return
    
    url = m.text.strip()
    
    # Detect link type
    if "youtube.com" in url or "youtu.be" in url:
        # YouTube - show quality selector
        try:
            formats = tm.yt_formats(url)
            if not formats:
                await m.reply("❌ Could not fetch video formats")
                return
            
            buttons = []
            for fmt_id, _, res, size in formats[:9]:  # Limit to 9 options
                buttons.append(InlineKeyboardButton(f"{res} ({size}MB)", callback_data=f"fmt_{fmt_id}"))
            
            # Arrange in rows of 2
            kb = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
            kb.append([InlineKeyboardButton("❌ Cancel", callback_data="back")])
            
            await m.reply("🎚 **Select Quality:**", reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            await m.reply(f"❌ Error: {e}")
    
    elif url.startswith("magnet:"):
        # Magnet/Torrent
        fname = f"torrent_{uuid.uuid4().hex[:8]}.mkv"
        status = await m.reply(f"⏳ **Starting torrent download...**\n`{fname}`")
        
        prefs = {
            "stream": user["streamable"],
            "thumb": user["thumbnail"],
            "shots": user["screenshots"]
        }
        
        asyncio.create_task(tm.run(url, "torrent", None, prefs, status, fname))
    
    else:
        # Direct link
        fname = f"file_{uuid.uuid4().hex[:8]}.mp4"
        status = await m.reply(f"⏳ **Starting download...**\n`{fname}`")
        
        prefs = {
            "stream": user["streamable"],
            "thumb": user["thumbnail"],
            "shots": user["screenshots"]
        }
        
        asyncio.create_task(tm.run(url, "direct", None, prefs, status, fname))

# ================= CANCEL COMMAND =================
@bot.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(_, m: Message):
    if not is_authorized(m.from_user.id):
        await m.reply("❌ Unauthorized")
        return
    
    if tm.busy():
        tm.cancel()
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
    webhook_url = f"{APP_URL}/webhook"
    await bot.set_webhook(webhook_url)
    print(f"✅ Bot started! Webhook set to: {webhook_url}")
    await web_server()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
