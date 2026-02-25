import datetime
import logging
import traceback

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
from config import ALLOWED_USER_IDS, TELEGRAM_BOT_TOKEN
from handlers.commands import budget, month, start, week
from handlers.expense import handle_text_expense, handle_voice
from handlers.photo import handle_photo
from handlers.setbudget import get_setbudget_handler
from reports import build_week_report

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Moscow timezone (UTC+3)
MSK = datetime.timezone(datetime.timedelta(hours=3))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception:\n%s", traceback.format_exc())
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте позже."
        )


async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send weekly report to all allowed users (Sunday 19:00 MSK)."""
    report = build_week_report()
    for user_id in ALLOWED_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=user_id, text=report, parse_mode="Markdown"
            )
        except Exception:
            logger.exception("Failed to send weekly report to %d", user_id)


def main() -> None:
    db.init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler must be added before generic text handler
    app.add_handler(get_setbudget_handler())

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("month", month))
    app.add_handler(CommandHandler("budget", budget))

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_expense)
    )

    app.add_error_handler(error_handler)

    # Weekly report: Sunday at 19:00 Moscow time
    app.job_queue.run_daily(
        send_weekly_report,
        time=datetime.time(hour=19, minute=0, tzinfo=MSK),
        days=(6,),  # Sunday
    )

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
