import db
from services.ai_parser import answer_question


def _expenses_to_text(expenses: list[dict]) -> str:
    if not expenses:
        return "Нет данных о расходах."
    lines = ["Дата | Категория | Сумма | Описание"]
    for e in expenses:
        date = e["created_at"][:10]
        lines.append(f"{date} | {e['category']} | {e['amount']} | {e['description']}")
    return "\n".join(lines)


async def handle_question(question: str) -> str:
    """Load recent expenses and answer a question about them."""
    expenses = db.get_last_n_days_expenses(90)
    table = _expenses_to_text(expenses)
    return await answer_question(question, table)
