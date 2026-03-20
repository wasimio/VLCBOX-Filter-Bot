# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import asyncio
import logging
from info import *
from pyrogram import Client
from VLCBox.util.config_parser import TokenParser
from VLCBox.bot import multi_clients, work_loads, VLCBoxBot


async def initialize_clients():
    multi_clients[0] = VLCBoxBot
    work_loads[0] = 0
    all_tokens = TokenParser().parse_from_env()
    if not all_tokens:
        print("No additional clients found, using default client")
        return
    
    async def start_client(client_id, token):
        if token == BOT_TOKEN:
            return None
        try:
            print(f"Starting - Client {client_id}")
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                print("This will take some time, please wait...")
            client = await Client(
                name=str(client_id),
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                sleep_threshold=SLEEP_THRESHOLD,
                no_updates=True,
                in_memory=True
            ).start()
            work_loads[client_id] = 0
            return client_id, client
        except Exception:
            logging.error(f"Failed starting Client - {client_id} Error:", exc_info=True)
    
    clients = await asyncio.gather(*[start_client(i, token) for i, token in all_tokens.items()])
    clients = [c for c in clients if c is not None]
    multi_clients.update(dict(clients))
    if len(multi_clients) != 1:
        MULTI_CLIENT = True
        print("Multi-Client Mode Enabled")
    else:
        print("No additional clients were initialized, using default client")

