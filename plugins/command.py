import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
OWNER_ID = 519459195  
AUTH_USERS = [OWNER_ID] 

def is_authorized(user_id):
    return user_id in AUTH_USERS

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Identify Role
    role = "👑 Owner" if user_id == OWNER_ID else "👤 Authorized User"
    if not is_authorized(user_id): role = "🚫 Guest"

    welcome_text = (
        f"👋 **Welcome, {user_name}!**\n\n"
        f"✨ **Role:** `{role}`\n"
        f"🤖 **Bot Status:** Online & Ready\n\n"
        "Send me any Magnet, Torrent, or YouTube link to start."
    )

    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/your_username"),
            InlineKeyboardButton("🆔 My ID", callback_data="show_id")
        ],
        [
            InlineKeyboardButton("📊 Check Storage", callback_data="check_disk"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ]

    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons), quote=True)

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    used_gb = round(used / (2**30), 2)
    
    status_text = (
        "📊 **Server Storage Status**\n\n"
        f"✅ **Available:** `{free_gb} GB`\n"
        f"❌ **Used:** `{used_gb} GB`\n"
        f"📈 **Total:** 16 GB\n\n"
        "Tip: Ensure the file size is less than available space."
    )
    await query.message.edit(status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("show_id"))
async def show_id_callback(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("show_help"))
async def help_callback(client, query: CallbackQuery):
    help_text = "📖 **Help Menu**\n\n1️⃣ Paste links directly.\n2️⃣ Use /set_thumb for thumbnails.\n3️⃣ Check storage before big files."
    await query.message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    await start_command(client, query.message)
