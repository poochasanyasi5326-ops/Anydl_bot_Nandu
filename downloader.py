import subprocess
import os

ARIA2_PROCESS = None


def start_download(magnet: str, download_dir: str):
    global ARIA2_PROCESS

    if ARIA2_PROCESS and ARIA2_PROCESS.poll() is None:
        return False, "Download already running"

    os.makedirs(download_dir, exist_ok=True)

    ARIA2_PROCESS = subprocess.Popen(
        [
            "aria2c",
            "--seed-time=0",
            "--summary-interval=5",
            "--dir",
            download_dir,
            magnet,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    return True, "Download started"


def stop_download():
    global ARIA2_PROCESS

    if ARIA2_PROCESS and ARIA2_PROCESS.poll() is None:
        ARIA2_PROCESS.terminate()
        ARIA2_PROCESS = None
        return True

    return False


def download_status():
    if not ARIA2_PROCESS:
        return "No active download"

    if ARIA2_PROCESS.poll() is not None:
        return "Download finished or stopped"

    return "Download in progress"
