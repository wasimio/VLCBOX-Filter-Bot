# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

# Clone Code Credit : TG - @rickakhtar / TG - @vlcbox / GitHub - @rickakhtar

import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

import pyromod
from pyrogram import Client, idle
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from plugins import web_server
from plugins.clone import restart_bots

from VLCBox.bot import VLCBoxBot
from VLCBox.util.keepalive import ping_server
from VLCBox.bot.clients import initialize_clients

async def start():
    print('\n')
    print('Initalizing Your Bot')
    
    # Start the main bot
    await VLCBoxBot.start()
    bot_info = await VLCBoxBot.get_me()
    print(f'Bot Started as {bot_info.first_name}')
    
    # Initialize multi-clients if any
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    
    temp.BOT = VLCBoxBot
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name
    
    logging.info(script.LOGO)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time_str = now.strftime("%H:%M:%S %p")
    
    try:
        await VLCBoxBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time_str))
    except Exception as e:
        print(f"Log Channel Error: {e}. Make Your Bot Admin In Log Channel")
        
    for ch in CHANNELS:
        try:
            k = await VLCBoxBot.send_message(chat_id=ch, text="**Bot Restarted**")
            await k.delete()
        except Exception as e:
            print(f"File Channel {ch} Error: {e}. Make Your Bot Admin In File Channels")
            
    try:
        if AUTH_CHANNEL:
            k = await VLCBoxBot.send_message(chat_id=AUTH_CHANNEL, text="**Bot Restarted**")
            await k.delete()
    except Exception as e:
        print(f"Auth Channel Error: {e}. Make Your Bot Admin In Force Subscribe Channel")
        
    if CLONE_MODE:
        print("Restarting All Clone Bots.......")
        await restart_bots()
        print("Restarted All Clone Bots.")
        
    # Start Web Server
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    print(f"Web Server started on port {PORT}")
    
    await idle()
    await VLCBoxBot.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
