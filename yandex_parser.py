import sys
import json
import random
import time
import requests
from playwright.sync_api import sync_playwright

# Данные из аргументов
region = sys.argv[1]
keyword = sys.argv[2]
print(f"📦 Получены данные: region={region}, keyword={keyword}")

# Параметры CapMonster
CAPMONSTER_API_KEY = "d495ca5c5f7003dee37df6a1789b6716"
CAPTCHA_SITEKEY = ""
CAPTCHA_URL = "https://yandex.ru/search/"

# Прокси от Froxy (авторизация по логину/паролю)
PROXY_LOGIN = "yQqnOlDHz02LAm20"
PROXY_PASSWORD = "mobile;;;;"
PROXY_HOST = "proxy.froxy.com"
PROXY_PORTS = list(range(9000, 9200))

# Получить список конкурентных сайтов из SERP
def parse_results(page):
    page.wait_for_selector("li.serp-item", timeout=10000)
    items = page.query_selector_all("li.serp-item")
    results = []
    for item in items[:3]:
        link = item.query_selector("a.Link")
        href = link.get_attribute("href") if link else None
        if href:
            results.append(href)
    return results

# Проверка наличия капчи
def is_captcha(page):
    return page.query_selector(".CheckboxCaptcha-Anchor") or page.query_selector("#captcha")

# Решение капчи через CapMonster
def solve_captcha():
    print("\ud83d\udce4 Отправляем капчу на CapMonster...")
    return {
        "errorId": 1,
        "errorCode": "ERROR_ZERO_CAPTCHA_FILESIZE",
        "errorDescription": "Симуляция - изображение не передано"
    }

# Основной цикл обхода прокси
with sync_playwright() as p:
    for port in PROXY_PORTS:
        proxy = f"http://{PROXY_LOGIN}:{PROXY_PASSWORD}@{PROXY_HOST}:{port}"
        print(f"🌐 Пробуем прокси: {proxy}")
        try:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": f"http://{PROXY_HOST}:{port}", "username": PROXY_LOGIN, "password": PROXY_PASSWORD}
            )
            page = browser.new_page()

            url = f"https://yandex.ru/search/?text={keyword}%20в%20{region}"
            page.goto(url, timeout=15000)

            if is_captcha(page):
                print("🔐 Обнаружена капча! Пробуем решить через CapMonster...")
                solution = solve_captcha()
                print(f"📥 Ответ от CapMonster: {solution}")
                print("⚠️ Ошибка: 🚑 Не удалось распознать капчу через CapMonster.")
                browser.close()
                continue

            results = parse_results(page)
            browser.close()
            print(json.dumps(results, ensure_ascii=False))
            sys.exit(0)

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

print(json.dumps({"error": "🚑 Все прокси дали сбой или Яндекс выдал капчу. Попробуй позже или добавь прокси."}, ensure_ascii=False))
