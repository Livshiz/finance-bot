import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_expenses_user_date
            ON expenses(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_expenses_category_date
            ON expenses(category, created_at);

        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.close()


def add_expense(
    user_id: int,
    amount: float,
    category: str,
    description: str,
    source: str = "text",
) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, description, source) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, description, source),
    )
    conn.commit()
    expense_id = cur.lastrowid
    conn.close()
    return expense_id


def get_monthly_total(category: str) -> float:
    now = datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
        "WHERE category = ? AND created_at >= ?",
        (category, start.isoformat()),
    ).fetchone()
    conn.close()
    return row["total"]


def get_budget(category: str) -> float | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT monthly_limit FROM budgets WHERE category = ?", (category,)
    ).fetchone()
    conn.close()
    return row["monthly_limit"] if row else None


def set_budget(category: str, monthly_limit: float) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO budgets (category, monthly_limit, updated_at) "
        "VALUES (?, ?, ?)",
        (category, monthly_limit, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_budgets() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT category, monthly_limit FROM budgets").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_expenses_since(since: datetime) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT user_id, amount, category, description, source, created_at "
        "FROM expenses WHERE created_at >= ? ORDER BY created_at",
        (since.isoformat(),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_week_expenses() -> list[dict]:
    since = datetime.now() - timedelta(days=7)
    return get_expenses_since(since)


def get_month_expenses() -> list[dict]:
    now = datetime.now()
    since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return get_expenses_since(since)


def get_last_n_days_expenses(days: int = 90) -> list[dict]:
    since = datetime.now() - timedelta(days=days)
    return get_expenses_since(since)


def get_previous_week_total() -> float:
    now = datetime.now()
    end = now - timedelta(days=7)
    start = end - timedelta(days=7)
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
        "WHERE created_at >= ? AND created_at < ?",
        (start.isoformat(), end.isoformat()),
    ).fetchone()
    conn.close()
    return row["total"]
