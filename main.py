import os
import asyncio
from pyrogram import Client
from aiohttp import web

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def handle(request):
    return web.Response(text="Bot is Active 🚀")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

class AnyDLBot(Client):
    def __init__(self):
        super().__init__(
            name="anydl_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50
        )

    async def start(self):
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        await super().start()
        await start_web_server()

if __name__ == "__main__":
    AnyDLBot().run()
