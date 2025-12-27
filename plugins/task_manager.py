from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import os
import re # Added Regex module
import aiohttp
import asyncio
import aria2p
import yt_dlp
from helper_funcs.display import progress_for_pyrogram, humanbytes, time_formatter
from helper_funcs.ffmpeg import take_screen_shot, get_metadata, generate_screenshots
from plugins.command import USER_THUMBS, is_authorized

# --- MEMORY ---
TASKS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# --- HELPERS ---
def run_ytdlp(url, mode, output_path):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'quiet': True, 'no_warnings': True, 'geo_bypass': True,
    }
    if mode == "audio":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        # Standardize format for Shorts/Videos
        ydl_opts.update({'format': 'bestvideo+bestaudio/best', 'merge_output_format': 'mp4'})

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ('.mp3' if mode == 'audio' else '.mp4')

def find_largest_file(path):
    if os.path.isfile(path): return path
    largest_file = None
    largest_size = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if file_size > largest_size:
                largest_size = file_size
                largest_file = file_path
    return largest_file

# --- 1. ENTRY POINT (IMPROVED REGEX) ---
# Now detects links anywhere in the message, not just at the start
@Client.on_message(filters.private & (filters.regex(r'http') | filters.regex(r'magnet') | filters.document | filters.video | filters.audio))
async def incoming_task(client, message):
    user_id = message.from_user.id

    # 🔒 Auth Check
    if not is_authorized(user_id):
        await message.reply_text("⚠️ **Access Denied.** Contact the owner: @poocha")
        return
    
    # Handle Rename Input
    if user_id in TASKS and TASKS[user_id].get("state") == "waiting_for_name":
        TASKS[user_id]["custom_name"] = message.text.strip()
        TASKS[user_id]["state"] = "menu"
        await message.delete()
        await show_dashboard(client, TASKS[user_id]["chat_id"], TASKS[user_id]["message_id"], user_id)
        return

    # --- DETECT SOURCE ---
    url = None
    is_torrent = False
    is_youtube = False
    is_telegram_file = False
    telegram_msg_obj = None
    custom_name = None

    if message.document or message.video or message.audio:
        if message.document and message.document.file_name and message.document.file_name.endswith(".torrent"):
            is_torrent = True
            file_path = await message.download()
            url = file_path
        else:
            is_telegram_file = True
            telegram_msg_obj = message
            if message.document: custom_name = message.document.file_name
            elif message.video: custom_name = message.video.file_name or "video.mp4"
            elif message.audio: custom_name = message.audio.file_name or "audio.mp3"
    else:
        # Extract URL from text (handles "Check this: https://link")
        text = message.text.strip()
        found_url = re.search(r'(?P<url>https?://[^\s]+)', text)
        if found_url:
            url = found_url.group("url")
        elif text.startswith("magnet:"):
            url = text
            is_torrent = True

        if url:
            if "youtube.com" in url or "youtu.be" in url: 
                is_youtube = True
                # 🛠️ FIX FOR SHORTS: Convert /shorts/ to /watch?v=
                if "/shorts/" in url:
                    url = url.replace("/shorts/", "/watch?v=")
            elif "magnet" in url: 
                is_torrent = True
            
            # Check for Inline Rename (Link | Name)
            if "|" in text:
                try: url, custom_name = text.split("|"); url = url.strip(); custom_name = custom_name.strip()
                except: pass

    # Stop if no valid content found
    if not url and not is_telegram_file:
        return

    # Default Mode
    current_mode = "video"

    TASKS[user_id] = {
        "url": url, "is_torrent": is_torrent, "is_youtube": is_youtube, 
        "is_telegram_file": is_telegram_file, "telegram_msg_obj": telegram_msg_obj,
        "custom_name": custom_name, "mode": current_mode,
        "state": "menu", "chat_id": message.chat.id, "message_id": None
    }

    sent_msg = await message.reply_text("🔄 **Analyzing Link...**", quote=True)
    TASKS[user_id]["message_id"] = sent_msg.id
    await show_dashboard(client, message.chat.id, sent_msg.id, user_id)


# --- 2. DASHBOARD ---
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return
    task = TASKS[user_id]
    
    name_display = task["custom_name"] if task["custom_name"] else "Default"
    
    if task["is_youtube"]:
        type_display = "🟥 YouTube / Shorts"
        mode_text = "🎵 Audio (MP3)" if task["mode"] == "audio" else "🎬 Video (MP4)"
        switch_btn = "🎬 Switch to Video" if task["mode"] == "audio" else "🎵 Switch to Audio"
    elif task["is_telegram_file"]:
        type_display = "📂 Telegram File"
        mode_text = "✨ Processing (Rename/Convert)"
        switch_btn = "No Mode (File)"
    else:
        type_display = "🧲 Torrent" if task["is_torrent"] else "🔗 Direct Link"
        mode_text = "🎥 Streamable Video" if task["mode"] == "video" else "📂 Normal File"
        switch_btn = "📂 Switch to File" if task["mode"] == "video" else "🎥 Switch to Video"

    text = (
        f"⚙️ **Task Dashboard**\n\n"
        f"**Source:** {type_display}\n"
        f"**Name:** `{name_display}`\n"
        f"**Mode:** {mode_text}\n\n"
        f"👇 **Select Option:**"
    )

    if task["is_telegram_file"]:
         buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
            [InlineKeyboardButton("▶️ Start Processing", callback_data="start_process"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]
        ])
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(switch_btn, callback_data="toggle_mode"),
             InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
            [InlineKeyboardButton("▶️ Start Download", callback_data="start_process"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]
        ])
    
    try: await client.edit_message_text(chat_id, message_id, text, reply_markup=buttons)
    except: pass


