import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195  # Your ID

# Function used by task_manager.py to block others
def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    # --- UNAUTHORIZED USER MESSAGE ---
    if not is_authorized(user_id):
        unauth_text = (
            "User welcome to my bot\n"
            "the bot basically works for me to fetch any sort of \n"
            "links and download strictly made for me"
        )
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
    await query.answer(f"Your ID is: {query.from_user.id}", show_alert=True)

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    # Live storage check for your 16GB limit
    total, used, free = shutil.disk_usage("/")
    storage_info = (
        f"📊 **Storage Status**\n\n"
        f"Total: `{humanbytes(total)}` (16GB Limit)\n"
        f"Used: `{humanbytes(used)}`\n"
        f"Free: `{humanbytes(free)}`"
    )
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    ))

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    # Returns the owner to the main menu
    await start_handler(client, query.message)
