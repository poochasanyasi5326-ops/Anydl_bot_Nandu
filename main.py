import os
import asyncio
from pyrogram import Client
from aiohttp import web

# Credentials from Environment Variables
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "abcdef")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "123:abc")

async def handle(request):
    return web.Response(text="Bot is running! 🚀")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

class AnyDLBot(Client):
    def __init__(self):
        super().__init__(
            name="anydl_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"), # Loads command.py and task_manager.py
            workers=50
        )

    async def start(self):
        await super().start()
        await start_web_server()
        print("✅ Bot and Web Server Started!")

if __name__ == "__main__":
    # Ensure the downloads directory exists for your 35GB storage
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    AnyDLBot().run()
