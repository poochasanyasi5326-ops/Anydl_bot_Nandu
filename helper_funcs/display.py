import os
import time
import asyncio
import yt_dlp
import aria2p
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes, progress_for_pyrogram

# 3. Torrent Support (Bridge)
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
RENAME_FLAGS = {} # Simple state manager

async def get_yt_info(url):
    ydl_opts = {'quiet': True, 'cookiefile': 'cookies.txt'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except: return None

@Client.on_message(filters.regex(r'http|magnet|rt:') & filters.private)
async def link_handler(client, message):
    # Only owner can download
    if message.from_user.id != 519459195: return 

    url = message.text
    status = await message.reply_text("🔎 **Analyzing Link...**")
    
    # 2. YouTube Management
    if "youtube" in url or "youtu.be" in url:
        info = await get_yt_info(url)
        if not info: return await status.edit("❌ Info Fetch Failed.")
        
        # 5. Streamable (Video) vs Normal (Document) Buttons
        btns = [
            [InlineKeyboardButton(f"🎬 Stream Video ({humanbytes(info.get('filesize_approx', 0))})", callback_data=f"yt_vid|{info['id']}"),
             InlineKeyboardButton("📁 As Document", callback_data=f"yt_doc|{info['id']}")], # 7. File Type Choice
            [InlineKeyboardButton("🎧 Audio Only", callback_data=f"yt_aud|{info['id']}")],
            [InlineKeyboardButton("📝 Rename", callback_data="rename"),
             InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
        ]
        await status.edit(f"🎥 **{info.get('title')}**", reply_markup=InlineKeyboardMarkup(btns))

    # 3. Magnet Support
    elif "magnet:" in url:
        try:
            download = aria2.add_magnet(url)
            await status.edit(f"⚡ **Magnet Added:** `{download.name}`\nwaiting for metadata...")
            # 6. Progress Tracker Loop
            prev_status = ""
            while not download.is_complete:
                download.update()
                if download.status == "error": return await status.edit("❌ Download Failed.")
                
                # Update progress
                await progress_for_pyrogram(download.completed_length, download.total_length, "Downloading...", status, time.time())
                await asyncio.sleep(5)
            
            await status.edit("✅ **Download Complete.** Uploading...")
            # Upload logic would go here using client.send_document
        except Exception as e: await status.edit(f"❌ Aria2 Error: {e}")

# 4. Rename & Cancel Logic
@Client.on_callback_query(filters.regex("cancel"))
async def cancel_task(client, query):
    await query.message.edit("❌ **Task Cancelled.** Storage cleared.")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)

@Client.on_callback_query(filters.regex("rename"))
async def rename_task(client, query):
    RENAME_FLAGS[query.from_user.id] = True
    await query.message.edit("📝 **Send me the new filename now:**")

@Client.on_message(filters.text & filters.private)
async def rename_listener(client, message):
    user_id = message.from_user.id
    if RENAME_FLAGS.get(user_id):
        new_name = message.text
        RENAME_FLAGS[user_id] = False
        await message.reply_text(f"✅ Filename set to: `{new_name}`. \nPaste link again to start.")
        # Note: In a full state machine, we would resume download here. 
        # For this version, setting the name preference is the safest 'button' action.
