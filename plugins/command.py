import re, random, shutil
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import handle_job, cancel_active_job, has_active_job, analyze_youtube

OWNER_ID = 519459195
USER_PREFS = {}

def prefs(uid):
    return USER_PREFS.setdefault(uid, {
        "streamable": True,
        "screenshots": True,
        "thumbnail": None
    })

def register_handlers(bot):

    @bot.on_message(filters.command("start"))
    async def start(_, m):
        if m.from_user.id != OWNER_ID:
            await m.reply_text(
                "🚫 Private Bot\n\n🆔 Your ID: `{}`".format(m.from_user.id),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/poocha")]]
                )
            )
            return

        await m.reply_text(
            "✅ AnyDL Ready",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Disk", callback_data="disk"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("📸 Toggle Screenshots", callback_data="shots"),
                    InlineKeyboardButton("🎞 Toggle Streamable", callback_data="stream")
                ],
                [
                    InlineKeyboardButton("🆔 My ID", callback_data="myid"),
                    InlineKeyboardButton("🔄 Reboot", callback_data="reboot")
                ]
            ])
        )

    @bot.on_message(filters.private & filters.text)
    async def detect(_, m):
        if m.from_user.id != OWNER_ID or has_active_job():
            return

        if "youtube.com" in m.text or "youtu.be" in m.text:
            formats = analyze_youtube(m.text)
            await m.reply(
                "Select quality:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{f['label']} – {f['size']}",
                     callback_data=f"yt|{m.text}|{f['id']}")] for f in formats
                ])
            )

    @bot.on_callback_query(filters.regex("^yt\\|"))
    async def yt_select(_, q):
        _, url, fmt = q.data.split("|")
        await handle_job(q.message, "youtube", url, fmt, prefs(q.from_user.id))
