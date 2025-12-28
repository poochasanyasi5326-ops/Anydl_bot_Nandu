 import time, os, asyncio, aria2p, shutil, yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata

# CRITICAL: This matches the functions in your new command.py
from plugins.command import OWNER_ID, is_authorized

aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))
TASKS = {}

async def show_dashboard(client, chat_id, msg_id, user_id):
    if user_id not in TASKS: return
    t = TASKS[user_id]
    name_display = t["new_name"] if t["new_name"] else "Default (Auto)"
    
    btn = [[InlineKeyboardButton("📝 Rename", callback_data="set_rename")],
           [InlineKeyboardButton("🚀 Start Download", callback_data="start_dl")]]
    
    text = f"📦 **Task Dashboard**\n\n📂 **Custom Name:** `{name_display}`\n🔗 **Link:** `Detected`"
    await client.edit_message_text(chat_id, msg_id, text, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.private & filters.regex(r'http|magnet'))
async def link_handler(client, message):
    if not is_authorized(message.from_user.id): return
    
    url = message.text.strip()
    sent = await message.reply_text("🔎 **Analyzing link...**")
    
    # Initialize task with Rename State
    TASKS[message.from_user.id] = {
        "url": url, "new_name": None, "gid": None, "state": None, "message_id": sent.id
    }
    await show_dashboard(client, message.chat.id, sent.id, message.from_user.id)

@Client.on_callback_query(filters.regex("start_dl"))
async def start_dl(client, query: CallbackQuery):
    u_id = query.from_user.id
    task = TASKS.get(u_id)
    if not task: return

    await query.message.edit("📡 **Connecting...**")
    try:
        # Download logic with 16GB limit awareness
        dl = aria2.add_magnet(task["url"], options={'dir': '/app/downloads'})
        task["gid"] = dl.gid
        
        while not dl.is_complete:
            dl.update()
            p = (dl.completed_length / dl.total_length * 100) if dl.total_length > 0 else 0
            await query.message.edit(
                f"⬇️ **Downloading:** `{round(p, 2)}%`\n⚡ Speed: `{humanbytes(dl.download_speed)}/s`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_dl")]])
            )
            await asyncio.sleep(5)

        # Handle Rename before upload
        file_path = dl.files[0].path
        if
