import os, uuid, requests, asyncio, subprocess
from helper_funcs.ui import progress
from helper_funcs.ffmpeg import screenshots, is_streamable

RD = os.getenv("REAL_DEBRID_API_KEY")
TMP = "/tmp/anydl"
os.makedirs(TMP, exist_ok=True)

ACTIVE = None

def busy(): return ACTIVE is not None
def cancel(): 
    if ACTIVE: ACTIVE["stop"] = True

def rd_hosts():
    return requests.get("https://api.real-debrid.com/rest/1.0/hosts").json()

def rd_supported(url):
    host = url.split("/")[2].lower()
    return host in rd_hosts()

async def rd_unrestrict(url):
    r = requests.post(
        "https://api.real-debrid.com/rest/1.0/unrestrict/link",
        headers={"Authorization": f"Bearer {RD}"},
        data={"link": url}
    ).json()
    return r["download"]

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
    return path

async def run(job, mode, fmt, prefs, msg, fname):
    global ACTIVE
    jid = str(uuid.uuid4())
    ACTIVE = {"stop": False}

    try:
        out = f"{TMP}/{fname}"

        if mode == "youtube":
            subprocess.run(
                ["yt-dlp","-f",fmt,"-o",out,job],
                check=True
            )

        elif mode == "direct":
            link = await rd_unrestrict(job) if rd_supported(job) else job
            await http_download(link, out, msg, jid)

        shots = []
        if prefs["shots"] and is_streamable(out):
            shots = screenshots(out)

        await msg.reply_document(
            out,
            supports_streaming=prefs["stream"],
            thumb=prefs["thumb"] or (shots[0] if shots else None)
        )
        await msg.edit("✅ Completed")

    except:
        await msg.edit("❌ Cancelled / Failed")

    finally:
        ACTIVE = None
