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
    role = "👑 Owner" if user_id == OWNER_ID else "👤 Authorized User"
    
    welcome_text = (
        f"👋 **Welcome back, Boss!**\n\n"
        f"👤 **Role:** `{role}`\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"📟 **System Status:** Online ✅\n"
        f"💾 **Storage:** Secure\n\n"
        "👇 **Select an option below:**"
    )

    # Creating the Inline Keyboard
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

    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(buttons), # This loads the keyboard
        quote=True
    )

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    status_text = f"📊 **Storage Status**\n\n✅ **Available:** `{free_gb} GB`\n📈 **Total Capacity:** 16 GB"
    await query.message.edit(status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("show_id"))
async def show_id_callback(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    await start_command(client, query.message)
