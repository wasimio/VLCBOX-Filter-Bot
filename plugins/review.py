# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

"""
Review & Rating System for VLCBox Bot
======================================
Admin commands:
  /sendreview  – Send a review-request message (to this chat or PM)
  /reviewstats – Show rating distribution, average, and latest reviews
  /broadcastreview – Broadcast review request to all bot users

User flow:
  1. User taps a star rating button  → rating saved
  2. Bot asks for optional text review
  3. User sends text (or /skip)      → forwarded to LOG_CHANNEL
"""

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

from VLCBox.bot import VLCBoxBot
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


def _fmt_username(user) -> str:
    if user.username:
        return f"@{user.username}"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip() or "Unknown"


# ─── Public: /review ──────────────────────────────────────────────────────────


@VLCBoxBot.on_message(filters.command("review") & filters.private)
async def cmd_public_review(client: Client, message: Message):
    """Allows any user to rate the bot manually in PM."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


# ─── Admin: /sendreview ───────────────────────────────────────────────────────


@VLCBoxBot.on_message(filters.command("sendreview") & filters.user(ADMINS))
async def cmd_send_review(client: Client, message: Message):
    """Admin command: send the review-request message here."""
    await message.reply_text(
        REVIEW_REQUEST_TEXT,
        reply_markup=build_star_keyboard(),
        parse_mode=enums.ParseMode.HTML,
    )


# ─── Admin: /broadcastreview ──────────────────────────────────────────────────


@VLCBoxBot.on_message(filters.command("broadcastreview") & filters.user(ADMINS))
async def cmd_broadcast_review(client: Client, message: Message):
    """Admin command: broadcast the review-request message to ALL bot users."""
    sts = await message.reply_text(
        "📡 <b>Starting review broadcast…</b>", parse_mode=enums.ParseMode.HTML
    )
    users = await db.get_all_users()
    start_time = time.time()
    total = await db.total_users_count()
    done = success = blocked = deleted = failed = 0

    async for user in users:
        uid = user.get("id")
        if not uid:
            done += 1
            failed += 1
            continue
        try:
            await client.send_message(
                chat_id=int(uid),
                text=REVIEW_REQUEST_TEXT,
                reply_markup=build_star_keyboard(),
                parse_mode=enums.ParseMode.HTML,
            )
            success += 1
        except UserIsBlocked:
            blocked += 1
        except InputUserDeactivated:
            deleted += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 2)
            try:
                await client.send_message(
                    chat_id=int(uid),
                    text=REVIEW_REQUEST_TEXT,
                    reply_markup=build_star_keyboard(),
                    parse_mode=enums.ParseMode.HTML,
                )
                success += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
        done += 1
        if done % 25 == 0:
            elapsed = datetime.timedelta(seconds=int(time.time() - start_time))
            await sts.edit_text(
                f"📡 <b>Broadcast in progress…</b>\n\n"
                f"👥 Total: {total}\n"
                f"✅ Done: {done}/{total}\n"
                f"📨 Sent: {success}  🚫 Blocked: {blocked}  🗑 Deleted: {deleted}",
                parse_mode=enums.ParseMode.HTML,
            )

    elapsed = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"⏱ Time: <code>{elapsed}</code>\n"
        f"👥 Total: {total}\n"
        f"📨 Sent: {success}  🚫 Blocked: {blocked}  🗑 Deleted: {deleted}  ❌ Failed: {failed}",
        parse_mode=enums.ParseMode.HTML,
    )


# ─── Admin: /reviewstats ──────────────────────────────────────────────────────


@VLCBoxBot.on_message(filters.command("reviewstats") & filters.user(ADMINS))
async def cmd_review_stats(client: Client, message: Message):
    """Admin command: show rating distribution, average, and latest reviews."""
    loading = await message.reply_text("📊 <i>Fetching stats…</i>", parse_mode=enums.ParseMode.HTML)

    total = await review_db.total_ratings_count()
    avg = await review_db.average_rating()
    dist = await review_db.distribution()
    latest = await review_db.latest_reviews(limit=5)

    # ── Distribution bar chart ──
    dist_lines = []
    for star in range(1, 6):
        count = dist[star]
        bar = "█" * min(count, 20) if count else "░"
        dist_lines.append(
            f"{STAR_BARS[star]} — <b>{count}</b> user{'s' if count != 1 else ''}"
        )

    dist_text = "\n".join(dist_lines)

    # ── Average stars display ──
    avg_display = f"{avg:.1f} ⭐" if avg else "No ratings yet"

    # ── Latest reviews ──
    if latest:
        reviews_text = ""
        for i, r in enumerate(latest, 1):
            uname = r.get("username", "Unknown")
            stars = STAR_BARS.get(r.get("stars", 0), "")
            text = r.get("review_text", "—") or "—"
            # Truncate long reviews
            if len(text) > 120:
                text = text[:117] + "…"
            dt = r.get("reviewed_at")
            dt_str = dt.strftime("%d %b %Y, %H:%M") if dt else "—"
            reviews_text += (
                f"\n<b>{i}.</b> {stars} | <i>{uname}</i>\n"
                f"   💬 {text}\n"
                f"   🕐 {dt_str}\n"
            )
    else:
        reviews_text = "\n<i>No text reviews yet.</i>"

    stats_msg = (
        f"📊 <b>VLCBox — Review Statistics</b>\n"
        f"{'─' * 30}\n\n"
        f"🗳 <b>Total Ratings:</b> <code>{total}</code>\n"
        f"⭐ <b>Average Rating:</b> {avg_display}\n\n"
        f"📈 <b>Rating Distribution</b>\n"
        f"{'─' * 30}\n"
        f"{dist_text}\n\n"
        f"💬 <b>Latest Reviews</b>\n"
        f"{'─' * 30}"
        f"{reviews_text}"
    )

    close_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔐 Close", callback_data="close_data")]])
    await loading.edit_text(stats_msg, parse_mode=enums.ParseMode.HTML, reply_markup=close_btn)


# ─── Callback: star rating button pressed ────────────────────────────────────


@VLCBoxBot.on_callback_query(filters.regex(r"^rate_(\d)$"))
async def cb_rate(client: Client, query: CallbackQuery):
    """Handle star rating button taps."""
    user = query.from_user
    stars = int(query.data.split("_")[1])

    # ── Duplicate guard ──
    if await review_db.has_rated(user.id):
        existing = await review_db.get_rating(user.id)
        existing_stars = existing.get("stars", "?")
        await query.answer(
            f"You already rated us {STAR_BARS.get(existing_stars, existing_stars)} — thank you! ❤️",
            show_alert=True,
        )
        return

    # ── Save rating ──
    username = _fmt_username(user)
    saved = await review_db.save_rating(user.id, username, stars)
    if not saved:
        await query.answer("You've already submitted a rating!", show_alert=True)
        return

    # ── Mark as pending text review ──
    await review_db.set_pending(user.id, stars)

    await query.answer(f"You rated {STAR_BARS[stars]} — thank you! 🙏")

    # ── Edit original message to confirm rating ──
    try:
        await query.message.edit_text(
            f"✅ <b>Rating Received!</b>\n\nYou gave us {STAR_BARS[stars]} — we appreciate it! 🙏",
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        pass

    # ── Ask for text review in PM ──
    skip_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏭ Skip", callback_data="review_skip")]]
    )
    try:
        await client.send_message(
            chat_id=user.id,
            text=(
                f"💖 <b>Thanks for rating VLCBox!</b>\n\n"
                f"Your rating: {STAR_BARS[stars]}\n\n"
                "Would you like to share a quick message about your experience?\n"
                "<i>Send your feedback below, or tap Skip.</i>"
            ),
            reply_markup=skip_btn,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        logger.warning(f"Could not send review prompt to {user.id}: {e}")
        # Clean up pending state — user can't receive PM
        await review_db.clear_pending(user.id)


# ─── Callback: user skips text review ────────────────────────────────────────


@VLCBoxBot.on_callback_query(filters.regex(r"^review_skip$"))
async def cb_review_skip(client: Client, query: CallbackQuery):
    """User decided to skip the written review."""
    user = query.from_user
    await review_db.clear_pending(user.id)

    await query.answer("No worries! Your rating has been saved. ✨")
    try:
        await query.message.edit_text(
            "✅ <b>Rating saved!</b>\n\nThanks for taking the time. We'll keep improving VLCBox for you! 🍿",
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        pass

    # ── Notify admin log channel (rating only, no text) ──
    rating_doc = await review_db.get_rating(user.id)
    if rating_doc:
        await _forward_to_log(client, rating_doc, review_text=None)


# ─── Message handler: capture text review in PM ───────────────────────────────


@VLCBoxBot.on_message(filters.private & filters.text & ~filters.command(["start", "help", "reviewstats", "sendreview", "broadcastreview", "skip", "review"]), group=-1)
async def handle_review_text(client: Client, message: Message):
    """Capture pending text reviews in PM."""
    user = message.from_user
    if not user:
        return
    pending = await review_db.get_pending(user.id)
    if not pending:
        return  # Not in review flow — let other handlers take it
    # Stop propagation so pm_filter.py doesn't also handle this message
    message.stop_propagation()

    review_text = message.text.strip()

    # ── Basic spam guard ──
    if len(review_text) < 2:
        await message.reply_text(
            "⚠️ Please write at least a few characters for your review.",
            parse_mode=enums.ParseMode.HTML,
        )
        return
    if len(review_text) > 1000:
        await message.reply_text(
            "⚠️ Your review is too long (max 1000 characters). Please shorten it.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    # ── Save review text ──
    saved = await review_db.save_review_text(user.id, review_text)
    await review_db.clear_pending(user.id)

    if saved:
        stars = pending.get("stars", 0)
        await message.reply_text(
            f"💖 <b>Thank you for your feedback!</b>\n\n"
            f"Rating: {STAR_BARS.get(stars, '')}\n"
            f"Your review has been submitted. 🙏\n\n"
            f"<i>Your feedback helps us make VLCBox even better for everyone!</i>",
            parse_mode=enums.ParseMode.HTML,
        )
        rating_doc = await review_db.get_rating(user.id)
        await _forward_to_log(client, rating_doc, review_text=review_text)
    else:
        await message.reply_text(
            "⚠️ Something went wrong saving your review. Please try again.",
            parse_mode=enums.ParseMode.HTML,
        )


# ─── Utility: forward completed review to admin log channel ──────────────────


async def _forward_to_log(client: Client, rating_doc: dict, review_text: str | None):
    """Send a formatted review card to LOG_CHANNEL."""
    uid = rating_doc.get("user_id")
    username = rating_doc.get("username", "Unknown")
    stars = rating_doc.get("stars", 0)
    rated_at = rating_doc.get("rated_at")
    dt_str = rated_at.strftime("%d %b %Y, %H:%M UTC") if rated_at else "—"

    text_section = (
        f"\n💬 <b>Review:</b>\n<blockquote>{review_text}</blockquote>"
        if review_text
        else "\n<i>No written review provided.</i>"
    )

    log_msg = (
        f"🌟 <b>New VLCBox Rating!</b>\n"
        f"{'─' * 28}\n"
        f"👤 <b>User:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"⭐ <b>Rating:</b> {STAR_BARS.get(stars, str(stars))} ({stars}/5)\n"
        f"📅 <b>Date:</b> {dt_str}"
        f"{text_section}"
    )

    try:
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=log_msg,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.warning(f"Failed to forward review to LOG_CHANNEL: {e}")
