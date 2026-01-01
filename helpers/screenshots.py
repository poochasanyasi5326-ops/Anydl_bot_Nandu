import subprocess
import os
from config import SCREENSHOT_COUNT

def generate_screenshots(video_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{SCREENSHOT_COUNT}",
        os.path.join(out_dir, "shot_%02d.jpg")
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [os.path.join(out_dir, f) for f in os.listdir(out_dir)]
