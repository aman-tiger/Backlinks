"""
Вспомогательный модуль для работы с testmail.app
Создаёт уникальные email-адреса и проверяет входящие письма через API
"""
import asyncio
import os
import random
import string
import time
import urllib.request
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

APIKEY = os.getenv("TESTMAIL_APIKEY", "")
NAMESPACE = os.getenv("TESTMAIL_NAMESPACE", "")


def make_email(tag: str = "") -> str:
    """Генерирует уникальный email через testmail.app"""
    if not tag:
        tag = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{NAMESPACE}.{tag}@inbox.testmail.app"


def make_password() -> str:
    chars = string.ascii_letters + string.digits + "!@#$"
    return "".join(random.choices(chars, k=14))


def check_inbox(tag: str, timeout: int = 60, poll: int = 5) -> dict | None:
    """
    Ждёт письмо с нужным тегом.
    Возвращает dict с письмом или None если не дождались.
    """
    if not APIKEY or not NAMESPACE:
        print("  ⚠️  TESTMAIL_APIKEY или TESTMAIL_NAMESPACE не заполнены в .env")
        return None

    url = (
        f"https://api.testmail.app/api/json"
        f"?apikey={APIKEY}&namespace={NAMESPACE}&tag={tag}&livequery=true"
    )
    deadline = time.time() + timeout
    print(f"  ⏳ Ждём письмо на тег '{tag}' (до {timeout}с)...")

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read())
                emails = data.get("emails", [])
                if emails:
                    print(f"  ✅ Письмо получено от: {emails[0].get('from','?')}")
                    return emails[0]
        except Exception as e:
            print(f"  ⚠️  API ошибка: {e}")
        time.sleep(poll)

    print(f"  ❌ Письмо не пришло за {timeout}с")
    return None


def extract_link(email_body: str, keyword: str = "confirm") -> str | None:
    """Ищет ссылку подтверждения в теле письма"""
    import re
    links = re.findall(r'https?://[^\s"\'<>]+', email_body)
    for link in links:
        if keyword.lower() in link.lower():
            return link
    # Если по ключевому слову не нашли — вернём первую ссылку
    return links[0] if links else None
