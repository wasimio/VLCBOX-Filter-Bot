# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Isolated Telegram Bot API Ephemeral Group Messages Wrapper for VLCBox.

Supports sending private/ephemeral messages to a specific user within
groups and supergroups according to Telegram Bot API 10.2 / 10.3 standards.
"""

import logging
import aiohttp
import asyncio
from typing import Optional, Union, Dict, Any
from pyrogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from pyrogram import enums
from info import EPHEMERAL_GROUP_MESSAGES, EXPERIMENTAL_BOT_TOKEN, BOT_TOKEN

logger = logging.getLogger(__name__)


def get_active_bot_token(client: Optional[Any] = None) -> str:
    """
    Determine the active bot token to use for direct Telegram Bot API requests.
    Prioritizes EXPERIMENTAL_BOT_TOKEN if configured, else client.bot_token or BOT_TOKEN.
    """
    if EXPERIMENTAL_BOT_TOKEN:
        return EXPERIMENTAL_BOT_TOKEN
    if client and hasattr(client, "bot_token") and client.bot_token:
        return client.bot_token
    return BOT_TOKEN


def serialize_reply_markup(reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
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
                btn_dict: Dict[str, Any] = {"text": btn.text}
                if hasattr(btn, "url") and btn.url:
                    btn_dict["url"] = btn.url
                elif hasattr(btn, "callback_data") and btn.callback_data:
                    btn_dict["callback_data"] = btn.callback_data
                elif hasattr(btn, "web_app") and btn.web_app:
                    btn_dict["web_app"] = {"url": btn.web_app.url}
                elif hasattr(btn, "switch_inline_query") and btn.switch_inline_query is not None:
                    btn_dict["switch_inline_query"] = btn.switch_inline_query
                elif hasattr(btn, "switch_inline_query_current_chat") and btn.switch_inline_query_current_chat is not None:
                    btn_dict["switch_inline_query_current_chat"] = btn.switch_inline_query_current_chat
                serialized_row.append(btn_dict)
            serialized_keyboard.append(serialized_row)
        return {"inline_keyboard": serialized_keyboard}

    if isinstance(reply_markup, ReplyKeyboardMarkup):
        serialized_keyboard = []
        for row in reply_markup.keyboard:
            serialized_row = []
            for btn in row:
                btn_dict = {"text": btn.text if hasattr(btn, "text") else str(btn)}
                serialized_row.append(btn_dict)
            serialized_keyboard.append(serialized_row)
        return {
            "keyboard": serialized_keyboard,
            "resize_keyboard": getattr(reply_markup, "resize_keyboard", False),
            "one_time_keyboard": getattr(reply_markup, "one_time_keyboard", False)
        }

    return None


async def send_ephemeral(
    client: Any,
    chat_id: Union[int, str],
    user_id: int,
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
    fallback_on_error: bool = True
) -> Dict[str, Any]:
    """
    Send an ephemeral / private message to a specific user inside a group or supergroup.

    Parameters:
        client: Pyrogram Client instance
        chat_id: Target group or supergroup chat ID (int or str)
        user_id: Target recipient user ID (int)
        text: Message text
        reply_markup: Optional inline keyboard or reply keyboard
        parse_mode: HTML / Markdown (default: HTML)
        disable_web_page_preview: Whether to disable link previews (default: True)
        fallback_on_error: Whether to send a standard group message if ephemeral delivery fails (default: True)

    Returns:
        Dict with keys: success (bool), ephemeral (bool), fallback_sent (bool), error (Optional[str]), result (Optional[Dict])
    """
    # 1. Check Feature Flag
    if not EPHEMERAL_GROUP_MESSAGES:
        logger.info(f"EPHEMERAL: unsupported - feature flag EPHEMERAL_GROUP_MESSAGES is disabled")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e:
                logger.error(f"EPHEMERAL: fallback send failed - {e}")
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": "feature_disabled"}

    # 2. Check Chat Eligibility (Must be a group or supergroup - negative chat_id)
    try:
        numeric_chat_id = int(chat_id)
    except (ValueError, TypeError):
        numeric_chat_id = 0

    if numeric_chat_id >= 0:
        logger.info(f"EPHEMERAL: unsupported - chat_id={chat_id} is not an eligible group or supergroup")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e:
                logger.error(f"EPHEMERAL: fallback send failed - {e}")
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": "unsupported_chat_type"}

    # 3. Prepare Direct Telegram Bot API Request
    token = get_active_bot_token(client)
    if not token:
        logger.error("EPHEMERAL: API error - no bot token available")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e:
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": "missing_token"}

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
        "ephemeral_message_parameters": {
            "receiver_user_id": int(user_id)
        }
    }

    serialized_markup = serialize_reply_markup(reply_markup)
    if serialized_markup:
        payload["reply_markup"] = serialized_markup

    logger.info(f"EPHEMERAL: attempt - chat_id={chat_id}, user_id={user_id}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(api_url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(f"EPHEMERAL: success - chat_id={chat_id}, user_id={user_id}")
                    return {"success": True, "ephemeral": True, "fallback_sent": False, "result": data.get("result")}
                else:
                    error_desc = data.get("description", "Unknown Telegram API Error")
                    error_code = data.get("error_code", resp.status)
                    logger.warning(f"EPHEMERAL: API error - code={error_code}, desc={error_desc}")

                    if fallback_on_error and client:
                        logger.info(f"EPHEMERAL: fallback - sending standard message to chat_id={chat_id}")
                        try:
                            sent = await client.send_message(
                                chat_id=chat_id,
                                text=text,
                                reply_markup=reply_markup,
                                disable_web_page_preview=disable_web_page_preview
                            )
                            return {
                                "success": True,
                                "ephemeral": False,
                                "fallback_sent": True,
                                "error": error_desc,
                                "result": sent
                            }
                        except Exception as fb_err:
                            logger.error(f"EPHEMERAL: fallback send failed - {fb_err}")
                            return {
                                "success": False,
                                "ephemeral": False,
                                "fallback_sent": False,
                                "error": f"{error_desc} | fallback_error: {fb_err}"
                            }

                    return {
                        "success": False,
                        "ephemeral": False,
                        "fallback_sent": False,
                        "error": error_desc
                    }

    except asyncio.TimeoutError:
        logger.warning(f"EPHEMERAL: API error - request timed out for chat_id={chat_id}")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e:
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": "timeout"}

    except aiohttp.ClientError as e:
        logger.warning(f"EPHEMERAL: API error - connection failure: {e}")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e_fb:
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e_fb)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}

    except Exception as e:
        logger.error(f"EPHEMERAL: unexpected error - {e}")
        if fallback_on_error and client:
            try:
                sent = await client.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
                return {"success": True, "ephemeral": False, "fallback_sent": True, "result": sent}
            except Exception as e_fb:
                return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e_fb)}
        return {"success": False, "ephemeral": False, "fallback_sent": False, "error": str(e)}
