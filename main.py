import os
import asyncio
import re
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

# ------------------ ENV ------------------
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 519459195  # YOUR Telegram ID

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing API credentials")

# ------------------ BOT ------------------
bot = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ------------------ OWNER GUARD ------------------
def owner_only(func):
    async def wrapper(client, message):
        if not message.from_user or message.from_user.id != OWNER_ID:
            await message.reply_text("⛔ Unauthorized")
            return
        return await func(client, message)
    return wrapper

# ------------------ HELP TEXT ------------------
HELP_TEXT = (
    "🎬 **AnyDL Bot – Phase 1**\n\n"
    "✅ Owner-only bot\n"
    "✅ YouTube link detection\n"
    "🚧 Variants, rename, progress: coming next\n\n"
    "Send a YouTube link to begin."
)

# ------------------ COMMANDS ------------------
@bot.on_message(filters.command("start"))
@owner_only
async def start_handler(_, message):
    await message.reply_text(HELP_TEXT)

# ------------------ YOUTUBE LINK HANDLER (PHASE 1) ------------------
YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
)

@bot.on_message(filters.text & ~filters.command(["start"]))
@owner_only
async def youtube_handler(_, message):
    text = message.text.strip()

    if not YOUTUBE_REGEX.match(text):
        await message.reply_text("❌ Not a YouTube link.")
        return

    # Phase-1 response (no download yet)
    await message.reply_text(
        "📥 **YouTube link received**\n\n"
        "Phase-1 active:\n"
        "• Link validated\n"
        "• Job registered in memory\n\n"
        "🚧 Next steps (Phase-2):\n"
        "• Quality selection buttons\n"
        "• Rename\n"
        "• Progress tracker\n"
        "• Upload options"
    )

# ------------------ MAIN ------------------
async def main():
    while True:
        try:
            await bot.start()
            print("✅ Bot started and polling")
            await idle()  # BLOCK FOREVER
        except FloodWait as e:
            print(f"⚠️ FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            await asyncio.sleep(5)

# ------------------ ENTRY ------------------
if __name__ == "__main__":
    asyncio.run(main())
