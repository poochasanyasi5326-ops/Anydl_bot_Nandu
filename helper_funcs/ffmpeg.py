import os
import asyncio
import logging

async def take_screen_shot(video_file, output_directory, ttl):
    # Generates a thumbnail at the 10-second mark
    out_file_path = os.path.join(output_directory, f"{os.path.basename(video_file)}.jpg")
    command = [
        "ffmpeg", "-ss", str(ttl),
        "-i", video_file,
        "-vframes", "1",
        out_file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if os.path.lexists(out_file_path):
        return out_file_path
    return None

async def get_metadata(video_file):
    # Extracts width, height, and duration for the Telegram player
    command = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_file
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    data = stdout.decode().split()
    if len(data) >= 3:
        return int(data[0]), int(data[1]), int(float(data[2]))
    return 0, 0, 0
