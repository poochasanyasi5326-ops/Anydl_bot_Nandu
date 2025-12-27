from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import os
import re
import asyncio
import aiohttp
import aria2p
import yt_dlp
from helper_funcs.display import progress_for_pyrogram, humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata
from plugins.command import USER_THUMBS, is_authorized

# --- MEMORY ---
TASKS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# --- 1. HELPER: GET YOUTUBE INFO ---
def get_yt_resolutions(url):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'geo_bypass': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Basic Details
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', None)
            
            # Find Available Formats
            formats_found = []
            seen_heights = set()
            
            # Iterate and filter best video-only streams (we merge audio later)
            for f in info['formats']:
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                # We only want standard resolutions (1080, 720, 480, 360)
                if height and height in [1080, 720, 480, 360] and height not in seen_heights:
                    size_text = humanbytes(filesize) if filesize else "N/A"
                    # Add to list (Resolution, Size, FormatID)
                    formats_found.append({
                        "res": f"{height}p",
                        "size": size_text,
                        "height": height
                    })
                    seen_heights.add(height)

            # Sort: High to Low
            formats_found.sort(key=lambda x: x['height'], reverse=True)
            return title, duration, thumbnail, formats_found
    except Exception as e:
        return None, 0, None, []

# --- 2. HELPER: DOWNLOADER ---
def run_ytdlp(url, quality_setting, output_path):
    # Quality Setting: "audio", "1080", "720", etc.
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'quiet': True, 'no_warnings': True, 'geo_bypass': True,
    }

    if quality_setting == "audio":
        # Best Audio -> MP3
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        })
    else:
        # Specific Video Resolution + Best Audio -> MP4
        # Logic: Find best video with height <= chosen_height, merge with best audio
        ydl_opts.update({
            'format': f'bestvideo[height<={quality_setting}]+bestaudio/best[height<={quality_setting}]',
            'merge_output_format': 'mp4'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Handle filename changes
        ext = 'mp3' if quality_setting == 'audio' else 'mp4'
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + f'.{ext}'

def find_largest_file(path):
    if os.path.isfile(path): return path
    largest_file, largest_size = None, 0
    for root, dirs, files in os.walk(path):
        for file in files:
            fp = os.path.join(root, file)
            fs = os.path.getsize(fp)
            if fs > largest_size: largest_size = fs; largest_file = fp
    return largest_file

# --- 3. ENTRY POINT ---
@Client.on_message(filters.private & (filters.regex(r'http') | filters.regex(r'magnet') | filters.document | filters.video | filters.audio))
async def incoming_task(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text("⚠️ Access Denied."); return

    # --- DETECT SOURCE ---
    url = None; is_torrent = False; is_youtube = False; is_tg_file = False; tg_obj = None; custom_name = None
    
    if message.document or message.video or message.audio:
        if message.document and str(message.document.file_name).endswith(".torrent"):
            is_torrent = True; url = await message.download()
        else:
            is_tg_file = True; tg_obj = message
            if message.document: custom_name = message.document.file_name
            elif message.video: custom_name = message.video.file_name or "video.mp4"
            elif message.audio: custom_name = message.audio.file_name or "audio.mp3"
    else:
        text = message.text.strip()
        found_url = re.search(r'(?P<url>https?://[^\s]+)', text)
        if found_url: url = found_url.group("url")
        elif text.startswith("magnet:"): url = text; is_torrent = True
        
        if url:
            if "youtube.com" in url or "youtu.be" in url:
                is_youtube = True
                if "/shorts/" in url: url = url.replace("/shorts/", "/watch?v=")
            elif "magnet" in url: is_torrent = True
            if "|" in text: 
                try: url, custom_name = text.split("|"); url=url.strip(); custom_name=custom_name.strip()
                except: pass

    if not url and not is_tg_file: return

    # Initialize Task
    TASKS[user_id] = {
        "url": url, "is_torrent": is_torrent, "is_youtube": is_youtube,
        "is_tg_file": is_tg_file, "tg_obj": tg_obj, "custom_name": custom_name,
        "mode": "video", "yt_resolutions": [], # To store fetched resolutions
        "chat_id": message.chat.id, "message_id": None
    }

    sent_msg = await message.reply_text("🔄 **Analyzing...**", quote=True)
    TASKS[user_id]["message_id"] = sent_msg.id

    # If YouTube, Fetch formats FIRST
    if is_youtube:
        await sent_msg.edit("🔎 **Scanning YouTube Qualities...**\n(This takes a few seconds)")
        # Run in thread to prevent blocking
        title, dur, thumb, formats = await asyncio.to_thread(get_yt_resolutions, url)
        if not formats:
            await sent_msg.edit("❌ Failed to fetch formats. Try again."); del TASKS[user_id]; return
        
        TASKS[user_id]["yt_resolutions"] = formats
        TASKS[user_id]["custom_name"] = title # Auto-set title
        
    await show_dashboard(client, message.chat.id, sent_msg.id, user_id)

# --- 4. DASHBOARD ---
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return
    task = TASKS[user_id]
    
    # UI Text
    name = task["custom_name"] if task["custom_name"] else "Default"
    buttons = []

    if task["is_youtube"]:
        # --- YOUTUBE QUALITY MENU ---
        text = f"📺 **YouTube Video Found**\n\n**Title:** `{name}`\n👇 **Select Quality to Download:**"
        
        # Create Dynamic Buttons from Fetched Formats
        for fmt in task["yt_resolutions"]:
            # Example: 🎬 1080p (~150MB)
            btn_text = f"🎬 {fmt['res']} ({fmt['size']})"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"yt_set_{fmt['height']}")])
        
        # Always add Audio Option
        buttons.append([InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="yt_set_audio")])
        buttons.append([InlineKeyboardButton("✏️ Rename", callback_data="ask_rename"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")])
    
    elif task["is_tg_file"]:
        text = f"📂 **File Manager**\n**Name:** `{name}`\n👇 **Rename or Upload:**"
        buttons = [[InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
                   [InlineKeyboardButton("▶️ Process", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]]
    
    else:
        # Standard Torrent/Link Dashboard
        mode_txt = "Streamable Video" if task["mode"] == "video" else "Normal File"
        sw_btn = "📂 Switch to File" if task["mode"] == "video" else "🎥 Switch to Video"
        text = f"⚙️ **Link Dashboard**\n**Source:** {'🧲 Torrent' if task['is_torrent'] else '🔗 Link'}\n**Name:** `{name}`\n**Mode:** {mode_txt}"
        buttons = [[InlineKeyboardButton(sw_btn, callback_data="toggle_mode"), InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
                   [InlineKeyboardButton("▶️ Start Download", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]]

    try: await client.edit_message_text(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup(buttons))
    except: pass

# --- 5. BUTTONS ---
@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    if user_id not in TASKS: await query.answer("❌ Expired.", show_alert=True); return

    if data.startswith("yt_set_"):
        # USER SELECTED A QUALITY (e.g., yt_set_1080 or yt_set_audio)
        quality = data.split("_")[2] # "1080" or "audio"
        TASKS[user_id]["mode"] = quality # Store chosen quality
        await query.message.edit(f"✅ Selected: **{quality}**\n🚀 **Starting Download...**")
        await process_task(client, query.message, user_id) # Auto-start
        return

    if data == "toggle_mode":
        TASKS[user_id]["mode"] = "document" if TASKS[user_id]["mode"] == "video" else "video"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)
    elif data == "ask_rename":
        TASKS[user_id]["state"] = "waiting_for_name"
        await query.message.edit("📝 **Send new name:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]))
    elif data == "back_to_menu":
        TASKS[user_id]["state"] = "menu"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)
    elif data == "cancel_task":
        del TASKS[user_id]; await query.message.edit("❌ Cancelled.")
    elif data == "start_process":
        await query.message.edit("🚀 **Starting...**")
        await process_task(client, query.message, user_id)

# --- 6. PROCESSOR ---
async def process_task(client, status_msg, user_id):
    task = TASKS[user_id]
    url, custom_name, mode = task["url"], task["custom_name"], task["mode"]
    download_path, start_time = "downloads/", time.time()
    if not os.path.exists(download_path): os.makedirs(download_path)
    final_path, gid = None, None

    try:
        if task["is_youtube"]:
            # YOUTUBE (Using Chosen Quality)
            await status_msg.edit(f"⬇️ **Downloading YouTube ({mode})...**")
            final_path = await asyncio.to_thread(run_ytdlp, url, mode, download_path)

        elif task["is_torrent"]:
            # TORRENT
            dl = aria2.add_torrent(url) if os.path.isfile(url) else aria2.add_magnet(url)
            if os.path.isfile(url): os.remove(url)
            gid = dl.gid
            while not dl.is_complete:
                dl.update(); p = dl.completed_length * 100 / dl.total_length if dl.total_length else 0
                if dl.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                if time.time() - start_time > 4:
                     try: await status_msg.edit(f"⬇️ **Downloading Torrent...**\n⏳ **{round(p,2)}%**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                     except: pass
                await asyncio.sleep(4)
            final_path = find_largest_file(str(dl.files[0].path)) or find_largest_file("downloads/")

        elif task["is_tg_file"]:
            # TELEGRAM FILE
            await status_msg.edit("⬇️ **Downloading File...**")
            final_path = await client.download_media(task["tg_obj"], file_name=download_path, progress=progress_for_pyrogram, progress_args=("⬇️ Downloading...", status_msg, start_time))

        else:
            # DIRECT LINK
            fname = custom_name if custom_name else url.split("/")[-1]
            final_path = os.path.join(download_path, fname)
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    with open(final_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk: break
                            f.write(chunk)
                            
        # SMART RENAME
        if custom_name and not task["is_youtube"]:
            ext = os.path.splitext(final_path)[1]
            if not os.path.splitext(custom_name)[1]: custom_name += ext
            new_path = os.path.join(os.path.dirname(final_path), custom_name)
            try: os.rename(final_path, new_path); final_path = new_path
            except: pass
        
        fname = os.path.basename(final_path)
        thumb_path = USER_THUMBS.get(user_id)
        if not thumb_path and fname.lower().endswith(('.mp4','.mkv','.webm')): 
            thumb_path = await take_screen_shot(final_path, download_path, 10)

        # UPLOAD
        await status_msg.edit("📤 **Uploading...**")
        is_vid = fname.lower().endswith(('.mp4','.mkv','.webm'))
        
        if mode == "audio" or fname.endswith(".mp3"):
            await client.send_audio(status_msg.chat.id, final_path, caption=f"🎵 **{fname}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))
        elif mode == "video" or is_vid:
            w, h, dur = await get_metadata(final_path)
            await client.send_video(status_msg.chat.id, final_path, caption=f"🎥 **{fname}**", thumb=thumb_path, width=w, height=h, duration=dur, supports_streaming=True, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))
        else:
            await client.send_document(status_msg.chat.id, final_path, caption=f"📂 **{fname}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))

        await status_msg.delete()
        if os.path.exists(final_path): os.remove(final_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        if gid: aria2.remove([gid])
        del TASKS[user_id]

    except Exception as e:
        await status_msg.edit(f"❌ **Error:** {e}"); del TASKS[user_id]
