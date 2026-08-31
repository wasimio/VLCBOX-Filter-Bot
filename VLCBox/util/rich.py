# Don't Remove Credit @vlcbox
# VLCBox - Minimal Telegram Rich Message Proof of Concept API Wrapper

import logging
import aiohttp
from typing import Any, Dict, Optional, Union

from info import BOT_TOKEN, EXPERIMENTAL_BOT_TOKEN

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


async def send_rich_message_api(
    client: Any,
    chat_id: Union[int, str],
    blocks: list,
    reply_markup: Optional[Dict[str, Any]] = None,
    reply_to_message_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Direct Telegram Bot API call to sendRichMessage.
    Sends structured Rich Message blocks without faking via ordinary text.
    """
    token = get_active_bot_token(client)
    if not token:
        return {"success": False, "error": "missing_token", "description": "Bot token is not configured."}

    url = f"https://api.telegram.org/bot{token}/sendRichMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "blocks": blocks
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, json=payload) as resp:
                status_code = resp.status
                try:
                    data = await resp.json()
                except Exception:
                    data = {"description": await resp.text()}

                if resp.status == 200 and data.get("ok"):
                    return {
                        "success": True,
                        "status_code": status_code,
                        "result": data.get("result"),
                        "raw": data
                    }
                else:
                    err_desc = data.get("description", "Unknown Telegram API Error")
                    error_code = data.get("error_code", status_code)
                    logger.warning(f"RICH_API: sendRichMessage failed ({error_code} - {err_desc})")
                    return {
                        "success": False,
                        "status_code": error_code,
                        "error": err_desc,
                        "description": err_desc,
                        "raw": data
                    }
    except Exception as e:
        logger.error(f"RICH_API: Network error calling sendRichMessage: {e}")
        return {
            "success": False,
            "status_code": 0,
            "error": "network_error",
            "description": str(e)
        }
