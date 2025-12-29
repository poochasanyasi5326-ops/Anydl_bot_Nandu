import subprocess
import os

def is_streamable(ext: str) -> bool:
    return ext.lower() in [".mp4", ".mkv", ".webm"]


def generate_screenshots(video_path: str, output_dir: str):
    """
    Generates 3 JPG screenshots from a video.
    Returns list of screenshot paths.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError("Video file not found")

    os.makedirs(output_dir, exist_ok=True)

    timestamps = ["00:00:03", "00:00:08", "00:00:15"]
    screenshots = []

    for i, ts in enumerate(timestamps, start=1):
        out = os.path.join(output_dir, f"screenshot_{i}.jpg")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", ts,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "4",        # good quality, small size
            out
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(out):
            screenshots.append(out)

    return screenshots
