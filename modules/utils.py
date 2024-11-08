
import time
import os
import logging
import threading
import asyncio
from datetime import timedelta
from pyrogram.errors import FloodWait
from concurrent.futures import ThreadPoolExecutor



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Timer:
    def __init__(self, time_between=5):
        """Initializes the timer with a time interval between actions."""
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        """Checks if the time interval has passed and resets the timer."""
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

    def reset(self):
        """Manually resets the timer."""
        self.start_time = time.time()

def hrb(value, digits=2, delim="", postfix=""):
    """Returns a human-readable file size string."""
    if value is None or value <= 0:
        return "0B"
    
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    for unit in units:
        if value < 1000:
            break
        value /= 1024
    return f"{value:.{digits}f}{delim}{unit}{postfix}"


def hrt(seconds, precision=0):
    """Returns a human-readable time string (e.g., 1h 30m 20s)."""
    value = timedelta(seconds=seconds)
    pieces = []

    if value.days:
        pieces.append(f"{value.days}d")
    seconds = value.seconds

    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}h")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}m")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")

    return "".join(pieces[:precision]) if precision else "".join(pieces)


async def progress_bar(current, total, reply, start, timer, bar_length=20):
    """Displays a progress bar during a file upload operation."""
    if not timer.can_send():
        return  

    now = time.time()
    diff = now - start

    if diff < 1:  
        return

    perc = f"{(current / total) * 100:.1f}%"
    elapsed_time = round(diff)
    speed = current / elapsed_time if elapsed_time > 0 else 0
    remaining_bytes = total - current
    eta = "-" if speed == 0 else hrt(remaining_bytes / speed, precision=1)

    sp = hrb(speed) + "/s"
    tot = hrb(total)
    cur = hrb(current)

    completed_length = int(current * bar_length / total)
    remaining_length = bar_length - completed_length
    progress_bar = "▰" * completed_length + "▱" * remaining_length

    try:
       
        if reply:
            await reply.edit(
                f'`╭──⌈📤 𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 📤⌋──╮ \n'
                f'├{progress_bar}\n'
                f'├ 𝙎𝙥𝙚𝙚𝙙 : {sp} \n'
                f'├ 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 : {perc} \n'
                f'├ 𝙇𝙤𝙖𝙙𝙚𝙙 : {cur}\n'
                f'├ 𝙎𝙞𝙯𝙚 : {tot} \n'
                f'├ 𝙀𝙏𝘼 : {eta} \n'
                f'╰─⌈𝙈𝙖𝙙𝙚 𝙗𝙮 𝙇𝙚𝙜𝙚𝙣𝙙𝙭𝘽𝙤𝙞⌋─╯`\n'
            )
        logger.info(f"Progress updated: {perc} ({cur}/{tot}), ETA: {eta}")
    except FloodWait as e:
        logger.warning(f"Flood wait triggered. Sleeping for {e.x} seconds.")
        time.sleep(e.x)



async def upload_with_retry(file_path, retry_limit=3, backoff_factor=2):
    """Handles file upload with retry logic."""
    attempt = 0
    while attempt < retry_limit:
        try:
            await upload_file(file_path)
            return  
        except Exception as e:
            attempt += 1
            wait_time = backoff_factor ** attempt 
            logger.error(f"Upload attempt {attempt} failed: {e}. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    logger.error(f"Upload failed after {retry_limit} attempts.")


async def upload_file(file_path, bar_length=20):
    """Simulates a file upload with progress updates."""
    total_size = os.path.getsize(file_path)
    uploaded = 0
    chunk_size = 1024 * 1024  

   
    timer = Timer(time_between=2)  
    start_time = time.time()

    
    async with aiofiles.open(file_path, 'rb') as file:
        while uploaded < total_size:
            chunk = await file.read(chunk_size)
            uploaded += len(chunk)

       
            await progress_bar(uploaded, total_size, reply=None, start=start_time, timer=timer, bar_length=bar_length)
            await asyncio.sleep(0.1) 

    logger.info(f"Upload completed for {file_path}")


def upload_in_thread(file_path):
    """Runs upload in a separate thread."""
    upload_thread = threading.Thread(target=asyncio.run, args=(upload_file(file_path),))
    upload_thread.start()
    return upload_thread


def upload_multiple_files(file_paths):
    """Upload multiple files concurrently using threading."""
    with ThreadPoolExecutor() as executor:
        
        futures = [executor.submit(upload_in_thread, file_path) for file_path in file_paths]

       
        for future in futures:
            future.result()  

