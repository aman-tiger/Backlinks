"""
Тест на простых сайтах без регистрации (категория: Авто)
Запуск: python3 test_simple.py
"""
import asyncio
import os
import sys
import csv
import random
import string
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

TARGET_URL = os.getenv("TARGET_URL", "https://example.com")
TARGET_ANCHOR = os.getenv("TARGET_ANCHOR", "Example Site")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

CSV_FILE = Path(__file__).parent.parent / "Таблицы беклинков  - Лист1.csv"
RESULTS_FILE = Path(__file__).parent / "results.csv"

ARTICLE_TEXTS = [
    f"Looking for a reliable resource? Check out {TARGET_ANCHOR} at {TARGET_URL} — great content and useful information for everyone.",
    f"Highly recommend visiting {TARGET_URL} — {TARGET_ANCHOR} provides excellent insights on this topic.",
    f"If you're interested in this subject, {TARGET_ANCHOR} ({TARGET_URL}) is definitely worth bookmarking.",
]


def random_text():
    return random.choice(ARTICLE_TEXTS)


def random_title():
    words = ["Guide", "Tips", "Review", "Overview", "Insights", "Resources"]
    topics = ["Technology", "Business", "Health", "Finance", "Education"]
    return f"{random.choice(topics)} {random.choice(words)} 2024"


def log(msg, status="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"OK": "✅", "FAIL": "❌", "INFO": "ℹ️", "WAIT": "⏳"}
    print(f"[{ts}] {icons.get(status, '•')} {msg}")


def save_result(site, result_url, status, notes=""):
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), site, result_url, status, notes])


