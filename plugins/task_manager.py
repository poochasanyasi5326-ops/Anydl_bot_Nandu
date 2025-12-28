import os, time, asyncio, yt_dlp, aria2p, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata

# Initialize Aria2 engine connection
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

async def get_yt_info(url):
    """Extracts YouTube titles and sizes for buttons"""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
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
        buttons = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
                   [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
        await sent.edit("🧲 **Link Detected**", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("start_dl|dl_video|dl_audio"))
async def process_download(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    mode = query.data
    d_path = f"downloads/{u_id}_{int(time.time())}/"
    if not os.path.exists(d_path): os.makedirs(d_path)

    try:
        await query.message.edit("⏳ **Downloading...**")
        
        if mode.startswith("dl_"):
            # YouTube Mastery: Audio+Video merging
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best' if mode == "dl_video" else 'bestaudio/best',
                'outtmpl': f'{d_path}%(title)s.%(ext)s',
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task["url"], download=True)
                file_path = ydl.prepare_filename(info)
        else:
            # Magnet logic with Tracker Injection
            trackers = "&tr=udp://tracker.opentrackr.org:1337/announce"
            dl = aria2.add_magnet(task["url"] + trackers, options={'dir': os.path.abspath(d_path)})
            while not dl.is_complete:
                dl.update()
                await query.message.edit(f"⬇️ **Downloading:** {dl.progress_string()}\nSpeed: {dl.download_speed_string()}")
                await asyncio.sleep(5)
            file_path = dl.files[0].path

        # SMART RENAME: Detects and adds extension if missing
        if task["new_name"]:
            ext = os.path.splitext(file_path)[1]
            if not task["new_name"].endswith(ext):
                task["new_name"] += ext
            new_path = os.path.join(os.path.dirname(file_path), task["new_name"])
            os.rename(file_path, new_path)
            file_path = new_path

        await query.message.edit("📤 **Uploading...**")
        # Metadata extraction for playable video
        width, height, duration = await get_metadata(file_path)
        thumb = await take_screen_shot(file_path, d_path, 10)
        
        await client.send_video(u_id, file_path, thumb=thumb, duration=duration, width=width, height=height, supports_streaming=True)
        await query.message.delete()

    except Exception as e:
        await query.message.edit(f"❌ **Error:** `{e}`")
    finally:
        # AUTO-CLEANUP: Protects 16GB Storage
        if os.path.exists(d_path):
            shutil.rmtree(d_path)
        if u_id in TASKS: del TASKS[u_id]

@Client.on_callback_query(filters.regex("cancel_dl"))
async def cancel_handler(client, query: CallbackQuery):
    u_id = query.from_user.id
    if u_id in TASKS:
        # Stop Aria2 if active
        if TASKS[u_id].get("gid"):
            aria2.remove([aria2.get_download(TASKS[u_id]["gid"])])
        del TASKS[u_id]
        await query.message.edit("❌ **Task Cancelled & Cleared.**")
