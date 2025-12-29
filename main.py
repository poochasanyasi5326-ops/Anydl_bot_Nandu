import os
import asyncio
from pyrogram import Client
from plugins.command import register
from aiohttp import web

# --- FAKE SERVER FOR KOYEB HEALTH CHECKS ---
async def health_check(request):
    return web.Response(text="Bot is Alive")

async def start_server():
    server = web.Application()
    server.router.add_get("/", health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    # Koyeb sends health checks to the PORT env variable (default 8000)
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌍 Health check server live on port {port}")

# --- BOT INITIALIZATION ---
app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

async def main():
    # 1. Start the web server so Koyeb health check passes
    await start_server()
    
    # 2. Start the Telegram Bot
    async with app:
        register(app)
        print("✅ AnyDL Bot is online and healthy")
        # 3. Keep everything running forever
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
