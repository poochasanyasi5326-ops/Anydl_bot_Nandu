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

# Funny 'Gatekeeper' messages for Unauthorized Users
UNAUTH_MESSAGES = [
    "🛑 **HALT!** You aren't my creator.",
    "🕵️‍♂️ **Access Denied.** My owner told me about people like you.",
    "🛡 **SYSTEM ERROR:** User is too cool for this bot.",
    "🤫 **Psst...** I'm a private bot.",
    "🚫 **Error 404: Permission Not Found.**",
    "⚠️ **Warning:** Sarcasm levels too high for guest access."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        unauth_text = random.choice(UNAUTH_MESSAGES)
        unauth_buttons = [[
            InlineKeyboardButton("🆔 Who am I?", callback_data="show_user_id"),
            InlineKeyboardButton("👨‍💻 Complain to Boss", url="https://t.me/poocha")
        ]]
        return await message.reply_text(unauth_text, reply_markup=InlineKeyboardMarkup(unauth_buttons))

    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    storage_info = (
        f"📊 **System Storage Status**\n\n"
        f"Total: `{humanbytes(total)}` (16GB Limit)\n"
        f"Used: `{humanbytes(used)}`\n"
        f"Free: `{humanbytes(free)}`"
    )
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
    await query.answer()

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    await start_handler(client, query.message)

@Client.on_callback_query(filters.regex("show_user_id"))
async def show_user_id(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)
