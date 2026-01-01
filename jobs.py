import asyncio

jobs = {}

class Job:
    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.cancel = asyncio.Event()
        self.filepath = None
