import os
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.environ["ALLOWED_USER_IDS"].split(",")
    if uid.strip()
]

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "finance.db"

CATEGORIES = [
    "Продукты",
    "Рестораны/Кафе",
    "Транспорт",
    "Здоровье",
    "Дом",
    "Дети",
    "Развлечения",
    "Одежда",
    "Подарки",
    "Пожертвования",
    "Другое",
]

