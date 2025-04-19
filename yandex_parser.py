# yandex_parser.py
import sys
import json
from playwright.sync_api import sync_playwright

keyword = sys.argv[1]
region = sys.argv[2]

query = f"{keyword} {region}"
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"https://yandex.ru/search/?text={query}", timeout=60000)
    page.wait_for_timeout(2000)

    if "Вы не робот?" in page.content():
        print(json.dumps({"error": "Яндекс выдал капчу. Попробуй позже или используй прокси."}, ensure_ascii=False))
        browser.close()
        sys.exit(0)

    try:
        page.wait_for_selector("li.serp-item", timeout=10000)
    except:
        print(json.dumps({"error": "⚠️ Элементы результатов не найдены. Возможно, капча или пустая выдача."}, ensure_ascii=False))
        browser.close()
        sys.exit(0)
