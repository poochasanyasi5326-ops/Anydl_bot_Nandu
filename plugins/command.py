from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup,InlineKeyboardButton
import shutil, os
from plugins.task_manager import yt_formats, run, busy, cancel

OWNER=519459195
STATE={}

def pref(uid):
    return STATE.setdefault(uid,{
        "stream":True,
        "shots":True,
        "thumb":None
    })

def register(bot):

    @bot.on_message(filters.command("start"))
    async def start(_,m):
        if m.from_user.id!=OWNER:
            await m.reply(
                f"🚫 Private bot\n🆔 `{m.from_user.id}`",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Contact Owner",url="https://t.me/poocha")]]
                )
            )
            return
        await m.reply(
            "AnyDL Ready",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Toggle Stream",callback_data="s"),
                 InlineKeyboardButton("Toggle Shots",callback_data="p")],
                [InlineKeyboardButton("Disk",callback_data="d"),
                 InlineKeyboardButton("Reboot",callback_data="r")]
            ])
        )

    @bot.on_callback_query(filters.regex("^s$"))
    async def s(_,q):
        pref(q.from_user.id)["stream"]^=True
        await q.answer("Toggled")

    @bot.on_callback_query(filters.regex("^p$"))
    async def p(_,q):
        pref(q.from_user.id)["shots"]^=True
        await q.answer("Toggled")

    @bot.on_callback_query(filters.regex("^d$"))
    async def d(_,q):
        t,u,f=shutil.disk_usage("/")
        await q.message.edit(f"Disk: {u//1e9}GB used")

    @bot.on_callback_query(filters.regex("^r$"))
    async def r(_,q):
        os._exit(0)

    @bot.on_message(filters.private & filters.text)
    async def link(_,m):
        if m.from_user.id!=OWNER or busy(): return
        p=pref(m.from_user.id)

        if "youtu" in m.text:
            btn=[[InlineKeyboardButton(f"{l} {s}MB",callback_data=f"yt|{m.text}|{i}")]
                 for i,l,s in yt_formats(m.text)]
            await m.reply("Select format",reply_markup=InlineKeyboardMarkup(btn))
        else:
            await run(m.text,"direct",None,p,m)

    @bot.on_callback_query(filters.regex("^yt\\|"))
    async def yt(_,q):
        _,url,fid=q.data.split("|")
        await run(url,"youtube",fid,pref(q.from_user.id),q.message)
