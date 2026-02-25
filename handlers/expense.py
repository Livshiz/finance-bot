import logging

from telegram import Update
from telegram.ext import ContextTypes

import db
from middleware import authorized, notify_others
from reports import format_expense_feedback
from services.ai_parser import parse_expense_text
from services.whisper import transcribe_voice
from handlers.question import handle_question

logger = logging.getLogger(__name__)


@authorized
async def handle_text_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages: parse as expense or question."""
    text = update.message.text.strip()
    if not text:
        return

    result = await parse_expense_text(text)
    if result is None:
        await update.message.reply_text("Не удалось распознать сообщение. Попробуйте ещё раз.")
        return

    if result["type"] == "question":
        answer = await handle_question(text)
        await update.message.reply_text(answer)
        return

    user_id = update.effective_user.id
    db.add_expense(
        user_id=user_id,
        amount=result["amount"],
        category=result["category"],
        description=result["description"],
        source="text",
    )
    feedback = format_expense_feedback(result["category"], result["amount"])
    await update.message.reply_text(feedback)
    name = update.effective_user.first_name
    await notify_others(
        context.bot, user_id,
        f"👤 {name}: {result['category']}, {result['amount']:.0f}₽ — {result['description']}"
    )


@authorized
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages: transcribe → parse → save."""
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    voice_bytes = await file.download_as_bytearray()

    transcription = await transcribe_voice(bytes(voice_bytes))
    if transcription is None:
        await update.message.reply_text("Не удалось распознать голосовое сообщение.")
        return

    await update.message.reply_text(f"🎤 _{transcription}_", parse_mode="Markdown")

    result = await parse_expense_text(transcription)
    if result is None:
        await update.message.reply_text("Не удалось распознать трату из голосового сообщения.")
        return

    if result["type"] == "question":
        answer = await handle_question(transcription)
        await update.message.reply_text(answer)
        return

    user_id = update.effective_user.id
    db.add_expense(
        user_id=user_id,
        amount=result["amount"],
        category=result["category"],
        description=result["description"],
        source="voice",
    )
    feedback = format_expense_feedback(result["category"], result["amount"])
    await update.message.reply_text(feedback)
    name = update.effective_user.first_name
    await notify_others(
        context.bot, user_id,
        f"👤 {name} (голос): {result['category']}, {result['amount']:.0f}₽ — {result['description']}"
    )
