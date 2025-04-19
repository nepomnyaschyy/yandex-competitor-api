from uuid import uuid4
import os
import sys
import time
import json
import base64
import requests
from playwright.sync_api import sync_playwright

region = sys.argv[1]
keyword = sys.argv[2]

print(f"📦 Получены данные: region={region}, keyword={keyword}")

CAPMONSTER_API_KEY = "d495ca5c5f7003dee37df6a1789b6716"

proxies = [
    "http://user283783:gz8nsj@46.174.196.141:9687",
    "http://user283783:gz8nsj@46.174.196.76:9687",
]

def solve_captcha(image_path):
    with open(image_path, "rb") as image_file:
        b64_image = base64.b64encode(image_file.read()).decode("utf-8")

    task_payload = {
        "clientKey": CAPMONSTER_API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": b64_image
        }
    }

    print("📤 Отправляем капчу на CapMonster...")
    task_create = requests.post("https://api.capmonster.cloud/createTask", json=task_payload).json()
    if task_create.get("errorId") != 0:
        return {"error": task_create.get("errorDescription", "Ошибка CapMonster при создании задачи")}

    task_id = task_create["taskId"]
    for _ in range(30):
        time.sleep(3)
        result = requests.post("https://api.capmonster.cloud/getTaskResult", json={
            "clientKey": CAPMONSTER_API_KEY,
            "taskId": task_id
        }).json()
        if result.get("status") == "ready":
            return result["solution"]["text"]
    return {"error": "🛑 Не удалось распознать капчу через CapMonster."}

results = []

for proxy in proxies:
    print(f"🌐 Пробуем прокси: {proxy}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(proxy={"server": proxy}, headless=True)
            page = browser.new_page()
            page.goto(f"https://yandex.ru/search/?text={keyword} в {region}", timeout=15000)

            if "showcaptcha" in page.url:
                print("🔐 Обнаружена капча! Пробуем решить через CapMonster...")
                image_element = page.query_selector("img")
                if not image_element:
                    raise Exception("🛑 Капча найдена, но не удалось найти элемент <img>.")
                try:
                    image_element.wait_for(state="visible", timeout=5000)
                except:
                    raise Exception("🛑 Изображение капчи не загрузилось за 5 секунд.")
                filename = f"captcha_{uuid4().hex}.png"
                image_element.screenshot(path=filename)

                if os.path.getsize(filename) < 100:
                    raise Exception("🛑 Скриншот капчи оказался пустым или повреждённым.")

                solution = solve_captcha(filename)
                if isinstance(solution, dict) and "error" in solution:
                    print(f"⚠️ Ошибка: {solution['error']}")
                    continue
                page.fill("input[name='rep']", solution)
                page.click("button[type='submit']")
                time.sleep(2)

            page.wait_for_selector("li.serp-item", timeout=10000)
            items = page.query_selector_all("li.serp-item")
            for item in items[:10]:
                link = item.query_selector("a.link")
                if link:
                    href = link.get_attribute("href")
                    if href:
                        results.append(href)
            browser.close()
            break

    except Exception as e:
        print(f"🔁 Капча или ошибка. Пробуем следующий прокси...\n⚠️ Ошибка: {e}")
        continue

if results:
    print(json.dumps(results, ensure_ascii=False))
else:
    print(json.dumps({"error": "🛑 Все прокси дали сбой или Яндекс выдал капчу. Попробуй позже или добавь новые прокси."}, ensure_ascii=False))
