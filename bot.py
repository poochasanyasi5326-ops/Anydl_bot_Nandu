import asyncio
import logging
import os
from pyrogram import Client, filters

# Load Config
from config import API_ID, API_HASH, BOT_TOKEN, LOG_LEVEL
from auth import owner_only
from cleanup import cleanup_loop

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(levelname)s | %(message)s"
)

SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

# Initialize Client
# We use "anydl_v3" to ensure a totally fresh connection path
if SESSION_STRING:
    print("🎟️ Found Session String! (Forcing IPv4...)")
    app = Client(
        "anydl_v3",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        plugins=dict(root="plugins"), 
        ipv6=False,
        in_memory=True
    )
else:
    print("⚠️ No Session String found. Using Bot Token...")
    app = Client(
        "anydl_v3",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=dict(root="plugins"),
        ipv6=False,
        in_memory=True
    )

@app.on_message(filters.private & filters.command("start") & owner_only())
async def start(client, message):
    await message.reply_text(
        f"✅ **Bot is ONLINE!**\n"
        f"🆔 Your ID: `{message.from_user.id}`\n\n"
        "**Send me:**\n"
        "1. A `.torrent` file\n"
        "2. A YouTube/Direct Link"
    )

@app.on_message(filters.private & ~owner_only())
async def unauthorized(client, message):
    await message.reply_text(f"🔒 **Access Denied**\nYour ID: `{message.from_user.id}` is not in the Owner List.")

async def main():
    print("⚡ Starting Bot...")
    try:
        await app.start()
        print("✅ Bot Started Successfully!")
        
        # We removed the crashing 'delete_webhook' line.
        # The bot is now free to stay alive.
        
        asyncio.create_task(cleanup_loop())
        await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())