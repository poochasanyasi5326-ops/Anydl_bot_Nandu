import os
import random
import shutil
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 

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
    if not is_authorized(message.from_user.id):
        return await message.reply_text("🛑 **Access Denied.**")

    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
         InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
         InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("show_help"))
async def show_help_callback(client, query: CallbackQuery):
    help_text = (
        "📖 **AnyDL Bot Manual**\n\n"
        "• `/setthumbnail` - Reply to a photo to save it.\n"
        "• `/clearthumbnail` - Delete custom thumbnail.\n"
        "• `Paste Link` - Supports YT, Magnets, Torrents, Direct URLs.\n\n"
        "**Features:**\n"
        "• **Rename/Cancel**: Available for every task.\n"
        "• **Storage**: 35GB Auto-cleaning environment."
    )
    await query.message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("view_thumb"))
async def view_thumb(client, query):
    path = f"downloads/{query.from_user.id}_thumb.jpg"
    if os.path.exists(path):
        await query.message.reply_photo(path, caption="🖼️ Current Custom Thumbnail")
    else:
        await query.answer("❌ No custom thumbnail found.", show_alert=True)

@Client.on_callback_query(filters.regex("reboot_bot"))
async def reboot_handler(client, query):
    await query.message.edit("🔄 Cleaning cache and rebooting...")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query):
    total, used, free = shutil.disk_usage("/")
    await query.message.edit(f"📊 **Storage:**\nTotal: {humanbytes(total)}\nFree: {humanbytes(free)}", 
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query):
    owner_buttons = [[InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"), InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
                     [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"), InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")]]
    await query.message.edit(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))
