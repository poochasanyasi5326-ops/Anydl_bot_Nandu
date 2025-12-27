from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import os
import aiohttp
from helper_funcs.display import progress_for_pyrogram

@Client.on_message(filters.private & (filters.regex(r'^http') | filters.regex(r'^magnet')))
async def download_handler(client, message):
    url = message.text.strip()
    
    # Check for Rename (User sends: link | new_name.mp4)
    custom_name = None
    if "|" in url:
        url, custom_name = url.split("|")
        url = url.strip()
        custom_name = custom_name.strip()

    status_msg = await message.reply_text("🔎 Processing...", quote=True)
    start_time = time.time()

    # Define path
    download_path = "downloads/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # Simple Direct Download Logic (For http links)
    try:
        filename = custom_name if custom_name else url.split("/")[-1]
        file_path = os.path.join(download_path, filename)

        await status_msg.edit(f"⬇️ Downloading: `{filename}`")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024) # 1MB chunks
                            if not chunk: break
                            f.write(chunk)
                else:
                    await status_msg.edit("❌ Error: Could not connect to link.")
                    return

        # Upload Logic
        await status_msg.edit("📤 Uploading...")
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"**File:** `{filename}`",
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg, start_time),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Rename ✏️", callback_data="rename_help")],
                [InlineKeyboardButton("Cancel ❌", callback_data="cancel")]
            ])
        )
        
        await status_msg.delete()
        os.remove(file_path) # Clean up

    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")

# Button Handler
@Client.on_callback_query()
async def button_handler(client, callback_query):
    data = callback_query.data
    if data == "cancel":
        await callback_query.message.edit("❌ Task Cancelled.")
    elif data == "rename_help":
        await callback_query.answer("To rename, send: Link | Name.mp4", show_alert=True)
