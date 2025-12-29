import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

_LAST = {}

def human(x):
    for u in ["B","KB","MB","GB","TB"]:
        if x < 1024:
            return f"{x:.2f}{u}"
        x /= 1024

async def progress(msg, jid, phase, cur, total):
    if time.time() - _LAST.get(jid, 0) < 5:
        return
    _LAST[jid] = time.time()

    pct = (cur / total) * 100 if total else 0
    bar = "█" * int(pct/10) + "░" * (10-int(pct/10))

    await msg.edit(
        f"⏳ **{phase.upper()}**\n\n"
        f"[{bar}] {pct:.1f}%\n"
        f"{human(cur)} / {human(total)}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{jid}")]]
        )
    )

async def close_keyboard(msg):
    await msg.edit_reply_markup(None)
