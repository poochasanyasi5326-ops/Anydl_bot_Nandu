import os
import time
import asyncio
import yt_dlp
import aria2p
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes, progress_for_pyrogram

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

async def get_yt_info(url):
    ydl_opts = {'quiet': True, 'cookiefile': 'cookies.txt'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except: return None

@Client.on_message(filters.regex(r'http|magnet|rt:'))
async def link_handler(client, message):
    url = message.text
    status = await message.reply_text("🔎 Analyzing...")
    
    if "youtube" in url or "youtu.be" in url:
        info = await get_yt_info(url)
        if not info: return await status.edit("❌ Info Error.")
        
        btns = [
            [InlineKeyboardButton("🎬 Video", callback_data=f"dl_v|{info['id']}"),
             InlineKeyboardButton("🎧 Audio", callback_data=f"dl_a|{info['id']}")],
            [InlineKeyboardButton("📝 Rename", callback_data="rename"),
             InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
        ]
        await status.edit(f"🎥 {info.get('title')[:50]}\nSize: {humanbytes(info.get('filesize_approx', 0))}", reply_markup=InlineKeyboardMarkup(btns))
    
    elif "magnet:" in url:
        try:
            download = aria2.add_magnet(url)
            await status.edit(f"⚡ Magnet Added: {download.name}")
            asyncio.create_task(monitor_aria_progress(download, status))
        except Exception as e: await status.edit(f"❌ Aria2 Error: {e}")

async def monitor_aria_progress(download, status):
    start_time = time.time()
    while not download.is_complete:
        download.update()
        await progress_for_pyrogram(download.completed_length, download.total_length, "Downloading Magnet", status, start_time)
        await asyncio.sleep(4)
    await status.edit("✅ Download Complete. Starting Upload...")

@Client.on_callback_query(filters.regex(r"cancel"))
async def cancel_callback(client, query):
    await query.message.edit("❌ Task Cancelled. Cleaning storage...")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)
