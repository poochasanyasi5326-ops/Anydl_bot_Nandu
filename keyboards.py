from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def rename_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

def upload_type_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶ Stream", callback_data="stream"),
            InlineKeyboardButton("📁 File", callback_data="file")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])
