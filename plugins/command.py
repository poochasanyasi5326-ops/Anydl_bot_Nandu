from pyrogram import Client, filters
import os

# Store user settings in memory (resets if bot restarts on free tier)
USER_THUMBS = {}

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👋 **Hello! I am your Pro Downloader.**\n\n"
        "**Features:**\n"
        "🎥 Streamable Videos\n"
        "🖼️ Custom Thumbnails\n"
        "📸 Auto-Screenshots\n\n"
        "**Commands:**\n"
        "/set_thumb - Reply to an image to set custom thumbnail\n"
        "/del_thumb - Delete your custom thumbnail\n"
        "Just send a Link or Magnet to start!"
    )

@Client.on_message(filters.command("set_thumb") & filters.reply)
async def set_thumbnail(client, message):
    if message.reply_to_message.photo:
        # Download the photo to a specific path for this user
        path = await client.download_media(message.reply_to_message, file_name=f"thumbs/{message.from_user.id}.jpg")
        USER_THUMBS[message.from_user.id] = path
        await message.reply_text("✅ **Thumbnail Saved!** Future videos will use this cover.")
    else:
        await message.reply_text("❌ Reply to a photo to set it as thumbnail.")

@Client.on_message(filters.command("del_thumb"))
async def delete_thumbnail(client, message):
    user_id = message.from_user.id
    if user_id in USER_THUMBS:
        if os.path.exists(USER_THUMBS[user_id]):
            os.remove(USER_THUMBS[user_id])
        del USER_THUMBS[user_id]
        await message.reply_text("🗑️ **Thumbnail Deleted.**")
    else:
        await message.reply_text("❌ You don't have a custom thumbnail set.")
