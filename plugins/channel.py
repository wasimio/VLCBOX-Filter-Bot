from VLCBox.util.base_clients import MainBot
# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file

media_filter = filters.document | filters.video

@MainBot.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    media.caption = message.caption
    await save_file(media)

