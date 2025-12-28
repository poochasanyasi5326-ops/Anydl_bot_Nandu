import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

OWNER_ID = 519459195  

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("🚫 Unauthorized Access.")

    welcome_text = (
        "👋 **Welcome Boss!**\n\n"
        "✨ **Role:** `👑 Owner`\n"
        "📟 **System Status:** Online ✅\n\n"
        "Send me a link or use the buttons below to manage the server."
    )

    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Owner", url="https://t.me/your_username"),
            InlineKeyboardButton("🆔 My ID", callback_data="show_my_id")
        ],
        [
            InlineKeyboardButton("📊 Check Storage", callback_data="check_disk"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    # Live monitoring of the actual server storage
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    used_gb = round(used / (2**30), 2)
    total_gb = round(total / (2**30), 2)
    
    status_text = (
        "📊 **Real-Time Storage Monitor**\n\n"
        f"✅ **Available:** `{free_gb} GB`\n"
        f"❌ **Used:** `{used_gb} GB`\n"
        f"📈 **Server Capacity:** `{total_gb} GB`\n\n"
        "⚠️ *Note: Bot will auto-clean files after upload.*"
    )
    await query.message.edit(status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex("show_help"))
async def help_callback(client, query: CallbackQuery):
    help_text = (
        "📖 **Bot Command List**\n\n"
        "⚡ **Magnets:** Paste link -> Bot adds trackers -> Progress shows -> Uploads.\n"
        "⚡ **YouTube:** Paste link -> Downloads Video+Audio -> Extracts metadata.\n"
        "⚡ **Rename:** Send link -> Click 'Rename' before starting.\n"
        "⚡ **Screenshots:** Automatically generated for videos."
    )
    await query.message.edit(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))

@Client.on_callback_query(filters.regex(r"show_my_id|back_to_start"))
async def back_handler(client, query: CallbackQuery):
    if query.data == "show_my_id":
        await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)
    else:
        await start_command(client, query.message)
