import os
from pyrogram import Client
from plugins.command import register

app = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

app.start()
register(app)
app.idle()
