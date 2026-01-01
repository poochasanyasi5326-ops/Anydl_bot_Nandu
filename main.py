    import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import *
from downloader import download
from uploader import upload
from rename import smart_rename
from keyboards import rename_keyboard, upload_type_keyboard
from jobs import Job, jobs
from utils import is_url

app = Client(
    "anydl",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def owner_only(_, __, m):
    return m.from_user and m.from_user.id == OWNER_ID

@app.on_message(filters.command("start") & filters.create(owner_only))
async def start(_, m):
    await m.reply(
        "✅ AnyDL Ready\nSend a YouTube or direct link."
    )

@app.on_message(filters.command("help") & filters.create(owner_only))
async def help(_, m):
    await m.reply(
        "/start – Start bot\n"
        "/help – Commands\n"
        "Send link – Download"
    )

@app.on_message(filters.text & filters.create(owner_only))
async def handle_link(client, m):
    if not is_url(m.text):
        return

    job = Job(m.chat.id, m.id)
    jobs[m.id] = job

    status = await m.reply("⬇ Downloading...")

    def hook(d):
        if job.cancel.is_set():
            raise Exception("Cancelled")

    try:
        path = download(m.text, hook)
        job.filepath = path
        await status.edit(
            "✅ Downloaded",
            reply_markup=rename_keyboard()
        )
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

@app.on_callback_query(filters.create(owner_only))
async def callbacks(client, q):
    job = jobs.get(q.message.reply_to_message.id)

    if q.data == "cancel":
        job.cancel.set()
        await q.message.edit("❌ Cancelled")
        return

    if q.data == "rename":
        await q.message.edit("✏ Send new filename (without extension)")
        job.awaiting_rename = True
        return

    if q.data in ("stream", "file"):
        await q.message.edit("⬆ Uploading...")
        await upload(client, job.chat_id, job.filepath, q.data == "stream")

@app.on_message(filters.text & filters.create(owner_only))
async def rename_handler(_, m):
    for job in jobs.values():
        if getattr(job, "awaiting_rename", False):
            job.filepath = smart_rename(job.filepath, m.text)
            job.awaiting_rename = False
            await m.reply(
                "Choose upload type:",
                reply_markup=upload_type_keyboard()
            )
            return

app.run()
