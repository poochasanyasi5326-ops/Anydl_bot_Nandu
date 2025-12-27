from pyrogram import Client
from os import environ
import logging
from aiohttp import web
import asyncio
import os
import time
import shutil

logging.basicConfig(level=logging.INFO)

API_ID = int(environ.get("API_ID", 0))
API_HASH = environ.get("API_HASH")
BOT_TOKEN = environ.get("BOT_TOKEN")
PORT = int(environ.get("PORT", 8000))

app = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    ipv6=False,
    in_memory=True
)

# --- 1. THE AUTO-JANITOR (Keeps Storage Clean) ---
async def clean_trash():
    while True:
        try:
            # Check 'downloads' folder
            folder = "downloads/"
            if os.path.exists(folder):
                now = time.time()
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    # If a file is older than 20 minutes, assume it's "stuck" and delete it
                    # (We give 20 mins because large files take time to upload)
                    if os.path.getctime(file_path) < (now - 1200):
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        print(f"🗑️ Auto-Cleaned Stuck File: {filename}")
        except Exception as e:
            print(f"⚠️ Cleaner Error: {e}")
        
        # Sleep for 60 seconds before checking again
        await asyncio.sleep(60)

# --- 2. FAKE WEB SERVER (For Koyeb Health Check) ---
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Running!")
    server = web.Application()
    server.router.add_get("/", handle)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🕸️ Fake Web Server started on Port {PORT}")

# --- 3. MAIN STARTUP ---
async def main():
    print("⚡ Starting Aria2 (Torrent Engine)...")
    os.system("aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --daemon")
    
    # Clean downloads folder on startup (In case it crashed last time)
    if os.path.exists("downloads/"):
        shutil.rmtree("downloads/")
        os.makedirs("downloads/")
        print("🧹 Startup Cleanup: 'downloads/' folder wiped.")
    
    print("⚡ Starting Bot + Web Server...")
    await app.start()
    
    # Start the Janitor and Server
    asyncio.create_task(web_server())
    asyncio.create_task(clean_trash())
    
    print("✅ Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        print(f"❌ Error: {e}")
