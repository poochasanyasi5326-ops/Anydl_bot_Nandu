import os
import asyncio
from pyrogram import Client
from aiohttp import web

# --- HEALTH CHECK SERVER FOR KOYEB ---
async def health_check(request):
    return web.Response(text="Bot is Alive and Healthy")

async def start_server():
    server = web.Application()
    server.router.add_get("/", health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- BOT INITIALIZATION ---
app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    plugins=dict(root="plugins") # Automatically loads files in /plugins
)

async def main():
    await start_server()
    print("🌍 Health check server live on port 8000")
    
    async with app:
        print("✅ AnyDL Bot is online. Testing connection...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
