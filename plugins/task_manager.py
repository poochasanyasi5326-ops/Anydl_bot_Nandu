import time, os, re, asyncio, aria2p, yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import progress_for_pyrogram, humanbytes
from plugins.command import OWNER_ID, is_authorized

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

@Client.on_message(filters.private & (filters.regex(r'http|magnet')))
async def handle_incoming(client, message):
    if not is_authorized(message.from_user.id): return
    
    url = message.text.strip()
    is_yt = "youtube.com" in url or "youtu.be" in url
    is_tor = url.startswith("magnet:")
    
    TASKS[message.from_user.id] = {"url": url, "mode": "video", "is_yt": is_yt, "is_tor": is_tor}
    
    buttons = [[InlineKeyboardButton("📂 Switch to Document", callback_data="toggle_mode")],
               [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
    
    await message.reply_text(f"📥 **Link Detected**\nType: `{'YouTube' if is_yt else 'Torrent' if is_tor else 'Direct'}`", 
                            reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("start_dl"))
async def start_dl(client, query: CallbackQuery):
    u_id = query.from_user.id
    if u_id not in TASKS: return
    
    task = TASKS[u_id]
    await query.message.edit("⏳ **Initializing...**")
    
    d_path = f"downloads/{u_id}_{int(time.time())}/"
    if not os.path.exists(d_path): os.makedirs(d_path)
    
    try:
        if task["is_yt"]:
            # YouTube Logic with Audio/Video Merge
            ydl_opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': f'{d_path}%(title)s.%(ext)s'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task["url"], download=True)
                f_path = ydl.prepare_filename(info)
        else:
            # Magnet/Direct Logic
            trackers = "&tr=udp://tracker.opentrackr.org:1337/announce" if task["is_tor"] else ""
            dl = aria2.add_magnet(task["url"] + trackers, options={'dir': os.path.abspath(d_path)})
            while not dl.is_complete:
                dl.update()
                await query.message.edit(f"⬇️ **Downloading:** {dl.progress_string()} | 👥 {dl.connections}")
                await asyncio.sleep(4)
            f_path = dl.files[0].path # Simplification

        await query.message.edit("📤 **Uploading to Telegram...**")
        await client.send_document(query.message.chat.id, f_path)
        
    except Exception as e:
        await query.message.edit(f"❌ Error: {e}")
    finally:
        # Step 7: Final Cleanup
        if os.path.exists(d_path):
            import shutil
            shutil.rmtree(d_path)
        if u_id in TASKS: del TASKS[u_id]
