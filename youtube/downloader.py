import yt_dlp
import os
from config import DOWNLOAD_DIR

def download(url, format_id):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ydl_opts = {
        "format": format_id,
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        return ydl.prepare_filename(info)
