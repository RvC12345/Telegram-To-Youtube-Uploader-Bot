import os
import time
import string
import random
import logging
import asyncio
import datetime
import yt_dlp
import aiohttp
import math
import traceback
from typing import Tuple, Union

from pyrogram import StopTransmission
from pyrogram import filters as Filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from ..translations import Messages as tr
from ..helpers.downloader import Downloader
from ..helpers.uploader import Uploader
from ..config import Config
from ..utubebot import UtubeBot


log = logging.getLogger(__name__)

@UtubeBot.on_message(
    Filters.private & Filters.command("uploadurl") & Filters.user(Config.AUTH_USERS)
)
async def _upload_url(c: UtubeBot, m: Message):
    if not os.path.exists(Config.CRED_FILE):
        await m.reply_text(tr.NOT_AUTHENTICATED_MSG, True)
        return

    parts = m.text.split(" ", 2)
    if len(parts) < 2:
        return await m.reply_text("Usage: `/uploadurl <url> <optional title>`", True)

    url = parts[1]
    title = parts[2] if len(parts) > 2 else "Uploaded via URL"
    snt = await m.reply_text("Processing your request...", True)

    download_id = get_download_id(c.download_controller)
    c.download_controller[download_id] = True
    file_path = f"url_{int(time.time())}.mp4"
    start_time = time.time()

    try:
        if url.endswith(".mp4") or ".mp4?" in url:
            await download_direct_url(url, file_path, snt, c, download_id, start_time)
        else:
            await snt.edit_text("Using yt-dlp to extract and download...")
            ydl_opts = {
                'outtmpl': file_path,
                'format': 'best',
                'merge_output_format': 'mp4',
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await snt.edit_text("Downloaded successfully. Now uploading to YouTube...")

        upload = Uploader(file_path, title)
        status, link = await upload.start(progress, snt)
        await snt.edit_text(link if status else f"Upload Failed:\n{link}")

    except Exception as e:
        err = traceback.format_exc()
        await snt.edit_text(f"Error: {str(e)}\n\n{err[-1000:]}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        c.download_controller.pop(download_id, None)
        

@UtubeBot.on_message(
    Filters.private
    & Filters.incoming
    & Filters.command("upload")
    & Filters.user(Config.AUTH_USERS)
)
async def _upload(c: UtubeBot, m: Message):
    if not os.path.exists(Config.CRED_FILE):
        await m.reply_text(tr.NOT_AUTHENTICATED_MSG, True)
        return

    if not m.reply_to_message:
        await m.reply_text(tr.NOT_A_REPLY_MSG, True)
        return

    message = m.reply_to_message

    if not message.media:
        await m.reply_text(tr.NOT_A_MEDIA_MSG, True)
        return

    if not valid_media(message):
        await m.reply_text(tr.NOT_A_VALID_MEDIA_MSG, True)
        return

    if c.counter >= 6:
        await m.reply_text(tr.DAILY_QOUTA_REACHED, True)

    snt = await m.reply_text(tr.PROCESSING, True)
    c.counter += 1
    download_id = get_download_id(c.download_controller)
    c.download_controller[download_id] = True

    download = Downloader(m)
    status, file = await download.start(progress, snt, c, download_id)
    log.debug(status, file)
    c.download_controller.pop(download_id)

    if not status:
        c.counter -= 1
        c.counter = max(0, c.counter)
        await snt.edit_text(file)
        return

    try:
        await snt.edit_text("Downloaded to local, Now starting to upload to youtube...")
    except Exception as e:
        log.warning(e, exc_info=True)
        pass

    title = " ".join(m.command[1:])
    upload = Uploader(file, title)
    status, link = await upload.start(progress, snt)
    log.debug(status, link)
    if not status:
        c.counter -= 1
        c.counter = max(0, c.counter)
    await snt.edit_text(link)
    #delete if downloaded file still exists...
    if os.path.exists(file):
        os.remove(file)


def get_download_id(storage: dict) -> str:
    while True:
        download_id = "".join([random.choice(string.ascii_letters) for i in range(3)])
        if download_id not in storage:
            break
    return download_id


def valid_media(media: Message) -> bool:
    if media.video:
        return True
    elif media.video_note:
        return True
    elif media.animation:
        return True
    elif media.document and "video" in media.document.mime_type:
        return True
    else:
        return False


def human_bytes(
    num: Union[int, float], split: bool = False
) -> Union[str, Tuple[int, str]]:
    base = 1024.0
    sufix_list = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    for unit in sufix_list:
        if abs(num) < base:
            if split:
                return round(num, 2), unit
            return f"{round(num, 2)} {unit}"
        num /= base

async def download_direct_url(url, filename, snt, c, download_id, start_time):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            chunk_size = 1024 * 512
            done = 0
            last_update = time.time()

            with open(filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    if not c.download_controller.get(download_id):
                        raise StopTransmission
                    f.write(chunk)
                    done += len(chunk)

                    now = time.time()
                    if now - last_update > 10 or done == total:
                        try:
                            percent = round((done * 100) / total, 2)
                            speed, unit = human_bytes(done / (now - start_time), True)
                            curr = human_bytes(done)
                            tott = human_bytes(total)
                            eta = datetime.timedelta(seconds=int(((total - done) / (1024 * 1024)) / speed))
                            elapsed = datetime.timedelta(seconds=int(now - start_time))

                            text = (
                                f"Downloading from URL...\n\n"
                                f"{percent}% done.\n{curr} of {tott}\n"
                                f"Speed: {speed} {unit}/s\nETA: {eta}\nElapsed: {elapsed}"
                            )
                            await snt.edit_text(
                                text=text,
                                reply_markup=InlineKeyboardMarkup(
                                    [[InlineKeyboardButton("Cancel", f"cncl+{download_id}")]]
                                ),
                            )
                            last_update = now
                        except Exception:
                            pass

async def progress(
    cur: Union[int, float],
    tot: Union[int, float],
    start_time: float,
    status: str,
    snt: Message,
    c: UtubeBot,
    download_id: str,
):
    if not c.download_controller.get(download_id):
        raise StopTransmission

    try:
        diff = int(time.time() - start_time)

        if (int(time.time()) % 5 == 0) or (cur == tot):
            await asyncio.sleep(1)
            speed, unit = human_bytes(cur / diff, True)
            curr = human_bytes(cur)
            tott = human_bytes(tot)
            eta = datetime.timedelta(seconds=int(((tot - cur) / (1024 * 1024)) / speed))
            elapsed = datetime.timedelta(seconds=diff)
            progress = round((cur * 100) / tot, 2)
            text = f"{status}\n\n{progress}% done.\n{curr} of {tott}\nSpeed: {speed} {unit}PS"
            f"\nETA: {eta}\nElapsed: {elapsed}"
            await snt.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel!🚫", f"cncl+{download_id}")]]
                ),
            )

    except Exception as e:
        log.info(e)
        pass


            
