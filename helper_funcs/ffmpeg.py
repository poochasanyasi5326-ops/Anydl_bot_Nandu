import subprocess
import os

def is_streamable(ext: str) -> bool:
    return ext.lower() in [".mp4", ".mkv", ".webm"]

def generate_screenshots(video_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    timestamps = ["00:00:03", "00:00:08", "00:00:15"]
    shots = []

    for i, ts in enumerate(timestamps, 1):
        out = os.path.join(output_dir, f"screenshot_{i}.jpg")
        cmd = [
            "ffmpeg", "-y",
            "-ss", ts,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "4",
            out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out):
            shots.append(out)

    return shots
