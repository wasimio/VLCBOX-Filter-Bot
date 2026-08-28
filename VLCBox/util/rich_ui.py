# Don't Remove Credit @vlcbox
# VLCBox - Experimental Rich Movie Result UI
# Handles modern Telegram Rich formatting (Expandable blockquotes, structured file listings, clean headings)
# and isolated direct Bot API delivery for normal messages.

import html
import logging
import re
import aiohttp
from typing import Any, Dict, List, Optional, Union

from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from info import BOT_TOKEN, EXPERIMENTAL_BOT_TOKEN, RICH_MOVIE_RESULTS
from utils import get_size, temp

logger = logging.getLogger(__name__)


def get_active_bot_token(client: Optional[Any] = None) -> str:
    """
    Determine the active bot token to use for direct Telegram Bot API requests.
    """
    if EXPERIMENTAL_BOT_TOKEN:
        return EXPERIMENTAL_BOT_TOKEN
    if client and hasattr(client, "bot_token") and client.bot_token:
        return client.bot_token
    return BOT_TOKEN


def serialize_reply_markup(
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]]
) -> Optional[Dict[str, Any]]:
    """
    Convert Pyrogram InlineKeyboardMarkup / ReplyKeyboardMarkup into Telegram Bot API JSON structure.
    """
    if not reply_markup:
        return None

    if isinstance(reply_markup, dict):
        return reply_markup

    if isinstance(reply_markup, InlineKeyboardMarkup):
        serialized_keyboard = []
        for row in reply_markup.inline_keyboard:
            serialized_row = []
            for btn in row:
                text_val = btn.text.decode('utf-8', errors='ignore') if isinstance(btn.text, bytes) else str(btn.text)
                btn_dict: Dict[str, Any] = {"text": text_val}

                if hasattr(btn, "url") and btn.url:
                    url_val = btn.url.decode('utf-8', errors='ignore') if isinstance(btn.url, bytes) else str(btn.url)
                    btn_dict["url"] = url_val
                elif hasattr(btn, "callback_data") and btn.callback_data is not None:
                    cb_val = btn.callback_data
                    if isinstance(cb_val, bytes):
                        cb_val = cb_val.decode('utf-8', errors='ignore')
                    btn_dict["callback_data"] = str(cb_val)
                elif hasattr(btn, "web_app") and btn.web_app:
                    web_url = btn.web_app.url.decode('utf-8', errors='ignore') if isinstance(btn.web_app.url, bytes) else str(btn.web_app.url)
                    btn_dict["web_app"] = {"url": web_url}
                elif hasattr(btn, "switch_inline_query") and btn.switch_inline_query is not None:
                    btn_dict["switch_inline_query"] = str(btn.switch_inline_query)
                elif hasattr(btn, "switch_inline_query_current_chat") and btn.switch_inline_query_current_chat is not None:
                    btn_dict["switch_inline_query_current_chat"] = str(btn.switch_inline_query_current_chat)
                serialized_row.append(btn_dict)
            serialized_keyboard.append(serialized_row)
        return {"inline_keyboard": serialized_keyboard}

    if isinstance(reply_markup, ReplyKeyboardMarkup):
        serialized_keyboard = []
        for row in reply_markup.keyboard:
            serialized_row = []
            for btn in row:
                text_val = btn.text if hasattr(btn, "text") else str(btn)
                if isinstance(text_val, bytes):
                    text_val = text_val.decode('utf-8', errors='ignore')
                serialized_row.append({"text": str(text_val)})
            serialized_keyboard.append(serialized_row)
        return {
            "keyboard": serialized_keyboard,
            "resize_keyboard": getattr(reply_markup, "resize_keyboard", False),
            "one_time_keyboard": getattr(reply_markup, "one_time_keyboard", False)
        }

    return None


def clean_filename(name: str) -> str:
    """
    Sanitize and clean file name for rich visual display.
    """
    if not name:
        return "Unknown File"
    cleaned = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), name.split()))
    return cleaned.strip() or name


