import os, time, asyncio, yt_dlp, aria2p, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes
from plugins.command import OWNER_ID, is_authorized

# Initialize Aria2
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def handle_media(client, message):
    if not is_authorized(message.from_user.id): return
    
    url = message.text.strip()
    sent = await message.reply_text("🔎 **Analyzing Link...**")
    
    # Store initial task data
    TASKS[message.from_user.id] = {
        "url": url, "new_name": None, "msg_id": sent.id, "state": None
    }

    if "youtube.com" in url or "youtu.be" in url:
        # YouTube Mastery: Get sizes for buttons
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            v_size = info.get('filesize_approx') or info.get('filesize') or 0
            a_size = info.get('filesize_approx') or 0
            
            buttons = [
                [InlineKeyboardButton(f"🎥 Video ({humanbytes(v_size)})", callback_data="dl_video")],
                [InlineKeyboardButton(f"🎵 Audio Only ({humanbytes(a_size)})", callback_data="dl_audio")],
                [InlineKeyboardButton("📝 Rename", callback_data="set_rename"), 
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]
            ]
            await sent.edit(f"🎬 **YouTube:** `{info.get('title')[:50]}`\nSelect Format:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        # Torrent/Direct Dashboard
        buttons = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
                   [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
        await sent.edit("🧲 **Link Detected**\nChoose an action:", reply_markup=InlineKeyboardMarkup(buttons))

# --- SMART RENAME LOGIC ---
def apply_smart_rename(original_path, custom_name):
    if not custom_name:
        return original_path
        
    directory = os.path.dirname(original_path)
    # Detect original extension (e.g., .mp4, .mkv)
    _, extension = os.path.splitext(original_path)
    
    # If user didn't type the extension, add it automatically
    if not custom_name.lower().endswith(extension.lower()):
        custom_name += extension
        
    new_path = os.path.join(directory, custom_name)
    os.rename(original_path, new_path)
    return new_path
