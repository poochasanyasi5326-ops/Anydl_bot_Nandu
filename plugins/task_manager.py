import time, os, asyncio, aria2p, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata
from plugins.command import OWNER_ID

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def link_handler(client, message):
    if message.from_user.id != OWNER_ID: return
    
    url = message.text.strip()
    TASKS[message.from_user.id] = {"url": url, "name": None, "gid": None}
    
    btn = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
           [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
    await message.reply_text("📦 **Task Detected**\nChoose an action:", reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex("start_dl"))
async def start_dl(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    await query.message.edit("📡 **Connecting to Seeds...**")
    try:
        # Initial trackers
        dl = aria2.add_magnet(task["url"], options={'dir': '/app/downloads'})
        task["gid"] = dl.gid
        
        start_time = time.time()
        tracker_added = False

        while not dl.is_complete:
            dl.update()
            elapsed = time.time() - start_time
            
            # Tracker Injection Logic
            if elapsed > 120 and dl.download_speed < 50000 and not tracker_added:
                # Add turbo trackers if slow after 2 mins
                aria2.change_options(dl.gid, {'bt-tracker': 'udp://tracker.opentrackr.org:1337/announce,udp://9.rarbg.com:2810/announce'})
                tracker_added = True
                await query.message.edit("🚀 **Low speed! Adding Turbo Trackers...**")
                await asyncio.sleep(2)

            p = (dl.completed_length / dl.total_length * 100) if dl.total_length > 0 else 0
            await query.message.edit(
                f"⬇️ **Downloading:** `{round(p, 2)}%`\n"
                f"⚡ Speed: `{humanbytes(dl.download_speed)}/s` | 👥 `{dl.connections}`\n"
                f"📂 Size: `{humanbytes(dl.total_length)}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]])
            )
            await asyncio.sleep(5)

        # Download Finished -> Handle Rename & Screenshot
        await query.message.edit("🎬 **Generating Screenshot & Metadata...**")
        file_path = dl.files[0].path
        
        # Take screenshot for thumbnail
        thumb = await take_screen_shot(file_path, "/app/downloads", 10)
        width, height, duration = await get_metadata(file_path)

        await query.message.edit("📤 **Uploading to Telegram...**")
        await client.send_video(
            query.message.chat.id, 
            file_path, 
            thumb=thumb, 
            width=width, 
            height=height, 
            duration=duration,
            supports_streaming=True
        )

    except Exception as e:
        await query.message.edit(f"❌ Error: {e}")
    finally:
        # Auto-clean Storage
        if u_id in TASKS:
            shutil.rmtree('/app/downloads', ignore_errors=True)
            del TASKS[u_id]
