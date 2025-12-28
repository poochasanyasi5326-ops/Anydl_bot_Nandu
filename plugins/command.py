from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

OWNER_ID = 519459195  # Your ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    # Check for Unauthorized User
    if user_id != OWNER_ID:
        unauth_text = (
            "User welcome to my bot\n"
            "the bot basically works for me to fetch any sort of \n"
            "links and download strictly made for me"
        )
        # Unauthorized Buttons
        unauth_buttons = [
            [
                InlineKeyboardButton("🆔 My ID", callback_data="show_user_id"),
                InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")
            ]
        ]
        return await message.reply_text(unauth_text, reply_markup=InlineKeyboardMarkup(unauth_buttons))

    # --- AUTHORIZED OWNER CONTENT ---
    welcome_text = "👋 **Welcome Boss!**\nSystem is ready for your links."
    owner_buttons = [
        [InlineKeyboardButton("📊 Check Storage", callback_data="check_disk")],
        [InlineKeyboardButton("🆔 My ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_callback_query(filters.regex("show_user_id"))
async def show_id_callback(client, query: CallbackQuery):
    # This works for both you and unauthorized users
    await query.answer(f"Your ID is: {query.from_user.id}", show_alert=True)
