import subprocess
import os
import uuid
import json

def is_streamable(path):
    """
    Checks if the file is a valid video/audio stream using ffprobe.
    This is more reliable than checking extensions.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
            "-of", "json", path
        ]
        res = subprocess.check_output(cmd).decode('utf-8')
        data = json.loads(res)
        # Check if any stream is 'video'
        return any(s.get("codec_type") == "video" for s in data.get("streams", []))
    except:
        # Fallback to extension if ffprobe fails
        return os.path.splitext(path)[1].lower() in [".mp4", ".mkv", ".webm", ".mov"]

def screenshots(video):
    """
    Generates 3 screenshots at fast-seek speeds.
    """
    shots = []
    # Timestamps to capture
    times = ["00:00:05", "00:05:00", "00:15:00"]
    
    for t in times:
        out = f"/tmp/{uuid.uuid4().hex}.jpg"
        # CRITICAL: -ss BEFORE -i for lightning-fast seeking
        cmd = [
            "ffmpeg", "-y", 
            "-ss", t, 
            "-i", video, 
            "-frames:v", "1", 
            "-q:v", "2", # High quality (2-5 is good)
            out
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(out):
            shots.append(out)
            
    return shots
