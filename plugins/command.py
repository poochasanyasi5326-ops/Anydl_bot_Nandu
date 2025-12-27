from pyrogram import Client, filters
import os

# --- 🔒 SECURITY SETTINGS ---
# YOUR ID (Owner)
AUTH_USERS = [519459195] 

# Helper to check if user is allowed
def is_authorized(user_id):
    return user_id in AUTH_USERS

# Store user settings in memory
USER_THUMBS = {}

# --- /start COMMAND ---
@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    
    # 1. Check Authorization
    if not is_authorized(user_id):
        await message.reply_text(
            f"⛔ **Access Denied**\n"
            f"👤 **Your ID:** `{user_id}`\n"
            f"⚠️ You are not authorized to use this bot.\n"
            f"Contact the owner: @poocha"
        )
        return

    # 2. If Authorized (Owner)
    await message.reply_text(
        f"👋 **Welcome back, Boss!**\n\n"
        f"👤 **Role:** 👑 Owner\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"**🤖 System Status:** Online ✅\n"
        f"**💾 Storage:** Secure\n\n"
        f"👇 **What would you like to do?**\n"
        f"Send a Link, Magnet, or File to start processing.\n"
        f"Type /help to see all available commands."
    )

# --- /help COMMAND ---
@Client.on_message(filters.command("help"))
async def help_command(client, message):
    # Security Check
    if not is_authorized(message.from_user.id):
        return

    await message.reply_text(
        "📚 **Bot Command List**\n\n"
        "**⚡ Core Functions:**\n"
        "• **Upload:** Send any Link, Magnet, YouTube URL, or File.\n"
        "• **Rename:** Use the Dashboard menu after sending a file.\n"
        "• **Modes:** Switch between Video (Streamable) and Document (File).\n\n"
        "**🛠️ Settings Commands:**\n"
        "• `/start` - Check bot status and your ID.\n"
        "• `/help` - Show this menu.\n"
        "• `/set_thumb` - Reply to a photo to set it as your custom thumbnail.\n"
        "• `/del_thumb` - Delete your current custom thumbnail.\n\n"
        "**💡 Pro Tip:**\n"
        "You can rename files simply by forwarding them to me!"
    )

# --- THUMBNAIL COMMANDS ---
@Client.on_message(filters.command("set_thumb") & filters.reply)
async def set_thumbnail(client, message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("⚠️ Access Denied.")
        return

    if message.reply_to_message.photo:
        # Create folder if not exists
        if not os.path.exists("thumbs"): os.makedirs("thumbs")
        
        path = await client.download_media(message.reply_to_message, file_name=f"thumbs/{message.from_user.id}.jpg")
        USER_THUMBS[message.from_user.id] = path
        await message.reply_text("✅ **Thumbnail Saved!**\nFuture uploads will use this cover image.")
    else:
        await message.reply_text("❌ **Error:** You must reply to a photo to set it.")

@Client.on_message(filters.command("del_thumb"))
async def delete_thumbnail(client, message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("⚠️ Access Denied.")
        return

    user_id = message.from_user.id
    if user_id in USER_THUMBS:
        if os.path.exists(USER_THUMBS[user_id]):
            os.remove(USER_THUMBS[user_id])
        del USER_THUMBS[user_id]
        await message.reply_text("🗑️ **Thumbnail Deleted.**\nReset to default auto-generated thumbnails.")
    else:
        await message.reply_text("❌ You don't have a custom thumbnail set.")
