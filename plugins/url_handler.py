from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
import time
import os
import aiohttp
from helper_funcs.display import progress_for_pyrogram
from helper_funcs.ffmpeg import take_screen_shot, get_metadata, generate_screenshots
from plugins.command import USER_THUMBS

# --- TEMPORARY MEMORY (To remember your link) ---
# Format: {user_id: {"url": "http...", "custom_name": "movie.mkv"}}
QUEUE = {}

# 1. STEP ONE: Catch Link & Ask Question
@Client.on_message(filters.private & (filters.regex(r'^http') | filters.regex(r'^https')))
async def ask_upload_mode(client, message):
    url = message.text.strip()
    
    # Check for Rename (Link | Name)
    custom_name = None
    if "|" in url:
        url, custom_name = url.split("|")
        url = url.strip()
        custom_name = custom_name.strip()

    # Save details to memory
    user_id = message.from_user.id
    QUEUE[user_id] = {"url": url, "custom_name": custom_name}

    # Show Buttons
    await message.reply_text(
        "🤔 **How would you like to upload this?**\n\n"
        f"🔗 **Link:** `{url}`\n"
        f"📝 **Name:** `{custom_name if custom_name else 'Default'}`",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎥 Streamable Video", callback_data="mode_video"),
                InlineKeyboardButton("📂 Normal File", callback_data="mode_document")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]),
        quote=True
    )

# 2. STEP TWO: Handle Button Click & Start Download
@Client.on_callback_query(filters.regex(r'^mode_'))
async def handle_download_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Check if we have a link waiting for this user
    if user_id not in QUEUE:
        await callback_query.answer("❌ No active task found. Send link again.", show_alert=True)
        return

    # Get details and clear memory
    task = QUEUE[user_id]
    url = task["url"]
    custom_name = task["custom_name"]
    mode = callback_query.data # "mode_video" or "mode_document"
    
    # Delete the button message to clean up
    await callback_query.message.delete()
    
    # --- START THE PROCESS ---
    status_msg = await callback_query.message.reply_text("🔎 **Processing...**")
    start_time = time.time()
    download_path = "downloads/"
    if not os.path.exists(download_path): os.makedirs(download_path)

    try:
        # A. DOWNLOAD
        filename = custom_name if custom_name else url.split("/")[-1]
        file_path = os.path.join(download_path, filename)

        await status_msg.edit(f"⬇️ **Downloading:** `{filename}`")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk: break
                            f.write(chunk)
                else:
                    await status_msg.edit("❌ Error: Link is broken.")
                    del QUEUE[user_id]
                    return

        # B. PREPARE THUMBNAIL
        await status_msg.edit("⚙️ **Processing...**")
        thumb_path = None
        
        # Check Custom Thumbnail
        if user_id in USER_THUMBS and os.path.exists(USER_THUMBS[user_id]):
            thumb_path = USER_THUMBS[user_id]
        else:
            # Auto-generate if video
            thumb_path = await take_screen_shot(file_path, download_path, 10)

        # C. UPLOAD BASED ON MODE
        await status_msg.edit("📤 **Uploading...**")
        
        if mode == "mode_video":
            # --- VIDEO MODE (Streamable + Screenshots) ---
            width, height, duration = await get_metadata(file_path)
            
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=file_path,
                caption=f"🎥 **Video:** `{filename}`\n⏱️ **Duration:** `{duration}s`",
                thumb=thumb_path,
                width=width,
                height=height,
                duration=duration,
                supports_streaming=True,
                progress=progress_for_pyrogram,
                progress_args=("📤 **Uploading Video...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )
            
            # Send Screenshots for Video
            await status_msg.edit("📸 **Generating Screenshots...**")
            screenshots = await generate_screenshots(file_path, download_path, duration)
            if screenshots:
                await client.send_media_group(
                    chat_id=callback_query.message.chat.id,
                    media=[filters.InputMediaPhoto(s) for s in screenshots]
                )
                for s in screenshots: os.remove(s)

        else:
            # --- DOCUMENT MODE (Normal File) ---
            await client.send_document(
                chat_id=callback_query.message.chat.id,
                document=file_path,
                caption=f"📂 **File:** `{filename}`",
                thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=("📤 **Uploading File...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )

        # Cleanup
        await status_msg.delete()
        if os.path.exists(file_path): os.remove(file_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)

    except MessageNotModified: pass
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            await status_msg.edit(f"❌ Error: {e}")
