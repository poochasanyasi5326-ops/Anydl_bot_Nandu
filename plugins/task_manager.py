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
    if ACTIVE: ACTIVE["stop"] = True

def cleanup(*paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except:
            pass

def rd_hosts():
    try:
        return requests.get("https://api.real-debrid.com/rest/1.0/hosts").json()
    except:
        return {}

def rd_supported(url):
    host = url.split("/")[2].lower()
    return host in rd_hosts()

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
            if ACTIVE["stop"]:
                raise Exception("cancel")
            cur += len(c)
            f.write(c)
            await progress(msg, jid, "download", cur, total)
    return path, total

async def rd_torrent(magnet):
    h={"Authorization": f"Bearer {RD}"}
    r = requests.post(
        "https://api.real-debrid.com/rest/1.0/torrents/addMagnet",
        headers=h, data={"magnet": magnet}
    ).json()
    tid = r["id"]

    # cached-first
    info = requests.get(
        f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}",
        headers=h
    ).json()
    if info["status"] != "downloaded":
        requests.post(
            f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{tid}",
            headers=h, data={"files": "all"}
        )
        while True:
            if ACTIVE["stop"]:
                raise Exception("cancel")
            info = requests.get(
                f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}",
                headers=h
            ).json()
            if info["status"] == "downloaded":
                break
            await asyncio.sleep(5)

    # largest file
    links = info["links"]
    sizes = info["files"]
    largest = max(range(len(sizes)), key=lambda i: sizes[i]["bytes"])
    link = links[largest]

    u = requests.post(
        "https://api.real-debrid.com/rest/1.0/unrestrict/link",
        headers=h, data={"link": link}
    ).json()
    return u["download"], int(u.get("filesize", 0))

def yt_formats(url):
    info = json.loads(subprocess.check_output(["yt-dlp","-J",url]))
    out=[]
    for f in info["formats"]:
        if not f.get("filesize"): continue
        mb = round(f["filesize"]/1024/1024,1)
        if f.get("vcodec")!="none":
            out.append(("v", f["format_id"], f"{f.get('height','?')}p", mb))
        elif f.get("acodec")!="none":
            out.append(("a", f["format_id"], f"Audio {f.get('abr','?')}k", mb))
    return out

async def run(job, mode, fmt, prefs, msg, fname):
    global ACTIVE, LAST_ACTION
    jid = str(uuid.uuid4())
    ACTIVE = {"stop": False}

    out = f"{TMP}/{fname}"
    shots = []
    try:
        # Large-file confirmation handled earlier (UI)
        if mode == "youtube":
            subprocess.run(["yt-dlp","-f",fmt,"-o",out,job], check=True)

        elif mode == "torrent":
            link, size = await rd_torrent(job)
            await http_download(link, out, msg, jid)

        else:  # direct
            if rd_supported(job):
                link, _ = await rd_unrestrict(job)
            else:
                link = job
            await http_download(link, out, msg, jid)

        if prefs["shots"] and is_streamable(out):
            shots = screenshots(out)

        await msg.reply_document(
            out,
            supports_streaming=prefs["stream"],
            thumb=prefs["thumb"] or (shots[0] if shots else None)
        )
        await msg.edit("✅ Completed")

        LAST_ACTION = (job, mode, fmt, prefs.copy(), fname)

    except Exception as e:
        await msg.edit("❌ Cancelled / Failed" + (f"\n`{e}`" if DEBUG else ""))

    finally:
        cleanup(out, *(shots or []))
        ACTIVE = None
