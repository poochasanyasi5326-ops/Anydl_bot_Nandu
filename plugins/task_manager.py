import os, asyncio, subprocess, uuid, json, requests
from pyrogram.types import InputMediaPhoto
from helper_funcs.ffmpeg import generate_screenshots, is_streamable
from helper_funcs.display import final_message

OWNER_ID = 519459195
SEEDR_TOKEN = os.getenv("SEEDR_TOKEN")
TMP = "/tmp/anydl"
os.makedirs(TMP, exist_ok=True)

ACTIVE_JOB = None

class JobCancelled(Exception): pass

def has_active_job():
    return ACTIVE_JOB is not None

def cancel_active_job():
    global ACTIVE_JOB
    if ACTIVE_JOB:
        ACTIVE_JOB["cancel"] = True

def analyze_youtube(url):
    info = json.loads(subprocess.check_output(["yt-dlp", "-J", url]))
    formats = []

    for f in info["formats"]:
        if not f.get("filesize"):
            continue
        size_mb = round(f["filesize"] / (1024*1024), 1)

        if f.get("vcodec") != "none":
            formats.append({
                "id": f["format_id"],
                "label": f"{f.get('height','?')}p Video",
                "size": f"{size_mb} MB"
            })
        elif f.get("acodec") != "none":
            formats.append({
                "id": f["format_id"],
                "label": f"Audio {f.get('abr','?')} kbps",
                "size": f"{size_mb} MB"
            })
    return formats

async def handle_job(message, mode, payload, fmt_id, prefs):
    global ACTIVE_JOB
    job_id = str(uuid.uuid4())
    ACTIVE_JOB = {"id": job_id, "cancel": False}

    try:
        out = f"{TMP}/{job_id}.%(ext)s"

        if mode == "youtube":
            subprocess.run(["yt-dlp", "-f", fmt_id, "-o", out, payload], check=True)
            file_path = _find_file(job_id)

        elif mode == "seedr":
            s = requests.Session()
            s.headers.update({"Authorization": f"Bearer {SEEDR_TOKEN}"})
            r = s.post("https://www.seedr.cc/api/torrent", data={"torrent_magnet": payload})
            tid = r.json()["torrent_id"]

            while True:
                if ACTIVE_JOB["cancel"]:
                    raise JobCancelled()
                p = s.get(f"https://www.seedr.cc/api/torrent/{tid}").json()
                if p.get("progress") == 100:
                    break
                await asyncio.sleep(8)

            files = s.get("https://www.seedr.cc/api/files").json()["files"]
            file_path = await _download_http(files[0]["download_url"], job_id)

        else:
            file_path = await _download_http(payload, job_id)

        shots = []
        if prefs["screenshots"] and is_streamable(os.path.splitext(file_path)[1]):
            shots = generate_screenshots(file_path, f"{TMP}/{job_id}_shots")

        if not prefs["streamable"] and shots:
            await message.reply_media_group([InputMediaPhoto(s) for s in shots])

        await message.reply_document(
            file_path,
            supports_streaming=prefs["streamable"],
            thumb=prefs["thumbnail"] or (shots[0] if shots else None)
        )

        await final_message(message, "✅ Completed")

    except JobCancelled:
        await final_message(message, "❌ Cancelled")
    except Exception as e:
        await final_message(message, f"❌ Error: {e}")
    finally:
        ACTIVE_JOB = None

async def _download_http(url, job_id):
    path = f"{TMP}/{job_id}"
    r = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for c in r.iter_content(1024*512):
            if ACTIVE_JOB["cancel"]:
                raise JobCancelled()
            f.write(c)
    return path

def _find_file(job_id):
    for f in os.listdir(TMP):
        if f.startswith(job_id):
            return os.path.join(TMP, f)
    raise Exception("File not found")
