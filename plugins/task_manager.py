import os
import uuid
import time
import asyncio
import subprocess
import requests

from helper_funcs.display import (
    edit_download_progress,
    edit_upload_progress,
    final_message,
)

# ===================== CONFIG =====================
OWNER_ID = 519459195
MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
SEEDR_TOKEN = os.getenv("SEEDR_TOKEN")

TMP_DIR = "/tmp/anydl"
os.makedirs(TMP_DIR, exist_ok=True)

# ===================== GLOBAL JOB =====================
ACTIVE_JOB = None


class JobCancelled(Exception):
    pass


class Job:
    def __init__(self, message):
        self.id = str(uuid.uuid4())
        self.message = message
        self.user_id = message.from_user.id
        self.cancelled = False
        self.process = None
        self.file_path = None
        self.start_time = time.time()

    def cancel(self):
        self.cancelled = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass


# ===================== PUBLIC API =====================
def has_active_job():
    return ACTIVE_JOB is not None


def cancel_active_job():
    global ACTIVE_JOB
    if ACTIVE_JOB:
        ACTIVE_JOB.cancel()


async def handle_job(message, job_type, payload, options):
    """
    job_type: youtube | seedr | direct
    payload : url / magnet
    options : dict (format, rename, streamable, etc)
    """
    global ACTIVE_JOB

    job = Job(message)
    ACTIVE_JOB = job

    try:
        if job_type == "youtube":
            await _handle_youtube(job, payload, options)
        elif job_type == "seedr":
            await _handle_seedr(job, payload, options)
        elif job_type == "direct":
            await _handle_direct(job, payload, options)

        await final_message(job.message, "✅ Completed")

    except JobCancelled:
        await final_message(job.message, "❌ Operation cancelled")

    except Exception as e:
        await final_message(job.message, f"❌ Error: {e}")

    finally:
        _cleanup(job)
        ACTIVE_JOB = None


# ===================== YOUTUBE =====================
async def _handle_youtube(job, url, options):
    """
    options:
      format_id
      final_name
      streamable (bool)
    """

    out_path = os.path.join(TMP_DIR, job.id)
    cmd = [
        "yt-dlp",
        "-f", options["format_id"],
        "-o", out_path,
        "--newline"
    ]

    job.process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    total = None
    downloaded = 0

    for line in job.process.stdout:
        if job.cancelled:
            raise JobCancelled()

        if "[download]" in line and "%" in line:
            # yt-dlp progress parsing (safe & simple)
            parts = line.split()
            try:
                percent = float(parts[1].replace("%", ""))
                downloaded = percent
            except Exception:
                pass

            await edit_download_progress(
                job.message,
                percent=downloaded,
                job_id=job.id
            )

    job.process.wait()

    if job.cancelled:
        raise JobCancelled()

    job.file_path = _resolve_downloaded_file(out_path)
    await _upload(job, options)


# ===================== SEEDR =====================
async def _handle_seedr(job, magnet, options):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {SEEDR_TOKEN}"})

    _seedr_cleanup(session)

    r = session.post(
        "https://www.seedr.cc/api/torrent",
        data={"torrent_magnet": magnet}
    )
    r.raise_for_status()
    torrent_id = r.json()["torrent_id"]

    while True:
        if job.cancelled:
            _seedr_cleanup(session)
            raise JobCancelled()

        data = session.get(
            f"https://www.seedr.cc/api/torrent/{torrent_id}"
        ).json()

        size = data.get("size", 0)
        progress = data.get("progress", 0)

        if size > MAX_SIZE:
            _seedr_cleanup(session)
            raise Exception("File exceeds 2GB limit")

        await edit_download_progress(
            job.message,
            percent=progress,
            job_id=job.id
        )

        if progress == 100:
            break

        await asyncio.sleep(10)

    files = session.get("https://www.seedr.cc/api/files").json()["files"]
    url = files[0]["download_url"]

    job.file_path = await _download_http(job, url)
    await _upload(job, options)
    _seedr_cleanup(session)


def _seedr_cleanup(session):
    for ep in ["files", "folders"]:
        r = session.get(f"https://www.seedr.cc/api/{ep}")
        for i in r.json().get(ep, []):
            session.delete(
                f"https://www.seedr.cc/api/{ep[:-1]}/{i['id']}"
            )


# ===================== DIRECT =====================
async def _handle_direct(job, url, options):
    job.file_path = await _download_http(job, url)
    await _upload(job, options)


async def _download_http(job, url):
    local = os.path.join(TMP_DIR, job.id)
    r = requests.get(url, stream=True)

    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    start = time.time()

    with open(local, "wb") as f:
        for chunk in r.iter_content(1024 * 512):
            if job.cancelled:
                raise JobCancelled()

            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

                percent = (
                    (downloaded / total) * 100 if total else 0
                )

                await edit_download_progress(
                    job.message,
                    percent=percent,
                    job_id=job.id
                )

    return local


# ===================== UPLOAD =====================
async def _upload(job, options):
    await edit_upload_progress(
        job.message,
        stage="starting",
        job_id=job.id
    )

    await job.message.reply_document(
        job.file_path,
        supports_streaming=options.get("streamable", False),
        progress=lambda c, t: edit_upload_progress(
            job.message,
            current=c,
            total=t,
            job_id=job.id,
            cancelled=lambda: job.cancelled
        )
    )

    if job.cancelled:
        raise JobCancelled()


# ===================== HELPERS =====================
def _resolve_downloaded_file(base):
    for f in os.listdir(TMP_DIR):
        if f.startswith(os.path.basename(base)):
            return os.path.join(TMP_DIR, f)
    raise Exception("Downloaded file not found")


def _cleanup(job):
    if job.file_path and os.path.exists(job.file_path):
        try:
            os.remove(job.file_path)
        except Exception:
            pass
