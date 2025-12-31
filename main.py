# ===================== FINAL main.py =====================
# Koyeb-safe Telegram bot (NO polling, NO crash loop)

import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Update

# ------------------ ENV ------------------
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

APP_URL = os.environ.get("APP_URL")   # OPTIONAL now
PORT = int(os.environ.get("PORT", 8000))

# ------------------ BOT ------------------
bot = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ------------------ BASIC HANDLER ------------------
@bot.on_message(filters.command("start"))
async def start_handler(_, m):
    await m.reply_text("✅ Bot is alive.")

# ------------------ HTTP ------------------
async def health(_):
    return web.Response(text="OK")

async def telegram_webhook(request):
    update = Update(**await request.json())
    await bot.process_update(update)
    return web.Response(text="OK")

async def start_http():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post("/webhook", telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🌍 Health check server live on port {PORT}")

# ------------------ MAIN ------------------
async def main():
    await bot.start()

    if APP_URL:
        await bot.bot.set_webhook(
            url=f"{APP_URL}/webhook",
            drop_pending_updates=True
        )
        print(f"🔗 Webhook set to {APP_URL}/webhook")
    else:
        print("⚠️ APP_URL not set — webhook NOT registered")
        print("⚠️ Bot will not receive updates until APP_URL is set")

    await start_http()
    print("✅ Service running (no polling)")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

# =================== END ===================
