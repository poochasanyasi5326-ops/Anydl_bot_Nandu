import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

# Load env vars
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Fail fast if misconfigured
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise RuntimeError("Missing API_ID / API_HASH / BOT_TOKEN")

bot = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "✅ Bot is running.\nSend a supported link to begin."
    )

async def main():
    while True:
        try:
            await bot.start()
            print("✅ Bot started successfully")
            await idle()          # BLOCK FOREVER
            break
        except FloodWait as e:
            print(f"⚠️ FloodWait: sleeping {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            await asyncio.sleep(10)

    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
