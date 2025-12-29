import os, uuid, time, asyncio, subprocess, requests
from helper_funcs.display import edit_progress, final_message
from helper_funcs.ffmpeg import generate_screenshots, is_streamable
from pyrogram.types import InputMediaPhoto

OWNER_ID = 519459195
MAX_SIZE = 2 * 1024 * 1024 * 1024
SEEDR_TOKEN = os.getenv("SEEDR_TOKEN")

TMP = "/tmp/anydl"
os.makedirs(TMP, exist_ok=True)

ACTIVE_JOB = None

class JobCancelled(Exception):
    pass

class Job:
    def __init__(self, message):
        self.id = str(uuid.uuid4())
        self.message = message
        self.cancelled = False
        self.process = None
        self.file = None

    def cancel(self):
        self.cancelled = True
        if self.process:
            self.process.terminate()

def has_active_job():
    return ACTIVE_JOB is not None

def cancel_active_job():
    global ACTIVE_JOB
    if ACTIVE_JOB:
        ACTIVE_JOB.cancel()

async def handle_job(message, mode, payload, streamable):
    global ACTIVE_JOB
    job = Job(message)
    ACTIVE_JOB = job

    try:
        if mode == "youtube":
            await _youtube(job, payload)
        elif mode == "seedr":
            await _seedr(job, payload)
        elif mode == "direct":
            await _direct(job, payload)

        shots = []
        if is_streamable(os.path.splitext(job.file)[1]):
            shots = generate_screenshots(job.file, f"{TMP}/{job.id}_shots")

        if not streamable and shots:
            await message.reply_media_group(
                [InputMediaPhoto(s) for s in shots]
            )

        await message.reply_document(
            job.file,
            supports_streaming=streamable,
            thumb=shots[0] if streamable and shots else None
        )

        await final_message(message, "✅ Completed")

    except JobCancelled:
        await final_message(message, "❌ Cancelled")

    except Exception as e:
        await final_message(message, f"❌ Error: {e}")

    finally:
        _cleanup(job)
        ACTIVE_JOB = None

async def _youtube(job, url):
    out = f"{TMP}/{job.id}.%(ext)s"
    cmd = ["yt-dlp", "-f", "best", "-o", out, url]
    job.process = subprocess.Popen(cmd)
    job.process.wait()
    job.file = _find_file(job.id)

async def _seedr(job, magnet):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {SEEDR_TOKEN}"})

    r = s.post("https://www.seedr.cc/api/torrent", data={"torrent_magnet": magnet})
    tid = r.json()["torrent_id"]

    while True:
        if job.cancelled:
            raise JobCancelled()
        data = s.get(f"https://www.seedr.cc/api/torrent/{tid}").json()
        if data.get("progress") == 100:
            break
        await asyncio.sleep(10)

    files = s.get("https://www.seedr.cc/api/files").json()["files"]
    job.file = await _download_http(job, files[0]["download_url"])

async def _direct(job, url):
    job.file = await _download_http(job, url)

async def _download_http(job, url):
    path = f"{TMP}/{job.id}"
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for c in r.iter_content(1024 * 512):
            if job.cancelled:
                raise JobCancelled()
            f.write(c)
    return path

def _find_file(job_id):
    for f in os.listdir(TMP):
        if f.startswith(job_id):
            return os.path.join(TMP, f)
    raise Exception("File not found")

def _cleanup(job):
    if job.file and os.path.exists(job.file):
        os.remove(job.file)
