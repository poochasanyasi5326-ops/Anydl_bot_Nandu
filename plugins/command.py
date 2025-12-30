import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import run, busy, yt_formats
from helper_funcs.ui import close_kb

# --- CONFIG ---
OWNER = 519459195 
OWNER_ONLY = False # Set to True once you confirm the bot responds

STATE = {}
RENAME = {}

def prefs(uid):
    return STATE.setdefault(uid, {"stream": True, "shots": True, "thumb": None})

def dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Help", callback_data="help"),
         InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🎞 Stream", callback_data="stream"),
         InlineKeyboardButton("📸 Screens", callback_data="shots")],
        [InlineKeyboardButton("📊 Disk", callback_data="disk"),
         InlineKeyboardButton("🔄 Reboot", callback_data="reboot")]
    ])

def rename_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Default", callback_data="r:def"),
         InlineKeyboardButton("✏️ Rename", callback_data="r:custom")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(bot, m):
    if OWNER_ONLY and m.from_user.id != OWNER:
        return await m.reply(f"🚫 Private Bot\nYour ID: `{m.from_user.id}`")
    await m.reply("🚀 **AnyDL Ready**\nSend me a link to begin.", reply_markup=dashboard())

@Client.on_message(filters.private & filters.text)
async def text_handler(bot, m):
    if OWNER_ONLY and m.from_user.id != OWNER: return
    if busy(): return

    # Custom Rename State
    if m.from_user.id in RENAME and RENAME[m.from_user.id][0] == "custom":
        _, data = RENAME.pop(m.from_user.id)
        kind, payload = data
        mode_map = {"dir": "direct", "tor": "torrent", "file": "file"}
        await run(payload, mode_map.get(kind, kind), None, prefs(m.from_user.id), m, m.text.strip())
        return

    link = m.text.strip()
    if "youtu" in link:
        formats = yt_formats(link)
        btn = [[InlineKeyboardButton(f"{l} - {s}MB", callback_data=f"yt:{f}")] for t, f, l, s in formats]
        RENAME[m.from_user.id] = ("yt", link)
        await m.reply("🎥 **Select Quality:**", reply_markup=InlineKeyboardMarkup(btn))
    elif link.startswith(("http", "magnet:")):
        RENAME[m.from_user.id] = ("dir" if "http" in link else "tor", link)
        await m.reply("📂 **Link detected.** Rename file?", reply_markup=rename_kb())

@Client.on_callback_query(filters.regex("^disk$"))
async def disk_chk(_, q):
    t, u, f = shutil.disk_usage(os.getcwd())
    await q.answer(f"Free Space: {f//1e9}GB", show_alert=True)

@Client.on_callback_query(filters.regex("^close$"))
async def _close(_, q):
    await q.message.delete()
