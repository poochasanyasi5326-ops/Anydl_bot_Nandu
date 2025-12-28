@Client.on_callback_query(filters.regex("check_disk"))
async def check_disk_callback(client, query: CallbackQuery):
    # Live storage check for your instance
    total, used, free = shutil.disk_usage("/")
    storage_info = (
        f"📊 **System Storage Status**\n\n"
        f"Total: `{humanbytes(total)}` (16GB Limit)\n"
        f"Used: `{humanbytes(used)}`\n"
        f"Free: `{humanbytes(free)}`"
    )
    # Edit the message to show storage info with an alert
    await query.message.edit(
        storage_info, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )
    await query.answer("Storage check complete!", show_alert=False)

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    # Returns the owner to the main funny welcome menu
    await start_handler(client, query.message)
