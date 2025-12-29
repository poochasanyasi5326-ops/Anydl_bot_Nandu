import os, uuid, subprocess, json, requests, asyncio
from helper_funcs.ffmpeg import screenshots, is_streamable
from helper_funcs.progress import update

RD = os.getenv("REAL_DEBRID_API_KEY")
TMP = "/tmp/anydl"
os.makedirs(TMP, exist_ok=True)

ACTIVE = None

def busy(): return ACTIVE is not None
def cancel(): 
    global ACTIVE
    if ACTIVE: ACTIVE["cancel"]=True

def yt_formats(url):
    info=json.loads(subprocess.check_output(["yt-dlp","-J",url]))
    out=[]
    for f in info["formats"]:
        if not f.get("filesize"): continue
        mb=round(f["filesize"]/1024/1024,1)
        if f["vcodec"]!="none":
            out.append((f["format_id"],f"{f.get('height','?')}p",mb))
        elif f["acodec"]!="none":
            out.append((f["format_id"],f"Audio {f.get('abr','?')}k",mb))
    return out

async def direct(url, jid):
    r=requests.get(url,stream=True)
    path=f"{TMP}/{jid}"
    with open(path,"wb") as f:
        for c in r.iter_content(1024*512):
            if ACTIVE["cancel"]: raise Exception("cancel")
            f.write(c)
    return path

async def rd_unrestrict(url):
    h={"Authorization":f"Bearer {RD}"}
    r=requests.post("https://api.real-debrid.com/rest/1.0/unrestrict/link",
                    headers=h,data={"link":url}).json()
    return r["download"]

async def rd_torrent(magnet):
    h={"Authorization":f"Bearer {RD}"}
    r=requests.post("https://api.real-debrid.com/rest/1.0/torrents/addMagnet",
                    headers=h,data={"magnet":magnet}).json()
    tid=r["id"]
    requests.post(f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{tid}",
                  headers=h,data={"files":"all"})
    while True:
        info=requests.get(f"https://api.real-debrid.com/rest/1.0/torrents/info/{tid}",headers=h).json()
        if info["status"]=="downloaded": break
        await asyncio.sleep(5)
    link=info["links"][0]
    return (await rd_unrestrict(link))

async def run(job, mode, data, prefs, msg):
    global ACTIVE
    jid=str(uuid.uuid4())
    ACTIVE={"cancel":False}
    try:
        if mode=="youtube":
            out=f"{TMP}/{jid}.%(ext)s"
            subprocess.run(["yt-dlp","-f",data,"-o",out,job],check=True)
            file=[f for f in os.listdir(TMP) if f.startswith(jid)][0]
            path=f"{TMP}/{file}"
        elif mode=="torrent":
            link=await rd_torrent(job)
            path=await direct(link,jid)
        else:
            link=await rd_unrestrict(job)
            path=await direct(link,jid)

        shots=[]
        if prefs["shots"] and is_streamable(path):
            shots=screenshots(path,f"{TMP}/{jid}_s")

        await msg.reply_document(
            path,
            supports_streaming=prefs["stream"],
            thumb=prefs["thumb"] or (shots[0] if shots else None)
        )
        await msg.edit("✅ Done")

    except:
        await msg.edit("❌ Cancelled / Failed")
    finally:
        ACTIVE=None
