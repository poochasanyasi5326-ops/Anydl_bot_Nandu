import os, shutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import run, busy, yt_formats, cancel
from helper_funcs.ui import close_kb

OWNER = 519459195 # <--- CHANGE THIS IF NEEDED
STATE = {} # Stores Prefs (Stream, Shots, Thumb)
RENAME = {} # Stores Pending Jobs

def prefs(uid):
    return STATE.setdefault(uid, {"stream": True, "shots": True, "thumb": None})

def dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Help", callback_data="help"), InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🎞 Stream", callback_data="stream"), InlineKeyboardButton("📸 Screens", callback_data="shots")],
        [InlineKeyboardButton("📊 Disk", callback_data="disk"), InlineKeyboardButton("🔄 Reboot", callback_data="reboot")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(bot, m):
    if m.from_user.id != OWNER:
        btn = [[InlineKeyboardButton("Contact Owner", url="https://t.me/poocha")]]
        return await m.reply(f"🚫 **Unauthorized Access**\nYour ID: `{m.from_user.id}`", reply_markup=InlineKeyboardMarkup(btn))
    await m.reply("🚀 **AnyDL Ready**\nChoose an option or send a link.", reply_markup=dashboard())

# --- THUMBNAIL MANAGEMENT ---
@Client.on_callback_query(filters.regex("^thumb$"))
async def thumb_menu(_, q):
    btn = [[InlineKeyboardButton("👁 View", callback_data="t:view"), InlineKeyboardButton("➕ Set", callback_data="t:set")],
           [InlineKeyboardButton("❌ Clear", callback_data="t:clear")], [InlineKeyboardButton("⬅️ Back", callback_data="back")]]
    await q.message.edit("🖼 **Thumbnail Settings**", reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex("^t:(view|clear)$"))
async def thumb_actions(bot, q):
    p = prefs(q.from_user.id)
    if "view" in q.data:
        if p["thumb"]: await q.message.reply_photo(p["thumb"], caption="Current Thumbnail")
        else: await q.answer("No thumbnail set!", show_alert=True)
    else:
        p["thumb"] = None
        await q.answer("Thumbnail cleared ✅")

@Client.on_callback_query(filters.regex("^t:set$"))
async def tset_mode(_, q):
    STATE[q.from_user.id]["wait"] = "thumb"
    await q.message.edit("📸 Send the image you want to use as a thumbnail.")

@Client.on_message(filters.private & filters.photo)
async def save_thumb(_, m):
    if STATE.get(m.from_user.id, {}).get("wait") == "thumb":
        prefs(m.from_user.id)["thumb"] = await m.download()
        STATE[m.from_user.id]["wait"] = None
        await m.reply("✅ **Thumbnail Saved & Remembered**")

# --- SMART RENAME & LINK HANDLING ---
@Client.on_message(filters.private & (filters.text | filters.document))
async def handle_input(bot, m):
    if m.from_user.id != OWNER or busy(): return

    # If user is in "custom rename" state
    if m.from_user.id in RENAME and RENAME[m.from_user.id][0] == "custom":
        _, data = RENAME.pop(m.from_user.id)
        kind, payload, fmt = data # Extract saved info
        await run(payload, kind, fmt, prefs(m.from_user.id), m, m.text.strip())
        return

    content = m.text or m.document.file_id
    if m.document:
        RENAME[m.from_user.id] = ("file", m, None)
        await m.reply("📄 **File Detected**\nRename it?", reply_markup=rename_kb())
    elif "youtu" in content:
        formats = yt_formats(content)
        btn = [[InlineKeyboardButton(f"🎬 {l} - {s}MB", callback_data=f"yt:{f}")] for t,f,l,s in formats]
        btn.append([InlineKeyboardButton("❌ Cancel", callback_data="close")])
        RENAME[m.from_user.id] = ("youtube", content, None)
        await m.reply("🎥 **Select Quality**", reply_markup=InlineKeyboardMarkup(btn))
    elif content.startswith(("http", "magnet:")):
        mode = "torrent" if "magnet:" in content or ".torrent" in content else "direct"
        RENAME[m.from_user.id] = (mode, content, None)
        await m.reply(f"🔗 **{mode.title()} Link Detected**\nRename it?", reply_markup=rename_kb())

@Client.on_callback_query(filters.regex("^yt:"))
async def yt_choice(_, q):
    fmt = q.data.split(":")[1]
    kind, link, _ = RENAME[q.from_user.id]
    RENAME[q.from_user.id] = (kind, link, fmt)
    await q.message.edit("✍️ **Rename the video?**", reply_markup=rename_kb())

@Client.on_callback_query(filters.regex("^r:(def|custom)$"))
async def rename_choice(_, q):
    if "def" in q.data:
        kind, payload, fmt = RENAME.pop(q.from_user.id)
        name = payload.split("/")[-1] if isinstance(payload, str) else "file"
        await run(payload, kind, fmt, prefs(q.from_user.id), q.message, name)
    else:
        # Switch state to wait for text input
        data = RENAME[q.from_user.id] # (kind, payload, fmt)
        RENAME[q.from_user.id] = ("custom", data)
        await q.message.edit("📝 **Send the new filename now:**")

# --- UTILS (REBOOT, DISK, CANCEL) ---
@Client.on_callback_query(filters.regex("^reboot$"))
async def reboot_bot(_, q):
    await q.answer("Rebooting instance...", show_alert=True)
    os._exit(0)

@Client.on_callback_query(filters.regex("^cancel$"))
async def cancel_job(_, q):
    cancel()
    await q.message.edit("❌ **Job Cancelled**")

@Client.on_callback_query(filters.regex("^close$"))
async def _close(_, q):
    await q.message.delete()
