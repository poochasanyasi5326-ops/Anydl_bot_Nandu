import re, random, shutil, os, json
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from plugins.task_manager import (
    handle_job,
    cancel_active_job,
    has_active_job,
    analyze_youtube
)

OWNER_ID = 519459195

USER_PREFS = {
    # user_id: {
    #   "streamable": bool,
    #   "screenshots": bool,
    #   "thumbnail": path or None
    # }
}

UNAUTH_MSGS = [
    "🚫 Private bot. Access denied.",
    "⛔ You are not authorized.",
    "🔒 Restricted access."
]

def get_prefs(uid):
    return USER_PREFS.setdefault(uid, {
        "streamable": True,
        "screenshots": True,
        "thumbnail": None
    })

def register_handlers(bot):

    # ---------- START ----------
    @bot.on_message(filters.command("start"))
    async def start(_, m):
        if m.from_user.id != OWNER_ID:
            await m.reply_text(
                random.choice(UNAUTH_MSGS) + f"\n\n🆔 `{m.from_user.id}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")]
                ])
            )
            return

        await m.reply_text(
            "✅ **AnyDL Ready**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Disk", callback_data="disk"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("📸 Toggle Screenshots", callback_data="toggle_shots"),
                    InlineKeyboardButton("🎞 Toggle Streamable", callback_data="toggle_stream")
                ],
                [
                    InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_menu"),
                    InlineKeyboardButton("🔄 Reboot", callback_data="reboot")
                ],
                [
                    InlineKeyboardButton("🆔 My ID", callback_data="myid")
                ]
            ])
        )

    # ---------- HELP ----------
    @bot.on_callback_query(filters.regex("^help$"))
    async def help_cb(_, q):
        await q.message.edit_text(
            "🛠 **Commands & Usage**\n\n"
            "/start – show controls\n"
            "/setcustomthumbnail – set thumbnail\n\n"
            "Supported:\n"
            "• YouTube (video/audio)\n"
            "• Magnet / Torrent (Seedr)\n"
            "• Direct links\n\n"
            "Buttons:\n"
            "• Cancel anytime\n"
            "• Rename / Default\n"
            "• Streamable toggle\n"
            "• Screenshot toggle"
        )

    # ---------- TOGGLES ----------
    @bot.on_callback_query(filters.regex("^toggle_shots$"))
    async def toggle_shots(_, q):
        p = get_prefs(q.from_user.id)
        p["screenshots"] = not p["screenshots"]
        await q.answer(f"Screenshots {'ON' if p['screenshots'] else 'OFF'}", show_alert=True)

    @bot.on_callback_query(filters.regex("^toggle_stream$"))
    async def toggle_stream(_, q):
        p = get_prefs(q.from_user.id)
        p["streamable"] = not p["streamable"]
        await q.answer(f"Streamable {'ON' if p['streamable'] else 'OFF'}", show_alert=True)

    # ---------- THUMBNAIL ----------
    @bot.on_callback_query(filters.regex("^thumb_menu$"))
    async def thumb_menu(_, q):
        await q.message.edit_text(
            "🖼 **Thumbnail Options**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👁 View", callback_data="thumb_view"),
                    InlineKeyboardButton("❌ Clear", callback_data="thumb_clear")
                ]
            ])
        )

    @bot.on_message(filters.command("setcustomthumbnail"))
    async def set_thumb(_, m):
        await m.reply("Send an image.")

        @bot.on_message(filters.photo)
        async def save(_, p):
            path = f"/tmp/thumb_{p.from_user.id}.jpg"
            await p.download(path)
            get_prefs(p.from_user.id)["thumbnail"] = path
            await p.reply("✅ Thumbnail saved")

    # ---------- LINK DETECT ----------
    @bot.on_message(filters.private & filters.text)
    async def detect(_, m):
        if m.from_user.id != OWNER_ID:
            return

        if has_active_job():
            await m.reply("⏳ Job already running")
            return

        text = m.text.strip()

        if "youtube.com" in text or "youtu.be" in text:
            formats = analyze_youtube(text)
            buttons = []
            for f in formats:
                buttons.append([
                    InlineKeyboardButton(
                        f"{f['label']} – {f['size']}",
                        callback_data=f"yt|{text}|{f['id']}"
                    )
                ])
            buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_job")])
            await m.reply("Select quality:", reply_markup=InlineKeyboardMarkup(buttons))
