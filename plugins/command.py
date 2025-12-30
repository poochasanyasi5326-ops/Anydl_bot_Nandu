# plugins/command.py
import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# TEMPORARY: Set this to False to verify the bot is working
OWNER_ONLY = False 
OWNER = 519459195 

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot, m):
    # This will print your REAL ID in the logs and send it back to you
    print(f"📩 Message from ID: {m.from_user.id}")
    
    await m.reply(
        f"🚀 **AnyDL is Working!**\n\nYour actual ID is: `{m.from_user.id}`\n"
        "Copy this ID and put it in your OWNER variable."
    )
