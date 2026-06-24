# Camoufox — практическое руководство

Camoufox — стелс-форк Firefox со встроенной защитой от обнаружения.
Патчи применяются на уровне C++, а не JS, поэтому обойти их гораздо сложнее.

## Установка

```bash
pip install camoufox[geoip] python-dotenv
pip install pyyaml --upgrade --ignore-installed
python -m camoufox fetch   # ~700MB, один раз
```

## Базовый шаблон

```python
import asyncio
from camoufox.async_api import AsyncCamoufox

async def main():
    async with AsyncCamoufox(
        headless=False,     # True для сервера
        geoip=True,         # IP = локация браузера
        # proxy={"server": "http://host:port", "username": "u", "password": "p"}
    ) as browser:
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://example.com")
        await page.close()

asyncio.run(main())
```

## Критически важные практики

### 1. Имитируй человеческое поведение

```python
import random

# Случайные паузы между действиями (не меньше 0.5с)
async def human_pause(min_s=0.5, max_s=2.5):
    await page.wait_for_timeout(random.uniform(min_s, max_s) * 1000)

# Печатай по символу, не вставляй сразу
async def human_type(page, selector, text):
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.20))

# Прокрутка страницы перед кликом
async def scroll_and_click(page, selector):
    el = page.locator(selector).first
    await el.scroll_into_view_if_needed()
    await human_pause(0.3, 0.8)
    await el.click()
```

### 2. Пауза между сайтами — обязательна

```python
# Минимум 3-7 секунд между разными сайтами
await asyncio.sleep(random.uniform(3, 7))

# При массовой обработке — случайные длинные паузы
if i % 10 == 0:
    await asyncio.sleep(random.uniform(30, 90))  # раз в 10 сайтов
```

### 3. Один контекст = один аккаунт

```python
# Каждый аккаунт — отдельный контекст браузера (своя куки/localStorage)
context1 = await browser.new_context()  # аккаунт 1
context2 = await browser.new_context()  # аккаунт 2
```

### 4. Прокси (опционально, но сильно помогает)

```python
async with AsyncCamoufox(
    headless=True,
    geoip=True,
    proxy={
        "server": "http://proxy-host:port",
        "username": "login",
        "password": "pass"
    }
) as browser:
    ...
```

Рекомендуемые провайдеры (по fraud score, чем меньше — лучше):
- **Smartproxy** — fraud score 32 (лучший)
- **Bright Data** — fraud score 38
- **Oxylabs** — fraud score 41
- IPRoyal — fraud score 72 (не рекомендуем)

### 5. Работа с testmail.app

```python
from email_helper import make_email, check_inbox, extract_link

# Создать уникальный email для регистрации
tag   = f"site_{int(time.time())}"
email = make_email(tag)  # namespace.site_1234567@inbox.testmail.app

# После отправки формы — ждём письмо
mail = check_inbox(tag, timeout=90)
if mail:
    link = extract_link(mail.get("html", ""), keyword="confirm")
    await page.goto(link)
```

### 6. Отладка — запускай с headless=False

```python
# Для отладки всегда смотри в браузере
async with AsyncCamoufox(headless=False, slow_mo=500) as browser:
    ...
```

## Что делать если сайт банит

| Симптом | Причина | Решение |
|---|---|---|
| Сразу редирект на captcha | Пришли слишком быстро | Увеличь паузы, добавь прокси |
| 403/Cloudflare | Детектирован headless | Убедись что `headless=True` работает у тебя, попробуй `headless="virtual"` |
| Email не приходит | Testmail лаг | Увеличь `timeout` до 120с |
| Аккаунт забанен после регистрации | Один IP на много аккаунтов | Прокси, 1 IP = 1 аккаунт |
| Форма не находится | Изменился HTML | Запусти с `headless=False` и посмотри |

## headless режимы в Camoufox

```python
headless=False          # Видимый браузер (для отладки)
headless=True           # Настоящий headless Firefox
headless="virtual"      # Xvfb виртуальный экран (лучший стелс на сервере)
```

На сервере без GUI:
```bash
# Установить Xvfb
sudo apt install xvfb -y

# Запустить через Xvfb
xvfb-run python3 backlink_bot/test_simple.py
```

## Запуск тестов

```bash
# Простые сайты (без email)
python3 backlink_bot/test_simple.py

# Только один сайт
python3 backlink_bot/test_simple.py telegra.ph

# Сайты с email-регистрацией (нужен testmail.app API key в .env)
python3 backlink_bot/test_email_sites.py

# На сервере через Xvfb
xvfb-run python3 backlink_bot/test_simple.py
```

## Структура .env

```env
TARGET_URL=https://your-domain.com
TARGET_ANCHOR=Your Brand Name

TESTMAIL_APIKEY=your_api_key_here
TESTMAIL_NAMESPACE=your_namespace

PROXY_SERVER=http://host:port
PROXY_USERNAME=
PROXY_PASSWORD=

HEADLESS=true
```

## Какие сайты не требуют email (самые простые)

| Сайт | Тип | Email нужен? |
|---|---|---|
| telegra.ph | Статья | Нет |
| anotepad.com | Заметка | Нет |
| controlc.com | Паста | Нет |
| pastelink.net | Паста | Нет (простая рег.) |
| folkd.com | Закладка | Нет |

## Какие сайты требуют email

| Сайт | Тип | Примечание |
|---|---|---|
| postheaven.net | Блог | Нужно подтвердить |
| over-blog.com | Блог | Нужно подтвердить |
| livejournal.com | Блог | Нужно подтвердить |

---

**Нет open-source решения для reCAPTCHA v2/v3, hCaptcha, Turnstile.**
При наличии CAPTCHA — платный сервис ($1-2 за 1000): 2captcha.com или anti-captcha.com.
Camoufox снижает вероятность показа CAPTCHA за счёт реалистичного браузера.
