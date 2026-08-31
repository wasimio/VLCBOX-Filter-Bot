# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Experimental Telegram Rich Message Plugin for VLCBox.

Bot API 10.3:
- Uses InputRichBlockButtons with RichMessageButton inside rich_message.blocks
- Buttons are PART OF the rich message, NOT a traditional reply_markup keyboard
- Uses InputRichBlockDetails for collapsible storyline
- Uses InputRichBlockTable for file listing
- RichText fields use plain strings (not nested type objects)
"""

import html
import logging
from pyrogram import filters, enums, Client
from pyrogram.types import Message, CallbackQuery
from VLCBox.util.base_clients import MainBot
from VLCBox.util.rich import send_rich_message_api
from info import RICH_MOVIE_RESULTS

logger = logging.getLogger(__name__)
print(">>> VLCBox: plugins.rich successfully loaded <<<")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGNOSTIC
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(filters.command(["richtestping", "richping"]) & filters.incoming, group=1)
async def rich_test_ping_command(client, message: Message):
    """Diagnostic — does NOT call the Rich Message API."""
    logger.info(f"RICH_DIAGNOSTIC: /richtestping in chat_id={message.chat.id}")
    await message.reply_text("RICH PLUGIN LOADED ✅")


# ─────────────────────────────────────────────────────────────────────────────
# /testrich — Minimal PoC: heading + paragraph + divider + buttons block
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(filters.command("testrich") & filters.incoming, group=1)
async def test_rich_command(client, message: Message):
    """
    Minimal Rich Message test.
    Buttons are inside blocks (InputRichBlockButtons), NOT in reply_markup.
    """
    chat_id = message.chat.id
    logger.info(f"RICH_TEST: /testrich in chat_id={chat_id}")

    blocks = [
        {
            "type": "heading",
            "text": "🎬 VLCBox Rich Message Test",
            "size": 1
        },
        {
            "type": "paragraph",
            "text": "This is a genuine Telegram Rich Message. The button below is INSIDE the rich message blocks."
        },
        {
            "type": "divider"
        },
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "✅ TEST BUTTON",
                    "style": "primary",
                    "callback_data": "rich_test_btn_clicked"
                }
            ]
        }
    ]

    try:
        res = await send_rich_message_api(
            client=client,
            chat_id=chat_id,
            blocks=blocks,
            reply_to_message_id=message.id
        )
        if not res.get("success"):
            error_desc = res.get("description", res.get("error", "Unknown API error"))
            status_code = res.get("status_code", "Unknown")
            logger.warning(f"RICH_TEST: failure {status_code} - {error_desc}")
            await message.reply_text(
                f"⚠️ <b>Rich Message API Test Result</b>\n\n"
                f"<b>Status:</b> <code>Rejected / Failed</code>\n"
                f"<b>HTTP Code:</b> <code>{status_code}</code>\n"
                f"<b>API Response:</b> <code>{error_desc}</code>\n\n"
                f"<i>RICH_MOVIE_RESULTS={RICH_MOVIE_RESULTS}</i>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            logger.info(f"RICH_TEST: success for chat_id={chat_id}")
    except Exception as e:
        logger.error(f"RICH_TEST: exception: {e}", exc_info=True)
        await message.reply_text(
            f"❌ <b>Exception:</b> <code>{html.escape(str(e))}</code>",
            parse_mode=enums.ParseMode.HTML
        )


# ─────────────────────────────────────────────────────────────────────────────
# /richmovie — Full Rich Movie UI with native InputRichBlockButtons
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(filters.command("richmovie") & filters.incoming, group=1)
async def rich_movie_prototype_command(client, message: Message):
    """
    Static Rich Movie UI Prototype using Bot API 10.3 native blocks.

    Structure (all inside rich_message.blocks — NO reply_markup keyboard):
    1. heading (movie title, size=1)
    2. paragraph (metadata)
    3. divider
    4. details block (collapsible storyline)
    5. divider
    6. buttons block (QUALITY + LANGUAGE)
    7. divider
    8. heading (available files, size=2)
    9. table (files, compact + bordered + striped)
    10. divider
    11. buttons block (WATCH + DOWNLOAD)
    12. buttons block (SEND ALL FILES)
    13. divider
    14. footer
    """
    chat_id = message.chat.id
    logger.info(f"RICH_MOVIE: /richmovie in chat_id={chat_id}")

    blocks = [
        # ── 1. Movie Title ──────────────────────────────────────────────────
        {
            "type": "heading",
            "text": "🎬 SPIDER-MAN: NO WAY HOME",
            "size": 1
        },

        # ── 2. Metadata paragraph ───────────────────────────────────────────
        {
            "type": "paragraph",
            "text": "2021  •  Action  •  Adventure  •  Sci-Fi\n⭐ 8.2 / 10  •  2h 28m"
        },

        # ── 3. Divider ──────────────────────────────────────────────────────
        {"type": "divider"},

        # ── 4. Storyline — collapsible details block ─────────────────────────
        # InputRichBlockDetails: summary is always visible; blocks expand on tap
        {
            "type": "details",
            "summary": "📖 STORYLINE  ▾ READ MORE",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "With Spider-Man's identity now revealed, our friendly neighborhood "
                        "web-slinger is unmasked and no longer able to separate his normal life "
                        "from the high-stakes of being a Super Hero. When he asks for help from "
                        "Doctor Strange, the stakes become even more dangerous, forcing him to "
                        "discover what it truly means to be Spider-Man."
                    )
                }
            ]
        },

        # ── 5. Divider ──────────────────────────────────────────────────────
        {"type": "divider"},

        # ── 6. Button Row 1: QUALITY + LANGUAGE ─────────────────────────────
        # InputRichBlockButtons — native Rich Message buttons, NOT reply_markup
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "🎞 QUALITY",
                    "style": "primary",
                    "callback_data": "rich_movie_quality"
                },
                {
                    "text": "🌐 LANGUAGE",
                    "style": "primary",
                    "callback_data": "rich_movie_language"
                }
            ]
        },

        # ── 7. Divider ──────────────────────────────────────────────────────
        {"type": "divider"},

        # ── 8. Available Files heading ───────────────────────────────────────
        {
            "type": "heading",
            "text": "📁 AVAILABLE FILES",
            "size": 2
        },

        # ── 9. Files table (InputRichBlockTable) ────────────────────────────
        # cells is a 2D array of InputRichBlockTableCell objects
        # text field inside each cell is a plain string
        {
            "type": "table",
            "is_compact": True,
            "is_bordered": True,
            "is_striped": True,
            "cells": [
                [
                    {"text": "Quality", "is_header": True},
                    {"text": "Language", "is_header": True},
                    {"text": "Size", "is_header": True}
                ],
                [
                    {"text": "1080p"},
                    {"text": "Hindi"},
                    {"text": "3.2 GB"}
                ],
                [
                    {"text": "1080p"},
                    {"text": "English"},
                    {"text": "3.5 GB"}
                ],
                [
                    {"text": "720p"},
                    {"text": "Hindi"},
                    {"text": "1.8 GB"}
                ],
                [
                    {"text": "720p"},
                    {"text": "English"},
                    {"text": "2.0 GB"}
                ]
            ]
        },

        # ── 10. Divider ─────────────────────────────────────────────────────
        {"type": "divider"},

        # ── 11. Button Row 2: WATCH + DOWNLOAD ──────────────────────────────
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "▶ WATCH",
                    "style": "success",
                    "callback_data": "rich_movie_watch"
                },
                {
                    "text": "⬇ DOWNLOAD",
                    "style": "primary",
                    "callback_data": "rich_movie_download"
                }
            ]
        },

        # ── 12. Button Row 3: SEND ALL FILES ────────────────────────────────
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "📂 SEND ALL FILES",
                    "style": "primary",
                    "callback_data": "rich_movie_send_all"
                }
            ]
        },

        # ── 13. Divider ─────────────────────────────────────────────────────
        {"type": "divider"},

        # ── 14. Footer ──────────────────────────────────────────────────────
        {
            "type": "footer",
            "text": "Requested by RICK  •  Powered by VLCBox"
        }
    ]

    try:
        # NO reply_markup — all buttons live inside blocks above
        res = await send_rich_message_api(
            client=client,
            chat_id=chat_id,
            blocks=blocks,
            reply_to_message_id=message.id
        )
        if not res.get("success"):
            error_desc = res.get("description", res.get("error", "Unknown API error"))
            status_code = res.get("status_code", "Unknown")
            logger.warning(f"RICH_MOVIE: failure {status_code} - {error_desc}")
            await message.reply_text(
                f"⚠️ <b>Rich Movie Prototype Result</b>\n\n"
                f"<b>Status:</b> <code>Rejected / Failed</code>\n"
                f"<b>HTTP Code:</b> <code>{status_code}</code>\n"
                f"<b>API Response:</b> <code>{error_desc}</code>\n\n"
                f"<i>RICH_MOVIE_RESULTS={RICH_MOVIE_RESULTS}</i>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            logger.info(f"RICH_MOVIE: success for chat_id={chat_id}")
    except Exception as e:
        logger.error(f"RICH_MOVIE: exception: {e}", exc_info=True)
        await message.reply_text(
            f"❌ <b>Exception:</b> <code>{html.escape(str(e))}</code>",
            parse_mode=enums.ParseMode.HTML
        )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK HANDLERS — for all Rich Message buttons
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_callback_query(filters.regex(r"^rich_test_btn_clicked$"), group=1)
async def rich_test_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_test_btn_clicked from user={query.from_user.id}")
    await query.answer("✅ Rich Message button works!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_quality$"), group=1)
async def rich_movie_quality_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_movie_quality from user={query.from_user.id}")
    await query.answer("🎞 Quality button works! (prototype)", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_language$"), group=1)
async def rich_movie_language_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_movie_language from user={query.from_user.id}")
    await query.answer("🌐 Language button works! (prototype)", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_watch$"), group=1)
async def rich_movie_watch_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_movie_watch from user={query.from_user.id}")
    await query.answer("▶ Watch button works! (prototype)", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_download$"), group=1)
async def rich_movie_download_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_movie_download from user={query.from_user.id}")
    await query.answer("⬇ Download button works! (prototype)", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_send_all$"), group=1)
async def rich_movie_send_all_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_movie_send_all from user={query.from_user.id}")
    await query.answer("📂 Send All Files button works! (prototype)", show_alert=True)
