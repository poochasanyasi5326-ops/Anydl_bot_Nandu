import os
import random
import shutil
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 
OWNER_MESSAGES = ["🚀 System Online, Boss!", "🤖 Ready to work.", "✨ Welcome back!"]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        owner_buttons = [
            [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
             InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
            [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
             InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")]
        ]
        return await message.reply_text(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))
    
    await message.reply_text("🛑 **Access Denied.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")]]))

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    owner_buttons = [[InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"), InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
                     [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"), InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")]]
    await query.message.edit(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))
    await query.answer()

@Client.on_callback_query(filters.regex("reboot_bot"))
async def reboot_handler(client, query):
    await query.answer("🔄 Rebooting...", show_alert=True)
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)
    os.execl(sys.executable, sys.executable, *sys.argv)
