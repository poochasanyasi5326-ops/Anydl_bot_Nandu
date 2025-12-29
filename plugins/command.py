from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import (
    run, busy, cancel, yt_formats, rd_supported
)
from helper_funcs.ui import close_kb
import shutil, os

OWNER = 519459195
STATE = {}
WAIT = {}
RENAME = {}
CONFIRM = {}

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
        [InlineKeyboardButton("✅ Use Default", callback_data="r:def"),
         InlineKeyboardButton("✏️ Rename", callback_data="r:custom")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

def register(bot):

    @bot.on_message(filters.command("start"))
    async def start(_, m):
        if m.from_user.id != OWNER:
            await m.reply(
                f"🚫 Private bot\n🆔 `{m.from_user.id}`",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Contact Owner", url="https://t.me/poocha")]]
                )
            )
            return
        await m.reply("AnyDL Ready", reply_markup=dashboard())

    @bot.on_callback_query(filters.regex("^help$"))
    async def help(_, q):
        await q.message.edit(
            "📥 **Help**\n\n"
            "• Send or forward files\n"
            "• Paste links (YouTube / magnet / direct)\n"
            "• Choose quality → Rename → Download\n"
            "• Cancel anytime",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Close", callback_data="close")]]
            )
        )

    @bot.on_callback_query(filters.regex("^thumb$"))
    async def thumb(_, q):
        await q.message.edit(
            "🖼 **Thumbnail**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 View", callback_data="t:view"),
                 InlineKeyboardButton("➕ Set", callback_data="t:set")],
                [InlineKeyboardButton("❌ Clear", callback_data="t:clear")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    @bot.on_callback_query(filters.regex("^t:view$"))
    async def tview(_, q):
        th = prefs(q.from_user.id)["thumb"]
        if th:
            await q.message.reply_photo(th)
        else:
            await q.answer("No thumbnail set", show_alert=True)

    @bot.on_callback_query(filters.regex("^t:set$"))
    async def tset(_, q):
        WAIT[q.from_user.id] = "thumb"
        await q.message.edit("Send an image to set as thumbnail")

    @bot.on_callback_query(filters.regex("^t:clear$"))
    async def tclear(_, q):
        prefs(q.from_user.id)["thumb"] = None
        await q.answer("Thumbnail cleared")

    @bot.on_callback_query(filters.regex("^close$"))
    async def close(_, q):
        WAIT.pop(q.from_user.id, None)
        RENAME.pop(q.from_user.id, None)
        CONFIRM.pop(q.from_user.id, None)
        await close_kb(q.message)

    @bot.on_callback_query(filters.regex("^stream$"))
    async def stream(_, q):
        prefs(q.from_user.id)["stream"] ^= True
        await q.answer(f"Stream: {'ON' if prefs(q.from_user.id)['stream'] else 'OFF'}")

    @bot.on_callback_query(filters.regex("^shots$"))
    async def shots(_, q):
        prefs(q.from_user.id)["shots"] ^= True
        await q.answer(f"Screenshots: {'ON' if prefs(q.from_user.id)['shots'] else 'OFF'}")

    @bot.on_callback_query(filters.regex("^disk$"))
    async def disk(_, q):
        # Using os.getcwd() is safer on cloud hosts like Koyeb
        t, u, f = shutil.disk_usage(os.getcwd())
        await q.answer(f"Free: {f//1e9}GB / Total: {t//1e9}GB", show_alert=True)

    @bot.on_callback_query(filters.regex("^reboot$"))
    async def reboot(_, q):
        await q.answer("Rebooting...")
        os._exit(0)

    @bot.on_message(filters.private & filters.photo)
    async def photo(_, m):
        if WAIT.get(m.from_user.id) == "thumb":
            prefs(m.from_user.id)["thumb"] = await m.download()
            WAIT.pop(m.from_user.id, None)
            await m.reply("✅ Thumbnail set")

    @bot.on_message(filters.private & filters.document)
    async def document_handler(_, m):
        if busy(): return
        RENAME[m.from_user.id] = ("file", m)
        await m.reply("Rename file?", reply_markup=rename_kb())

    @bot.on_message(filters.private & filters.text)
    async def text_handler(_, m):
        if m.from_user.id != OWNER or busy(): return

        # Handling Custom Rename Input
        if m.from_user.id in RENAME and RENAME[m.from_user.id][0] == "custom":
            # Extract the original data stored in rcustom
            _, data = RENAME.pop(m.from_user.id)
            kind, payload = data
            new_name = m.text.strip()
            
            if kind == "yt":
                # For YouTube, we still need the format which hasn't been picked yet
                # This part usually needs a more complex flow, but for now:
                await m.reply("Please select quality first, then rename.")
            else:
                mode_map = {"dir": "direct", "tor": "torrent", "file": "file"}
                await run(payload, mode_map.get(kind, kind), None, prefs(m.from_user.id), m, new_name)
            return

        link = m.text.strip()

        if "youtu" in link:
            btn = []
            formats = yt_formats(link)
            for t, f, l, s in formats:
                btn.append([InlineKeyboardButton(f"{l} – {s} MB", callback_data=f"yt:{f}")])
            btn.append([InlineKeyboardButton("❌ Close", callback_data="close")])
            RENAME[m.from_user.id] = ("yt", link)
            await m.reply("🎥 Select Quality", reply_markup=InlineKeyboardMarkup(btn))
            return

        if link.startswith("magnet:") or link.endswith(".torrent"):
            RENAME[m.from_user.id] = ("tor", link)
            await m.reply("Rename file?", reply_markup=rename_kb())
            return

        if link.startswith(("http://", "https://")):
            RENAME[m.from_user.id] = ("dir", link)
            await m.reply("Rename file?", reply_markup=rename_kb())

    @bot.on_callback_query(filters.regex("^yt:"))
    async def yt_callback(_, q):
        fmt = q.data.split(":")[1]
        kind, link = RENAME.get(q.from_user.id, (None, None))
        if not link:
            await q.answer("Session expired", show_alert=True)
            return
        RENAME[q.from_user.id] = (("youtube", fmt), link)
        await q.message.edit("Rename file?", reply_markup=rename_kb())

    @bot.on_callback_query(filters.regex("^r:def$"))
    async def rdef(_, q):
        if q.from_user.id not in RENAME:
            await q.answer("Expired")
            return
        
        kind, payload = RENAME.pop(q.from_user.id)
        name = "file.bin"
        if isinstance(payload, str):
            name = payload.split("/")[-1].split("?")[0] or "file.bin"

        if kind == "file":
            await payload.download() # payload is the message object
            await q.message.edit("Download started...")
        elif kind == "dir":
            await run(payload, "direct", None, prefs(q.from_user.id), q.message, name)
        elif kind == "tor":
            await run(payload, "torrent", None, prefs(q.from_user.id), q.message, name)
        elif isinstance(kind, tuple): # it's ('youtube', fmt)
            mode, fmt = kind
            await run(payload, mode, fmt, prefs(q.from_user.id), q.message, name)

    @bot.on_callback_query(filters.regex("^r:custom$"))
    async def rcustom(_, q):
        if q.from_user.id not in RENAME:
            await q.answer("Expired")
            return
        data = RENAME[q.from_user.id]
        RENAME[q.from_user.id] = ("custom", data)
        await q.message.edit("✍️ Send the new filename now.")

    @bot.on_callback_query(filters.regex("^cancel:"))
    async def cancel_callback(_, q):
        cancel()
        await q.message.edit("❌ Cancelled")
