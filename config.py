"""Configuration loaded from environment variables (optionally via a .env file)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")

# --- Target ---
CATEGORY_JSON_URL = os.environ.get(
    "CATEGORY_JSON_URL",
    "https://shop.funbox.com.tw/category_products/XI/KB.json",
)
CATEGORY_PAGE_URL = os.environ.get(
    "CATEGORY_PAGE_URL",
    "https://shop.funbox.com.tw/categories/XI/KB",
)
SHOP_BASE_URL = os.environ.get("SHOP_BASE_URL", "https://shop.funbox.com.tw")
PAGE_LIMIT = int(os.environ.get("PAGE_LIMIT", "50"))
MAX_PAGES = int(os.environ.get("MAX_PAGES", "20"))

# --- State ---
STATE_FILE = Path(os.environ.get("STATE_FILE", str(BASE_DIR / "state" / "state.json")))

# --- LINE Messaging API (LINE Notify was shut down 2025-03-31) ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Email (SMTP) ---
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.environ.get("EMAIL_TO", "sonic0209work@gmail.com")
