import subprocess, os, uuid

def is_streamable(path):
    return os.path.splitext(path)[1].lower() in [".mp4", ".mkv", ".webm"]

def screenshots(video):
    shots=[]
    for t in ["00:00:03","00:00:08","00:00:15"]:
        out=f"/tmp/{uuid.uuid4().hex}.jpg"
        subprocess.run(
            ["ffmpeg","-y","-ss",t,"-i",video,"-frames:v","1",out],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if os.path.exists(out):
            shots.append(out)
    return shots
