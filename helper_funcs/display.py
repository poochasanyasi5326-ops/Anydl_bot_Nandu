import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LAST_EDIT = {}

async def edit_progress(message, text, job_id):
    now = time.time()
    if now - LAST_EDIT.get(job_id, 0) < 10:
        return
    LAST_EDIT[job_id] = now

    await message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{job_id}")]
        ])
    )

async def final_message(message, text):
    await message.edit_text(text)
