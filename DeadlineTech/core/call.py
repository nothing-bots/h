import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, LowQualityAudio, MediumQualityVideo, LowQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from DeadlineTech import LOGGER, YouTube, app
from DeadlineTech.misc import db
from DeadlineTech.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from DeadlineTech.utils.exceptions import AssistantErr
from DeadlineTech.utils.formatters import check_duration, seconds_to_min, speed_converter
from DeadlineTech.utils.inline.play import stream_markup
from DeadlineTech.utils.stream.autoclear import auto_clean
from DeadlineTech.utils.thumbnails import get_thumb
from DeadlineTech.utils.thumbnails import get_thumb as gen_thumb
from strings import get_string


autoend = {}
counter = {}

def is_url(link: str) -> bool:
    return link.startswith("http://") or link.startswith("https://")


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="DeadlineAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=240,
        )
        self.userbot2 = Client(
            name="DeadlineAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(
            self.userbot2,
            cache_duration=240,
        )
        self.userbot3 = Client(
            name="DeadlineAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(
            self.userbot3,
            cache_duration=1,
        )
        self.userbot4 = Client(
            name="DeadlineAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(
            self.userbot4,
            cache_duration=1,
        )
        self.userbot5 = Client(
            name="DeadlineAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(
            self.userbot5,
            cache_duration=100,
        )

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            if config.STRING1:
                await self.one.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING2:
                await self.two.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING3:
                await self.three.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING4:
                await self.four.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING5:
                await self.five.leave_group_call(chat_id)
        except:
            pass
        try:
            await _clear_(chat_id)
        except:
            pass

    
    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.join_group_call(
            config.LOG_GROUP_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOG_GROUP_ID)

    async def stream_test(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.join_group_call(
            config.LOG_GROUP_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        print(f"[JOIN_CALL] Starting join_call for chat_id: {chat_id}")
        
        assistant = await group_assistant(self, chat_id)
        print(f"[JOIN_CALL] Assistant acquired")
        
        language = await get_lang(chat_id)
        _ = get_string(language)

        try:
            if video:
                print("[JOIN_CALL] Setting up AudioVideoPiped stream")
                stream = AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
            else:
                print("[JOIN_CALL] Setting up AudioPiped stream")
                stream = AudioPiped(link, audio_parameters=HighQualityAudio())

            print("[JOIN_CALL] Attempting to join group call with pulse_stream")
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            print("[JOIN_CALL] NoActiveGroupCall error raised")
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            print("[JOIN_CALL] AlreadyJoinedError raised")
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            print("[JOIN_CALL] TelegramServerError raised")
            raise AssistantErr(_["call_10"])
        except Exception as e:
            print(f"[JOIN_CALL] Unexpected error: {e}")
            raise

        print("[JOIN_CALL] Joined call successfully")

        await add_active_chat(chat_id)
        await music_on(chat_id)

        if video:
            print("[JOIN_CALL] Adding to active video chat")
            await add_active_video_chat(chat_id)

        if await is_autoend():
            print("[JOIN_CALL] Setting up auto-end")
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

        print("[JOIN_CALL] Finished join_call function")


    async def change_stream(self, client, chat_id):
        print("[change_stream] Started")
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        print(f"[change_stream] loop = {loop}")

        try:
            if loop == 0:
                popped = check.pop(0)
                print("[change_stream] Loop is 0, popped first element")
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
                print(f"[change_stream] Decreased loop to {loop}")
            await auto_clean(popped)
            print("[change_stream] Auto clean done")
            if not check:
                print("[change_stream] Queue empty, clearing...")
                await _clear_(chat_id)    
                return await client.leave_group_call(chat_id)
        except Exception as e:
            print(f"[change_stream] Exception in try block: {e}")
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except Exception as e2:
                print(f"[change_stream] Exception in except block: {e2}")
                return

        else:
            queued = check[0].get("file")
            if not queued:
                print(f"[change_stream] ❌ Queued file is None for chat_id {chat_id}")
                # If no more in queue
                if not db.get(chat_id):
                    await _clear_(chat_id)
                    return await client.leave_group_call(chat_id)
                else:
                    # Still songs left → play next
                    return await self.change_stream(client, chat_id)

            queued = check[0]["file"]
            print(f"[change_stream] Queued file: {queued}")
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            print(f"[change_stream] Stream type: {'video' if video else 'audio'}")

            if "live_" in queued:
                print("[change_stream] Handling live stream")
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    xop = "[change_stream] live link not found"
                    print(xop)
                    return await app.send_message(original_chat_id, text=_["call_6"])
                stream = AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                ) if video else AudioPiped(link, audio_parameters=HighQualityAudio())

                try:
                    await client.change_stream(chat_id, stream)
                    print("[change_stream] Live stream changed successfully")
                except Exception as e:
                    xop = f"[change_stream] Error changing live stream: {e}\n\nData :- {check[0]}"
                    print(xop)
                    return await app.send_message(original_chat_id, text=_["call_6"])

                img = await gen_thumb(videoid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif "vid_" in queued:
                print("[change_stream] Handling YouTube download stream")
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=video,
                    )
                    print("[change_stream] YouTube download successful")
                except Exception as e:
                    xop=f"[change_stream] YouTube download failed: {e}\n\nData :- {check[0]}"
                    print(xop)
                    return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)

                stream = AudioVideoPiped(
                    file_path,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                ) if video else AudioPiped(file_path, audio_parameters=HighQualityAudio())

                try:
                    await client.change_stream(chat_id, stream)
                    print("[change_stream] YouTube stream changed successfully")

                except Exception as e:
                    print(f"[change_stream] YouTube stream change failed: {e}")
                    xop = f"[change_stream] ❌ YouTube stream change failed: {e}\n\nData: {check[0]}"
                    print(xop)

                    if not db.get(chat_id):
                        await _clear_(chat_id)
                        return await client.leave_group_call(chat_id)
                    else:
                        return await self.change_stream(client, chat_id)

            
                img = await gen_thumb(videoid)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

            elif "index_" in queued:
                print("[change_stream] Handling indexed file stream")
                stream = AudioVideoPiped(
                    videoid,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                ) if video else AudioPiped(videoid, audio_parameters=HighQualityAudio())

                try:
                    await client.change_stream(chat_id, stream)
                    print("[change_stream] Indexed stream changed successfully")
                except Exception as e:
                    xop = f"[change_stream] Indexed stream change failed: {e}\n\nData :- {check[0]}"
                    print(xop)
                    return await app.send_message(original_chat_id, text=_["call_6"])

                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                print("[change_stream] Handling telegram/soundcloud/custom stream")
                stream = AudioVideoPiped(
                    queued,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                ) if video else AudioPiped(queued, audio_parameters=HighQualityAudio())

                try:
                    await client.change_stream(chat_id, stream)
                    print("[change_stream] Custom stream changed successfully")
                except Exception as e:
                    xop = f"[change_stream] Custom stream change failed: {e}\n\n{check[0]}"
                    print(xop)
                    if not db.get(chat_id):
                        await _clear_(chat_id)
                        return await client.leave_group_call(chat_id)
                    else:
                        return await self.change_stream(client, chat_id)
                        
                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.TELEGRAM_AUDIO_URL if streamtype == "audio" else config.TELEGRAM_VIDEO_URL,
                        caption=_["stream_1"].format(config.SUPPORT_GROUP, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(config.SUPPORT_GROUP, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    img = await gen_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
        print("[change_stream] Finished")


    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        if config.STRING2:
            pings.append(await self.two.ping)
        if config.STRING3:
            pings.append(await self.three.ping)
        if config.STRING4:
            pings.append(await self.four.ping)
        if config.STRING5:
            pings.append(await self.five.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    async def decorators(self):
        @self.one.on_kicked()
        @self.two.on_kicked()
        @self.three.on_kicked()
        @self.four.on_kicked()
        @self.five.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.two.on_closed_voice_chat()
        @self.three.on_closed_voice_chat()
        @self.four.on_closed_voice_chat()
        @self.five.on_closed_voice_chat()
        @self.one.on_left()
        @self.two.on_left()
        @self.three.on_left()
        @self.four.on_left()
        @self.five.on_left()
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        @self.two.on_stream_end()
        @self.three.on_stream_end()
        @self.four.on_stream_end()
        @self.five.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)


Anony = Call()
