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

# --- HELPERS ---
def get_yt_resolutions(url):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'geo_bypass': True, 'noplaylist': True}
        if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            formats_found = []
            seen_heights = set()
            for f in info['formats']:
                h = f.get('height')
                fs = f.get('filesize') or f.get('filesize_approx')
                if h and h in [1080, 720, 480, 360] and h not in seen_heights:
                    formats_found.append({"res": f"{h}p", "size": humanbytes(fs) if fs else "N/A", "height": h})
                    seen_heights.add(h)
            formats_found.sort(key=lambda x: x['height'], reverse=True)
            return title, formats_found
    except: return None, []

def run_ytdlp(url, q, path):
    ydl_opts = {'outtmpl': f'{path}/%(title)s.%(ext)s', 'quiet': True, 'geo_bypass': True, 'noplaylist': True}
    if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
    if q == "audio":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        ydl_opts.update({'format': f'bestvideo[height<={q}]+bestaudio/best[height<={q}]', 'merge_output_format': 'mp4'})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ('.mp3' if q == 'audio' else '.mp4')

def find_largest_file(path):
    if os.path.isfile(path): return path
    l_file, l_size = None, 0
    for r, d, f in os.walk(path):
        for file in f:
            fp = os.path.join(r, file); fs = os.path.getsize(fp)
            if fs > l_size: l_size = fs; l_file = fp
    return l_file

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
            if "|" in text: url, c_name = map(str.strip, text.split("|")[:2])

    if not url and not is_tg: return
    TASKS[user_id] = {"url": url, "is_torrent": is_tor, "is_youtube": is_yt, "is_tg_file": is_tg, "tg_obj": tg_obj, "custom_name": c_name, "mode": "video"}
    sent = await message.reply_text("🔄 **Analyzing...**", quote=True)
    TASKS[user_id]["message_id"] = sent.id
    if is_yt:
        t, f = await asyncio.to_thread(get_yt_resolutions, url)
        if not f: await sent.edit("❌ YouTube Error."); return
        TASKS[user_id].update({"yt_resolutions": f, "custom_name": t})
    await show_dashboard(client, message.chat.id, sent.id, user_id)

async def show_dashboard(client, chat_id, msg_id, user_id):
    if user_id not in TASKS: return
    t = TASKS[user_id]; name = t["custom_name"] or "Default"; buttons = []
    if t["is_youtube"]:
        text = f"📺 **YouTube**\n`{name}`"
        for f in t["yt_resolutions"]: buttons.append([InlineKeyboardButton(f"🎬 {f['res']} ({f['size']})", callback_data=f"yt_set_{f['height']}")])
        buttons.append([InlineKeyboardButton("🎵 MP3", callback_data="yt_set_audio")])
    else:
        m_txt = "Streamable Video" if t["mode"] == "video" else "Safe File"
        text = f"⚙️ **Dashboard**\n**Source:** {'🧲 Torrent' if t['is_torrent'] else '🔗 Link'}\n**Name:** `{name}`\n**Mode:** {m_txt}"
        buttons = [[InlineKeyboardButton("📂 Switch Mode", callback_data="toggle_mode")], [InlineKeyboardButton("▶️ Start", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    await client.edit_message_text(chat_id, msg_id, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query()
async def handle_buttons(client, query):
    u_id = query.from_user.id
    if query.data == "cancel":
        if u_id in TASKS and TASKS[u_id].get("gid"):
            try: aria2.client.remove(TASKS[u_id]["gid"])
            except: pass
        if u_id in TASKS: del TASKS[u_id]
        await query.message.edit("❌ Cancelled."); return
    if u_id not in TASKS: return
    if query.data.startswith("yt_set_"):
        TASKS[u_id]["mode"] = query.data.split("_")[2]
        await query.message.edit("🚀 Starting YouTube Download...")
        await process_task(client, query.message, u_id)
    elif query.data == "toggle_mode":
        TASKS[u_id]["mode"] = "document" if TASKS[u_id]["mode"] == "video" else "video"
        await show_dashboard(client, query.message.chat.id, query.message.id, u_id)
    elif query.data == "start_process":
        await query.message.edit("🚀 Starting...")
        await process_task(client, query.message, u_id)

async def process_task(client, status_msg, u_id):
    t = TASKS[u_id]; url, mode, d_path = t["url"], t["mode"], "downloads/"
    if not os.path.exists(d_path): os.makedirs(d_path)
    start_t, f_path = time.time(), None
    try:
        if t["is_youtube"]: f_path = await asyncio.to_thread(run_ytdlp, url, mode, d_path)
        elif t["is_torrent"]:
            if "magnet:?" in url:
                for tr in TRACKER_LIST: url += f"&tr={tr}" # INJECT TRACKERS
            dl = aria2.add_torrent(url, options={'dir': os.path.abspath(d_path)}) if os.path.isfile(url) else aria2.add_magnet(url, options={'dir': os.path.abspath(d_path)})
            TASKS[u_id]["gid"] = dl.gid
            while not dl.is_complete:
                dl.update()
                if dl.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                if dl.total_length > 0:
                    p = (dl.completed_length / dl.total_length) * 100
                    bar = "■" * int(p/10) + "□" * (10-int(p/10))
                    await status_msg.edit(f"⬇️ **Downloading...**\n`{humanbytes(dl.completed_length)}` / `{humanbytes(dl.total_length)}`\n⚡ `{humanbytes(dl.download_speed)}/s` | 👥 `{dl.connections}`\n⏳ [{bar}] `{round(p, 2)}%`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                await asyncio.sleep(4)
            f_path = find_largest_file(str(dl.files[0].path) if dl.files else d_path)
        elif t["is_tg_file"]: f_path = await client.download_media(t["tg_obj"], file_name=d_path, progress=progress_for_pyrogram, progress_args=("⬇️ Downloading...", status_msg, start_t))
        
        if not f_path or not os.path.exists(f_path): await status_msg.edit("❌ Error: File not found."); return
        await status_msg.edit("📤 **Uploading...**")
        if mode == "video" and f_path.lower().endswith(VIDEO_EXT):
            w, h, dur = await get_metadata(f_path)
            thumb = await take_screen_shot(f_path, d_path, 10)
            await client.send_video(status_msg.chat.id, f_path, caption=f"🎥 `{os.path.basename(f_path)}`", thumb=thumb, width=w, height=h, duration=dur, supports_streaming=True, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_t))
        else:
            await client.send_document(status_msg.chat.id, f_path, caption=f"📂 `{os.path.basename(f_path)}`", progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_t))
        await status_msg.delete()
    except Exception as e: await status_msg.edit(f"❌ Error: {e}")
    finally:
        if f_path and os.path.exists(f_path): os.remove(f_path)
        if u_id in TASKS: del TASKS[u_id]
