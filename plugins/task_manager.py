import os
import time
import asyncio
import yt_dlp
import aria2p
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper_funcs.display import humanbytes, progress_for_pyrogram
from helper_funcs.ffmpeg import take_screen_shot

# Initialize Aria2
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
RENAME_FLAGS = {} # Stores user rename requests

async def get_yt_info(url):
    ydl_opts = {'quiet': True, 'cookiefile': 'cookies.txt'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except: return None

@Client.on_message(filters.regex(r'http|magnet|rt:') & filters.private)
async def link_handler(client, message):
    if message.from_user.id != 519459195: return # Security Check

    url = message.text
    status = await message.reply_text("🔎 **Analyzing Link...**")

    # --- YouTube Logic ---
    if "youtube" in url or "youtu.be" in url:
        info = await get_yt_info(url)
        if not info: return await status.edit("❌ Error fetching info.")
        
        # Buttons for Feature 5 (Stream vs Doc) & Feature 2 (Size)
        btns = [
            [InlineKeyboardButton(f"🎬 Stream Video ({humanbytes(info.get('filesize_approx',0))})", callback_data=f"yt_vid|{info['id']}"),
             InlineKeyboardButton("📁 As Document", callback_data=f"yt_doc|{info['id']}")],
            [InlineKeyboardButton("🎧 Audio Only", callback_data=f"yt_aud|{info['id']}")],
            [InlineKeyboardButton("📝 Rename", callback_data="rename"),
             InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
        ]
        await status.edit(f"🎥 **{info.get('title', 'Unknown')}**", reply_markup=InlineKeyboardMarkup(btns))

    # --- Magnet Logic ---
    elif "magnet:" in url:
        try:
            download = aria2.add_magnet(url)
            await status.edit(f"⚡ **Magnet Added:** `{download.name}`\nwaiting for metadata...")
            
            while not download.is_complete:
                download.update()
                if download.status == 'error': return await status.edit("❌ Download Failed.")
                await progress_for_pyrogram(download.completed_length, download.total_length, "Downloading Magnet", status, time.time())
                await asyncio.sleep(5)
            
            await status.edit("✅ Download Complete. Uploading...")
            # Here is where you would trigger the upload function
        except Exception as e: await status.edit(f"❌ Aria2 Error: {e}")

# --- Helper to Decide Thumbnail ---
async def get_thumbnail(user_id, file_path):
    # 1. Check for Custom Thumbnail (Feature 1 & 8)
    custom_thumb = f"downloads/{user_id}_thumb.jpg"
    if os.path.exists(custom_thumb):
        return custom_thumb
    
    # 2. Else, Take Screenshot (Feature supported via ffmpeg.py)
    return await take_screen_shot(file_path, "downloads", 5) # Takes shot at 5th second

# --- Rename & Cancel Handlers (Feature 4) ---
@Client.on_callback_query(filters.regex("rename"))
async def ask_rename(client, query):
    RENAME_FLAGS[query.from_user.id] = True
    await query.message.edit("📝 **Send me the new filename now:**")

@Client.on_message(filters.text & filters.private)
async def set_new_name(client, message):
    if RENAME_FLAGS.get(message.from_user.id):
        # In a full bot, you'd save this name to a variable to use during upload
        await message.reply_text(f"✅ Name set to: `{message.text}`")
        RENAME_FLAGS[message.from_user.id] = False
