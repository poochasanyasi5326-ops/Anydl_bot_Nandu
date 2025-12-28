import time, os, asyncio, aria2p, shutil, re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata

OWNER_ID = 519459195  
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

async def show_dashboard(client, chat_id, msg_id, user_id):
    if user_id not in TASKS: return
    t = TASKS[user_id]
    name_display = t["new_name"] if t["new_name"] else "Default (Auto)"
    
    btn = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
           [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
    
    text = f"📦 **Task Dashboard**\n\n📂 **Custom Name:** `{name_display}`\n🔗 **Target:** `Link Detected`"
    await client.edit_message_text(chat_id, msg_id, text, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def link_handler(client, message):
    if message.from_user.id != OWNER_ID: return
    url = message.text.strip()
    sent = await message.reply_text("🔎 **Analyzing link...**")
    
    TASKS[message.from_user.id] = {
        "url": url, "new_name": None, "gid": None, "state": None, "message_id": sent.id
    }
    await show_dashboard(client, message.chat.id, sent.id, message.from_user.id)

@Client.on_callback_query(filters.regex("start_dl"))
async def start_dl(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    try:
        # Step 1: Add Magnet with initial trackers
        dl = aria2.add_magnet(task["url"], options={'dir': '/app/downloads'})
        task["gid"] = dl.gid
        
        # Step 2: Progress Loop with Tracker Injection
        start_t = time.time()
        while not dl.is_complete:
            dl.update()
            if (time.time() - start_t) > 60 and dl.download_speed < 10000:
                # Add turbo trackers after 1 min if speed is < 10KB/s
                aria2.change_options(dl.gid, {'bt-tracker': 'udp://tracker.opentrackr.org:1337/announce,udp://9.rarbg.com:2810/announce'})
            
            p = (dl.completed_length / dl.total_length * 100) if dl.total_length > 0 else 0
            await query.message.edit(
                f"⬇️ **Downloading:** `{round(p, 2)}%` | 👥 `{dl.connections}`\n⚡ Speed: `{humanbytes(dl.download_speed)}/s`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]])
            )
            await asyncio.sleep(5)

        # Step 3: Rename & Process
        file_path = dl.files[0].path
        if task["new_name"]:
            new_path = os.path.join(os.path.dirname(file_path), task["new_name"])
            os.rename(file_path, new_path)
            file_path = new_path

        await query.message.edit("🎬 **Generating Thumbnail...**")
        thumb = await take_screen_shot(file_path, "/app/downloads", 10)
        w, h, dur = await get_metadata(file_path)

        await query.message.edit("📤 **Uploading...**")
        await client.send_video(query.message.chat.id, file_path, thumb=thumb, width=w, height=h, duration=dur, supports_streaming=True)

    except Exception as e:
        await query.message.edit(f"❌ Error: {e}")
    finally:
        # Step 7: Final Cleanup of 16GB Storage
        shutil.rmtree('/app/downloads', ignore_errors=True)
        if u_id in TASKS: del TASKS[u_id]
