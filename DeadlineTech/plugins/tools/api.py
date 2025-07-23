from pyrogram import Client, filters
from pyrogram.types import Message
from DeadlineTech import app
from DeadlineTech.misc import SUDOERS
from DeadlineTech.platforms.Youtube import get_stream_stats
import config
import datetime

# 📥 Pyrogram command handler
@app.on_message(filters.command("yt") & SUDOERS)
async def yt_stats_handler(client: Client, message: Message):
    html_summary = get_stats_message_html()
    stream_summary = get_stream_stats()

    await message.reply_text(
        "{stream_summary}",
        disable_web_page_preview=True
    )