def format_rich_movie_result(
    search: str,
    imdb: Optional[Dict[str, Any]],
    files: List[Dict[str, Any]],
    message: Any,
    chat_id_str: str,
    max_len: int = 1024
) -> str:
    """
    Constructs a modern Telegram Rich Movie Result block using:
    - 🎬 Rich Headings
    - Expandable blockquotes for storyline (<blockquote expandable>)
    - Structured, readable file list
    - Requested by metadata
    Guarantees valid HTML closing tags and adheres strictly to max_len.
    """
    user_mention = message.from_user.mention if getattr(message, "from_user", None) else "User"

    if imdb:
        title = html.escape(str(imdb.get('title') or search.title()))
        year = str(imdb.get('year') or 'N/A')
        rating = str(imdb.get('rating') or 'N/A')
        genres = html.escape(str(imdb.get('genres') or 'N/A'))
        plot = str(imdb.get('plot') or '')
        
        header = (
            f"<b>🎬 {title}</b>\n"
            f"<b>📅 Year:</b> <code>{year}</code> | <b>⭐ Rating:</b> <code>{rating}/10</code>\n"
            f"<b>🎭 Genres:</b> <i>{genres}</i>\n\n"
        )
    else:
        title = html.escape(search.title())
        header = (
            f"<b>🎬 Search Results for:</b> <code>{title}</code>\n\n"
        )
        plot = None

    # Determine maximum files to display based on budget
    max_files_display = 3 if max_len <= 1024 else 7
    display_files = files[:max_files_display]
    
    files_header = f"<b>📁 Available Files ({len(files)}):</b>\n"
    file_lines = []
    for file in display_files:
        f_size = get_size(file.get('file_size', 0))
        f_name = html.escape(clean_filename(file.get('file_name', '')))
        f_id = file.get('file_id', '')
        file_lines.append(
            f"• <b>[{f_size}]</b> <a href='https://telegram.me/{temp.U_NAME}?start=files_{chat_id_str}_{f_id}'>{f_name}</a>"
        )
    
    if len(files) > max_files_display:
        file_lines.append(f"<i>... and {len(files) - max_files_display} more files via buttons below</i>")

    files_content = "\n".join(file_lines) + "\n\n" if file_lines else ""
    footer = f"<b>👤 Requested by:</b> {user_mention}"

    if plot:
        frame_structure = (
            f"{header}"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>💬 Storyline:</b>\n"
            f"<blockquote expandable></blockquote expandable>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{files_header}"
            f"{files_content}"
            f"{footer}"
        )
        allowed_plot_len = max(0, max_len - len(frame_structure) - 10)
        clean_plot = html.escape(plot.strip())
        
        if allowed_plot_len >= 30:
            if len(clean_plot) > allowed_plot_len:
                clean_plot = clean_plot[:allowed_plot_len - 3].rstrip() + "..."
            
            story_section = (
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<b>💬 Storyline:</b>\n"
                f"<blockquote expandable>{clean_plot}</blockquote>\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
            )
        else:
            story_section = "━━━━━━━━━━━━━━━━━━\n\n"

        rich_text = f"{header}{story_section}{files_header}{files_content}{footer}"
    else:
        rich_text = f"{header}━━━━━━━━━━━━━━━━━━\n\n{files_header}{files_content}━━━━━━━━━━━━━━━━━━\n\n{footer}"

    return rich_text


async def send_rich_message_http(
    client: Any,
    chat_id: Union[int, str],
    text: str,
    photo: Optional[str] = None,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]] = None,
    reply_to_message_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Direct Telegram Bot API HTTP sender for Rich Messages.
    Uses parse_mode='HTML' directly through the Telegram Bot API server
    to ensure full support for modern HTML tags (such as <blockquote expandable>).
    """
    token = get_active_bot_token(client)
    if not token:
        return {"success": False, "error": "missing_token"}

    serialized_markup = serialize_reply_markup(reply_markup)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        if photo:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload: Dict[str, Any] = {
                "chat_id": chat_id,
                "photo": photo,
                "caption": text,
                "parse_mode": "HTML"
            }
            if serialized_markup:
                payload["reply_markup"] = serialized_markup
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id

            try:
                async with session.post(url, json=payload) as resp:
                    data = await resp.json()
                    if data.get("ok"):
                        return {"success": True, "result": data.get("result")}
                    
                    err_desc = data.get("description", "Unknown error")
                    logger.warning(f"RICH_UI: sendPhoto failed ({err_desc}), attempting sendMessage fallback")
            except Exception as e:
                logger.warning(f"RICH_UI: sendPhoto network error: {e}")

        # Send text message fallback
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if serialized_markup:
            payload["reply_markup"] = serialized_markup
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    return {"success": True, "result": data.get("result")}
                
                err_desc = data.get("description", "Unknown error")
                logger.error(f"RICH_UI: sendMessage failed: {err_desc}")
                return {"success": False, "error": err_desc}
        except Exception as e:
            logger.error(f"RICH_UI: sendMessage network error: {e}")
            return {"success": False, "error": str(e)}


async def send_rich_search_result(
    client: Any,
    message: Any,
    reply_msg: Any,
    text: str,
    photo: Optional[str] = None,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
) -> Any:
    """
    Unified entry point for sending an Experimental Rich Movie Result.
    Delivers as a NORMAL Telegram message using Bot API HTTP wrapper,
    with safe graceful fallback to standard Pyrogram methods.
    """
    chat_id = message.chat.id
    reply_to_id = message.id if hasattr(message, "id") else None

    # Attempt direct Bot API Rich Message delivery
    http_res = await send_rich_message_http(
        client=client,
        chat_id=chat_id,
        text=text,
        photo=photo,
        reply_markup=reply_markup,
        reply_to_message_id=reply_to_id
    )

    if http_res and http_res.get("success"):
        if reply_msg:
            try:
                await reply_msg.delete()
            except Exception:
                pass
        return http_res.get("result")

    # Safe Fallback to standard Pyrogram methods if HTTP API fails
    logger.warning("RICH_UI: falling back to standard Pyrogram message delivery")
    if photo:
        try:
            res = await message.reply_photo(photo=photo, caption=text, reply_markup=reply_markup)
            if reply_msg:
                try:
                    await reply_msg.delete()
                except Exception:
                    pass
            return res
        except Exception as e:
            logger.warning(f"RICH_UI: fallback photo failed ({e}), attempting text reply")
            if reply_msg:
                try:
                    return await reply_msg.edit_text(text=text, reply_markup=reply_markup, disable_web_page_preview=True)
                except Exception:
                    pass
            return await message.reply_text(text=text, reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        if reply_msg:
            try:
                return await reply_msg.edit_text(text=text, reply_markup=reply_markup, disable_web_page_preview=True)
            except Exception:
                pass
        return await message.reply_text(text=text, reply_markup=reply_markup, disable_web_page_preview=True)
