import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# TEMPORARY: Set to False to bypass all security and force a response
OWNER_ONLY = False 
OWNER = 519459195 

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, m):
    # This WILL show in your Koyeb logs to confirm it saw you
    print(f"DEBUG: Received /start from User ID {m.from_user.id}")
    
    # This message will reveal your CORRECT ID
    await m.reply(
        f"✅ **AnyDL is Finally Working!**\n\n"
        f"Your actual numerical ID is: `{m.from_user.id}`\n\n"
        "Copy this ID and update the OWNER variable in your code."
    )

@Client.on_callback_query(filters.regex("^close$"))
async def _close(_, q):
    await q.message.delete()
