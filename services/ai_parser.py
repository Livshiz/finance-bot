import base64
import json
import logging
import re

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, CATEGORIES

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

GPT_MODEL = "gpt-4o-mini"
CATEGORIES_STR = ", ".join(CATEGORIES)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences that LLMs sometimes add around JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


async def parse_expense_text(text: str) -> dict | None:
    """Parse user text as either an expense or a question.

    Returns:
        {"type": "expense", "amount": float, "category": str, "description": str}
        or {"type": "question"}
        or None on error
    """
    prompt = f"""Ты — финансовый помощник. Пользователь отправил сообщение. Определи, это запись расхода или вопрос о финансах.

Если это расход, верни JSON:
{{"type": "expense", "amount": <число>, "category": "<категория>", "description": "<краткое описание>"}}

Если это вопрос или просьба показать информацию, верни:
{{"type": "question"}}

Доступные категории: {CATEGORIES_STR}
Выбирай наиболее подходящую категорию. Если ни одна не подходит, используй "Другое".
Сумму всегда возвращай как число (без "₽", "руб" и т.д.).

Верни ТОЛЬКО JSON, без пояснений."""

    try:
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            max_tokens=256,
            timeout=15.0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content
        parsed = json.loads(_strip_code_fences(raw))
        if parsed.get("type") == "expense":
            parsed["amount"] = float(parsed["amount"])
            if parsed["category"] not in CATEGORIES:
                parsed["category"] = "Другое"
        return parsed
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Failed to parse GPT response: %s", e)
        return None
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return None


async def parse_receipt_photo(image_bytes: bytes, media_type: str = "image/jpeg") -> list[dict] | None:
    """Parse receipt photo via GPT-4o Vision.

    Returns list of {"amount": float, "category": str, "description": str}
    or None on error.
    """
    b64 = base64.standard_b64encode(image_bytes).decode()

    prompt = f"""Ты — финансовый помощник. На фото — чек из магазина или ресторана.
Извлеки все позиции и верни JSON-массив:
[{{"amount": <число>, "category": "<категория>", "description": "<название товара/услуги>"}}]

Доступные категории: {CATEGORIES_STR}
Если на фото нет чека или невозможно разобрать — верни пустой массив [].
Суммы — числа без валюты. Верни ТОЛЬКО JSON."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            timeout=30.0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64}",
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        raw = response.choices[0].message.content
        items = json.loads(_strip_code_fences(raw))
        if not isinstance(items, list):
            return None
        for item in items:
            item["amount"] = float(item["amount"])
            if item["category"] not in CATEGORIES:
                item["category"] = "Другое"
        return items
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Failed to parse receipt response: %s", e)
        return None
    except Exception as e:
        logger.error("OpenAI API error (receipt): %s", e)
        return None


async def answer_question(question: str, expenses_text: str) -> str:
    """Answer a user question about their finances using expense data.

    Returns the answer string or an error message.
    """
    prompt = f"""Ты — финансовый помощник семьи. Вот данные о расходах за последние 90 дней:

{expenses_text}

Ответь на вопрос пользователя кратко и по делу. Используй числа из данных.
Если данных недостаточно, так и скажи."""

    try:
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            max_tokens=1024,
            timeout=15.0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI API error (Q&A): %s", e)
        return "Не удалось получить ответ от AI. Попробуйте позже."
