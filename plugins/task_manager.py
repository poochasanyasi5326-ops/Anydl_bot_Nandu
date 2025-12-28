import os, time, yt_dlp, aria2p, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper_funcs.display import humanbytes, progress_for_pyrogram

# Initialize Aria2 Bridge
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

@Client.on_message(filters.regex(r'http|magnet|rt:'))
async def link_handler(client, message):
    url = message.text
    status = await message.reply_text("🔎 Analyzing Link...")
    
    # --- 2. YouTube Management (Size/Format Selection) ---
    if "youtube" in url or "youtu.be" in url:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            btns = [
                [InlineKeyboardButton("🎬 Video", callback_data=f"yt_v_{info['id']}"),
                 InlineKeyboardButton("🎧 Audio", callback_data=f"yt_a_{info['id']}")],
                [InlineKeyboardButton("📝 Rename", callback_data="rename"),
                 InlineKeyboardButton("✖️ Cancel", callback_data="cancel")]
            ]
            await status.edit(f"🎥 **Title:** {info.get('title')}\nSize: {humanbytes(info.get('filesize_approx', 0))}", reply_markup=InlineKeyboardMarkup(btns))
    
    # --- 3. Torrent & Magnet Support ---
    elif "magnet:" in url or url.endswith(".torrent"):
        try:
            download = aria2.add_magnet(url)
            await status.edit(f"⚡ Magnet Added!\n`{download.name}`\n\nChecking peers...")
            # Trigger Progress Tracker (Feature 6)
            while not download.is_complete:
                await asyncio.sleep(4)
                download.update()
                await progress_for_pyrogram(download.completed_length, download.total_length, "Downloading Magnet", status, time.time())
        except Exception as e:
            await status.edit(f"❌ Aria2 Error: {e}")

# --- 4. Cancel & Rename Handlers ---
@Client.on_callback_query(filters.regex("cancel"))
async def cancel_task(client, query):
    await query.message.edit("❌ Task Cancelled. Storage cleared.")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)

@Client.on_callback_query(filters.regex("rename"))
async def rename_query(client, query):
    await query.message.edit("📝 **Send me the new name** for this file:")
    # Logic to wait for next message would go here using client.listen()
