import subprocess, os

def is_streamable(path):
    return os.path.splitext(path)[1].lower() in [".mp4", ".mkv", ".webm"]

def screenshots(video, outdir):
    os.makedirs(outdir, exist_ok=True)
    times = ["00:00:03","00:00:08","00:00:15"]
    shots=[]
    for i,t in enumerate(times):
        out=f"{outdir}/shot{i}.jpg"
        subprocess.run(["ffmpeg","-y","-ss",t,"-i",video,"-frames:v","1",out],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if os.path.exists(out):
            shots.append(out)
    return shots
