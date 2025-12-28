import os
from pyrogram import Client
from aiohttp import web
import asyncio

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "abcdef")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "123:abc")

# --- KEEPALIVE WEB SERVER ---
# Koyeb requires an open port to stay "Healthy"
async def handle(request):
    return web.Response(text="Bot is running! 🚀")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# --- START BOT ---
class Bot(Client):
    def __init__(self):
        super().__init__(
            name="anydl_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"), # This loads command.py and task_manager.py
            workers=50
        )

    async def start(self):
        await super().start()
        print("✅ Bot Started Successfully!")
        await start_web_server()
        print("🕸️ Fake Web Server started on Port 8000")

    async def stop(self, *args):
        await super().stop()
        print("❌ Bot Stopped.")

if __name__ == "__main__":
    app = Bot()
    app.run()
