import os
from pyrogram import Client
from plugins.command import register

BOT = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

BOT.start()
register(BOT)
BOT.idle()
