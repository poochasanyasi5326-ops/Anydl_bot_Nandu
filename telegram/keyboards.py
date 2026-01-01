from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def format_keyboard(formats):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=name, callback_data=f"fmt|{fid}")]
        for fid, name in formats
    ])

def rename_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Stream", callback_data="stream"),
         InlineKeyboardButton("📁 File", callback_data="file")],
        [InlineKeyboardButton("📸 Screenshots", callback_data="shots")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])
