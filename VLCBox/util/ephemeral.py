# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Isolated Telegram Bot API Ephemeral Group Messages Wrapper for VLCBox.

Supports sending private/ephemeral messages to a specific user within
groups and supergroups according to Telegram Bot API 10.2 / 10.3 standards.
"""

import logging
import re
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


def fix_telegram_html(text: str) -> str:
    """
    Clean up common HTML formatting inconsistencies for Telegram Bot API:
    - Fix unquoted href attributes: <a href=http...> -> <a href="http...">
    """
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ""
    return re.sub(r'<a\s+href=([^"\'>\s]+)>', r'<a href="\1">', text)


def serialize_reply_markup(reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """
    Convert Pyrogram InlineKeyboardMarkup / ReplyKeyboardMarkup into Telegram Bot API JSON structure.
    Safely converts bytes to strings to prevent JSON serialization errors.
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


async def send_ephemeral(
    client: Any,
    chat_id: Union[int, str],
    user_id: int,
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]] = None,
    parse_mode: Optional[str] = "HTML",
    disable_web_page_preview: bool = True,
    fallback_on_error: bool = True
) -> Dict[str, Any]:
    """
    Send an ephemeral / private message to a specific user inside a group or supergroup.
    """
    # 1. Check Feature Flag
    if not EPHEMERAL_GROUP_MESSAGES:
        logger.info("EPHEMERAL: unsupported - feature flag EPHEMERAL_GROUP_MESSAGES is disabled")
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

    clean_text = fix_telegram_html(text)
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": clean_text,
        "disable_web_page_preview": disable_web_page_preview,
        "ephemeral_message_parameters": {
            "receiver_user_id": int(user_id)
        }
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

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

                error_desc = data.get("description", "Unknown Telegram API Error")
                error_code = data.get("error_code", resp.status)
                logger.warning(f"EPHEMERAL: API error - code={error_code}, desc={error_desc}")

                # If HTML entity parsing failed, retry once without parse_mode
                if parse_mode and ("can't parse entities" in error_desc.lower() or "entity" in error_desc.lower()):
                    logger.info(f"EPHEMERAL: HTML entity error, retrying without parse_mode")
                    retry_payload = payload.copy()
                    retry_payload.pop("parse_mode", None)
                    async with session.post(api_url, json=retry_payload) as retry_resp:
                        retry_data = await retry_resp.json()
                        if retry_data.get("ok"):
                            logger.info(f"EPHEMERAL: success on plain text retry - chat_id={chat_id}, user_id={user_id}")
                            return {"success": True, "ephemeral": True, "fallback_sent": False, "result": retry_data.get("result")}

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


async def send_ephemeral_photo(
    client: Any,
    chat_id: Union[int, str],
    user_id: int,
    photo: str,
    caption: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, Dict[str, Any]]] = None,
    parse_mode: Optional[str] = "HTML"
) -> Dict[str, Any]:
    """
    Send an ephemeral photo with caption to a specific user inside a group or supergroup.
    If sendPhoto fails (e.g. invalid URL, dimension error, caption too long), attempts fallback to ephemeral text.
    """
    token = get_active_bot_token(client)
    if not token or not photo or len(caption) > 1024:
        return await send_ephemeral(client, chat_id, user_id, caption, reply_markup, parse_mode, fallback_on_error=False)

    clean_caption = fix_telegram_html(caption)
    api_url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "photo": photo,
        "caption": clean_caption,
        "ephemeral_message_parameters": {
            "receiver_user_id": int(user_id)
        }
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    serialized_markup = serialize_reply_markup(reply_markup)
    if serialized_markup:
        payload["reply_markup"] = serialized_markup

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(api_url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(f"EPHEMERAL: photo success - chat_id={chat_id}, user_id={user_id}")
                    return {"success": True, "ephemeral": True, "result": data.get("result")}

                error_desc = data.get("description", "Unknown Telegram API Error")
                logger.warning(f"EPHEMERAL: sendPhoto API error - {error_desc}, falling back to ephemeral text")

                # If HTML entity error, retry photo once without parse_mode
                if parse_mode and ("can't parse entities" in error_desc.lower() or "entity" in error_desc.lower()):
                    retry_payload = payload.copy()
                    retry_payload.pop("parse_mode", None)
                    async with session.post(api_url, json=retry_payload) as retry_resp:
                        retry_data = await retry_resp.json()
                        if retry_data.get("ok"):
                            logger.info(f"EPHEMERAL: photo success on plain text retry - chat_id={chat_id}, user_id={user_id}")
                            return {"success": True, "ephemeral": True, "result": retry_data.get("result")}

                # Fallback to ephemeral text delivery
                return await send_ephemeral(
                    client=client,
                    chat_id=chat_id,
                    user_id=user_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    fallback_on_error=False
                )
    except Exception as e:
        logger.warning(f"EPHEMERAL: sendPhoto network error - {e}, falling back to ephemeral text")
        return await send_ephemeral(
            client=client,
            chat_id=chat_id,
            user_id=user_id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            fallback_on_error=False
        )


async def send_group_search_result(
    client: Any,
    message: Any,
    reply_msg: Any,
    text: str,
    photo: Optional[str] = None,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    settings: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Unified movie search delivery abstraction.

    Decides whether to deliver as an Ephemeral result (visible only to requesting user)
    or standard Public result based on global feature flag and per-group setting.

    Ensures exactly ONE result message is delivered (no duplicates) and provides safe fallback.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    is_group = message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
    private_results_enabled = bool(settings and settings.get("private_results", False))

    # Check if Ephemeral delivery should be used
    if EPHEMERAL_GROUP_MESSAGES and is_group and private_results_enabled and user_id != 0:
        logger.info(f"EPHEMERAL_SEARCH: attempt - chat_id={chat_id}, user_id={user_id}")

        ephemeral_res = None
        if photo:
            ephemeral_res = await send_ephemeral_photo(
                client=client,
                chat_id=chat_id,
                user_id=user_id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            # If photo failed, try text ephemeral delivery before falling back to public!
            if not ephemeral_res or not ephemeral_res.get("success"):
                logger.warning(f"EPHEMERAL_SEARCH: photo ephemeral failed, attempting text ephemeral delivery")
                ephemeral_res = await send_ephemeral(
                    client=client,
                    chat_id=chat_id,
                    user_id=user_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    fallback_on_error=False
                )
        else:
            ephemeral_res = await send_ephemeral(
                client=client,
                chat_id=chat_id,
                user_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                fallback_on_error=False
            )

        if ephemeral_res and ephemeral_res.get("success"):
            logger.info(f"EPHEMERAL_SEARCH: success - chat_id={chat_id}, user_id={user_id}")
            # Clean up the public "Searching For..." placeholder
            if reply_msg:
                try:
                    await reply_msg.delete()
                except Exception:
                    pass
            return ephemeral_res.get("result")

        # Ephemeral delivery failed -> Log and fall back to public delivery
        err_msg = ephemeral_res.get("error", "Unknown error") if ephemeral_res else "No response"
        logger.warning(f"EPHEMERAL_SEARCH: fallback - chat_id={chat_id}, user_id={user_id}, reason: {err_msg}")

    # Standard Public Delivery (Fallback or default)
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
            logger.warning(f"EPHEMERAL_SEARCH: public photo send failed ({e}), falling back to text")
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
