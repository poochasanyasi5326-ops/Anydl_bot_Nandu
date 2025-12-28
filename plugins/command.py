import random
import shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 

# Sarcastic & Witty messages for the Owner
OWNER_MESSAGES = [
    "🚀 **System Online.** Ready to download the internet, or just that one movie again, Boss?",
    "🤖 **Beep Boop.** Your digital slave is at your service. What’s the mission today?",
    "✨ **Welcome back, Overlord.** The servers are humming and I've cleared the crumbs from the storage.",
    "🎩 **At your service!** I'm essentially 42 lines of code and a lot of caffeine. Ready when you are.",
    "🛰 **GPS Locked.** I’ve spotted your next download from space. Just paste the link, Captain."
]

# Funny 'Gatekeeper' messages for Unauthorized Users
UNAUTH_MESSAGES = [
    "🛑 **HALT!** You aren't my creator. I don't talk to strangers... usually.",
    "🕵️‍♂️ **Access Denied.** My owner told me about people like you. Please move along!",
    "🛡 **SYSTEM ERROR:** User is too cool for this bot. (Just kidding, you're just not authorized).",
    "🤫 **Psst...** I'm a private bot. Unless you're the Boss, I'm just a very expensive calculator.",
    "🚫 **Error 404: Permission Not Found.** Have you tried being the person who built me?",
    "⚠️ **Warning:** Sarcasm levels too high for guest access. Please log out."
]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    
    # 1. Funny Logic for Unauthorized Users
    if not is_authorized(user_id):
        unauth_text = random.choice(UNAUTH_MESSAGES)
        unauth_buttons = [[
            InlineKeyboardButton("🆔 Who am I?", callback_data="show_user_id"),
            InlineKeyboardButton("👨‍💻 Complain to Boss", url="https://t.me/poocha")
        ]]
        return await message.reply_text(unauth_text, reply_markup=InlineKeyboardMarkup(unauth_buttons))

    # 2. Funny Logic for the Owner
    welcome_text = random.choice(OWNER_MESSAGES)
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(owner_buttons))
