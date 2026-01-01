import asyncio

jobs = {}

def create_job(msg_id):
    jobs[msg_id] = {
        "cancel": asyncio.Event(),
        "file": None
    }

def cancel_job(msg_id):
    if msg_id in jobs:
        jobs[msg_id]["cancel"].set()
