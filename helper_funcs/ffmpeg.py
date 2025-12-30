import subprocess, os, uuid

def is_streamable(path):
    return os.path.splitext(path)[1].lower() in [".mp4", ".mkv", ".webm"]

def screenshots(video):
    shots=[]
    for t in ["00:00:05", "00:10:00"]:
        out=f"/tmp/{uuid.uuid4().hex}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", t, "-i", video, "-vframes", "1", out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out): shots.append(out)
    return shots
