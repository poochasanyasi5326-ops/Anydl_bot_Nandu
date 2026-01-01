import os
import asyncio
from dotenv import load_dotenv

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing API_ID / API_HASH / BOT_TOKEN")

# -------------------------------------------------
# Pyrogram client (POLLING ONLY)
# -------------------------------------------------
bot = Client(
    name="anydl_personal",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------------------------------------
# Commands
# -------------------------------------------------
@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    await message.reply_text(
        "✅ AnyDL bot is running.\nSend a YouTube or direct link."
    )

@bot.on_message(filters.command("help"))
async def help_handler(_, message):
    await message.reply_text(
        "/start - Check bot status\n"
        "/help - Show this message\n\n"
        "Send a supported link to begin."
    )

# -------------------------------------------------
# Lifecycle (FloodWait safe)
# -------------------------------------------------
async def main():
    while True:
        try:
            await bot.start()
            print("✅ Bot started and polling")
            await idle()          # KEEP PROCESS ALIVE
            break
        except FloodWait as e:
            print(f"⚠️ FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            await asyncio.sleep(10)

    await bot.stop()

# -------------------------------------------------
# Entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
