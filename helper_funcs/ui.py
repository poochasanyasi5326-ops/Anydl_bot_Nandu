import time
import math
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, MessageNotModified

# Dictionary to track last update time to avoid flooding
_LAST = {}

def human(x):
    """Converts bytes to human-readable format."""
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if x < 1024:
            return f"{x:.2f} {u}"
        x /= 1024

async def progress(msg, jid, phase, cur, total):
    """
    Updates the Telegram message with a progress bar, 
    speed, and estimated time remaining.
    """
    now = time.time()
    
    # Initialize tracking for the first time
    if jid not in _LAST:
        _LAST[jid] = {"time": now, "start": now, "last_cur": cur}
        return

    # Only update every 4 seconds to be safe from Telegram flood limits
    if now - _LAST[jid]["time"] < 4:
        return

    # Calculate Speed and ETA
    elapsed = now - _LAST[jid]["start"]
    # Instant speed (bytes per second)
    speed = (cur - _LAST[jid]["last_cur"]) / (now - _LAST[jid]["time"]) if total else 0
    
    # Calculate ETA
    remaining = total - cur
    eta = ""
    if speed > 0:
        eta_seconds = remaining / speed
        # Format seconds into mm:ss or hh:mm:ss
        eta = f" | ⏱ {time.strftime('%H:%M:%S', time.gmtime(eta_seconds))}"

    # Visual Progress Bar (10 blocks)
    pct = (cur / total) * 100 if total else 0
    filled = min(int(pct / 10), 10)
    bar = "▰" * filled + "▱" * (10 - filled)

    # Update state
    _LAST[jid]["time"] = now
    _LAST[jid]["last_cur"] = cur

    text = (
        f"⏳ **{phase.upper()}**\n\n"
        f"<code>{bar}</code> {pct:.1f}%\n"
        f"📦 **Size:** {human(cur)} / {human(total)}\n"
        f"🚀 **Speed:** {human(speed)}/s{eta}"
    )

    try:
        await msg.edit(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{jid}")]]
            )
        )
    except FloodWait as e:
        # If we hit a flood wait, stop updating for a bit
        _LAST[jid]["time"] = now + e.value
    except MessageNotModified:
        pass
    except Exception:
        pass

async def close_kb(msg):
    """Removes the reply markup (buttons) from a message."""
    try:
        await msg.edit_reply_markup(None)
    except:
        pass
