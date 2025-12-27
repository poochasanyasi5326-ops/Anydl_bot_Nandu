import os
import asyncio
import time

async def get_metadata(video_path):
    # Extracts duration, width, height
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        output = stdout.decode().split()
        
        if len(output) >= 3:
            width = int(output[0])
            height = int(output[1])
            duration = int(float(output[2]))
            return width, height, duration
    except:
        return 0, 0, 0
    return 0, 0, 0

async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg", "-ss", str(ttl), "-i", video_file,
        "-vframes", "1", out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None

# Generate 4 screenshots for the "Screenshots" post
async def generate_screenshots(video_file, output_dir, duration):
    screenshots = []
    if duration > 10:
        # Take shots at 10%, 30%, 50%, 70%
        intervals = [duration * 0.1, duration * 0.3, duration * 0.5, duration * 0.7]
        for ttl in intervals:
            ss = await take_screen_shot(video_file, output_dir, ttl)
            if ss: screenshots.append(ss)
    return screenshots
