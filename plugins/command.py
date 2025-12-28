import os, random, shutil, sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_funcs.display import humanbytes

OWNER_ID = 519459195 
OWNER_MESSAGES = ["🚀 System Online, Boss!", "🤖 Ready to download, Overlord.", "🛰 GPS Locked, Captain."]

def is_authorized(user_id):
    return user_id == OWNER_ID

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if not is_authorized(message.from_user.id):
        return await message.reply_text("🛑 Access Denied.")
    
    owner_buttons = [
        [InlineKeyboardButton("📊 Disk Health", callback_data="check_disk"),
         InlineKeyboardButton("🖼️ View Thumb", callback_data="view_thumb")],
        [InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
         InlineKeyboardButton("🔄 Reboot Bot", callback_data="reboot_bot")],
        [InlineKeyboardButton("🆔 My Secret ID", callback_data="show_user_id")]
    ]
    await message.reply_text(random.choice(OWNER_MESSAGES), reply_markup=InlineKeyboardMarkup(owner_buttons))

@Client.on_message(filters.command("setthumbnail") & filters.private)
async def set_thumb(client, message):
    if not is_authorized(message.from_user.id) or not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("❌ Reply to a photo with /setthumbnail")
    
    thumb_path = os.path.join("downloads", f"{message.from_user.id}_thumb.jpg")
    os.makedirs("downloads", exist_ok=True)
    await message.reply_to_message.download(file_name=thumb_path)
    await message.reply_text("✅ Thumbnail saved!")

@Client.on_callback_query(filters.regex("view_thumb"))
async def view_thumb(client, query):
    path = os.path.join("downloads", f"{query.from_user.id}_thumb.jpg")
    if os.path.exists(path):
        await query.message.reply_photo(path, caption="🖼️ Current Custom Thumbnail")
    else:
        await query.answer("❌ No custom thumbnail found.", show_alert=True)

@Client.on_callback_query(filters.regex("reboot_bot"))
async def reboot_handler(client, query):
    await query.message.edit("🔄 Cleaning cache and rebooting...")
    shutil.rmtree("downloads", ignore_errors=True)
    os.makedirs("downloads", exist_ok=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    total, used, free = shutil.disk_usage("/")
    storage_info = (f"📊 **System Storage Status**\n\nTotal: `{humanbytes(total)}`"
                    f"\nUsed: `{humanbytes(used)}`"
                    f"\nFree: `{humanbytes(free)}`")
    await query.message.edit(storage_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
