from collections import defaultdict

import db


def _format_amount(amount: float) -> str:
    if amount == int(amount):
        return f"{int(amount)}₽"
    return f"{amount:.2f}₽"


def build_week_report() -> str:
    expenses = db.get_week_expenses()
    if not expenses:
        return "📊 За последнюю неделю расходов нет."

    total = sum(e["amount"] for e in expenses)
    by_category: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_category[e["category"]] += e["amount"]

    top = sorted(by_category.items(), key=lambda x: x[1], reverse=True)

    lines = ["📊 *Отчёт за неделю*", ""]
    for cat, amt in top:
        lines.append(f"  {cat}: {_format_amount(amt)}")
    lines.append(f"\n*Итого: {_format_amount(total)}*")

    prev_total = db.get_previous_week_total()
    if prev_total > 0:
        diff = total - prev_total
        pct = (diff / prev_total) * 100
        sign = "+" if diff > 0 else ""
        lines.append(
            f"vs прошлая неделя: {sign}{_format_amount(diff)} ({sign}{pct:.0f}%)"
        )

    return "\n".join(lines)


def build_month_report() -> str:
    expenses = db.get_month_expenses()
    if not expenses:
        return "📊 В этом месяце расходов нет."

    total = sum(e["amount"] for e in expenses)
    by_category: dict[str, float] = defaultdict(float)
    for e in expenses:
        by_category[e["category"]] += e["amount"]

    top = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    budgets = {b["category"]: b["monthly_limit"] for b in db.get_all_budgets()}

    lines = ["📊 *Отчёт за месяц*", ""]
    for cat, amt in top:
        line = f"  {cat}: {_format_amount(amt)}"
        if cat in budgets:
            limit = budgets[cat]
            pct = (amt / limit) * 100
            line += f" из {_format_amount(limit)} ({pct:.0f}%)"
            if amt > limit:
                line += " ⚠️"
        lines.append(line)

    lines.append(f"\n*Итого: {_format_amount(total)}*")
    return "\n".join(lines)


def build_budget_report() -> str:
    budgets = db.get_all_budgets()
    if not budgets:
        return "Бюджеты не установлены. Используйте /setbudget."

    lines = ["📋 *Бюджеты на месяц*", ""]
    for b in budgets:
        cat = b["category"]
        limit = b["monthly_limit"]
        spent = db.get_monthly_total(cat)
        pct = (spent / limit) * 100 if limit > 0 else 0
        status = "⚠️" if spent > limit else "✅"
        lines.append(
            f"  {status} {cat}: {_format_amount(spent)} / {_format_amount(limit)} ({pct:.0f}%)"
        )

    return "\n".join(lines)


def format_expense_feedback(category: str, amount: float) -> str:
    """Format feedback message after recording an expense."""
    lines = [f"✅ {category}, {_format_amount(amount)}"]

    monthly_total = db.get_monthly_total(category)
    budget = db.get_budget(category)

    if budget is not None:
        pct = (monthly_total / budget) * 100
        if monthly_total > budget:
            over = monthly_total - budget
            lines.append(
                f"⚠️ {category}: {_format_amount(monthly_total)} — "
                f"превышен лимит {_format_amount(budget)} на {_format_amount(over)}"
            )
        else:
            lines.append(
                f"📊 {category} в этом месяце: "
                f"{_format_amount(monthly_total)} из {_format_amount(budget)} ({pct:.0f}%)"
            )

    return "\n".join(lines)
