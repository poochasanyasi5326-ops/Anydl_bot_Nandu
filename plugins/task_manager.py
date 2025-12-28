from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time, os, re, asyncio, aria2p
from helper_funcs.display import progress_for_pyrogram, humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata
from plugins.command import is_authorized

TASKS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

TRACKER_LIST = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://9.rarbg.com:2810/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://open.stealth.si:80/announce",
    "udp://exodus.desync.com:6969/announce"
]

def find_largest_file(path):
    if os.path.isfile(path): return path
    l_file, l_size = None, 0
    for r, d, f in os.walk(path):
        for file in f:
            fp = os.path.join(r, file); fs = os.path.getsize(fp)
            if fs > l_size: l_size, l_file = fs, fp
    return l_file

async def show_dashboard(client, chat_id, msg_id, user_id):
    if user_id not in TASKS: return
    t = TASKS[user_id]
    m_txt = "Streamable Video" if t["mode"] == "video" else "Safe File"
    text = f"⚙️ **Dashboard**\n**Source:** {'🧲 Torrent' if t['is_torrent'] else '🔗 Link'}\n**Name:** `{t['custom_name'] or 'Default'}`\n**Mode:** {m_txt}"
    buttons = [[InlineKeyboardButton("📂 Switch Mode", callback_data="toggle_mode")], 
               [InlineKeyboardButton("▶️ Start", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    try: await client.edit_message_text(chat_id, msg_id, text, reply_markup=InlineKeyboardMarkup(buttons))
    except: pass

@Client.on_message(filters.private & (filters.regex(r'http') | filters.regex(r'magnet') | filters.document))
async def incoming_task(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    url, is_tor, is_tg, tg_obj, c_name = None, False, False, None, None

    if message.document:
        is_tg, tg_obj = True, message
        c_name = message.document.file_name
    else:
        text = message.text.strip()
        if text.startswith("magnet:"): url, is_tor = text, True
        else:
            f_url = re.search(r'(?P<url>https?://[^\s]+)', text)
            if f_url: url = f_url.group("url")
        if url and "|" in text: url, c_name = map(str.strip, text.split("|")[:2])

    if not url and not is_tg: return
    TASKS[user_id] = {"url": url, "is_torrent": is_tor, "is_tg_file": is_tg, "tg_obj": tg_obj, "custom_name": c_name, "mode": "video"}
    sent = await message.reply_text("🔄 **Analyzing...**", quote=True)
    TASKS[user_id]["message_id"] = sent.id
    await show_dashboard(client, message.chat.id, sent.id, user_id)

@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    u_id = query.from_user.id
    if query.data == "cancel":
        if u_id in TASKS and TASKS[u_id].get("gid"):
            try: aria2.client.remove(TASKS[u_id]["gid"])
            except: pass
        if u_id in TASKS: del TASKS[u_id]
        await query.message.edit("❌ Cancelled."); return
    if u_id not in TASKS: return
    if query.data == "toggle_mode":
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
        if t["is_torrent"]:
            if url.startswith("magnet:?"):
                for tr in TRACKER_LIST: url += f"&tr={tr}"
            dl = aria2.add_magnet(url, options={'dir': os.path.abspath(d_path)})
            TASKS[u_id]["gid"] = dl.gid
            while not dl.is_complete:
                dl.update()
                if dl.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                if dl.total_length > 0:
                    p = (dl.completed_length / dl.total_length) * 100
                    await status_msg.edit(f"⬇️ **Downloading...**\n`{humanbytes(dl.completed_length)}` / `{humanbytes(dl.total_length)}` | 👥 `{dl.connections}`\n⏳ `{round(p, 2)}%`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                await asyncio.sleep(4)
            f_path = find_largest_file(str(dl.files[0].path) if dl.files else d_path)
        elif t["is_tg_file"]:
            f_path = await client.download_media(t["tg_obj"], file_name=d_path, progress=progress_for_pyrogram, progress_args=("⬇️ Downloading...", status_msg, start_t))
        
        await status_msg.edit("📤 **Uploading...**")
        # Video conversion/metadata extraction logic
        if mode == "video" and f_path.lower().endswith(('.mp4', '.mkv', '.webm', '.avi')):
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
