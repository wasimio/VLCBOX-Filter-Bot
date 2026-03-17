# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import pyromod
import sys
import glob
import importlib
import logging
import logging.config
import pytz
import asyncio
from pathlib import Path
from pyrogram import Client, idle
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from plugins import web_server
from plugins.clone import restart_bots

from VLCBox.bot import VLCBoxBot
from VLCBox.util.keepalive import ping_server
from VLCBox.bot.clients import initialize_clients

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

async def start():
    print('\n')
    print('-----------------------')
    print('Initializing VLCBox Bot')
    print('-----------------------')
    
    # Start the main bot
    await VLCBoxBot.start()
    bot_info = await VLCBoxBot.get_me()
    print(f'>>> Bot Started as {bot_info.first_name} (@{bot_info.username})')
    
    # Manual Plugin Loading (Recursive to catch Extra folder)
    print(">>> Loading Plugins...")
    plugins_path = "plugins/**/*.py"
    plugin_files = glob.glob(plugins_path, recursive=True)
    
    for file_path in plugin_files:
        if file_path.endswith("__init__.py"):
            continue
        
        path = Path(file_path)
        # Convert path to module name: plugins/Extra/telegraph.py -> plugins.Extra.telegraph
        parts = list(path.with_suffix('').parts)
        module_path = ".".join(parts)
        
        try:
            # Check if already loaded by pyrogram's internal loader
            if module_path in sys.modules:
                continue
                
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)
            print(f"  + Imported: {module_path}")
        except Exception as e:
            print(f"  - Failed to load {module_path}: {e}")

    # Initialize multi-clients
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        
    # Set temp variables
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    temp.BOT = VLCBoxBot
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name
    
    logging.info(script.LOGO)
    
    # Notify Restart
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time_str = now.strftime("%H:%M:%S %p")
    
    try:
        await VLCBoxBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time_str))
    except Exception as e:
        print(f"Log Channel Error: {e}")
        
    # Start Web Server
    print(">>> Starting Web Server...")
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()
    print(f">>> Web Server started on port {PORT}")
    
    if CLONE_MODE:
        print(">>> Restarting Clone Bots...")
        await restart_bots()
    
    print("-------------------------")
    print("VLCBox Bot is now ONLINE!")
    print("-------------------------")
    
    await idle()
    await VLCBoxBot.stop()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        print('Service Stopped Bye 👋')
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
