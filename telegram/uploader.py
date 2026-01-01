from pyrogram import Client
from helpers.cleanup import cleanup_path

async def upload(client: Client, chat_id, path, stream):
    if stream:
        await client.send_video(chat_id, path)
    else:
        await client.send_document(chat_id, path)
    cleanup_path(path)
