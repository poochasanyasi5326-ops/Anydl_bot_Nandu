import asyncio, os
from pyrogram import Client
from fastapi import FastAPI
import uvicorn
from plugins.command import register_handlers

BOT = Client(
    "anydl",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

app = FastAPI()

@app.get("/health")
async def health():
    return {"ok": True}

async def main():
    register_handlers(BOT)
    await BOT.start()
    uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=8000)
    ).run()

if __name__ == "__main__":
    asyncio.run(main())
