import functools
import logging

from telegram import Bot, Update
from telegram.ext import ContextTypes

from config import ALLOWED_USER_IDS

logger = logging.getLogger(__name__)


async def notify_others(bot: Bot, sender_id: int, text: str) -> None:
    """Send a notification to all allowed users except the sender."""
    for user_id in ALLOWED_USER_IDS:
        if user_id != sender_id:
            try:
                await bot.send_message(chat_id=user_id, text=text)
            except Exception:
                logger.warning("Failed to notify user %d", user_id)


def authorized(func):
    """Decorator that restricts handler to ALLOWED_USER_IDS."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            logger.warning("Unauthorized access attempt from user %d", user_id)
            await update.message.reply_text("⛔ Доступ запрещён.")
            return
        return await func(update, context)

    return wrapper
