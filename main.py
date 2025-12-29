import os
import asyncio
from pyrogram import Client
from plugins.command import register

print("🚀 AnyDL starting (main.py)")

app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

async def main():
    async with app:
        register(app)
        print("✅ Bot started successfully")
        # This keeps the bot running until the process is killed
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
