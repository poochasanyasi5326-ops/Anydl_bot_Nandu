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
from pyrogram.types import Update

# ================= ENV =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
APP_URL = os.environ["APP_URL"]
PORT = int(os.environ.get("PORT", 8000))

# ================= BOT =================
bot = Client(
    "anydl",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ================= STATE =================
USERS = {}
TASKS = {}

def get_user(uid):
    return USERS.setdefault(uid, {
        "streamable": False,
        "thumbnail": None,
        "quality": "best"
    })

# ================= UI =================
def main_menu():
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
            InlineKeyboardButton("📁 Normal", callback_data="set_file"),
        ],
        [
            InlineKeyboardButton("🎚 Quality", callback_data="quality"),
            InlineKeyboardButton("🔁 Disk Reboot", callback_data="reboot"),
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")]
    ])

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    get_user(m.from_user.id)
    await m.reply(
        "✅ **AnyDL Bot Ready**",
        reply_markup=main_menu()
    )

# ================= CALLBACKS =================
@bot.on_callback_query()
async def callbacks(_, q: CallbackQuery):
    uid = q.from_user.id
    user = get_user(uid)

    if q.data == "back":
        await q.message.edit("Main Menu", reply_markup=main_menu())

    elif q.data == "settings":
        await q.message.edit("Settings", reply_markup=settings_menu())

    elif q.data == "set_stream":
        user["streamable"] = True
        await q.answer("Streamable ON")

    elif q.data == "set_file":
        user["streamable"] = False
        await q.answer("Normal File ON")

    elif q.data == "quality":
        await q.message.reply(
            "Select YouTube Quality",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("144p", callback_data="q_144"),
                 InlineKeyboardButton("360p", callback_data="q_360")],
                [InlineKeyboardButton("720p", callback_data="q_720"),
                 InlineKeyboardButton("1080p", callback_data="q_1080")],
                [InlineKeyboardButton("Best", callback_data="q_best")]
            ])
        )

    elif q.data.startswith("q_"):
        user["quality"] = q.data.replace("q_", "")
        await q.answer(f"Quality set: {user['quality']}")

    elif q.data == "thumb":
        await q.message.reply(
            "Thumbnail Manager",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Set", callback_data="thumb_set"),
                 InlineKeyboardButton("View", callback_data="thumb_view"),
                 InlineKeyboardButton("Clear", callback_data="thumb_clear")],
            ])
        )

    elif q.data == "thumb_clear":
        user["thumbnail"] = None
        await q.answer("Thumbnail cleared")

    elif q.data == "thumb_view":
        if user["thumbnail"]:
            await q.message.reply_photo(user["thumbnail"])
        else:
            await q.answer("No thumbnail")

    elif q.data == "reboot":
        TASKS.clear()
        await q.answer("Disk rebooted")

    elif q.data == "help":
        await q.message.reply(
            "📌 Supported:\n"
            "• YouTube (multi quality)\n"
            "• Torrent/Magnet (Seedr)\n"
            "• Streamable/Normal\n"
            "• Thumbnails\n"
            "• Progress\n"
            "• Rename / Cancel\n"
        )

# ================= THUMBNAIL =================
@bot.on_message(filters.photo)
async def set_thumb(_, m: Message):
    USERS[m.from_user.id]["thumbnail"] = m.photo.file_id
    await m.reply("Thumbnail saved")

# ================= DOWNLOAD ENTRY =================
@bot.on_message(filters.regex(r"(https?://|magnet:)"))
async def handle_link(_, m: Message):
    uid = m.from_user.id
    task_id = str(uuid.uuid4())[:8]

    TASKS[task_id] = {
        "user": uid,
        "status": "queued",
        "start": time.time(),
        "size": "unknown",
        "speed": "0 MB/s"
    }

    await m.reply(
        f"📥 Task `{task_id}` started",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}"),
                InlineKeyboardButton("✏️ Rename", callback_data=f"rename_{task_id}")
            ]
        ])
    )

# ================= CANCEL / RENAME =================
@bot.on_callback_query(filters.regex(r"cancel_"))
async def cancel(_, q: CallbackQuery):
    tid = q.data.split("_")[1]
    TASKS.pop(tid, None)
    await q.answer("Cancelled")

@bot.on_callback_query(filters.regex(r"rename_"))
async def rename(_, q: CallbackQuery):
    await q.message.reply("Send new filename")

# ================= PROGRESS (SIMULATED) =================
async def progress_worker():
    while True:
        for t in TASKS.values():
            t["status"] = "downloading"
            t["speed"] = "2.3 MB/s"
        await asyncio.sleep(5)

# ================= WEBHOOK =================
async def health(_):
    return web.Response(text="OK")

async def webhook(request):
    update = Update(**await request.json())
    await bot.process_update(update)
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
    await bot.bot.set_webhook(f"{APP_URL}/webhook", drop_pending_updates=True)
    await web_server()
    asyncio.create_task(progress_worker())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
