import os

# --- CONFIGURATION ---
API_ID = 6788995
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# 1. YOUR ID (Hardcoded)
OWNER_IDS = {519459195}

# 2. File Settings (4GB Limit)
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE_GB = 4
FILE_TTL_HOURS = 24

# 3. Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")