import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# TEMPORARY: Set these to allow the bot to respond to anyone for testing
OWNER_ONLY = False 
OWNER = 519459195 

def dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Help", callback_data="help"),
         InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("📊 Disk", callback_data="disk"),
         InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, m):
    # This print will show up in your Koyeb logs
    print(f"📩 DEBUG: Received /start from User ID: {m.from_user.id}")
    
    # This message will tell you your EXACT ID
    await m.reply(
        f"✅ **AnyDL is LIVE!**\n\n"
        f"Your numerical ID is: `{m.from_user.id}`\n\n"
        "Copy this ID and put it in your OWNER variable later."
    )

@Client.on_callback_query(filters.regex("^disk$"))
async def disk_chk(_, q):
    t, u, f = shutil.disk_usage(os.getcwd())
    await q.answer(f"Free: {f//1e9}GB", show_alert=True)

@Client.on_callback_query(filters.regex("^close$"))
async def _close(_, q):
    await q.message.delete()
