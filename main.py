import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 519459195  # your Telegram ID

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing API credentials")

bot = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def owner_only(func):
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            await message.reply_text("⛔ Unauthorized")
            return
        return await func(client, message)
    return wrapper

@bot.on_message(filters.command("start"))
@owner_only
async def start_handler(_, message):
    await message.reply_text(
        "✅ AnyDL Bot is running.\n\n"
        "Send a YouTube link to begin."
    )

async def main():
    while True:
        try:
            await bot.start()
            print("✅ Bot started and polling")
            await idle()   # BLOCKS FOREVER
            break
        except FloodWait as e:
            print(f"⚠️ FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
