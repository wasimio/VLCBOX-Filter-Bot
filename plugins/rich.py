# Don't Remove Credit @vlcbox
# Subscribe Telegram Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Experimental Telegram Rich Message Plugin for VLCBox.
Bot API 10.3 — fully native Rich Message blocks.

Layout:
  heading (size=2) → metadata → photo (landscape) → details (storyline, collapsed)
  → buttons row 1 (quality/language) → heading (size=4) → compact table
  → buttons row 2 (watch/download) → buttons row 3 (send all) → footer

All buttons are InputRichBlockButtons — NO reply_markup keyboard.
"""

import html
import logging
from pyrogram import filters, enums, Client
from pyrogram.types import Message, CallbackQuery
from VLCBox.util.base_clients import MainBot
from VLCBox.util.rich import send_rich_message_api
from info import RICH_MOVIE_RESULTS

logger = logging.getLogger(__name__)
print(">>> VLCBox: plugins.rich loaded <<<")

# Landscape banner for Spider-Man: No Way Home (TMDb 16:9 backdrop)
_SPIDERMAN_BANNER = (
    "https://image.tmdb.org/t/p/w1280/"
    "1g0dhYtq4irTY1GPXvft6k4YLjm.jpg"
)


# ─────────────────────────────────────────────────────────────────────────────
# DIAGNOSTIC
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(
    filters.command(["richtestping", "richping"]) & filters.incoming, group=1
)
async def rich_test_ping_command(client, message: Message):
    """Diagnostic — does NOT call the Rich Message API."""
    logger.info(f"RICH_DIAGNOSTIC: /richtestping chat_id={message.chat.id}")
    await message.reply_text("✅ RICH PLUGIN LOADED")


# ─────────────────────────────────────────────────────────────────────────────
# /testrich — Minimal proof-of-concept
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(
    filters.command("testrich") & filters.incoming, group=1
)
async def test_rich_command(client, message: Message):
    """Minimal test: heading + paragraph + divider + buttons block."""
    chat_id = message.chat.id
    logger.info(f"RICH_TEST: /testrich chat_id={chat_id}")

    blocks = [
        {"type": "heading", "text": "VLCBox Rich Message Test", "size": 2},
        {"type": "paragraph", "text": "Telegram Bot API 10.3 — native Rich Message with inline buttons."},
        {"type": "divider"},
        {
            "type": "buttons",
            "buttons": [
                {"text": "✅ Tap to Test", "style": "primary", "callback_data": "rich_test_btn_clicked"}
            ]
        }
    ]

    try:
        res = await send_rich_message_api(
            client=client, chat_id=chat_id, blocks=blocks,
            reply_to_message_id=message.id
        )
        if not res.get("success"):
            err = res.get("description", res.get("error", "Unknown error"))
            code = res.get("status_code", "?")
            await message.reply_text(
                f"⚠️ <b>Rich Test Failed</b>\n<code>{code}: {err}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            logger.info(f"RICH_TEST: success chat_id={chat_id}")
    except Exception as e:
        logger.error(f"RICH_TEST: {e}", exc_info=True)
        await message.reply_text(
            f"❌ <code>{html.escape(str(e))}</code>",
            parse_mode=enums.ParseMode.HTML
        )


# ─────────────────────────────────────────────────────────────────────────────
# /richmovie — Polished Rich Movie card
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_message(
    filters.command("richmovie") & filters.incoming, group=1
)
async def rich_movie_prototype_command(client, message: Message):
    """
    Static Rich Movie UI prototype — Spider-Man: No Way Home.
    All buttons live inside rich_message.blocks (no reply_markup keyboard).
    """
    chat_id = message.chat.id
    logger.info(f"RICH_MOVIE: /richmovie chat_id={chat_id}")

    # ── Build the photo block (landscape banner) ─────────────────────────────
    # InputRichBlockPhoto: photo field is InputMediaPhoto {type, media}
    photo_block = {
        "type": "photo",
        "photo": {
            "type": "photo",
            "media": _SPIDERMAN_BANNER
        }
    }

    blocks = [
        # ─ 1. Movie title (size=2 — prominent but not massive) ─────────────
        {
            "type": "heading",
            "text": "Spider-Man: No Way Home",
            "size": 2
        },

        # ─ 2. Compact metadata row ─────────────────────────────────────────
        {
            "type": "paragraph",
            "text": "2021  ·  Action · Adventure · Sci-Fi  ·  ⭐ 8.2  ·  2h 28m"
        },

        # ─ 3. Landscape banner image ────────────────────────────────────────
        photo_block,

        # ─ 4. Collapsible storyline (InputRichBlockDetails) ─────────────────
        {
            "type": "details",
            "summary": "📖 Storyline",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": (
                        "With Spider-Man's identity now revealed, Peter Parker is no longer "
                        "able to separate his normal life from the high-stakes of being a "
                        "Super Hero. When he asks Doctor Strange for help, the stakes become "
                        "even more dangerous, forcing him to discover what it truly means "
                        "to be Spider-Man."
                    )
                }
            ]
        },

        # ─ 5. Action row 1: Quality + Language ──────────────────────────────
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "🎞 Quality",
                    "style": "primary",
                    "callback_data": "rich_movie_quality"
                },
                {
                    "text": "🌐 Language",
                    "style": "primary",
                    "callback_data": "rich_movie_language"
                }
            ]
        },

        # ─ 6. Available files heading (size=4 — small, label-like) ──────────
        {
            "type": "heading",
            "text": "📁 Available Files",
            "size": 4
        },

        # ─ 7. File table (compact + bordered) ───────────────────────────────
        {
            "type": "table",
            "is_compact": True,
            "is_bordered": True,
            "is_striped": True,
            "cells": [
                [
                    {"text": "Quality",  "is_header": True},
                    {"text": "Language", "is_header": True},
                    {"text": "Size",     "is_header": True}
                ],
                [{"text": "1080p"}, {"text": "Hindi"},   {"text": "3.2 GB"}],
                [{"text": "1080p"}, {"text": "English"}, {"text": "3.5 GB"}],
                [{"text": "720p"},  {"text": "Hindi"},   {"text": "1.8 GB"}],
                [{"text": "720p"},  {"text": "English"}, {"text": "2.0 GB"}]
            ]
        },

        # ─ 8. Action row 2: Watch + Download ────────────────────────────────
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "▶ Watch",
                    "style": "success",
                    "callback_data": "rich_movie_watch"
                },
                {
                    "text": "⬇ Download",
                    "style": "primary",
                    "callback_data": "rich_movie_download"
                }
            ]
        },

        # ─ 9. Action row 3: Send All ─────────────────────────────────────────
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "📂 Send All Files",
                    "style": "primary",
                    "callback_data": "rich_movie_send_all"
                }
            ]
        },

        # ─ 10. Subtle footer ─────────────────────────────────────────────────
        {
            "type": "footer",
            "text": "Requested by RICK  ·  Powered by VLCBox"
        }
    ]

    try:
        # No reply_markup — all interaction is through Rich button blocks above
        res = await send_rich_message_api(
            client=client,
            chat_id=chat_id,
            blocks=blocks,
            reply_to_message_id=message.id
        )

        if not res.get("success"):
            err = res.get("description", res.get("error", "Unknown error"))
            code = res.get("status_code", "?")
            logger.warning(f"RICH_MOVIE: API failure {code} — {err}")

            # If photo block fails, retry without it
            if "photo" in str(err).lower() or "InputRichBlockPhoto" in str(err):
                logger.info("RICH_MOVIE: retrying without photo block")
                blocks_no_photo = [b for b in blocks if b.get("type") != "photo"]
                res2 = await send_rich_message_api(
                    client=client, chat_id=chat_id,
                    blocks=blocks_no_photo,
                    reply_to_message_id=message.id
                )
                if res2.get("success"):
                    logger.info("RICH_MOVIE: success without photo block")
                    return
                err = res2.get("description", res2.get("error", err))
                code = res2.get("status_code", code)

            await message.reply_text(
                f"⚠️ <b>Rich Movie Result</b>\n\n"
                f"<b>Status:</b> <code>Rejected / Failed</code>\n"
                f"<b>HTTP:</b> <code>{code}</code>\n"
                f"<b>API:</b> <code>{err}</code>\n\n"
                f"<i>RICH_MOVIE_RESULTS={RICH_MOVIE_RESULTS}</i>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            logger.info(f"RICH_MOVIE: success chat_id={chat_id}")
    except Exception as e:
        logger.error(f"RICH_MOVIE: exception {e}", exc_info=True)
        await message.reply_text(
            f"❌ <b>Exception:</b> <code>{html.escape(str(e))}</code>",
            parse_mode=enums.ParseMode.HTML
        )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK HANDLERS — native Rich Message button callbacks
# ─────────────────────────────────────────────────────────────────────────────

@MainBot.on_callback_query(filters.regex(r"^rich_test_btn_clicked$"), group=1)
async def rich_test_callback_handler(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: rich_test_btn_clicked user={query.from_user.id}")
    await query.answer("✅ Rich Message button works!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_quality$"), group=1)
async def rich_movie_quality_cb(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: quality user={query.from_user.id}")
    await query.answer("🎞 Quality filter — coming soon!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_language$"), group=1)
async def rich_movie_language_cb(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: language user={query.from_user.id}")
    await query.answer("🌐 Language filter — coming soon!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_watch$"), group=1)
async def rich_movie_watch_cb(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: watch user={query.from_user.id}")
    await query.answer("▶ Watch — coming soon!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_download$"), group=1)
async def rich_movie_download_cb(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: download user={query.from_user.id}")
    await query.answer("⬇ Download — coming soon!", show_alert=True)


@MainBot.on_callback_query(filters.regex(r"^rich_movie_send_all$"), group=1)
async def rich_movie_send_all_cb(client: Client, query: CallbackQuery):
    logger.info(f"RICH_CB: send_all user={query.from_user.id}")
    await query.answer("📂 Send All Files — coming soon!", show_alert=True)
