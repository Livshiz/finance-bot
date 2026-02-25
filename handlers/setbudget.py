import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import db
from config import CATEGORIES
from middleware import authorized

logger = logging.getLogger(__name__)

CHOOSING_CATEGORY, ENTERING_AMOUNT = range(2)


def _category_keyboard() -> ReplyKeyboardMarkup:
    rows = [CATEGORIES[i : i + 3] for i in range(0, len(CATEGORIES), 3)]
    return ReplyKeyboardMarkup(rows, one_time_keyboard=True, resize_keyboard=True)


@authorized
async def setbudget_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Выберите категорию для установки бюджета:",
        reply_markup=_category_keyboard(),
    )
    return CHOOSING_CATEGORY


@authorized
async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.strip()
    if category not in CATEGORIES:
        await update.message.reply_text(
            "Неизвестная категория. Выберите из списка:",
            reply_markup=_category_keyboard(),
        )
        return CHOOSING_CATEGORY

    context.user_data["budget_category"] = category
    current = db.get_budget(category)
    msg = f"Категория: {category}\n"
    if current is not None:
        msg += f"Текущий лимит: {current:.0f}₽\n"
    msg += "\nВведите новый месячный лимит (число):"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ENTERING_AMOUNT


@authorized
async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(" ", "").replace("₽", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введите положительное число:")
        return ENTERING_AMOUNT

    category = context.user_data.pop("budget_category")
    db.set_budget(category, amount)
    await update.message.reply_text(
        f"✅ Бюджет установлен: {category} — {amount:.0f}₽/мес"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("budget_category", None)
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_setbudget_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("setbudget", setbudget_start)],
        states={
            CHOOSING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_chosen)
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
