import sys
import json
import time
import requests
from uuid import uuid4
from playwright.sync_api import sync_playwright

region = sys.argv[1]
keyword = sys.argv[2]

print(f"📦 Получены данные: region={region}, keyword={keyword}")

CAPMONSTER_API_KEY = "d495ca5c5f7003dee37df6a1789b6716"

PROXIES = [
    {"server": "http://46.174.196.141:9687", "username": "user283783", "password": "gz8nsj"},
    {"server": "http://46.174.196.76:9687", "username": "user283783", "password": "gz8nsj"},
]

def solve_captcha(filepath):
    with open(filepath, "rb") as f:
        encoded = f.read()

    task_payload = {
        "clientKey": CAPMONSTER_API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": encoded.hex(),
            "phrase": False,
            "case": False
        }
    }

    task_response = requests.post("https://api.capmonster.cloud/createTask", json=task_payload).json()
    task_id = task_response.get("taskId")

    if not task_id:
        return None

    for _ in range(20):
        time.sleep(3)
        result = requests.post("https://api.capmonster.cloud/getTaskResult", json={
            "clientKey": CAPMONSTER_API_KEY,
            "taskId": task_id
        }).json()

        if result.get("status") == "ready":
            return result["solution"]["text"]

    return None

results = []

with sync_playwright() as p:
    for proxy in PROXIES:
        print(f"🌐 Пробуем прокси: {proxy['server']}")
        try:
            browser = p.chromium.launch(
                headless=True,
                proxy=proxy
            )
            context = browser.new_context()
            page = context.new_page()

            page.goto(f"https://yandex.ru/search/?text={keyword}+{region}", timeout=20000)

            if "showcaptcha" in page.url:
                print("🔐 Обнаружена капча! Пробуем решить через CapMonster...")
                image_element = page.query_selector("img")

                if not image_element:
                    raise Exception("🛑 Капча найдена, но не удалось найти изображение.")

                filename = f"captcha_{uuid4().hex}.png"
                image_element.screenshot(path=filename)

                captcha_text = solve_captcha(filename)

                if not captcha_text:
                    raise Exception("🛑 Не удалось распознать капчу через CapMonster.")

                input_field = page.query_selector("input[name='rep']") or page.query_selector("input[type='text']")
                if input_field:
                    input_field.fill(captcha_text)
                    input_field.press("Enter")
                    time.sleep(5)
                else:
                    raise Exception("🛑 Поле для ввода капчи не найдено.")

            page.wait_for_selector("li.serp-item", timeout=10000)
            items = page.query_selector_all("li.serp-item")

            for item in items[:10]:
                title_el = item.query_selector("h2 a")
                link = title_el.get_attribute("href") if title_el else ""
                title = title_el.inner_text().strip() if title_el else ""
                if title and link:
                    results.append({"title": title, "link": link})

            browser.close()
            break  # Успешно — выходим из цикла
        except Exception as e:
            print("🔁 Капча или ошибка. Пробуем следующий прокси...")
            print(f"⚠️ Ошибка: {str(e)}")
            try:
                browser.close()
            except:
                pass
            continue

if results:
    print(json.dumps(results, ensure_ascii=False))
else:
    print(json.dumps({"error": "🛑 Все прокси дали сбой или Яндекс выдал капчу. Попробуй позже или добавь новые прокси."}, ensure_ascii=False))
