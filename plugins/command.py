import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import run, busy, yt_formats

# 1. TEMPORARILY SET THIS TO False TO FORCE THE BOT TO RESPOND
OWNER_ONLY = False 
OWNER = 519459195 

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

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, m):
    # This WILL show up in your Koyeb logs when you send /start
    print(f"DEBUG: Received /start from ID {m.from_user.id}")
    
    if OWNER_ONLY and m.from_user.id != OWNER:
        return await m.reply(f"🚫 Admin Only. Your ID is `{m.from_user.id}`. Update this in command.py")
        
    await m.reply("🚀 **AnyDL Ready**\nSend a link to start.", reply_markup=dashboard())

@Client.on_message(filters.private & filters.text)
async def text_handler(bot, m):
    if OWNER_ONLY and m.from_user.id != OWNER:
        return
    if busy(): 
        return await m.reply("⚠️ Bot is busy.")

    link = m.text.strip()
    if link.startswith(("http", "magnet:")):
        RENAME[m.from_user.id] = ("dir" if "http" in link else "tor", link)
        await m.reply("📂 Link detected. Rename?", 
                      reply_markup=InlineKeyboardMarkup([[
                          InlineKeyboardButton("✅ Default", callback_data="r:def"),
                          InlineKeyboardButton("✏️ Rename", callback_data="r:custom")
                      ]]))
