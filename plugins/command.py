import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
# This ensures task_manager.py can find the owner and the authorization function
OWNER_ID = 519459195  

def is_authorized(user_id):
    """Checks if the user is the owner (519459195)"""
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    # Security: Usage is restricted only to you
    if not is_authorized(message.from_user.id):
        return await message.reply("🚫 Access Denied. This bot is private.")

    welcome_text = (
        f"👋 **Welcome back, Boss!**\n\n"
        f"👤 **Role:** `👑 Owner`\n"
        f"🆔 **Your ID:** `{message.from_user.id}`\n\n"
        f"📟 **System Status:** Online ✅\n"
        f"💾 **Storage Capacity:** 16 GB\n\n"
        "👇 **Select an option below:**"
    )

    # Inline Keyboard Layout
    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/your_username"), # Change your_username
            InlineKeyboardButton("🆔 My ID", callback_data="show_my_id")
        ],
        [
            InlineKeyboardButton("📊 Check Storage", callback_data="check_disk"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ]

    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(buttons), # Renders buttons
        quote=True
    )

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    # Real-time monitoring of the 16GB Koyeb disk
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    used_gb = round(used / (2**30), 2)
    
    status_text = (
        "📊 **Real-Time Storage Monitor**\n\n"
        f"✅ **Available:** `{free_gb} GB`\n"
        f"❌ **Used:** `{used_gb} GB`\n"
        f"📈 **Total Quota:** 16.0 GB\n\n"
        "⚠️ *Files are auto-cleaned after every upload.*"
    )
    await query.message.edit(
        status_text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

@Client.on_callback_query(filters.regex("show_my_id"))
async def show_id_callback(client, query: CallbackQuery):
    # This identifies the user clicking the button
    await query.answer(f"Your Telegram ID: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("show_help"))
async def help_callback(client, query: CallbackQuery):
    help_text = (
        "📖 **AnyDL Bot Guide**\n\n"
        "1️⃣ **Magnets:** Just paste the link. Bot will add trackers automatically.\n"
        "2️⃣ **YouTube:** Paste URL. Extracts best Audio + Video.\n"
        "3️⃣ **Rename:** Click 'Rename' on the dashboard before starting the download.\n"
        "4️⃣ **Security:** All functions are exclusive to the Owner."
    )
    await query.message.edit(
        help_text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    # Refreshes the main menu
    await start_command(client, query.message)
