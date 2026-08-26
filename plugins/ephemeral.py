# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Experimental Ephemeral Group Messages Plugin for VLCBox.

Provides:
- /testephemeral: Tests private/ephemeral delivery to the requesting user in groups.
- /ephemeralstatus: Admin-only inspection of ephemeral feature flag and Bot API status.
- /private_results: Admin-only command to toggle ephemeral movie results for a group.
- /ephemeral_results: Alias for /private_results.
"""

import logging
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from VLCBox.util.base_clients import MainBot
from VLCBox.util.ephemeral import send_ephemeral, get_active_bot_token
from utils import get_settings, save_group_settings
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


@MainBot.on_message(filters.command(["private_results", "ephemeral_results"]) & filters.incoming)
async def toggle_private_results_command(client: MainBot, message: Message):
    """
    Group Admin command to toggle private/ephemeral movie search results.
    """
    if not message.from_user:
        return

    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text(
            "ℹ️ This setting is only applicable inside <b>Groups</b> and <b>Supergroups</b>.",
            parse_mode=enums.ParseMode.HTML
        )

    user_id = message.from_user.id
    try:
        member = await client.get_chat_member(message.chat.id, user_id)
        is_admin = (
            member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
            or user_id in ADMINS
            or str(user_id) in ADMINS
        )
    except Exception:
        is_admin = user_id in ADMINS or str(user_id) in ADMINS

    if not is_admin:
        return await message.reply_text(
            "❌ <b>You must be a group administrator to change this setting.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    settings = await get_settings(message.chat.id)
    current_status = settings.get("private_results", False)

    args = message.command[1].lower() if len(message.command) > 1 else ""

    if args in ["on", "enable", "true", "1"]:
        await save_group_settings(message.chat.id, "private_results", True)
        return await message.reply_text(
            "✅ <b>Private Movie Results: ENABLED 🟢</b>\n\n"
            "Movie search results in this group will now be sent as <b>ephemeral messages</b> visible only to the user who requested them.\n"
            "<i>(Global safety switch EPHEMERAL_GROUP_MESSAGES must also be active)</i>",
            parse_mode=enums.ParseMode.HTML
        )
    elif args in ["off", "disable", "false", "0"]:
        await save_group_settings(message.chat.id, "private_results", False)
        return await message.reply_text(
            "❌ <b>Private Movie Results: DISABLED 🔴</b>\n\n"
            "Movie search results in this group will now be sent as standard <b>public messages</b>.",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        status_str = "ENABLED 🟢" if current_status else "DISABLED 🔴"
        btn = [
            [
                InlineKeyboardButton(
                    "🔴 Disable" if current_status else "🟢 Enable",
                    callback_data=f"setgs#private_results#{current_status}#{message.chat.id}"
                )
            ]
        ]
        return await message.reply_text(
            f"⚙️ <b>Private Movie Results Setting</b>\n\n"
            f"Current Status: <b>{status_str}</b>\n\n"
            f"• <b>Enabled:</b> Movie search results are delivered privately (only requesting user sees them).\n"
            f"• <b>Disabled:</b> Movie search results are delivered publicly in the group.\n\n"
            f"<b>Commands:</b>\n"
            f"<code>/private_results on</code> — Turn ON\n"
            f"<code>/private_results off</code> — Turn OFF",
            reply_markup=InlineKeyboardMarkup(btn),
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
    group_setting_str = "N/A"
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
        try:
            bot_member = await client.get_chat_member(message.chat.id, "me")
            if bot_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                is_admin = "Yes (Administrator)"
            else:
                is_admin = "No (Member)"
        except Exception:
            is_admin = "Unknown"

        try:
            settings = await get_settings(message.chat.id)
            group_setting_str = "ENABLED 🟢" if settings.get("private_results", False) else "DISABLED 🔴"
        except Exception:
            group_setting_str = "Unknown"

    token_source = "EXPERIMENTAL_BOT_TOKEN" if EXPERIMENTAL_BOT_TOKEN else "Standard BOT_TOKEN"
    feature_status = "ENABLED 🟢" if EPHEMERAL_GROUP_MESSAGES else "DISABLED 🔴"

    status_text = (
        f"🧪 <b>VLCBox Experimental Features Status</b>\n\n"
        f"• <b>Global Ephemeral Switch:</b> <code>{feature_status}</code>\n"
        f"• <b>Group Private Results Setting:</b> <code>{group_setting_str}</code>\n"
        f"• <b>Implementation:</b> <code>Direct Telegram Bot API (10.3)</code>\n"
        f"• <b>Active Token Source:</b> <code>{token_source}</code>\n"
        f"• <b>Current Chat:</b> <code>{chat_type_str}</code> (<code>{message.chat.id}</code>)\n"
        f"• <b>Bot Admin Rights:</b> <code>{is_admin}</code>\n"
        f"• <b>Eligible Chat Types:</b> <code>Group, Supergroup</code>"
    )

    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML)
