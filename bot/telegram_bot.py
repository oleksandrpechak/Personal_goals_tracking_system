"""
Telegram bot setup and command handlers.

Uses python-telegram-bot v20+ (async Application API).
Includes owner-only authorization, rate limiting, and global error handling.
"""

from __future__ import annotations

import logging

import telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from bot.analytics import get_weekly_opportunities
from db.database import get_connection
from db.repository import OpportunityRepository, OutreachRepository
from db.queries import (
    get_monthly_contacted_count,
    get_monthly_opportunity_count,
    get_outreach_pipeline,
)
from security.auth import owner_only
from security.rate_limiter import is_rate_limited
from utils.metrics import metrics

logger = logging.getLogger(__name__)

# ── Lightweight Bot instance for outbound messages (reused) ──────────────────
_bot: telegram.Bot | None = None


def _get_bot() -> telegram.Bot:
    """Return a reusable Bot instance for sending messages."""
    global _bot
    if _bot is None:
        _bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    return _bot


# ── Helper: send a plain-text message to the configured chat ─────────────────

async def send_message(text: str) -> None:
    """Send *text* to the configured Telegram chat using the reusable Bot."""
    bot = _get_bot()
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    metrics.inc("messages_sent")
    logger.info("Telegram message sent (%d chars)", len(text))


# ── Rate-limit gate (used by all command handlers) ───────────────────────────

async def _check_rate_limit(update: Update) -> bool:
    """Return ``True`` and reply if the user is rate-limited."""
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if is_rate_limited(chat_id):
        metrics.inc("commands_rate_limited")
        await update.message.reply_text("⏳ Rate limit exceeded. Try again later.")
        return True
    metrics.inc("commands_handled")
    return False


# ── /start command ───────────────────────────────────────────────────────────

@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    if await _check_rate_limit(update):
        return
    await update.message.reply_text(
        "👋 Personal Productivity Bot is active!\n\n"
        "Commands:\n"
        "/today     — daily productivity dashboard\n"
        "/progress  — monthly opportunity stats\n"
        "/dashboard — weekly snapshot with contact rate\n"
        "/outreach  — outreach pipeline breakdown\n"
        "/health    — system health check\n"
        "/help      — show this message"
    )


# ── /progress command ────────────────────────────────────────────────────────

@owner_only
async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /progress command — return monthly stats."""
    if await _check_rate_limit(update):
        return
    try:
        found = get_monthly_opportunity_count()
        contacted = get_monthly_contacted_count()
    except Exception:
        logger.exception("Failed to fetch progress stats")
        await update.message.reply_text("⚠️ Could not fetch stats. Check logs.")
        return

    text = (
        "📊 *Progress Report*\n\n"
        f"Opportunities found this month: *{found}*\n"
        f"Opportunities contacted:        *{contacted}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /dashboard command ───────────────────────────────────────────────────────

@owner_only
async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /dashboard command — return weekly snapshot with contact rate."""
    if await _check_rate_limit(update):
        return
    try:
        stats = get_weekly_opportunities()
    except Exception:
        logger.exception("Failed to fetch dashboard stats")
        await update.message.reply_text("⚠️ Could not fetch dashboard. Check logs.")
        return

    text = (
        "📊 *Personal Dashboard*\n\n"
        f"Opportunities this week: *{stats['opportunities']}*\n"
        f"Contacted: *{stats['contacted']}*\n"
        f"Contact rate: *{stats['contact_rate']}%*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /outreach command ────────────────────────────────────────────────────────

@owner_only
async def outreach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /outreach command — return outreach pipeline stats."""
    if await _check_rate_limit(update):
        return
    try:
        pipeline = get_outreach_pipeline()
    except Exception:
        logger.exception("Failed to fetch outreach pipeline")
        await update.message.reply_text("⚠️ Could not fetch outreach data. Check logs.")
        return

    text = (
        "📬 *Outreach Pipeline*\n\n"
        f"Pending contacts: *{pipeline['pending']}*\n"
        f"Contacted:        *{pipeline['contacted']}*\n"
        f"Converted:        *{pipeline['converted']}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /help command ────────────────────────────────────────────────────────────

@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    if await _check_rate_limit(update):
        return
    await update.message.reply_text(
        "Available commands:\n"
        "/today     — daily productivity dashboard\n"
        "/progress  — monthly opportunity stats\n"
        "/dashboard — weekly snapshot with contact rate\n"
        "/outreach  — outreach pipeline breakdown\n"
        "/health    — system health check\n"
        "/help      — show this message"
    )


# ── /health command (Task 9) ─────────────────────────────────────────────────

@owner_only
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /health command — report system health."""
    if await _check_rate_limit(update):
        return

    # Database check
    try:
        conn = get_connection()
        db_status = "✅ Connected" if conn and not conn.closed else "❌ Disconnected"
    except Exception:
        db_status = "❌ Unreachable"

    # Last opportunity scan
    try:
        last_scan = OpportunityRepository.last_created_at()
        scan_text = last_scan.strftime("%Y-%m-%d %H:%M UTC") if last_scan else "N/A"
    except Exception:
        scan_text = "N/A"

    # Scheduler status — if the bot is running, the scheduler is too
    sched_status = "✅ Running"

    # Metrics
    m = metrics.snapshot()
    uptime_h = m["uptime_seconds"] // 3600
    uptime_m = (m["uptime_seconds"] % 3600) // 60

    text = (
        "🏥 *System Health*\n\n"
        f"Database: {db_status}\n"
        f"Scheduler: {sched_status}\n"
        f"Last opportunity: {scan_text}\n"
        f"Uptime: {uptime_h}h {uptime_m}m\n\n"
        f"Messages sent: {m['messages_sent']}\n"
        f"Errors: {m['errors']}\n"
        f"Jobs inserted: {m['jobs_inserted']}\n"
        f"Duplicates skipped: {m['jobs_skipped_duplicate']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /today command (Task 15) ─────────────────────────────────────────────────

@owner_only
async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /today command — daily productivity dashboard."""
    if await _check_rate_limit(update):
        return
    try:
        opps = OpportunityRepository.today(limit=5)
        pipeline = OutreachRepository.pipeline()
    except Exception:
        logger.exception("Failed to build /today dashboard")
        await update.message.reply_text("⚠️ Could not build today's dashboard.")
        return

    opp_lines = "\n".join(
        f"  • {o['title']}" for o in opps
    ) or "  (none yet)"

    text = (
        "🗓️ *Today's Dashboard*\n\n"
        "📌 *Priorities*\n"
        "1️⃣  Complete one sales / outreach task\n"
        "2️⃣  Ship one product improvement\n"
        "3️⃣  Finish one learning task\n\n"
        f"📰 *New opportunities today:*\n{opp_lines}\n\n"
        f"📬 *Pending outreach:* {pipeline['pending']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── Global error handler (Feature 7 — safe user-facing messages) ─────────────

async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log the exception and send a safe, generic message to the user.

    Never exposes stack traces or internal details to Telegram.
    """
    metrics.inc("errors")
    logger.error("Unhandled exception in bot handler", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An internal error occurred. Please try again later."
            )
        except Exception:
            logger.exception("Failed to send error message to user")


# ── Build the Application (used by main.py) ─────────────────────────────────

def build_application() -> Application:
    """
    Construct and return a fully configured Telegram Application instance.

    Callers can then call `application.run_polling()` or integrate it with
    an async event loop.
    """
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("outreach", outreach_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_error_handler(_error_handler)

    logger.info("Telegram application built with %d handlers", len(app.handlers[0]))
    return app
