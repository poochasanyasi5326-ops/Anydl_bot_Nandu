import os
import random
import shutil
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

# --- Configuration ---
OWNER_ID = 519459195 

OWNER_MESSAGES = [
    "🚀 **System Online.** Ready to download the internet, Boss?",
    "🤖 **Beep Boop.** Your digital slave is at your service.",
    "✨ **Welcome back, Overlord.** The servers are humming.",
    "🎩 **At your service!** Ready when you are."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

# --- Start Command Handler ---
@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    # 9. Start Response (Authorized)
    if is_authorized(user_id):
        welcome_text = random.choice(OWNER_MESSAGES)
        owner_buttons = [
            [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
             InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")], # 1. View Thumb
            [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
             InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")], # 10. Reboot
            [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
        ]
        return await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

    # 9. Start Response (Unauthorized / Guest)
    guest_text = (
        "🛑 **Access Denied.**\n\n"
        "This is a private bot reserved for the administrator. "
        "Your request has been logged.\n\n"
        f"🆔 **Your ID:** `{user_id}`"
    )
    guest_buttons = [[InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")]]
    await message.reply_text(guest_text, reply_markup=InlineKeyboardMarkup(guest_buttons))

# --- Help Menu ---
@Client.on_callback_query(filters.regex("show_help"))
async def show_help_callback(client, query: CallbackQuery):
    help_text = (
        "📖 **AnyDL Bot Manual**\n\n"
        "**Thumbnail Management:**\n"
        "• `/setthumbnail` - Reply to photo to save.\n"
        "• `/clearthumbnail` - Reset to default.\n"
        "• **View Thumb** - Check current image in menu.\n\n"
        "**Download Features:**\n"
        "• **Youtube**: Select Audio/Video/File sizes.\n"
        "• **Magnets**: Auto-detects and uses Aria2.\n"
        "• **Rename/Cancel**: Buttons available for every task."
    )
    await query.message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

# --- Feature 1: Thumbnail Management ---
@Client.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if not is_authorized(message.from_user.id): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("❌ Reply to a photo.")
    
    os.makedirs("downloads", exist_ok=True)
    path = f"downloads/{message.from_user.id}_thumb.jpg"
    await message.reply_to_message.download(file_name=path)
    await message.reply_text("✅ **Thumbnail Saved!**")

@Client.on_message(filters.command("clearthumbnail") & filters.private)
async def clear_thumb(client, message):
    path = f"downloads/{message.from_user.id}_thumb.jpg"
    if os.path.exists(path):
        os.remove(path)
        await message.reply_text("🗑️ Thumbnail Cleared.")
    else:
        await message.reply_text("❌ No thumbnail found.")

@Client.on_callback_query(filters.regex("view_thumb"))
async def view_thumb(client, query):
    path = f"downloads/{query.from_user.id}_thumb.jpg"
    if os.path.exists(path):
        await query.message.reply_photo(path, caption="🖼️ Current Custom Thumbnail")
    else:
        await query.answer("❌ No custom thumbnail found.", show_alert=True)

# --- Feature 10: Disk Reboot ---
@Client.on_callback_query(filters.regex("reboot_bot"))
async def reboot_handler(client, query):
    await query.message.edit("🔄 **Rebooting...** Cleaning 35GB cache.")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- Storage Check (MISSING IN YOUR CODE) ---
@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    storage_info = (f"📊 **System Storage Status**\n\nTotal: `{humanbytes(total)}`"
                    f"\nUsed: `{humanbytes(used)}`"
                    f"\nFree: `{humanbytes(free)}`")
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

# --- Navigation (FIXED) ---
@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    # We must explicitly rebuild the menu because query.message comes from the Bot, not the User.
    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
         InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
         InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await query.message.edit(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("show_user_id"))
async def show_user_id(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)
