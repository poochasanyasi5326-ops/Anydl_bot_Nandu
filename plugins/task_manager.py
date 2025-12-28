from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time, os, re, asyncio, aiohttp, aria2p, yt_dlp, mimetypes
from helper_funcs.display import progress_for_pyrogram, humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata
from plugins.command import USER_THUMBS, is_authorized

TASKS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# 🚀 MASSIVE TRACKER LIST (Injected into magnet links to find seeds)
TRACKER_LIST = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://9.rarbg.com:2810/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://opentracker.i2p.rocks:6969/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://explodie.org:6969/announce",
    "udp://exodus.desync.com:6969/announce"
]

VIDEO_EXT = ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.3gp', '.ts', '.mpeg')

# --- CORE LOGIC ---
@Client.on_message(filters.private & (filters.regex(r'http') | filters.regex(r'magnet') | filters.document | filters.video | filters.audio))
async def incoming_task(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    url, is_tor, is_yt, is_tg, tg_obj, c_name = None, False, False, False, None, None

    if message.document or message.video or message.audio:
        if message.document and str(message.document.file_name).endswith(".torrent"):
            is_tor = True; url = await message.download()
        else:
            is_tg = True; tg_obj = message
            c_name = getattr(message.document or message.video or message.audio, 'file_name', 'file')
    else:
        text = message.text.strip()
        f_url = re.search(r'(?P<url>https?://[^\s]+)', text)
        if f_url: url = f_url.group("url")
        elif text.startswith("magnet:"): url = text; is_tor = True
        if url:
            if "youtube.com" in url or "youtu.be" in url: is_yt = True
            elif "magnet" in url: is_tor = True
            if "|" in text: 
                parts = text.split("|")
                url = parts[0].strip()
                c_name = parts[1].strip()

    if not url and not is_tg: return
    TASKS[user_id] = {"url": url, "is_torrent": is_tor, "is_youtube": is_yt, "is_tg_file": is_tg, "tg_obj": tg_obj, "custom_name": c_name, "mode": "video"}
    sent = await message.reply_text("🔄 **Analyzing...**", quote=True)
    TASKS[user_id]["message_id"] = sent.id
    await show_dashboard(client, message.chat.id, sent.id, user_id)

async def process_task(client, status_msg, u_id):
    t = TASKS[u_id]; url, mode, d_path = t["url"], t["mode"], "downloads/"
    if not os.path.exists(d_path): os.makedirs(d_path)
    start_t, f_path = time.time(), None
    try:
        if t["is_torrent"]:
            if "magnet:?" in url:
                for tr in TRACKER_LIST: 
                    url = url + "&tr=" + tr # INJECT TRACKERS
            
            dl_opts = {'dir': os.path.abspath(d_path)}
            if os.path.isfile(url):
                dl = aria2.add_torrent(url, options=dl_opts)
            else:
                dl = aria2.add_magnet(url, options=dl_opts)
            
            TASKS[u_id]["gid"] = dl.gid
            while not dl.is_complete:
                dl.update()
                if dl.status == 'error':
                    await status_msg.edit("❌ Torrent Error.")
                    return
                if dl.total_length > 0:
                    p = (dl.completed_length / dl.total_length) * 100
                    bar = "■" * int(p/10) + "□" * (10-int(p/10))
                    await status_msg.edit(f"⬇️ **Downloading...**\n`{humanbytes(dl.completed_length)}` / `{humanbytes(dl.total_length)}`\n⚡ `{humanbytes(dl.download_speed)}/s` | 👥 `{dl.connections}`\n⏳ [{bar}] `{round(p, 2)}%`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                await asyncio.sleep(4)
            # Find largest file inside the downloaded folder
            f_path = find_largest_file(str(dl.files[0].path) if dl.files else d_path)
        
        # ... Rest of your upload logic here ...
        await status_msg.edit("📤 **Uploading...**")
        await client.send_document(status_msg.chat.id, f_path, caption=f"📂 `{os.path.basename(f_path)}`", progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_t))
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")
