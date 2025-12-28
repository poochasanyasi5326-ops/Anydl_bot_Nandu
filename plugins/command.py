from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# --- CONFIGURATION ---
# Replace with your actual Telegram User ID
OWNER_ID = 123456789  
# Authorized users list
AUTH_USERS = [OWNER_ID] 

# Simple memory for thumbnails
USER_THUMBS = {}

def is_authorized(user_id):
    return user_id in AUTH_USERS

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Determine Role
    role = "👑 Owner" if user_id == OWNER_ID else "👤 Authorized User"
    if not is_authorized(user_id):
        role = "🚫 Unauthorized"

    welcome_text = (
        f"👋 **Welcome to Anydl Bot, {user_name}!**\n\n"
        f"✨ **Role:** `{role}`\n"
        f"🤖 **Status:** Online & Ready\n\n"
        "I can mirror links, leeach torrents, and download YouTube videos directly to Telegram."
    )

    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/your_username"),
            InlineKeyboardButton("🆔 My ID", callback_data="show_id")
        ],
        [
            InlineKeyboardButton("❓ Help & Commands", callback_data="show_help")
        ]
    ]

    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

@Client.on_callback_query(filters.regex("show_id"))
async def show_id_callback(client, query):
    await query.answer(f"Your ID is: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("show_help"))
async def help_callback(client, query):
    help_text = (
        "📖 **How to use me:**\n\n"
        "1️⃣ **Send a Link:** Paste any Magnet, Torrent, or YouTube link.\n"
        "2️⃣ **Choose Mode:** Select 'Stream' or 'Safe' via buttons.\n"
        "3️⃣ **Commands:**\n"
        "• /set_thumb - Reply to an image to save as thumbnail.\n"
        "• /del_thumb - Delete your saved thumbnail."
    )
    await query.message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query):
    # This calls your start logic again to refresh the menu
    await start_command(client, query.message)
