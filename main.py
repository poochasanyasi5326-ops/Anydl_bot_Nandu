import os
import asyncio
from pyrogram import Client
from plugins.command import register

print("🚀 AnyDL starting (main.py – async loop)")

app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

async def main():
    await app.start()
    register(app)
    print("✅ Bot started successfully")
    while True:
        await asyncio.sleep(3600)

asyncio.run(main())
