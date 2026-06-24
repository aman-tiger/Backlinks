"""
Тест на сайтах с email-регистрацией через testmail.app
Сайты: postheaven.net, over-blog.com

Запуск:
  python3 backlink_bot/test_email_sites.py
  python3 backlink_bot/test_email_sites.py postheaven.net
"""
import asyncio
import os
import sys
import csv
import random
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from email_helper import make_email, make_password, check_inbox, extract_link

load_dotenv(Path(__file__).parent.parent / ".env")

TARGET_URL   = os.getenv("TARGET_URL", "https://example.com")
TARGET_ANCHOR = os.getenv("TARGET_ANCHOR", "Example")
HEADLESS     = os.getenv("HEADLESS", "false").lower() == "true"
RESULTS_FILE = Path(__file__).parent / "results.csv"

ARTICLE_TEXTS = [
    f"{TARGET_ANCHOR} is a great resource. Check it out at {TARGET_URL} for detailed information and expert advice.",
    f"I recently discovered {TARGET_URL} — {TARGET_ANCHOR} offers valuable content that's worth reading.",
    f"For anyone interested in this topic, {TARGET_ANCHOR} at {TARGET_URL} is highly recommended.",
]

def random_text():
    return random.choice(ARTICLE_TEXTS)

def random_title():
    prefixes = ["Best", "Top", "Ultimate", "Complete", "Essential"]
    topics   = ["Guide", "Tips", "Resources", "Overview", "Review"]
    return f"{random.choice(prefixes)} {random.choice(topics)} {datetime.now().year}"

def log(msg, status="INFO"):
    icons = {"OK": "✅", "FAIL": "❌", "INFO": "ℹ️", "WAIT": "⏳"}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {icons.get(status, '•')} {msg}")

def save_result(site, result_url, status, notes=""):
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([datetime.now().isoformat(), site, result_url, status, notes])


# ─────────────────────────────────────────────
# postheaven.net  — блог-платформа, email нужен
# ─────────────────────────────────────────────
async def test_postheaven(page):
    log("postheaven.net — регистрация", "WAIT")
    tag   = f"posthvn{int(time.time())}"
    email = make_email(tag)
    pwd   = make_password()

    await page.goto("https://postheaven.net/users/sign_up", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(1500)

    await page.fill("input[name='user[email]'], input[type='email']", email)
    await page.fill("input[name='user[password]'], input[type='password']", pwd)

    confirm_field = page.locator("input[name='user[password_confirmation]']")
    if await confirm_field.count() > 0:
        await confirm_field.fill(pwd)

    await page.locator("input[type='submit'], button[type='submit']").first.click()
    await page.wait_for_timeout(3000)

    log(f"Письмо отправлено на {email}", "INFO")
    mail = check_inbox(tag, timeout=90)

    if not mail:
        log("postheaven.net — письмо не пришло", "FAIL")
        save_result("postheaven.net", "", "NO_EMAIL", email)
        return False

    body = mail.get("html", mail.get("text", ""))
    confirm_url = extract_link(body, "confirm")

    if confirm_url:
        log(f"Переходим по ссылке подтверждения...", "WAIT")
        await page.goto(confirm_url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

    # Создаём пост
    await page.goto("https://postheaven.net/posts/new", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(1500)

    title_f = page.locator("input[name='post[title]'], input[placeholder*='title' i]").first
    await title_f.fill(random_title())
    body_f  = page.locator("textarea, div[contenteditable='true']").first
    await body_f.fill(random_text())

    await page.locator("input[type='submit'], button[type='submit']").first.click()
    await page.wait_for_timeout(3000)

    result_url = page.url
    if "postheaven.net" in result_url and "/posts/" in result_url:
        log(f"postheaven.net — успех! {result_url}", "OK")
        save_result("postheaven.net", result_url, "SUCCESS")
        return True

    log(f"postheaven.net — не удалось. URL: {result_url}", "FAIL")
    save_result("postheaven.net", result_url, "FAILED")
    return False


# ─────────────────────────────────────────────
# over-blog.com — блог-платформа с email
# ─────────────────────────────────────────────
async def test_overblog(page):
    log("over-blog.com — регистрация", "WAIT")
    tag   = f"overblog{int(time.time())}"
    email = make_email(tag)
    pwd   = make_password()
    username = f"user{random.randint(10000,99999)}"

    await page.goto("https://www.over-blog.com/create-blog.php", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    # Заполняем форму регистрации
    email_f = page.locator("input[name='email'], input[type='email']").first
    if await email_f.count() == 0:
        await page.goto("https://www.over-blog.com/register", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1500)

    await page.locator("input[type='email'], input[name='email']").first.fill(email)
    await page.locator("input[type='password'], input[name='password']").first.fill(pwd)

    username_f = page.locator("input[name='username'], input[name='login'], input[name='pseudo']")
    if await username_f.count() > 0:
        await username_f.first.fill(username)

    await page.locator("button[type='submit'], input[type='submit']").first.click()
    await page.wait_for_timeout(3000)

    log(f"Регистрация отправлена на {email}", "INFO")
    mail = check_inbox(tag, timeout=90)

    if not mail:
        log("over-blog.com — письмо не пришло", "FAIL")
        save_result("over-blog.com", "", "NO_EMAIL", email)
        return False

    body = mail.get("html", mail.get("text", ""))
    confirm_url = extract_link(body, "confirm")
    if confirm_url:
        await page.goto(confirm_url, timeout=20000)
        await page.wait_for_timeout(2000)

    result_url = page.url
    log(f"over-blog.com — URL после подтверждения: {result_url}", "INFO")
    save_result("over-blog.com", result_url, "CONFIRMED")
    return True


TESTS = [
    ("postheaven.net", test_postheaven),
    ("over-blog.com",  test_overblog),
]


async def main():
    from camoufox.async_api import AsyncCamoufox

    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "site", "result_url", "status", "notes"])

    targets = sys.argv[1:] if len(sys.argv) > 1 else [n for n, _ in TESTS]

    print("=" * 60)
    print(f"📧 Тест сайтов с email-регистрацией (testmail.app)")
    print(f"   Домен: {TARGET_URL}")
    print("=" * 60)

    async with AsyncCamoufox(headless=HEADLESS, geoip=True) as browser:
        ctx = await browser.new_context()
        results = {"success": 0, "failed": 0}

        for name, fn in TESTS:
            if name not in targets:
                continue
            log(f"--- {name} ---", "INFO")
            page = await ctx.new_page()
            try:
                ok = await fn(page)
                results["success" if ok else "failed"] += 1
            except Exception as e:
                log(f"{name} — ошибка: {e}", "FAIL")
                save_result(name, "", "ERROR", str(e)[:120])
                results["failed"] += 1
            finally:
                await page.close()

            await asyncio.sleep(random.uniform(3, 6))

    print(f"\n✅ Успешно: {results['success']}  ❌ Ошибки: {results['failed']}")
    print(f"📋 Результаты: {RESULTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
