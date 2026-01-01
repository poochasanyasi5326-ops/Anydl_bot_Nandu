import os
import asyncio
from dotenv import load_dotenv

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================
# ENV + OWNER
# =====================================================
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 519459195  # 🔒 YOU ONLY

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise RuntimeError("Missing API_ID / API_HASH / BOT_TOKEN")

# =====================================================
# BOT CLIENT (POLLING ONLY)
# =====================================================
bot = Client(
    name="anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =====================================================
# IN-MEMORY STATE (PHASE-1)
# =====================================================
ACTIVE_JOBS = {}   # message_id → job dict
RENAME_WAIT = {}   # user_id → file info

# =====================================================
# AUTH GUARD
# =====================================================
def owner_only(_, __, message):
    return message.from_user and message.from_user.id == OWNER_ID

OWNER_FILTER = filters.create(owner_only)

# =====================================================
# /start
# =====================================================
@bot.on_message(filters.command("start") & OWNER_FILTER)
async def start_handler(_, message):
    await message.reply_text(
        "✅ **AnyDL Bot Ready**\n\n"
        "• Send a YouTube link\n"
        "• Choose quality\n"
        "• Rename before upload\n"
        "• Optional screenshots\n\n"
        "_Owner-only access enabled_",
        quote=True
    )

@bot.on_message(filters.command("start"))
async def blocked_start(_, message):
    await message.reply_text("⛔ Unauthorized access.")

# =====================================================
# LINK HANDLER (PHASE-1 STUB)
# =====================================================
@bot.on_message(filters.text & OWNER_FILTER)
async def link_router(_, message):
    text = message.text.strip()

    if "youtube.com" in text or "youtu.be" in text:
        await message.reply_text(
            "🎬 **YouTube link detected**\n\n"
            "Choose an action:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎞 Variants", callback_data="yt_variants"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ])
        )
    else:
        await message.reply_text("❓ Unsupported link (Phase-1 supports YouTube only)")

# =====================================================
# CALLBACK HANDLER
# =====================================================
@bot.on_callback_query()
async def callbacks(_, query):
    data = query.data

    if data == "cancel":
        await query.message.edit_text("❌ Cancelled.")
        return

    if data == "yt_variants":
        await query.message.edit_text(
            "📥 **Variants will be listed here**\n\n"
            "(yt-dlp integration comes next)",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏ Rename", callback_data="rename"),
                    InlineKeyboardButton("📸 Generate Screenshots", callback_data="shots")
                ],
                [
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ])
        )

    elif data == "rename":
        RENAME_WAIT[query.from_user.id] = True
        await query.message.edit_text(
            "✏ **Send new file name**\n\n"
            "_Extension will be preserved automatically_",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Back", callback_data="yt_variants")]
            ])
        )

    elif data == "shots":
        await query.answer("📸 Screenshot generation will run after download", show_alert=True)

# =====================================================
# RENAME INPUT
# =====================================================
@bot.on_message(filters.text & OWNER_FILTER)
async def rename_input(_, message):
    if message.from_user.id not in RENAME_WAIT:
        return

    new_name = message.text.strip()
    del RENAME_WAIT[message.from_user.id]

    await message.reply_text(
        f"✅ **Rename set:** `{new_name}`\n\n"
        "Upload will start after download.",
        quote=True
    )

# =====================================================
# MAIN LOOP (FloodWait-safe)
# =====================================================
async def main():
    while True:
        try:
            await bot.start()
            print("✅ Bot started (polling mode)")
            await idle()
            break
        except FloodWait as e:
            print(f"FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value)
        except Exception as e:
            print("Fatal error:", e)
            await asyncio.sleep(5)

    await bot.stop()

# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    asyncio.run(main())
