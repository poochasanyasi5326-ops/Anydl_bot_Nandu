import time
import math
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Requirement 6: Progress Tracker Logic
def humanbytes(size):
    if not size: return "0 B"
    for unit in ['','Ki','Mi','Gi','Ti']:
        if size < 1024.0: return f"{size:.2f} {unit}B"
        size /= 1024.0

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {seconds}s"

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        eta = time_formatter(round((total - current) / speed) * 1000) if speed > 0 else "0s"
        
        progress = "[{0}{1}] {2}%".format(
            ''.join(["●" for i in range(math.floor(percentage / 10))]),
            ''.join(["○" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2)
        )
        
        tmp = f"**{ud_type}**\n{progress}\n📂 {humanbytes(current)} / {humanbytes(total)}\n🚀 Speed: {humanbytes(speed)}/s\n⏳ ETA: {eta}"
        try:
            await message.edit(
                text=tmp, 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )
        except:
            pass
