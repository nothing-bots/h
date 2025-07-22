from pyrogram import Client, filters
from pyrogram.types import Message
import datetime

from DeadlineTech import app
from DeadlineTech.misc import SUDOERS
import config
from DeadlineTech.platforms.Youtube import (
    ReqGetStream,
    SuccessGetStream,
    FailedGetStream,
    TimeOutStream,
    ReqGetVideoStream,
    SuccessGetVideoStream,
    FailedGetVideoStream,
    TimeOutVideoStream,
)


def get_stats_message_html():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = f"📊 <b>Download Stats Summary</b>\n"
    msg += f"<i>As of {now}</i>\n\n"

    msg += "📺 <b>Video</b>\n"
    msg += f"  ├─ Requested: <code>{config.video_requests}</code>\n"
    msg += f"  ├─ Success  : <code>{config.video_success}</code>\n"
    msg += f"  └─ Failed   : <code>{config.video_failed}</code>\n\n"

    msg += "🔊 <b>Audio</b>\n"
    msg += f"  ├─ Requested: <code>{config.audio_requests}</code>\n"
    msg += f"  ├─ Success  : <code>{config.audio_success}</code>\n"
    msg += f"  └─ Failed   : <code>{config.audio_failed}</code>\n\n"

    msg += "🎥 <b>Stream Stats</b>\n"
    msg += f"  ├─ Requested: <code>{ReqGetStream}</code>\n"
    msg += f"  ├─ Success  : <code>{SuccessGetStream}</code>\n"
    msg += f"  ├─ Failed   : <code>{FailedGetStream}</code>\n"
    msg += f"  └─ Timeout  : <code>{TimeOutStream}</code>\n\n"

    msg += "🔗 <b>Video URL Stream Stats</b>\n"
    msg += f"  ├─ Requested: <code>{ReqGetVideoStream}</code>\n"
    msg += f"  ├─ Success  : <code>{SuccessGetVideoStream}</code>\n"
    msg += f"  ├─ Failed   : <code>{FailedGetVideoStream}</code>\n"
    msg += f"  └─ Timeout  : <code>{TimeOutVideoStream}</code>\n"

    return msg


@app.on_message(filters.command("yt") & SUDOERS)
async def stats_handler(client: Client, message: Message):
    html = get_stats_message_html()
    await message.reply_text(html)