# --- 3. BUTTONS ---
@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if not is_authorized(user_id):
        await query.answer("⚠️ Access Denied.", show_alert=True); return
    if data == "cancel": 
        await query.message.edit("❌ Cancelled."); return
    if user_id not in TASKS:
        await query.answer("❌ Task expired.", show_alert=True); return

    if data == "toggle_mode":
        current = TASKS[user_id]["mode"]
        if TASKS[user_id]["is_youtube"]:
            new_mode = "audio" if current == "video" else "video"
        else:
            new_mode = "document" if current == "video" else "video"
        TASKS[user_id]["mode"] = new_mode
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)

    elif data == "ask_rename":
        TASKS[user_id]["state"] = "waiting_for_name"
        await query.message.edit("📝 **Send new name:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]))

    elif data == "back_to_menu":
        TASKS[user_id]["state"] = "menu"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)

    elif data == "cancel_task":
        del TASKS[user_id]
        await query.message.edit("❌ Task Cancelled.")

    elif data == "start_process":
        await query.message.edit("🚀 **Starting...**")
        await process_task(client, query.message, user_id)


# --- 4. PROCESSOR ---
async def process_task(client, status_msg, user_id):
    task = TASKS[user_id]
    url, custom_name, mode = task["url"], task["custom_name"], task["mode"]
    download_path, start_time = "downloads/", time.time()
    if not os.path.exists(download_path): os.makedirs(download_path)
    final_file_path = None
    gid = None

    try:
        if task["is_youtube"]:
            await status_msg.edit(f"⬇️ **Downloading from YouTube...**")
            final_file_path = await asyncio.to_thread(run_ytdlp, url, mode, download_path)

        elif task["is_torrent"]:
            if os.path.isfile(url): download = aria2.add_torrent(url); os.remove(url)
            else: download = aria2.add_magnet(url)
            gid = download.gid
            while not download.is_complete:
                download.update()
                if download.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                if download.total_length > 0:
                     p = download.completed_length * 100 / download.total_length
                     try: await status_msg.edit(f"⬇️ **Downloading Torrent...**\n⏳ **Progress:** {round(p, 2)}%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                     except: pass
                await asyncio.sleep(4)
            final_file_path = find_largest_file(str(download.files[0].path))
            if not final_file_path: final_file_path = find_largest_file("downloads/")

        elif task["is_telegram_file"]:
            msg_obj = task["telegram_msg_obj"]
            await status_msg.edit("⬇️ **Downloading File from Telegram...**")
            final_file_path = await client.download_media(
                msg_obj, file_name=download_path,
                progress=progress_for_pyrogram, 
                progress_args=("⬇️ **Downloading File...**", status_msg, start_time)
            )
            
        else:
            filename = custom_name if custom_name else url.split("/")[-1]
            final_file_path = os.path.join(download_path, filename)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200: await status_msg.edit("❌ HTTP Error."); return
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    with open(final_file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk: break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if time.time() - start_time > 4:
                                try: await status_msg.edit(f"⬇️ **Downloading:** {humanbytes(downloaded)} / {humanbytes(total_size)}")
                                except: pass

        if custom_name and not task["is_youtube"]:
            original_ext = os.path.splitext(final_file_path)[1]
            if not os.path.splitext(custom_name)[1]: custom_name += original_ext
            folder = os.path.dirname(final_file_path)
            new_path = os.path.join(folder, custom_name)
            try: os.rename(final_file_path, new_path); final_file_path = new_path
            except: pass
        
        filename = os.path.basename(final_file_path)
        await status_msg.edit("⚙️ **Processing...**")
        thumb_path = USER_THUMBS.get(user_id)
        if not thumb_path and (mode == "video" or filename.lower().endswith(('.mp4','.mkv','.webm'))): 
            thumb_path = await take_screen_shot(final_file_path, download_path, 10)

        await status_msg.edit("📤 **Uploading...**")
        is_video = filename.lower().endswith(('.mkv', '.mp4', '.webm', '.avi'))
        
        if mode == "audio":
            await client.send_audio(chat_id=status_msg.chat.id, audio=final_file_path, caption=f"🎵 **{filename}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 **Uploading Audio...**", status_msg, start_time), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
        elif mode == "video" or is_video:
            width, height, duration = await get_metadata(final_file_path)
            await client.send_video(chat_id=status_msg.chat.id, video=final_file_path, caption=f"🎥 **{filename}**\n⏱️ **Duration:** `{duration}s`", thumb=thumb_path, width=width, height=height, duration=duration, supports_streaming=True, progress=progress_for_pyrogram, progress_args=("📤 **Uploading Video...**", status_msg, start_time), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
        else:
            await client.send_document(chat_id=status_msg.chat.id, document=final_file_path, caption=f"📂 **{filename}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 **Uploading File...**", status_msg, start_time), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))

        await status_msg.delete()
        if os.path.exists(final_file_path): os.remove(final_file_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        if gid: aria2.remove([gid])
        del TASKS[user_id]

    except Exception as e:
        await status_msg.edit(f"❌ **Error:** {e}")
        if user_id in TASKS: del TASKS[user_id]
