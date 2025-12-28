# 1. Imports and Memory (Keep at top)
TASKS = {}
# ... (Other code)

# 2. MOVE THIS FUNCTION UP (Above incoming_task)
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return
    # ... (Rest of the dashboard code)

# 3. ENTRY POINT (Now this can safely call show_dashboard)
@Client.on_message(filters.private & ...)
async def incoming_task(client, message):
    # ... (Setup code)
    
    # This call will now work!
    await show_dashboard(client, message.chat.id, sent.id, user_id)

# 4. Rest of the file (handle_buttons, process_task, etc.)
