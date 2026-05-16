# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import asyncio
import datetime
import logging
import time

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from pyrogram.errors import UserIsBlocked, InputUserDeactivated, FloodWait

from VLCBox.util.base_clients import MainBot
from database.users_chats_db import db
# from database.review_db import review_db  # Temporarily disabled for debugging
from info import ADMINS, LOG_CHANNEL

logger = logging.getLogger(__name__)

# DEBUG: Print to console when plugin is loaded
print("DEBUG: Review Plugin Loading...")

# ─── Constants ────────────────────────────────────────────────────────────────

STAR_LABELS = {
    1: "⭐ 1 Star",
    2: "⭐⭐ 2 Stars",
    3: "⭐⭐⭐ 3 Stars",
    4: "⭐⭐⭐⭐ 4 Stars",
    5: "⭐⭐⭐⭐⭐ 5 Stars",
}

STAR_BARS = {
    1: "⭐",
    2: "⭐⭐",
    3: "⭐⭐⭐",
    4: "⭐⭐⭐⭐",
    5: "⭐⭐⭐⭐⭐",
}

REVIEW_REQUEST_TEXT = (
    "🍿 <b>How was your experience with VLCBox?</b>\n\n"
    "Your feedback helps us improve and serve you better.\n"
    "Tap a star below to rate us — it only takes a second! ✨"
)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def build_star_keyboard() -> InlineKeyboardMarkup:
    """Build the 5-star inline rating keyboard."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"rate_{star}")]
        for star, label in STAR_LABELS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def format_user_name(user) -> str:
    """Extract a display name for the user."""
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip() or "Unknown"


# ─── Testing: /reviewping ──────────────────────────────────────────────────────


@MainBot.on_message(filters.command("reviewping"))
async def cmd_review_ping(client: Client, message: Message):
    """Confirm the review plugin is loaded."""
    print("DEBUG: Received /reviewping")
    await message.reply_text("✅ <b>Review Plugin is Active (Fail-Safe Mode)!</b>", parse_mode=enums.ParseMode.HTML)


# ─── Public: /review ──────────────────────────────────────────────────────────


@MainBot.on_message(filters.command("review") & filters.private)
async def cmd_public_review(client: Client, message: Message):
    """Allows any user to rate the bot manually in PM."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


# ─── Admin: /sendreview ───────────────────────────────────────────────────────


@MainBot.on_message(filters.command("sendreview") & filters.user(ADMINS))
async def cmd_send_review(client: Client, message: Message):
    """Admin command: send the review-request message here."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )
