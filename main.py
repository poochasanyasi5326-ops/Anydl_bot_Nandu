import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait
from aiohttp import web

from yt_handler import handle_youtube
from jobs import JOBS

# ---------------- ENV ----------------
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 519459195
PORT = int(os.getenv("PORT", 8000))

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing API credentials")

# ---------------- BOT ----------------
bot = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- OWNER GUARD ----------------
def owner_only(func):
    async def wrapper(client, message):
        if not message.from_user or message.from_user.id != OWNER_ID:
            await message.reply_text("⛔ Unauthorized")
            return
        return await func(client, message)
    return wrapper

# ---------------- COMMANDS ----------------
@bot.on_message(filters.command("start"))
@owner_only
async def start_handler(_, message):
    await message.reply_text(
        "✅ AnyDL Phase-1 is running\n\n"
        "• YouTube downloader\n"
        "• Variants + Rename\n"
        "• Progress + Cancel\n"
        "• Screenshot on demand\n\n"
        "Send a YouTube link."
    )

@bot.on_message(filters.text & ~filters.command)
@owner_only
async def link_handler(client, message):
    if "youtu" in message.text:
        await handle_youtube(client, message)
    else:
        await message.reply_text("❌ Unsupported link")

# ---------------- HEALTH SERVER ----------------
async def health(request):
    return web.Response(text="OK")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# ---------------- MAIN ----------------
async def main():
    await start_health_server()

    while True:
        try:
            await bot.start()
            print("✅ Bot started and polling")
            await idle()
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print("Fatal:", e)
            await asyncio.sleep(5)

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    asyncio.run(main())
