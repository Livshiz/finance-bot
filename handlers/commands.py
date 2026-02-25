from telegram import Update
from telegram.ext import ContextTypes

from middleware import authorized
from reports import build_week_report, build_month_report, build_budget_report


WIFE_USER_ID = 6783217385


@authorized
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id == WIFE_USER_ID:
        greeting = "Привет, любимая! 💕"
    else:
        greeting = "👋 Привет!"

    await update.message.reply_text(
        f"{greeting} Я бот для учёта семейных расходов.\n\n"
        "Отправь мне трату текстом, голосом или фото чека.\n\n"
        "Команды:\n"
        "/week — отчёт за неделю\n"
        "/month — отчёт за месяц\n"
        "/budget — статус бюджетов\n"
        "/setbudget — установить лимит на категорию\n\n"
        "Также можешь задать вопрос о расходах в свободной форме."
    )


@authorized
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    report = build_week_report()
    await update.message.reply_text(report, parse_mode="Markdown")


@authorized
async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    report = build_month_report()
    await update.message.reply_text(report, parse_mode="Markdown")


@authorized
async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    report = build_budget_report()
    await update.message.reply_text(report, parse_mode="Markdown")
