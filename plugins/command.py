# ... (Keep previous imports and start_command)

@Client.on_callback_query(filters.regex("set_rename"))
async def set_rename_callback(client, query: CallbackQuery):
    u_id = query.from_user.id
    from plugins.task_manager import TASKS
    
    if u_id not in TASKS:
        return await query.answer("❌ No active task found. Send a link first.", show_alert=True)
    
    TASKS[u_id]["state"] = "waiting_for_name"
    await query.message.edit(
        "📝 **Rename Mode Active**\n\nSend the new filename (with extension, e.g., `movie.mp4`) as a reply to this message."
    )

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "id"]))
async def rename_input_handler(client, message):
    u_id = message.from_user.id
    from plugins.task_manager import TASKS, show_dashboard # Importing inside to avoid circular import
    
    if u_id in TASKS and TASKS[u_id].get("state") == "waiting_for_name":
        new_name = message.text.strip()
        TASKS[u_id]["new_name"] = new_name
        TASKS[u_id]["state"] = None # Reset state
        
        await message.reply_text(f"✅ Name set to: `{new_name}`")
        # Return to dashboard so user can click "Start"
        await show_dashboard(client, message.chat.id, TASKS[u_id]["message_id"], u_id)
