from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.task_manager import run, busy, cancel
from helper_funcs.ui import close_keyboard
import shutil, os

OWNER = 519459195
STATE = {}
WAIT = {}

def prefs(uid):
    return STATE.setdefault(uid, {
        "stream": True,
        "shots": True,
        "thumb": None
    })

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Help", callback_data="help"),
         InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🎞 Stream", callback_data="stream"),
         InlineKeyboardButton("📸 Screens", callback_data="shots")],
        [InlineKeyboardButton("📊 Disk", callback_data="disk"),
         InlineKeyboardButton("🔄 Reboot", callback_data="reboot")]
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
        await m.reply("AnyDL Ready", reply_markup=main_kb())

    @bot.on_callback_query(filters.regex("^help$"))
    async def help(_, q):
        await q.message.edit(
            "📥 **How to use AnyDL**\n\n"
            "• Send or forward a file\n"
            "• Send links (YouTube / direct)\n"
            "• Rename or use default\n"
            "• Cancel anytime",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Close", callback_data="close")]]
            )
        )

    @bot.on_callback_query(filters.regex("^thumb$"))
    async def thumb(_, q):
        await q.message.edit(
            "🖼 Thumbnail",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 View", callback_data="t_view"),
                 InlineKeyboardButton("➕ Set", callback_data="t_set")],
                [InlineKeyboardButton("❌ Clear", callback_data="t_clear")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    @bot.on_callback_query(filters.regex("^close$"))
    async def close(_, q):
        await close_keyboard(q.message)

    @bot.on_callback_query(filters.regex("^stream$"))
    async def stream(_, q):
        prefs(q.from_user.id)["stream"] ^= True
        await q.answer("Toggled")

    @bot.on_callback_query(filters.regex("^shots$"))
    async def shots(_, q):
        prefs(q.from_user.id)["shots"] ^= True
        await q.answer("Toggled")

    @bot.on_callback_query(filters.regex("^disk$"))
    async def disk(_, q):
        t,u,f = shutil.disk_usage("/")
        await q.answer(f"Used: {u//1e9}GB", show_alert=True)

    @bot.on_callback_query(filters.regex("^reboot$"))
    async def reboot(_, q):
        os._exit(0)

    @bot.on_message(filters.private & filters.document)
    async def forwarded(_, m):
        WAIT[m.from_user.id] = m
        await m.reply(
            "Rename file?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Default", callback_data="r_def"),
                 InlineKeyboardButton("✏️ Rename", callback_data="r_custom")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    @bot.on_callback_query(filters.regex("^r_def$"))
    async def rdef(_, q):
        m = WAIT.pop(q.from_user.id)
        await m.download(file_name=m.document.file_name)

    @bot.on_callback_query(filters.regex("^cancel:"))
    async def c(_, q):
        cancel()
        await q.message.edit("❌ Cancelled")
