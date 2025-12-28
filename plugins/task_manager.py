import os
import yt_dlp
from pyrogram import Client, filters

async def get_yt_info(url):
    """Safely extracts info and prevents NoneType errors"""
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'format': 'best', 
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We add a check to ensure info is not None
            info = ydl.extract_info(url, download=False)
            if not info:
                return "Unknown Title", 0, 0
            
            # Use .get() with defaults to avoid NoneType attribute errors
            title = info.get('title') or "Untitled Video"
            v_size = info.get('filesize_approx') or info.get('filesize') or 0
            
            formats = info.get('formats', [])
            a_size = sum(f.get('filesize', 0) for f in formats if f.get('vcodec') == 'none')
            
            return str(title), v_size, a_size
    except Exception as e:
        print(f"Extraction Error: {e}")
        return "Unreadable Link", 0, 0

# (Keep your existing download and upload logic below this function)
