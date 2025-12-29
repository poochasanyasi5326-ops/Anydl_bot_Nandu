import os, uuid, requests, asyncio, subprocess, json, shutil
from helper_funcs.ui import progress
from helper_funcs.ffmpeg import screenshots, is_streamable

RD = os.getenv("REAL_DEBRID_API_KEY")
TMP = "/tmp/anydl"
os.makedirs(TMP, exist_ok=True)

ACTIVE = None
LAST_ACTION = None
DEBUG = False

def busy(): return ACTIVE is not None

def cancel(): 
    global ACTIVE
    if ACTIVE: 
        ACTIVE["stop"] = True

def cleanup(*paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
        except:
            pass

def rd_hosts():
    try:
        r = requests.get("https://api.real-debrid.com/rest/1.0/hosts")
        return r.json()
    except:
        return {}

def rd_supported(url):
    try:
        host = url.split("/")[2].lower()
        return host in rd_hosts()
    except:
        return False

async def rd_unrestrict(url):
    r = requests.post(
        "https://api.real-debrid.com/rest/1.0/unrestrict/link",
        headers={"Authorization": f"Bearer {RD}"},
        data={"link": url}
    ).json()
    if "error" in r:
        raise Exception(r.get("error"))
    return r["download"], int(r.get("filesize", 0))

async def http_download(url, path, msg, jid):
    r = requests.get(url, stream=True)
    total = int(r.headers.get("content-length", 0))
    cur = 0
    with open(path, "wb") as f:
        for c in r.iter_content(1024*512):
            if ACTIVE and ACTIVE.get("stop"):
                raise Exception("cancel")
            if c:
                cur += len(c)
                f.write(c)
                await progress(msg, jid, "download", cur, total)
    return path, total

async def rd_torrent(magnet):
    h = {"Authorization": f"Bearer {RD}"}
    r = requests.post(
        "https://api.real-debrid.com/rest/1.0/torrents/addMagnet",
        headers=h, data={"magnet": magnet}
    ).json()
    tid = r["id"]

    # Check info and select files
    info = requests.get(f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}", headers=h).json()
    requests.post(f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{tid}", headers=h, data={"files": "all"})

    while True:
        if ACTIVE and ACTIVE.get("stop"):
            raise Exception("cancel")
        info = requests.get(f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}", headers=h).json()
        if info["status"] == "downloaded":
            break
        await asyncio.sleep(5)

    links = info["links"]
    # Unrestrict the largest file in the torrent
    u = requests.post(
        "https://api.real-debrid.com/rest/1.0/unrestrict/link",
        headers=h, data={"link": links[0]}
    ).json()
    return u["download"], int(u.get("filesize", 0))

def yt_formats(url):
    cmd = ["yt-dlp", "-J", "--no-warnings", url]
    info = json.loads(subprocess.check_output(cmd).decode("utf-8"))
    out = []
    for f in info.get("formats", []):
        if not f.get("filesize") and not f.get("filesize_approx"): continue
        size = f.get("filesize") or f.get("filesize_approx")
        mb = round(size / 1024 / 1024, 1)
        if f.get("vcodec") != "none":
            out.append(("v", f["format_id"], f"{f.get('height','?')}p", mb))
        elif f.get("acodec") != "none":
            out.append(("a", f["format_id"], f"Audio {f.get('abr','?')}k", mb))
    return out

async def run(job, mode, fmt, prefs, msg, fname):
    global ACTIVE, LAST_ACTION
    jid = str(uuid.uuid4())
    ACTIVE = {"stop": False}
    
    out = os.path.join(TMP, fname)
    shots = []
    
    # Update status in Telegram
    status_msg = await msg.edit(f"⏳ **Processing:** `{fname}`")

    try:
        if mode == "youtube":
            # Async subprocess call
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "-f", fmt, "-o", out, job,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()

        elif mode == "torrent":
            link, size = await rd_torrent(job)
            await http_download(link, out, status_msg, jid)

        elif mode == "file":
            # job is the original Message object
            await job.download(file_name=out)

        else:  # direct
            if rd_supported(job):
                link, _ = await rd_unrestrict(job)
            else:
                link = job
            await http_download(link, out, status_msg, jid)

        # Post-Processing: Screenshots
        if prefs.get("shots") and is_streamable(out):
            await status_msg.edit("📸 **Generating Screenshots...**")
            shots = screenshots(out)

        await status_msg.edit("📤 **Uploading to Telegram...**")
        
        # Determine thumbnail (Custom > Screenshot > None)
        final_thumb = prefs.get("thumb")
        if not final_thumb and shots:
            final_thumb = shots[0]

        await msg.reply_document(
            out,
            caption=f"✅ `{fname}`",
            supports_streaming=prefs.get("stream", True),
            thumb=final_thumb
        )
        await status_msg.delete()
        LAST_ACTION = (job, mode, fmt, prefs.copy(), fname)

    except Exception as e:
        error_text = f"❌ **Failed**"
        if str(e) == "cancel":
            error_text = "❌ **Cancelled by User**"
        elif DEBUG:
            error_text += f"\n`{e}`"
        await status_msg.edit(error_text)

    finally:
        cleanup(out, *(shots or []))
        ACTIVE = None
