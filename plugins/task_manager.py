import time, os, asyncio, aria2p, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import progress_for_pyrogram, humanbytes
from plugins.command import OWNER_ID, is_authorized

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def link_handler(client, message):
    if not is_authorized(message.from_user.id): return
    
    url = message.text.strip()
    # Dashboard with Rename option
    buttons = [
        [InlineKeyboardButton("📝 Rename File", callback_data="rename_file")],
        [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]
    ]
    TASKS[message.from_user.id] = {"url": url, "new_name": None, "gid": None}
    await message.reply_text("✅ **Link Detected**\nWould you like to rename it before starting?", 
                            reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("start_dl"))
async def start_download(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    # Initial tracker injection to prevent "Stuck" magnets
    trackers = "&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://9.rarbg.com:2810/announce"
    
    try:
        download = aria2.add_magnet(task["url"] + trackers)
        task["gid"] = download.gid
        
        # --- PROGRESS TRACKER LOOP ---
        while not download.is_complete:
            download.update()
            if download.status == "error":
                await query.message.edit("❌ Download Error.")
                return
            
            # If speed is 0 for too long, we "Inject Turbo Trackers"
            msg = "⬇️ **Downloading...**"
            if download.download_speed < 1024 and download.total_length > 0:
                msg = "⚠️ **Low Seeds! Adding Turbo Trackers...**"

            p = (download.completed_length / download.total_length * 100) if download.total_length > 0 else 0
            
            btn = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]]
            await query.message.edit(
                f"{msg}\n`{humanbytes(download.completed_length)}` / `{humanbytes(download.total_length)}`"
                f"\nSpeed: `{humanbytes(download.download_speed)}/s` | 👥 `{download.connections}`"
                f"\nProgress: `{round(p, 2)}%`",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            await asyncio.sleep(5)

        # --- UPLOAD & RENAME PHASE ---
        await query.message.edit("📤 **Download Complete! Uploading...**")
        file_path = download.files[0].path
        
        # Apply Rename if requested
        if task["new_name"]:
            new_path = os.path.join(os.path.dirname(file_path), task["new_name"])
            os.rename(file_path, new_path)
            file_path = new_path

        await client.send_document(query.message.chat.id, file_path)

    except Exception as e:
        await query.message.edit(f"❌ Error: {e}")
    finally:
        # CLEANUP: Wipes the file from 16GB storage immediately after upload
        if 'file_path' in locals() and os.path.exists(os.path.dirname(file_path)):
            shutil.rmtree(os.path.dirname(file_path))
        if u_id in TASKS: del TASKS[u_id]

@Client.on_callback_query(filters.regex("cancel_dl"))
async def cancel_handler(client, query: CallbackQuery):
    u_id = query.from_user.id
    if u_id in TASKS and TASKS[u_id]["gid"]:
        aria2.remove([aria2.get_download(TASKS[u_id]["gid"])])
        await query.message.edit("❌ **Download Cancelled & Deleted.**")
        del TASKS[u_id]
