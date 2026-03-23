from VLCBox.util.base_clients import MainBot
# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

def upload_image_requests(image_path):
    """Uploads an image to graph.org (Telegraph)"""
    upload_url = "https://graph.org/upload"
    try:
        with open(image_path, 'rb') as file:
            files = {'file': ('file', file, 'image/jpeg')}
            response = requests.post(upload_url, files=files)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return "https://graph.org" + data[0]['src']
                return None
            else:
                print(f"Upload failed with status code {response.status_code}")
                return None
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

@MainBot.on_message(filters.command("telegraph") & filters.private)
async def telegraph_upload(bot, update):
    t_msg = await bot.ask(chat_id = update.from_user.id, text = "Now Send Me Your Photo Or Video Under 5MB To Get Media Link.")
    if not t_msg.media:
        return await update.reply_text("**Only Media Supported.**")
    
    # Check file size (5MB limit)
    file_size = getattr(t_msg.photo or t_msg.video or t_msg.document or t_msg.sticker or t_msg.animation, "file_size", 0)
    if file_size > 5242880: # 5MB in bytes
        return await update.reply_text("**File size exceeds 5MB limit. Please send a smaller file.**")

    path = await t_msg.download()
    uploading_message = await update.reply_text("<b>ᴜᴘʟᴏᴀᴅɪɴɢ...</b>")
    try:
        image_url = upload_image_requests(path)
        if not image_url:
            return await uploading_message.edit_text("**Failed to upload file. The server might be down or file type not supported.**")
    except Exception as error:
        await uploading_message.edit_text(f"**Upload failed: {error}**")
        if os.path.exists(path):
            os.remove(path)
        return
    
    if os.path.exists(path):
        os.remove(path)
    await uploading_message.edit_text(
        text=f"<b>Link :-</b>\n\n<code>{image_url}</code>",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup( [[
            InlineKeyboardButton(text="Open Link", url=image_url),
            InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url={image_url}")
            ],[
            InlineKeyboardButton(text="✗ Close ✗", callback_data="close")
            ]])
        )
    
