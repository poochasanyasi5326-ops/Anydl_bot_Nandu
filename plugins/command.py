import os
import random
import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 

# Sarcastic & Witty messages for the Owner
OWNER_MESSAGES = [
    "🚀 **System Online.** Ready to download the internet, Boss?",
    "🤖 **Beep Boop.** Your digital slave is at your service.",
    "✨ **Welcome back, Overlord.** The servers are humming.",
    "🎩 **At your service!** Ready when you are.",
    "🛰 **GPS Locked.** Paste the link, Captain."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply_text("🛑 **Access Denied.** This is a private bot.")

    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("show_help"))
async def show_help_callback(client, query: CallbackQuery):
    help_text = (
        "📖 **AnyDL Bot Manual**\n\n"
        "**Available Commands:**\n"
        "• `/start` - Open the main control menu.\n"
        "• `/setthumbnail` - Reply to a photo to save it as a permanent thumbnail.\n"
        "• `/clearthumbnail` - Delete your custom thumbnail.\n"

        "**Features:**\n"
        "• **Rename**: Change filenames before the final upload.\n"
        "• **Audio Mode**: Extract MP3s from any video link.\n"
        "• **Storage**: You have ~35GB total space for processing.\n\n"
        "• `Paste Link` - Send any YouTube, Magnet, or Direct URL.\n\n"
        "🧹 *Note: All files are automatically deleted after upload to save space.*"
    )
    await query.message.edit(
        help_text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )
    await query.answer()

# --- Thumbnail Logic ---

@Client.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if not is_authorized(message.from_user.id):
        return
    
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("❌ Please **reply** to a photo to set it as a thumbnail.")
    
    # Ensure downloads directory exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    thumb_path = os.path.join("downloads", f"{message.from_user.id}_thumb.jpg")
    await message.reply_to_message.download(file_name=thumb_path)
    await message.reply_text("✅ **Custom thumbnail saved!** It will be applied to all your future uploads.")

@Client.on_message(filters.command("clearthumbnail") & filters.private)
async def clear_thumb(client, message):
    if not is_authorized(message.from_user.id):
        return
        
    thumb_path = os.path.join("downloads", f"{message.from_user.id}_thumb.jpg")
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply_text("🗑️ **Custom thumbnail cleared.** Switching back to auto-generated thumbs.")
    else:
        await message.reply_text("❌ You don't have a custom thumbnail set.")

# --- Disk & ID Logic ---

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    storage_info = (
        f"📊 **System Storage Status**\n\n"
        f"Total: `{humanbytes(total)}` (Your instance limit)\n"
        f"Used: `{humanbytes(used)}`\n"
        f"Free: `{humanbytes(free)}`"
    )
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
    await query.answer()

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await query.message.edit(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("show_user_id"))
async def show_user_id(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)
