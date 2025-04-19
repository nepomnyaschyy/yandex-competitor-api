import sys
import time
import json
from playwright.sync_api import sync_playwright
import requests

# === Параметры из аргументов ===
region = sys.argv[1]
keyword = sys.argv[2]
print(f"📦 Получены данные: region={region}, keyword={keyword}")

# === Настройки прокси ===
proxies = [
    {
        "server": "http://proxy.froxy.com:9000",
        "username": "yQqnOlDHz02LAm20",
        "password": ""
    }
]

# === Настройки CapMonster ===
CAPMONSTER_API_KEY = "d495ca5c5f7003dee37df6a1789b6716"

def solve_captcha(image_bytes):
    print("📤 Отправляем капчу на CapMonster...")
    task_payload = {
        "clientKey": CAPMONSTER_API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": image_bytes.encode("base64") if hasattr(image_bytes, "encode") else "",
        }
    }
    try:
        response = requests.post("https://api.capmonster.cloud/createTask", json=task_payload)
        task_id = response.json().get("taskId")

        if not task_id:
            return None

        for _ in range(10):
            time.sleep(5)
            result = requests.post("https://api.capmonster.cloud/getTaskResult", json={
                "clientKey": CAPMONSTER_API_KEY,
                "taskId": task_id
            }).json()
            if result.get("status") == "ready":
                return result.get("solution", {}).get("text")
        return None
    except Exception as e:
        print(f"⚠️ Ошибка при распознавании капчи: {e}")
        return None

def extract_links(page):
    items = page.query_selector_all("li.serp-item")
    results = []
    for item in items[:10]:
        link = item.query_selector("a.Link")
        if link:
            href = link.get_attribute("href")
            if href:
                results.append(href)
    return results

with sync_playwright() as p:
    for proxy in proxies:
        print(f"🌐 Пробуем прокси: {proxy['server']}")
        try:
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": proxy["server"],
                    "username": proxy["username"],
                    "password": proxy["password"]
                }
            )
            context = browser.new_context()
            page = context.new_page()

            search_url = f"https://yandex.ru/search/?text={keyword}%20в%20{region}"
            page.goto(search_url, timeout=15000)
            page.wait_for_selector("li.serp-item", timeout=10000)

            links = extract_links(page)
            browser.close()
            print(json.dumps(links, ensure_ascii=False))
            sys.exit(0)

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

    print(json.dumps({
        "error": "🛑 Все прокси дали сбой или Яндекс выдал капчу. Попробуй позже или добавь новые прокси."
    }, ensure_ascii=False))
