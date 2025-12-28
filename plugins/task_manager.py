import os, time, asyncio, yt_dlp, aria2p, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

# Initialize Aria2 engine connection
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

async def get_yt_info(url):
    """Extracts YouTube titles and sizes for buttons"""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Approximate size detection
        v_size = info.get('filesize_approx') or info.get('filesize') or 0
        a_size = sum(f.get('filesize', 0) for f in info.get('formats', []) if f.get('vcodec') == 'none')
        return info.get('title'), v_size, a_size

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def link_handler(client, message):
    # LAZY IMPORT to prevent Circular Import Error
    from plugins.command import is_authorized
    if not is_authorized(message.from_user.id): return
    
    url = message.text.strip()
    sent = await message.reply_text("🔎 **Analyzing Media...**")
    
    TASKS[message.from_user.id] = {"url": url, "new_name": None, "msg_id": sent.id}

    if "youtube.com" in url or "youtu.be" in url:
        title, v_size, a_size = await get_yt_info(url)
        buttons = [
            [InlineKeyboardButton(f"🎥 Video ({humanbytes(v_size)})", callback_data="dl_video")],
            [InlineKeyboardButton(f"🎵 Audio Only ({humanbytes(a_size)})", callback_data="dl_audio")],
            [InlineKeyboardButton("📝 Rename", callback_data="set_rename"), 
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]
        ]
        await sent.edit(f"🎬 **Title:** `{title[:50]}`", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        # Standard Magnet Dashboard
        buttons = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
                   [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
        await sent.edit("🧲 **Link Detected**", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("start_dl|dl_video|dl_audio"))
async def process_download(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    await query.message.edit("⏳ **Downloading...**")
    # Tracker Injection for Magnets
    # YouTube merging logic (Audio+Video)
    
    # After download: SMART RENAME logic
    # Checks original extension and adds it if missing
    # then sends to Telegram and triggers AUTO-CLEANUP
