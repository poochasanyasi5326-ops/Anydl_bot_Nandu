import os
from pathlib import Path

OWNER_IDS = {519459195}

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB
FILE_TTL_HOURS = 6

TORRENT_STATE = {
    "active": False,
    "process": None,
    "downloaded_bytes": 0,
    "start_time": None,
    "path": None
}
