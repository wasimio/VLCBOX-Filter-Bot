# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Experimental Ephemeral Group Messages Plugin for VLCBox.

Provides:
- /testephemeral: Tests private/ephemeral delivery to the requesting user in groups.
- /ephemeralstatus: Admin-only inspection of ephemeral feature flag and Bot API status.
"""

import logging
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from VLCBox.util.base_clients import MainBot
from VLCBox.util.ephemeral import send_ephemeral, get_active_bot_token
from info import EPHEMERAL_GROUP_MESSAGES, EXPERIMENTAL_BOT_TOKEN, ADMINS

logger = logging.getLogger(__name__)


@MainBot.on_message(filters.command("testephemeral") & filters.incoming)
async def test_ephemeral_command(client: MainBot, message: Message):
    """
    Test command for Telegram Ephemeral / Private Group Messages.
    Only operates in eligible groups/supergroups.
    """
    if not message.from_user:
        return

    # Check chat eligibility
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await message.reply_text(
            "ℹ️ <b>VLCBox Ephemeral Test</b>\n\n"
            "This test is only available inside <b>Groups</b> and <b>Supergroups</b>.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    chat_type_str = "Supergroup" if message.chat.type == enums.ChatType.SUPERGROUP else "Group"

    if not EPHEMERAL_GROUP_MESSAGES:
        await message.reply_text(
            f"🧪 <b>VLCBox Ephemeral Test</b>\n\n"
            f"⚠️ <b>Feature Status:</b> <code>DISABLED</code>\n\n"
            f"The experimental ephemeral feature flag (<code>EPHEMERAL_GROUP_MESSAGES</code>) is currently disabled.\n"
            f"VLCBox is operating in standard mode.",
            parse_mode=enums.ParseMode.HTML
        )
        return

    # Construct test message text
    test_text = (
        f"🧪 <b>VLCBox Ephemeral Test</b>\n\n"
        f"Hello <b>{user_name}</b>! If you can see this message privately, "
        f"the Telegram ephemeral-message integration is working correctly.\n\n"
        f"📊 <b>Diagnostic Information:</b>\n"
        f"• <b>Feature Status:</b> <code>ENABLED</code>\n"
        f"• <b>Chat Type:</b> <code>{chat_type_str}</code>\n"
        f"• <b>Recipient ID:</b> <code>{user_id}</code>\n"
        f"• <b>Engine:</b> <code>Direct Bot API (10.3)</code>"
    )

    test_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Test Acknowledged", callback_data="ephemeral_test_ack")]
    ])

    result = await send_ephemeral(
        client=client,
        chat_id=message.chat.id,
        user_id=user_id,
        text=test_text,
        reply_markup=test_keyboard,
        parse_mode="HTML",
        fallback_on_error=True
    )

    if not result.get("success") and not result.get("fallback_sent"):
        err = result.get("error", "Unknown Error")
        await message.reply_text(
            f"⚠️ <b>Ephemeral messages aren't available in this chat.</b>\n\n"
            f"<i>Reason: {err}</i>\n\n"
            f"VLCBox will continue using the normal message system.",
            parse_mode=enums.ParseMode.HTML
        )


@MainBot.on_message(filters.command("ephemeralstatus") & filters.incoming & filters.user(ADMINS))
async def ephemeral_status_command(client: MainBot, message: Message):
    """
    Admin-only status and diagnostics for Ephemeral Group Messages feature.
    """
    chat_type_str = "Private"
    if message.chat.type == enums.ChatType.SUPERGROUP:
        chat_type_str = "Supergroup"
    elif message.chat.type == enums.ChatType.GROUP:
        chat_type_str = "Group"
    elif message.chat.type == enums.ChatType.CHANNEL:
        chat_type_str = "Channel"

    # Check bot admin status in current chat
    is_admin = "N/A (Private)"
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
        try:
            bot_member = await client.get_chat_member(message.chat.id, "me")
            if bot_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                is_admin = "Yes (Administrator)"
            else:
                is_admin = "No (Member)"
        except Exception:
            is_admin = "Unknown"

    token_source = "EXPERIMENTAL_BOT_TOKEN" if EXPERIMENTAL_BOT_TOKEN else "Standard BOT_TOKEN"
    feature_status = "ENABLED 🟢" if EPHEMERAL_GROUP_MESSAGES else "DISABLED 🔴"

    status_text = (
        f"🧪 <b>VLCBox Experimental Features Status</b>\n\n"
        f"• <b>Ephemeral Messages:</b> <code>{feature_status}</code>\n"
        f"• <b>Implementation:</b> <code>Direct Telegram Bot API (10.3)</code>\n"
        f"• <b>Active Token Source:</b> <code>{token_source}</code>\n"
        f"• <b>Current Chat:</b> <code>{chat_type_str}</code> (<code>{message.chat.id}</code>)\n"
        f"• <b>Bot Admin Rights:</b> <code>{is_admin}</code>\n"
        f"• <b>Eligible Chat Types:</b> <code>Group, Supergroup</code>"
    )

    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML)
