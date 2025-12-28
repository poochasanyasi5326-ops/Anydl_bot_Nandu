import os, time, asyncio, yt_dlp, aria2p
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes, progress_for_pyrogram

# Must match the secret in run.sh
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret="AnyDL_Secret_123"))

@Client.on_message(filters.regex(r'http|magnet|rt:') & filters.private)
async def link_handler(client, message):
    if message.from_user.id != 519459195: return 
    url = message.text
    status = await message.reply_text("🔎 Analyzing Link...")

    if "youtube" in url or "youtu.be" in url:
        with yt_dlp.YoutubeDL({'quiet': True, 'cookiefile': 'cookies.txt'}) as ydl:
            info = ydl.extract_info(url, download=False)
            vid_id = info['id']
            btns = [
                [InlineKeyboardButton(f"🎬 Stream", callback_data=f"yt_vid|{vid_id}"),
                 InlineKeyboardButton("📁 Document", callback_data=f"yt_doc|{vid_id}")],
                [InlineKeyboardButton("📝 Rename", callback_data="rename"), 
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ]
            await status.edit(f"🎥 **{info.get('title')}**", reply_markup=InlineKeyboardMarkup(btns))
    
    elif "magnet:" in url:
        try:
            download = aria2.add_magnet(url)
            await status.edit(f"⚡ Magnet Added: `{download.name}`")
            # Logic for progress tracking Requirement #6
            while not download.is_complete:
                download.update()
                await progress_for_pyrogram(download.completed_length, download.total_length, "Downloading", status, time.time())
                await asyncio.sleep(5)
        except Exception as e: await status.edit(f"❌ Error: {e}")

@Client.on_callback_query(filters.regex("cancel"))
async def cancel_task(client, query):
    await query.answer("Task Cancelled")
    await query.message.edit("❌ Terminated.")
