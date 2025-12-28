import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

OWNER_ID = 519459195  

def is_authorized(u_id):
    return u_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if not is_authorized(message.from_user.id):
        return await message.reply("🚫 Access Denied. Contact @your_username.")

    welcome_text = (
        f"👋 **Welcome Boss!**\n\n"
        f"👤 **Role:** `👑 Owner`\n"
        f"🆔 **Your ID:** `{message.from_user.id}`\n\n"
        "Paste any link to start the dashboard."
    )

    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/your_username"),
            InlineKeyboardButton("🆔 My ID", callback_data="show_my_id")
        ],
        [
            InlineKeyboardButton("📊 Check Storage", callback_data="check_disk"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        ]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("show_my_id"))
async def show_id(client, query: CallbackQuery):
    await query.answer(f"Your ID: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("check_disk"))
async def disk_usage(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    # Hardcoded 16GB limit for display accuracy
    await query.message.edit(
        f"📊 **Storage Dashboard**\n\n✅ **Free:** `{free_gb} GB`\n📈 **Quota:** `16.0 GB`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

@Client.on_callback_query(filters.regex("back_to_start"))
async def back(client, query: CallbackQuery):
    await start_command(client, query.message)
