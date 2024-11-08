import os
import time
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
import threading

from utils import progress_bar
from pyrogram import Client, filters
from pyrogram.types import Message


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d] [Thread:%(threadName)s]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs.txt"),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger()

failed_counter = 0


def duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return float(result.stdout)


def exec(cmd):
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.stdout.decode()
    error = process.stderr.decode()
    if process.returncode != 0:
        logger.error(f"Command failed: {cmd} with error: {error}")
    else:
        logger.info(f"Command succeeded: {cmd}")
    return output


def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        logger.info("Waiting for tasks to complete")
        futures = [executor.submit(exec, cmd) for cmd in cmds]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            logger.debug(f"Command result: {result}")


async def aio(url, name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(k, mode='wb') as f:
                    await f.write(await resp.read())
    return k


async def download(url, name, speed_limit="500K"):
    """
    Download a file while enforcing a consistent speed limit.
    Uses aria2c to download with a rate limit.
    :param url: URL of the file to download
    :param name: Name of the file to save as
    :param speed_limit: Maximum download speed (e.g., "500K" for 500KB/s)
    """
    k = f'{name}.pdf'
    cmd = f"aria2c --max-download-limit={speed_limit} -o {k} {url}"
    logger.info(f"Starting download with command: {cmd}")
    process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        logger.error(f"Download failed for {url} with error: {process.stderr.decode()}")
        return None
    return k


def parse_vid_info(info):
    info = info.strip().split("\n")
    new_info = []
    temp = []
    for i in info:
        i = i.strip()
        if "[" not in i and '---' not in i:
            i = i.replace("  ", " ").split("|")[0].split(" ", 2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except IndexError:
                pass
    return new_info


def vid_info(info):
    info = info.strip().split("\n")
    new_info = {}
    temp = []
    for i in info:
        i = i.strip()
        if "[" not in i and '---' not in i:
            i = i.replace("  ", " ").split("|")[0].split(" ", 3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({i[2]: i[0]})
            except IndexError:
                pass
    return new_info


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info(f'[{cmd!r}] succeeded')
        return stdout.decode() if stdout else None
    else:
        logger.error(f'[{cmd!r}] failed with error: {stderr.decode()}')
        return None


def old_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


async def download_video(url, cmd, name, speed_limit="500K"):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32 --max-download-limit={speed_limit}"'
    global failed_counter
    logger.info(f"Executing command: {download_cmd}")
    k = subprocess.run(download_cmd, shell=True)
    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        return await download_video(url, cmd, name, speed_limit)
    failed_counter = 0
    if os.path.isfile(name):
        return name
    return name.split(".")[0]


async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    reply = await m.reply_text(f"Uploading - `{name}`")
    await asyncio.sleep(1)
    start_time = time.time()
    await m.reply_document(ka, caption=cc1)
    count += 1
    await reply.delete(True)
    await asyncio.sleep(1)
    os.remove(ka)
    await asyncio.sleep(3)


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
    await prog.delete(True)
    reply = await m.reply_text(f"**Uploading ...** - `{name}`")
    try:
        thumbnail = f"{filename}.jpg" if thumb == "no" else thumb
    except Exception as e:
        await m.reply_text(str(e))

    dur = int(duration(filename))

    try:
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
    except Exception:
        await m.reply_document(
            filename,
            caption=cc,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
    os.remove(filename)
    os.remove(f"{filename}.jpg")
    await reply.delete(True)


    
