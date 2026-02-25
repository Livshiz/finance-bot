import logging

from telegram import Update
from telegram.ext import ContextTypes

import db
from middleware import authorized
from reports import format_expense_feedback
from services.ai_parser import parse_receipt_photo

logger = logging.getLogger(__name__)


@authorized
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receipt photos: parse via Claude Vision → save items."""
    photo = update.message.photo[-1]  # highest resolution
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    await update.message.reply_text("🔍 Анализирую чек...")

    items = await parse_receipt_photo(bytes(image_bytes))
    if items is None:
        await update.message.reply_text("Не удалось распознать чек. Попробуйте другое фото.")
        return

    if not items:
        await update.message.reply_text("На фото не найдено позиций чека.")
        return

    user_id = update.effective_user.id
    feedback_lines = []
    for item in items:
        db.add_expense(
            user_id=user_id,
            amount=item["amount"],
            category=item["category"],
            description=item["description"],
            source="photo",
        )
        feedback_lines.append(
            format_expense_feedback(item["category"], item["amount"])
        )

    total = sum(item["amount"] for item in items)
    header = f"🧾 Распознано позиций: {len(items)}, итого: {total:.0f}₽\n"
    await update.message.reply_text(header + "\n".join(feedback_lines))
