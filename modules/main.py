import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import logging
import core as helper
from utils import progress_bar
from vars import API_ID as api_id
from vars import API_HASH as api_hash
from vars import BOT_TOKEN as bot_token
from vars import OWNER_ID as owner
from vars import SUDO_USERS as sudo_users
from datetime import datetime, timedelta
import time
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


bot = Client(
    name=":memory:",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
)



logging.basicConfig(filename="bot_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

bot = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

SUDO_USERS = set(map(int, sudo_users))  
SUDO_USERS.add(int(owner))
premium_users = set()

# T
bot_start_time = datetime.now()


def get_current_time():
    """Return the current time in HH:MM:SS format."""
    return datetime.now().strftime('%H:%M:%S')

def get_bot_uptime():
    """Calculate and return bot uptime."""
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

async def send_admin_notification(message: str):
    """Send a message to all admin users."""
    for admin_id in SUDO_USERS:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


@bot.on_message(filters.command("start"))
async def start_handler(_, m: Message):
    """Send a welcome message when the bot starts."""
    try:
        await m.reply_text("I am a Text Downloader Bot.\nUse /txt command to extract text files.")
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")
        await m.reply_text("An error occurred while processing the command.")

@bot.on_message(filters.command("status") & filters.user(SUDO_USERS))
async def status_handler(_, m: Message):
    """Send bot status including uptime and current time."""
    try:
        uptime = get_bot_uptime() 
        current_time = get_current_time()  
        status_message = f"**Bot Status**\nUptime: {uptime}\nCurrent Time: {current_time}"
        await m.reply_text(status_message)
        logger.info(f"Bot status requested by user {m.from_user.id}")
    except Exception as e:
        logger.error(f"Error in status_handler: {e}")
        await m.reply_text("An error occurred while fetching the status.")

@bot.on_message(filters.command("help"))
async def help_handler(_, m: Message):
    """Send the list of available bot commands."""
    try:
        help_message = (
            "/status - View bot status\n"
            "/shutdown - Shutdown bot (admin only)\n"
            "/premium - Mark user as premium (admin only)\n"
            "/removepremium - Remove premium status (admin only)"
        )
        await m.reply_text(help_message)
    except Exception as e:
        logger.error(f"Error in help_handler: {e}")
        await m.reply_text("An error occurred while processing the help command.")

@bot.on_message(filters.command("ping"))
async def ping_handler(_, m: Message):
    """Respond to ping command and measure bot's latency."""
    try:
        start_time = time.time()
        response = await m.reply_text("Pong! 🏓")
        latency = time.time() - start_time
        await response.edit(f"Pong! 🏓\nLatency: {latency * 1000:.2f}ms")
        logger.info(f"Ping response sent to user {m.from_user.id} with latency {latency * 1000:.2f}ms")
    except Exception as e:
        logger.error(f"Error in ping_handler: {e}")
        await m.reply_text("An error occurred while processing the ping command.")


@bot.on_message(filters.command("shutdown") & filters.user(SUDO_USERS))
async def shutdown_handler(_, m: Message):
    """Shutdown the bot gracefully."""
    try:
        await send_admin_notification(f"Bot shutdown initiated by {m.from_user.id} at {get_current_time()}.")
        await m.reply_text("**Shutdown initiated** 🛑\nBot is shutting down...")
        logger.info(f"Shutdown requested by user {m.from_user.id}")
        await bot.stop()  
    except Exception as e:
        logger.error(f"Error in shutdown_handler: {e}")
        await m.reply_text(f"Error during shutdown: {e}")


@bot.on_message(filters.command("premium") & filters.user(SUDO_USERS))
async def premium_handler(_, m: Message):
    """Mark a user as a premium user."""
    try:
        if m.reply_to_message:
            user_id = m.reply_to_message.from_user.id
            premium_users.add(user_id)
            await m.reply_text(f"User {user_id} marked as premium! 🎉")
            logger.info(f"User {user_id} marked as premium by {m.from_user.id}")
        else:
            await m.reply_text("Please reply to a user to mark as premium.")
    except Exception as e:
        logger.error(f"Error in premium_handler: {e}")
        await m.reply_text("An error occurred while marking the user as premium.")

@bot.on_message(filters.command("removepremium") & filters.user(SUDO_USERS))
async def remove_premium_handler(_, m: Message):
    """Remove premium status from a user."""
    try:
        if m.reply_to_message:
            user_id = m.reply_to_message.from_user.id
            if user_id in premium_users:
                premium_users.remove(user_id)
                await m.reply_text(f"User {user_id}'s premium status removed. ❌")
                logger.info(f"User {user_id}'s premium status removed by {m.from_user.id}")
            else:
                await m.reply_text(f"User {user_id} is not a premium user.")
        else:
            await m.reply_text("Please reply to a user to remove premium status.")
    except Exception as e:
        logger.error(f"Error in remove_premium_handler: {e}")
        await m.reply_text("An error occurred while removing premium status.")

@bot.on_message(filters.command(["txt"]) & filters.user(SUDO_USERS))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text('➤𝐈 𝐜𝐚𝐧 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐕𝐢𝐝𝐞𝐨𝐬 𝐅𝐫𝐨𝐦 𝐓𝐗𝐓 𝐅𝐢𝐥𝐞 𝐎𝐧𝐞 𝐁𝐲 𝐎𝐧𝐞.\n➤𝐍𝐨𝐰 𝐒𝐞𝐧𝐝 𝐌𝐞 𝐘𝐨𝐮𝐫 𝐓𝐗𝐓 𝐅𝐢𝐥𝐞 𝐢𝐧 𝐀 𝐏𝐫𝐨𝐩𝐞𝐫 𝐖𝐚𝐲\n')
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)

    path = f"./downloads"

    try:
       with open(x, "r") as f:
           content = f.read()
       content = content.split("\n")
       links = []
       for i in content:
           links.append(i.split("://", 1))
       os.remove(x)
       
    except:
           await m.reply_text("Invalid file input.")
           os.remove(x)
           return
    
   
    await editable.edit(f"Total links found are **{len(links)}**\n\nSend From where you want to download initial is **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("**Enter Batch Name**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    

    await editable.edit("**Enter resolution**")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
    
    

    await editable.edit("**Enter A Highlighter (Download By) **")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    highlighter  = f"️ ⁪⁬⁮⁮⁮"
    if raw_text3 == 'Co':
        MR = highlighter 
    else:
        MR = raw_text3
   
    await editable.edit("Now send the **Thumb url**\nEg : ```https://telegra.ph/file/0633f8b6a6f110d34f044.jpg```\n\nor Send `no`")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    if len(links) == 1:
        count = 1
    else:
        count = int(raw_text)

    try:
        for i in range(count - 1, len(links)):

            V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","") # .replace("mpd","m3u8")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'}).json()['url']

            if "tencdn.classplusapp" in url:
                headers = {'Host': 'api.classplusapp.com', 'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0', 'user-agent': 'Mobile-Android', 'app-version': '1.4.37.1', 'api-version': '18', 'device-id': '5d0d17ac8b3c9f51', 'device-details': '2848b866799971ca_2848b8667a33216c_SDK-30', 'accept-encoding': 'gzip'}
                params = (('url', f'{url}'),)
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']
            elif '/master.mpd' in url:
             id =  url.split("/")[-2]
             url =  "https://d26g5bnklkwsh4.cloudfront.net/" + id + "/master.m3u8"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                
                cc = f'**[📂] Vid ID :** {str(count).zfill(3)}\n**Video Title :** {name1} {res} .mkv\n**Batch :** {raw_text0}\n\n**Downloaded By : **{raw_text3}\n\n'
                cc1 = f'****[📕]Pdf_ID :** {str(count).zfill(3)}\n**Pdf Title :** {name1} .pdf \n**Batch :** {raw_text0}\n\n'
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                
                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                else:
                    Show = f"**Downloading:-**\n\n**Name :-** `{name}\nQuality - {raw_text2}`\n\n**Url :-** `{url}`\n"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"**downloading failed 🥺**\n{str(e)}\n**Name** - {name}\n**Link** - `{url}`"
                )
                continue

    except Exception as e:
        await m.reply_text(e)
    await m.reply_text("Done")


bot.run()
