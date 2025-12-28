import random
import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 

# Rotating messages for the Owner
OWNER_MESSAGES = [
    "👋 **Welcome Boss!**\nSystem is ready for your links.",
    "🚀 **All Systems Go!**\nI'm standing by for your next download.",
    "🤖 **Ready for Duty!**\nPaste a link and let's get to work, Boss.",
    "✨ **Welcome back!**\nEverything is clear. Send me a link to start."
]

# Rotating messages for Unauthorized Users
UNAUTH_MESSAGES = [
    "User, welcome to my bot. It fetchs links and downloads strictly for me.",
    "Access Denied. This bot is a private tool built for my personal use.",
    "Welcome! Note that this bot only processes downloads for its owner.",
    "Hello! This is a private instance. All functions are locked to the owner."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    # 1. Logic for Unauthorized Users
    if not is_authorized(user_id):
        unauth_text = random.choice(UNAUTH_MESSAGES)
        unauth_buttons = [[
            InlineKeyboardButton("🆔 My ID", callback_data="show_user_id"),
            InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")
        ]]
        return await message.reply_text(unauth_text, reply_markup=InlineKeyboardMarkup(unauth_buttons))

    # 2. Logic for the Owner
    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Check Storage", callback_data="check_disk")],
        [InlineKeyboardButton("🆔 My ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))
