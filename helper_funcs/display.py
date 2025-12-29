import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LAST_EDIT = {}

async def edit_download_progress(message, percent, job_id):
    now = time.time()
    if now - LAST_EDIT.get(job_id, 0) < 10:
        return
    LAST_EDIT[job_id] = now

    await message.edit_text(
        f"⬇️ Downloading\n\nProgress: {percent:.2f}%",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{job_id}")]
        ])
    )

async def edit_upload_progress(message, current=None, total=None, job_id=None, cancelled=None, stage=None):
    if cancelled and cancelled():
        raise Exception("Cancelled")

    now = time.time()
    if now - LAST_EDIT.get(job_id, 0) < 10:
        return
    LAST_EDIT[job_id] = now

    if current and total:
        percent = (current / total) * 100
        await message.edit_text(
            f"⬆️ Uploading\n\nProgress: {percent:.2f}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{job_id}")]
            ])
        )

async def final_message(message, text):
    await message.edit_text(text)
