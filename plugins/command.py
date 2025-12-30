from pyrogram import Client, filters

# EVERYTHING REMOVED EXCEPT THIS SIMPLE ECHO
@Client.on_message()
async def force_debug_handler(bot, message):
    # This WILL print in your Koyeb logs every time you send ANY message
    print(f"DEBUG: I received a message: {message.text} from {message.from_user.id}")
    
    try:
        await message.reply(f"🚨 BOT IS ALIVE!\nYour ID: `{message.from_user.id}`\nMessage: {message.text}")
    except Exception as e:
        print(f"ERROR: Could not send reply: {e}")
