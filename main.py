import os
import asyncio
from pyrogram import Client
from aiohttp import web

# --- FAKE SERVER FOR KOYEB HEALTH CHECKS ---
async def health_check(request):
    return web.Response(text="AnyDL is Online")

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
# Using the 'plugins' dict tells Pyrogram to automatically import everything in /plugins
app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
    plugins=dict(root="plugins") 
)

async def main():
    # 1. Start web server first so Koyeb doesn't restart us
    await start_server()
    
    # 2. Start the Telegram Bot
    async with app:
        print("✅ AnyDL Bot is connected to Telegram and listening for updates")
        # 3. Keep the event loop running
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
