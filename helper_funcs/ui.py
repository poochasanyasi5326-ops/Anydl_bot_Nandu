import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

_LAST = {}

def human(x):
    for u in ["B","KB","MB","GB","TB"]:
        if x < 1024: return f"{x:.2f} {u}"
        x /= 1024

async def progress(msg, jid, phase, cur, total):
    now = time.time()
    if jid not in _LAST: _LAST[jid] = now
    if now - _LAST[jid] < 4: return
    _LAST[jid] = now

    pct = (cur/total)*100 if total else 0
    bar = "▰" * int(pct/10) + "▱" * (10-int(pct/10))
    
    # Speed/ETA logic simplified for stability
    text = f"⏳ **{phase}**\n`{bar}` {pct:.1f}%\n📦 {human(cur)} / {human(total)}"
    try:
        await msg.edit(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]))
    except: pass

async def close_kb(msg):
    try: await msg.edit_reply_markup(None)
    except: pass
