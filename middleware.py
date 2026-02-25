import functools
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ALLOWED_USER_IDS

logger = logging.getLogger(__name__)


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