async def test_telegraph(page):
    """telegra.ph — нет регистрации, просто пишем статью"""
    log("telegra.ph — открываем редактор", "WAIT")
    await page.goto("https://telegra.ph", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    # Заголовок
    title_field = page.locator("h1.title-editor, [placeholder*='Title'], [name='title']").first
    await title_field.click()
    await title_field.fill(random_title())
    await page.wait_for_timeout(500)

    # Тело статьи
    content_field = page.locator("div.content-editor, [contenteditable='true']").first
    await content_field.click()
    text = random_text()
    await content_field.fill(text)
    await page.wait_for_timeout(500)

    # Публикуем
    publish_btn = page.locator("button:has-text('PUBLISH'), button:has-text('Публиковать')").first
    await publish_btn.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    if "telegra.ph/" in result_url and result_url != "https://telegra.ph/":
        log(f"telegra.ph — успех! URL: {result_url}", "OK")
        save_result("telegra.ph", result_url, "SUCCESS")
        return True
    else:
        log(f"telegra.ph — не удалось. URL: {result_url}", "FAIL")
        save_result("telegra.ph", result_url, "FAILED", "Не переадресовало на результат")
        return False


async def test_anotepad(page):
    """anotepad.com — нет регистрации"""
    log("anotepad.com — открываем", "WAIT")
    await page.goto("https://anotepad.com", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    text_area = page.locator("textarea, div[contenteditable='true']").first
    await text_area.click()
    await text_area.fill(random_text())
    await page.wait_for_timeout(500)

    save_btn = page.locator("button:has-text('Save'), input[value*='Save'], button:has-text('Сохранить')").first
    await save_btn.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    if "anotepad.com/notes/" in result_url:
        log(f"anotepad.com — успех! URL: {result_url}", "OK")
        save_result("anotepad.com", result_url, "SUCCESS")
        return True
    else:
        log(f"anotepad.com — не удалось. URL: {result_url}", "FAIL")
        save_result("anotepad.com", result_url, "FAILED")
        return False


async def test_controlc(page):
    """controlc.com — нет регистрации"""
    log("controlc.com — открываем", "WAIT")
    await page.goto("https://controlc.com", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    text_area = page.locator("textarea").first
    await text_area.click()
    await text_area.fill(random_text())
    await page.wait_for_timeout(500)

    submit = page.locator("input[type='submit'], button[type='submit']").first
    await submit.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    if "controlc.com/" in result_url and result_url != "https://controlc.com/":
        log(f"controlc.com — успех! URL: {result_url}", "OK")
        save_result("controlc.com", result_url, "SUCCESS")
        return True
    else:
        log(f"controlc.com — не удалось. URL: {result_url}", "FAIL")
        save_result("controlc.com", result_url, "FAILED")
        return False


async def test_pastelink(page):
    """pastelink.net — регистрация без подтверждения email"""
    log("pastelink.net — открываем", "WAIT")
    await page.goto("https://pastelink.net/account/register", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    rand_user = "user_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    rand_pass = "Pass_" + "".join(random.choices(string.ascii_letters + string.digits, k=10))
    rand_email = rand_user + "@mailnull.com"

    await page.fill("input[name='username'], input[placeholder*='user']", rand_user)
    await page.fill("input[name='email'], input[type='email']", rand_email)
    await page.fill("input[name='password'], input[type='password']", rand_pass)

    await page.locator("button[type='submit'], input[type='submit']").first.click()
    await page.wait_for_timeout(3000)

    # Публикуем пасту
    await page.goto("https://pastelink.net", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(1000)

    content_area = page.locator("textarea, div[contenteditable='true']").first
    await content_area.fill(random_text())
    await page.wait_for_timeout(300)

    await page.locator("button:has-text('Publish'), button:has-text('Submit'), button[type='submit']").first.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    log(f"pastelink.net — URL: {result_url}", "INFO")
    save_result("pastelink.net", result_url, "CHECK_MANUALLY")
    return True


async def test_folkd(page):
    """folkd.com — нет регистрации, добавляем ссылку"""
    log("folkd.com — открываем", "WAIT")
    await page.goto("https://www.folkd.com", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    url_input = page.locator("input[name='url'], input[placeholder*='URL'], input[placeholder*='url']").first
    await url_input.fill(TARGET_URL)

    submit = page.locator("button:has-text('Add'), input[value*='Add'], button[type='submit']").first
    await submit.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    log(f"folkd.com — URL: {result_url}", "INFO")
    save_result("folkd.com", result_url, "CHECK_MANUALLY")
    return True


TESTS = [
    ("telegra.ph", test_telegraph),
    ("anotepad.com", test_anotepad),
    ("controlc.com", test_controlc),
    ("pastelink.net", test_pastelink),
    ("folkd.com", test_folkd),
]


async def main():
    from camoufox.async_api import AsyncCamoufox

    # Создаём файл результатов
    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "site", "result_url", "status", "notes"])

    print("=" * 60)
    print(f"🚀 Тест бэклинк-бота")
    print(f"   Домен: {TARGET_URL}")
    print(f"   Сайтов: {len(TESTS)}")
    print("=" * 60)

    # Какие тесты запускать (из аргументов или все)
    targets = sys.argv[1:] if len(sys.argv) > 1 else [name for name, _ in TESTS]

    async with AsyncCamoufox(headless=HEADLESS, geoip=True) as browser:
        context = await browser.new_context()

        results = {"success": 0, "failed": 0, "manual": 0}

        for name, test_fn in TESTS:
            if name not in targets:
                continue

            log(f"--- Тест: {name} ---", "INFO")
            page = await context.new_page()
            try:
                ok = await test_fn(page)
                if ok:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                log(f"{name} — ошибка: {e}", "FAIL")
                save_result(name, "", "ERROR", str(e)[:100])
                results["failed"] += 1
            finally:
                await page.close()

            # Пауза между сайтами
            await asyncio.sleep(random.uniform(2, 5))

        print("\n" + "=" * 60)
        print(f"✅ Успешно:  {results['success']}")
        print(f"❌ Ошибки:   {results['failed']}")
        print(f"📋 Результаты: {RESULTS_FILE}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
