import sys
import json
from playwright.sync_api import sync_playwright

# Получаем параметры из командной строки
region = sys.argv[1]
keyword = sys.argv[2]

print(f"📦 Получены данные: region={region}, keyword={keyword}")

# Настройка прокси
proxy_config = {
    "server": "http://95.181.157.185:8000",
    "username": "z8m9cu",
    "password": "zMmuCv"
}

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy_config
        )
        page = browser.new_page()
        page.goto(f"https://yandex.ru/search/?text={keyword}+{region}", timeout=60000)

        # Ждём появления результатов
        page.wait_for_selector("li.serp-item", timeout=10000)

        items = page.query_selector_all("li.serp-item")
        results = []

        for item in items[:10]:  # Берём только первые 10
