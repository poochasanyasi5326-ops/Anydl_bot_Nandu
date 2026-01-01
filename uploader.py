import os
from pyrogram.errors import FloodWait
import asyncio

async def upload(client, chat_id, path, stream):
    try:
        if stream:
            await client.send_video(chat_id, path, supports_streaming=True)
        else:
            await client.send_document(chat_id, path)
    finally:
        os.remove(path)
