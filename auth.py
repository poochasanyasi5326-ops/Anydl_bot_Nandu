from pyrogram import filters
from config import OWNER_IDS

def owner_only():
    async def func(_, __, message):
        return message.from_user and message.from_user.id in OWNER_IDS
    return filters.create(func)
