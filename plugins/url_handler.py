import os
import time
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
from auth import owner_only

# Progress Bar Logic
async def progress_hook(d, status_msg, last_edit_time):
    if d['status'] == 'downloading':
        try:
            now = time.time()
            if now - last_edit_time[0] > 5:  # Update every 5 seconds
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                await status_msg.edit_text(f"⬇️ **Downloading...**\n📊 Progress: {percent}\n🚀 Speed: {speed}")
                last_edit_time[0] = now
        except:
            pass

# Handle HTTP/HTTPS Links
@Client.on_message(filters.regex(r"^https?://") & filters.private & owner_only())
async def download_url(client, message):
    url = message.text.strip()
    status_msg = await message.reply_text("🔎 **Analyzing Link...**")
    
    download_path = "downloads"
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    # yt-dlp Configuration
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        # 'format': 'best', # Auto-select best quality
    }

    last_edit_time = [0]

    try:
        # 1. Download
        await status_msg.edit_text("⬇️ **Starting Download...**")
        
        # We run this in a separate thread to not block the bot
        loop = asyncio.get_event_loop()
        file_info = await loop.run_in_executor(None, lambda: run_download(ydl_opts, url, status_msg, last_edit_time))
        
        filename = file_info['filename']
        title = file_info.get('title', 'Downloaded File')

        # 2. Upload
        await status_msg.edit_text("🚀 **Uploading to Telegram...**")
        await client.send_document(
            chat_id=message.chat.id,
            document=filename,
            caption=f"✅ **Downloaded:** `{title}`",
            force_document=True
        )
        
        # 3. Cleanup
        os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")

def run_download(opts, url, msg, time_tracker):
    with YoutubeDL(opts) as ydl:
        # Note: We can't easily await inside the standard hook, so simple progress is used
        info = ydl.extract_info(url, download=True)
        return {'filename': ydl.prepare_filename(info), 'title': info.get('title')}