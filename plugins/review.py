# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import asyncio
import datetime
import logging

from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from pyrogram.errors import UserIsBlocked, InputUserDeactivated, FloodWait

from VLCBox.util.base_clients import MainBot
from database.users_chats_db import db
from database.review_db import review_db
from info import ADMINS, LOG_CHANNEL

logger = logging.getLogger(__name__)

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

# ─── Commands ─────────────────────────────────────────────────────────────────

@MainBot.on_message(filters.command("reviewping"))
async def cmd_review_ping(client: Client, message: Message):
    """Test command to verify the plugin is active."""
    await message.reply_text("✅ <b>Review Plugin is Active!</b>", parse_mode=enums.ParseMode.HTML)


@MainBot.on_message(filters.command("review") & filters.private)
async def cmd_public_review(client: Client, message: Message):
    """Allows any user to rate the bot manually in PM."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


@MainBot.on_message(filters.command("sendreview") & filters.user(ADMINS))
async def cmd_send_review(client: Client, message: Message):
    """Admin command: send the review-request message here."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


@MainBot.on_message(filters.command("broadcastreview") & filters.user(ADMINS))
async def cmd_broadcast_review(client: Client, message: Message):
    """Admin command: broadcast the review-request message to ALL bot users."""
    sts = await message.reply_text(
        "🚀 <b>Preparing Review Broadcast…</b>\n<i>Please wait, this might take a while.</i>",
        parse_mode=enums.ParseMode.HTML,
    )

    users = await db.get_all_users()
    total = await db.total_users_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0

    async for user in users:
        user_id = user["id"]
        try:
            await client.send_message(
                chat_id=user_id,
                text=REVIEW_REQUEST_TEXT,
                reply_markup=build_star_keyboard(),
                parse_mode=enums.ParseMode.HTML,
            )
            done += 1
        except UserIsBlocked:
            blocked += 1
        except InputUserDeactivated:
            deleted += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await client.send_message(
                chat_id=user_id,
                text=REVIEW_REQUEST_TEXT,
                reply_markup=build_star_keyboard(),
                parse_mode=enums.ParseMode.HTML,
            )
            done += 1
        except Exception as e:
            logger.error(f"Review Broadcast failed for {user_id}: {e}")
            failed += 1

        if (done + blocked + deleted + failed) % 100 == 0:
            await sts.edit_text(
                f"🚀 <b>Review Broadcast in Progress…</b>\n\n"
                f"✅ Done: {done}\n"
                f"🚫 Blocked: {blocked}\n"
                f"👻 Deleted: {deleted}\n"
                f"⚠️ Failed: {failed}\n\n"
                f"<i>Progress: {((done + blocked + deleted + failed) / total) * 100:.1f}%</i>",
                parse_mode=enums.ParseMode.HTML,
            )

    await sts.edit_text(
        f"🏁 <b>Review Broadcast Completed!</b>\n\n"
        f"✅ Successfully Sent: {done}\n"
        f"🚫 Blocked: {blocked}\n"
        f"👻 Deleted: {deleted}\n"
        f"⚠️ Failed: {failed}",
        parse_mode=enums.ParseMode.HTML,
    )


@MainBot.on_message(filters.command("reviewstats") & filters.user(ADMINS))
async def cmd_review_stats(client: Client, message: Message):
    """Admin command: show rating distribution, average, and latest reviews."""
    loading = await message.reply_text("📊 <i>Fetching stats…</i>", parse_mode=enums.ParseMode.HTML)

    total = await review_db.total_ratings_count()
    if total == 0:
        return await loading.edit_text("❌ <b>No ratings found in the database yet.</b>", parse_mode=enums.ParseMode.HTML)

    avg = await review_db.average_rating()
    dist = await review_db.distribution()
    latest = await review_db.latest_reviews(5)

    stats_text = f"📊 <b>VLCBox Review Statistics</b>\n"
    stats_text += f"━━━━━━━━━━━━━━━━━━━━\n"
    stats_text += f"🌟 <b>Average Rating: {avg} / 5.0</b>\n"
    stats_text += f"👥 <b>Total Ratings: {total}</b>\n\n"

    stats_text += "<b>Distribution:</b>\n"
    for stars in range(5, 0, -1):
        count = dist.get(stars, 0)
        percent = (count / total) * 100 if total > 0 else 0
        bar = "▰" * int(percent / 10) + "▱" * (10 - int(percent / 10))
        stats_text += f"{stars} ⭐ {bar} {count} ({percent:.1f}%)\n"

    if latest:
        stats_text += f"\n📝 <b>Latest Written Reviews:</b>\n"
        for rev in latest:
            text_snippet = rev['review_text'][:50] + "…" if len(rev['review_text']) > 50 else rev['review_text']
            stats_text += f"• <b>{rev['stars']}⭐</b>: <i>\"{text_snippet}\"</i>\n"

    await loading.edit_text(stats_text, parse_mode=enums.ParseMode.HTML)


