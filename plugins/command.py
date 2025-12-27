from pyrogram import Client, filters

@Client.on_message(filters.command(["start", "help"]))
async def start_command(client, message):
    # This is the message the bot will send back
    await message.reply_text(
        "**Hello! I am alive.** 🤖\n\n"
        "Send me a **Magnet Link**, **Torrent File**, or **Direct URL** "
        "and I will start downloading it for you!"
    )