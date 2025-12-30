import os
import asyncio
from aiohttp import web
from pyrogram import Client
from pyrogram.types import Update

# ===== Environment Variables =====
BOT_TOKEN = os.environ["BOT_TOKEN"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

APP_URL = os.environ["APP_URL"]          # https://your-app.koyeb.app
PORT = int(os.environ.get("PORT", 8000))

WEBHOOK_PATH = "/webhook"

# ===== Pyrogram Client =====
bot = Client(
    name="anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

# ===== HTTP Handlers =====
async def health(request):
    return web.Response(text="OK")

async def telegram_webhook(request):
    data = await request.json()
    update = Update(**data)
    await bot.process_update(update)
    return web.Response(text="OK")

# ===== Web Server =====
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# ===== Main =====
async def main():
    await bot.start()

    await bot.bot.set_webhook(
        url=f"{APP_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True
    )

    await start_web_server()

    print("✅ AnyDL Bot running via Telegram Webhook")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
