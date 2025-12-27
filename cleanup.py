import os
import time
import shutil
import asyncio
from config import DOWNLOAD_DIR, FILE_TTL_HOURS

async def cleanup_loop():
    while True:
        try:
            print("🧹 Checking for old files to clean...")
            now = time.time()
            ttl_seconds = FILE_TTL_HOURS * 3600

            if os.path.exists(DOWNLOAD_DIR):
                for filename in os.listdir(DOWNLOAD_DIR):
                    file_path = os.path.join(DOWNLOAD_DIR, filename)
                    
                    # Check if it's a file or directory
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        file_age = now - os.path.getmtime(file_path)
                        if file_age > ttl_seconds:
                            try:
                                os.remove(file_path)
                                print(f"🗑️ Deleted old file: {filename}")
                            except Exception as e:
                                print(f"❌ Failed to delete {filename}: {e}")
                    
                    elif os.path.isdir(file_path):
                        # For directories (unzipped content), check folder age
                        dir_age = now - os.path.getmtime(file_path)
                        if dir_age > ttl_seconds:
                            try:
                                shutil.rmtree(file_path)
                                print(f"🗑️ Deleted old folder: {filename}")
                            except Exception as e:
                                print(f"❌ Failed to delete folder {filename}: {e}")

        except Exception as e:
            print(f"⚠️ Cleanup Error: {e}")
        
        # Wait 1 hour before checking again
        await asyncio.sleep(3600)