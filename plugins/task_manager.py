import os, uuid, requests, asyncio, subprocess, json
from helper_funcs.ui import progress
from helper_funcs.ffmpeg import screenshots, is_streamable

RD_KEY = os.getenv("REAL_DEBRID_API_KEY")
ACTIVE = None

def busy(): return ACTIVE is not None
def cancel(): 
    global ACTIVE
    if ACTIVE: ACTIVE["stop"] = True

async def run(job, mode, fmt, prefs, msg, fname):
    global ACTIVE
    jid = str(uuid.uuid4())
    ACTIVE = {"stop": False}
    out = f"/tmp/{fname}"
    
    status = await msg.edit(f"⏳ **Initializing:** `{fname}`")
    try:
        if mode == "youtube":
            proc = await asyncio.create_subprocess_exec("yt-dlp", "-f", fmt, "-o", out, job)
            await proc.wait()
        elif mode == "torrent":
            # Real-Debrid Torrent Logic
            h = {"Authorization": f"Bearer {RD_KEY}"}
            r = requests.post("https://api.real-debrid.com/rest/1.0/torrents/addMagnet", headers=h, data={"magnet": job}).json()
            tid = r['id']
            requests.post(f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{tid}", headers=h, data={"files": "all"})
            # Simple wait logic
            await asyncio.sleep(5)
            info = requests.get(f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}", headers=h).json()
            link = info['links'][0]
            unrestrict = requests.post("https://api.real-debrid.com/rest/1.0/unrestrict/link", headers=h, data={"link": link}).json()
            await http_dl(unrestrict['download'], out, status, jid)
        elif mode == "file":
            await job.download(file_name=out)
        else: # Direct
            await http_dl(job, out, status, jid)

        # Post Process
        shots = []
        if prefs["shots"] and is_streamable(out):
            shots = screenshots(out)
        
        await status.edit("📤 **Uploading...**")
        await msg.reply_document(out, thumb=prefs["thumb"] or (shots[0] if shots else None), 
                                 supports_streaming=prefs["stream"], caption=f"✅ `{fname}`")
        await status.delete()
    except Exception as e:
        await status.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(out): os.remove(out)
        ACTIVE = None

async def http_dl(url, path, msg, jid):
    r = requests.get(url, stream=True)
    total = int(r.headers.get('content-length', 0))
    cur = 0
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*512):
            if ACTIVE["stop"]: raise Exception("User Cancelled")
            f.write(chunk)
            cur += len(chunk)
            await progress(msg, jid, "Downloading", cur, total)

def yt_formats(url):
    cmd = ["yt-dlp", "-J", url]
    info = json.loads(subprocess.check_output(cmd).decode())
    return [(f['format_id'], f['format_id'], f"{f.get('height','audio')}p", round(f.get('filesize',0)/1e6,1)) for f in info['formats'] if f.get('filesize')]