# ─── Callbacks & Messages ─────────────────────────────────────────────────────

@MainBot.on_callback_query(filters.regex(r"^rate_(\d)$"))
async def cb_rate(client: Client, query: CallbackQuery):
    """Handle star rating button taps."""
    user = query.from_user
    stars = int(query.data.split("_")[1])

    # Check if user already rated
    if await review_db.has_rated(user.id):
        return await query.answer("⚠️ You have already submitted a rating! Thanks for your support.", show_alert=True)

    # Save rating
    success = await review_db.save_rating(user.id, format_user_name(user), stars)
    if not success:
        return await query.answer("❌ Error saving rating. Please try again later.", show_alert=True)

    await query.answer(f"Thanks for your {stars}-star rating! ❤️", show_alert=False)

    # Set pending state for text review
    await review_db.set_pending(user.id, stars)

    # Ask for text feedback
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏩ Skip & Finish", callback_data="review_skip")]]
    )

    await query.message.edit_text(
        f"<b>Thanks for rating VLCBox {STAR_BARS[stars]}!</b> ❤️\n\n"
        f"Would you like to share a quick text review or feedback? Your suggestions help us grow!\n\n"
        f"<i>Just send your feedback as a text message below.</i>",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
    )


@MainBot.on_callback_query(filters.regex(r"^review_skip$"))
async def cb_review_skip(client: Client, query: CallbackQuery):
    """User decided to skip the written review."""
    user = query.from_user
    pending = await review_db.get_pending(user.id)

    if pending:
        # Forward to log channel even without text
        stars = pending['stars']
        log_msg = (
            f"🌟 <b>New Rating Received!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.mention} (<code>{user.id}</code>)\n"
            f"⭐ <b>Rating:</b> {STAR_BARS[stars]}\n"
            f"📝 <b>Feedback:</b> <i>No text provided</i>\n"
            f"⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await client.send_message(LOG_CHANNEL, log_msg, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send log: {e}")
        await review_db.clear_pending(user.id)

    await query.message.edit_text(
        "<b>Thank you for your feedback!</b> ❤️\n\n"
        "Your rating has been saved. We appreciate your support!",
        parse_mode=enums.ParseMode.HTML,
    )


# Use group=-1 to ensure it runs before pm_filter's generic search (group 0)
@MainBot.on_message(filters.private & filters.text & ~filters.command(["start", "help", "reviewstats", "sendreview", "broadcastreview", "skip", "review", "reviewping"]), group=-1)
async def handle_review_text(client: Client, message: Message):
    """Capture pending text reviews in PM."""
    user = message.from_user
    if not user:
        return
    try:
        pending = await review_db.get_pending(user.id)
    except Exception as e:
        logger.error(f"Error checking pending review: {e}")
        return
    
    if not pending:
        return  # Not in review flow

    text = message.text
    stars = pending['stars']

    # Save the text feedback
    await review_db.save_review_text(user.id, text)
    await review_db.clear_pending(user.id)

    # Success message to user
    await message.reply_text(
        "<b>Thank you for your detailed feedback!</b> ❤️\n\n"
        "Your review has been successfully submitted. We appreciate your time!",
        parse_mode=enums.ParseMode.HTML,
    )

    # Forward to log channel
    log_msg = (
        f"🌟 <b>New Review Received!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {user.mention} (<code>{user.id}</code>)\n"
        f"⭐ <b>Rating:</b> {STAR_BARS[stars]}\n"
        f"📝 <b>Feedback:</b> {text}\n"
        f"⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        await client.send_message(LOG_CHANNEL, log_msg, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to send log: {e}")
        
    raise StopPropagation

