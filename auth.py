from pyrogram import filters
from config import OWNER_IDS

def owner_only():
    async def _check(_, __, message):
        # Allow if the user ID is in the OWNER_IDS list
        if message.from_user and message.from_user.id in OWNER_IDS:
            return True
        return False
    
    return filters.create(_check)