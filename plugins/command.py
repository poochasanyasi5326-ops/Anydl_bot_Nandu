import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import run, busy, yt_formats
from helper_funcs.ui import close_kb

# Replace with your actual ID or set OWNER_ONLY to False for testing
OWNER = 519459195 
OWNER_ONLY = False 

RENAME = {}
STATE = {}

def prefs(uid):
    return STATE.setdefault(uid, {"stream": True, "shots": True, "thumb": None})

def dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Help", callback_data="help"),
         InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🎞 Stream", callback_data="stream"),
         InlineKeyboardButton("📸 Screens", callback_data="shots")],
        [InlineKeyboardButton("📊 Disk", callback_data="disk"),
         InlineKeyboardButton("🔄 Reboot", callback_data="reboot")]
    ])

# This decorator is what Pyrogram looks for in the plugins folder
@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, m):
    if OWNER_ONLY and m.from_user.id != OWNER:
        return
    await m.reply("🚀 **AnyDL Ready**\nSend me a link to start.", reply_markup=dashboard())

@Client.on_message(filters.private & filters.text)
async def text_handler(bot, m):
    if OWNER_ONLY and m.from_user.id != OWNER:
        return
    if busy(): 
        return await m.reply("⚠️ Bot is busy with another task.")

    link = m.text.strip()
    # Simple check to see if it's a URL
    if link.startswith(("http", "magnet:")):
        if "youtu" in link:
            formats = yt_formats(link)
            btn = [[InlineKeyboardButton(f"{l} - {s}MB", callback_data=f"yt:{f}")] for t, f, l, s in formats]
            RENAME[m.from_user.id] = ("yt", link)
            await m.reply("🎥 **Select Quality:**", reply_markup=InlineKeyboardMarkup(btn))
        else:
            RENAME[m.from_user.id] = ("dir" if "http" in link else "tor", link)
            await m.reply("📂 **Link detected.** Do you want to rename?", 
                          reply_markup=InlineKeyboardMarkup([[
                              InlineKeyboardButton("✅ Default", callback_data="r:def"),
                              InlineKeyboardButton("✏️ Rename", callback_data="r:custom")
                          ]]))
