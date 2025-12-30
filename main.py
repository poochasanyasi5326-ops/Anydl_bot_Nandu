import os
import asyncio
from pyrogram import Client
from aiohttp import web

# --- FAKE SERVER FOR KOYEB ---
async def health_check(request):
    return web.Response(text="AnyDL is Alive")

async def start_server():
    server = web.Application()
    server.router.add_get("/", health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- BOT CONFIG ---
app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    plugins=dict(root="plugins")
)

async def main():
    await start_server()
    print("🌍 Health Server on port 8000")
    async with app:
        print("✅ Bot is Online")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
