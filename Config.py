import os
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "519459195"))

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set")
    sys.exit(1)
