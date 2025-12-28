import os
import random
import shutil
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes  # This import is now safe 

# --- Configuration ---
OWNER_ID = 519459195 

OWNER_MESSAGES = [
    "🚀 **System Online.** Ready to download the internet, Boss?",
    "🤖 **Beep Boop.** Your digital slave is at your service.",
    "✨ **Welcome back, Overlord.** The servers are humming."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

# --- Main Start Menu (Requirement 9) ---
@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    if is_authorized(user_id):
        welcome_text = random.choice(OWNER_MESSAGES)
        owner_buttons = [
            [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
             InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")], # Requirement 1
            [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
             InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")], # Requirement 10
            [InlineKeyboardButton("🆔 My ID", callback_data="show_user_id")]
        ]
        return await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

    # Guest Block logic
    guest_text = "🛑 **Access Denied.** This is a private bot.\n\n🆔 **Your ID:** `{}`".format(user_id)
    guest_buttons = [[InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")]]
    await message.reply_text(guest_text, reply_markup=InlineKeyboardMarkup(guest_buttons))

# --- Button Callbacks (Fixes Unresponsive Buttons) ---
@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    # Manual rebuild to prevent User ID mismatch bugs
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
         InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
         InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")]
    ]
    await query.message.edit(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))
    await query.answer() # CRITICAL: Stops the button from spinning/freezing

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    storage_info = (f"📊 **Storage Status**\n\nTotal: `{humanbytes(total)}`"
                    f"\nUsed: `{humanbytes(used)}`"
                    f"\nFree: `{humanbytes(free)}`")
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
    await query.answer()

# --- Disk Reboot logic (Requirement 10) ---
@Client.on_callback_query(filters.regex("reboot_bot"))
async def reboot_handler(client, query):
    await query.answer("🔄 Rebooting & Cleaning Cache...", show_alert=True)
    shutil.rmtree("downloads", ignore_errors=True) # Clears your 35GB cache
    os.makedirs("downloads", exist_ok=True)
    os.execl(sys.executable, sys.executable, *sys.argv) # Hard restart
