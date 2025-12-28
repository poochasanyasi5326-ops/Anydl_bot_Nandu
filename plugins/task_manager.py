import os
import time
import asyncio
import yt_dlp
import aria2p
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes, progress_for_pyrogram
from helper_funcs.ffmpeg import take_screen_shot

# Initialize Aria2
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
RENAME_FLAGS = {} 

# --- LINK ANALYZER (Menu Generator) ---
async def get_yt_info(url):
    ydl_opts = {'quiet': True, 'cookiefile': 'cookies.txt'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except: return None

@Client.on_message(filters.regex(r'http|magnet|rt:') & filters.private)
async def link_handler(client, message):
    if message.from_user.id != 519459195: return 

    url = message.text
    status = await message.reply_text("🔎 **Analyzing Link...**")

    # 1. YouTube Logic
    if "youtube" in url or "youtu.be" in url:
        info = await get_yt_info(url)
        if not info: return await status.edit("❌ Error fetching info.")
        
        btns = [
            [InlineKeyboardButton(f"🎬 Stream Video ({humanbytes(info.get('filesize_approx',0))})", callback_data=f"yt_vid|{url}"),
             InlineKeyboardButton("📁 As Document", callback_data=f"yt_doc|{url}")],
            [InlineKeyboardButton("🎧 Audio Only", callback_data=f"yt_aud|{url}")],
            [InlineKeyboardButton("📝 Rename", callback_data="rename"),
             InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
        ]
        await status.edit(f"🎥 **{info.get('title', 'Unknown')}**", reply_markup=InlineKeyboardMarkup(btns))

    # 2. Magnet Logic
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
            
            # UPLOAD LOGIC FOR MAGNETS
            for file in download.files:
                if os.path.exists(file.path):
                    thumb = await get_thumbnail(message.from_user.id, file.path)
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=file.path,
                        thumb=thumb,
                        caption=f"📂 **{file.name}**",
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading", status, time.time())
                    )
                    os.remove(file.path) # Clean up
            await status.delete()
        except Exception as e: await status.edit(f"❌ Aria2 Error: {e}")

# --- BUTTON HANDLERS (The Missing Part) ---
@Client.on_callback_query(filters.regex(r"^yt_"))
async def yt_button_handler(client, query: CallbackQuery):
    mode, url = query.data.split("|")
    await query.message.edit(f"⬇️ **Processing {mode}...**")
    
    # Check for Rename
    custom_name = RENAME_FLAGS.get(query.from_user.id)
    
    ydl_opts = {
        'outtmpl': f"downloads/{custom_name if custom_name else '%(title)s'}.%(ext)s",
        'cookiefile': 'cookies.txt',
        'quiet': True
    }

    if mode == "yt_aud":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode == "yt_aud": filename = filename.rsplit(".", 1)[0] + ".mp3"

        # Upload
        thumb = await get_thumbnail(query.from_user.id, filename)
        upload_func = client.send_video if mode == "yt_vid" else client.send_document
        
        await upload_func(
            chat_id=query.message.chat.id,
            video=filename if mode == "yt_vid" else None,
            document=filename if mode != "yt_vid" else None,
            audio=filename if mode == "yt_aud" else None,
            caption=f"✅ **{os.path.basename(filename)}**",
            thumb=thumb,
            progress=progress_for_pyrogram,
            progress_args=("Uploading", query.message, time.time())
        )
        os.remove(filename) # Auto-Clean
    except Exception as e:
        await query.message.edit(f"❌ Error: {str(e)}")

# --- UTILS ---
async def get_thumbnail(user_id, file_path):
    custom = f"downloads/{user_id}_thumb.jpg"
    if os.path.exists(custom): return custom
    return await take_screen_shot(file_path, "downloads", 5)

@Client.on_callback_query(filters.regex("rename"))
async def ask_rename(client, query):
    await query.message.edit("📝 **Send new name (Text Only):**")
    # Simple listener hack for demo; proper way needs conversation state
    RENAME_FLAGS[query.from_user.id] = "WAITING"

@Client.on_message(filters.text & filters.private)
async def set_new_name(client, message):
    if RENAME_FLAGS.get(message.from_user.id) == "WAITING":
        RENAME_FLAGS[message.from_user.id] = message.text
        await message.reply_text(f"✅ Name set to: `{message.text}`. \nClick the download button now.")

@Client.on_callback_query(filters.regex("cancel"))
async def cancel_task(client, query):
    await query.message.edit("❌ Cancelled.")
