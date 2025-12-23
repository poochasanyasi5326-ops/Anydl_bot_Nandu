import asyncio
import logging
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from auth import owner_only
from cleanup import cleanup_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

app = Client(
    "anydl-owner-only",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

@app.on_message(filters.private & ~owner_only())
async def unauthorized(_, message):
    await message.reply_text("❌ Not authorized")

@app.on_message(filters.private & owner_only() & filters.command("start"))
async def start(_, message):
    await message.reply_text("✅ Owner-only torrent bot running.")

async def main():
    await app.start()
    asyncio.create_task(cleanup_loop())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
