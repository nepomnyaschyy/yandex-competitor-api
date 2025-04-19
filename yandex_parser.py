import sys
import json
import random
import time
import base64
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# === Настройки ===
froxy_login = "yQqnOlDHz02LAm20"
froxy_password = "mobile;;;;"
capmonster_api_key = "d495ca5c5f7003dee37df6a1789b6716"

# Рабочие порты (из проверки)
working_ports = [
    9000, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9011, 9012, 9013, 9014, 9015, 9016, 9017, 9018, 9019,
    9020, 9021, 9022, 9023, 9024, 9025, 9026, 9027, 9028, 9029, 9030, 9031, 9032, 9033, 9034, 9035, 9036, 9037,
    9038, 9039, 9041, 9042, 9043, 9044, 9045, 9046, 9047, 9048, 9049, 9050, 9051, 9052, 9053, 9054, 9055, 9056,
    9057, 9058, 9059, 9060, 9061, 9062, 9063, 9064, 9065, 9066, 9067, 9068, 9069, 9070, 9071, 9072, 9073, 9074,
    9075, 9076, 9077, 9078, 9079, 9080, 9081, 9082, 9083, 9084, 9085, 9086, 9088, 9089, 9090, 9091, 9092, 9093,
    9094, 9095, 9096, 9097, 9098, 9099, 9100, 9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109, 9110, 9111,
    9112, 9113, 9114, 9115, 9116, 9117, 9118, 9119, 9120, 9121, 9122, 9123, 9124, 9125, 9126, 9127, 9128, 9129,
    9130, 9131, 9132, 9133, 9134, 9135, 9136, 9137, 9139, 9140, 9141, 9143, 9144, 9145, 9146, 9147, 9148, 9149,
    9150, 9151, 9152, 9153, 9154, 9155, 9156, 9157, 9158, 9159, 9161, 9162, 9163, 9164, 9165, 9166, 9167, 9168,
    9169, 9170, 9171, 9172, 9173, 9174, 9175, 9176, 9177, 9178, 9179, 9180, 9181, 9182, 9183, 9184, 9185, 9186,
    9187, 9188, 9189, 9190, 9191, 9192, 9193, 9194, 9195, 9196, 9197, 9198, 9199
]

# === Функция решения капчи через CapMonster ===
def solve_captcha(image_bytes):
    task_payload = {
        "clientKey": capmonster_api_key,
        "task": {
            "type": "ImageToTextTask",
            "body": base64.b64encode(image_bytes).decode("utf-8")
        }
    }
    task_resp = requests.post("https://api.capmonster.cloud/createTask", json=task_payload).json()
    if task_resp.get("errorId") != 0:
        return None

    task_id = task_resp["taskId"]
    for _ in range(20):
        time.sleep(2)
        res = requests.post("https://api.capmonster.cloud/getTaskResult", json={
            "clientKey": capmonster_api_key,
            "taskId": task_id
        }).json()
        if res.get("status") == "ready":
            return res["solution"]["text"]
    return None

# === Основной код ===
region = sys.argv[1]
keyword = sys.argv[2]
print(f"📦 Получены данные: region={region}, keyword={keyword}")

for port in random.sample(working_ports, len(working_ports)):
    proxy = f"http://{froxy_login}:{froxy_password}@proxy.froxy.com:{port}"
    print(f"🌐 Пробуем прокси: {proxy}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(proxy={"server": proxy}, headless=True)
            context = browser.new_context()
            page = context.new_page()
            url = f"https://yandex.ru/search/?text={keyword}+в+{region}"
            page.goto(url, timeout=15000)

            # Ждём либо результаты, либо капчу
            if page.is_visible("form[action*='showcaptcha']"):
                print("🔐 Обнаружена капча! Пробуем решить через CapMonster...")

                try:
                    img = page.query_selector("form img")
                    if not img:
                        raise Exception("Картинка с капчей не найдена.")

                    src = img.get_attribute("src")
                    captcha_url = "https://yandex.ru" + src
                    image_bytes = requests.get(captcha_url, proxies={"http": proxy, "https": proxy}, timeout=10).content

                    print("📤 Отправляем капчу на CapMonster...")
                    text = solve_captcha(image_bytes)
                    print("📥 Ответ от CapMonster:", text)

                    if not text:
                        raise Exception("🛑 Не удалось распознать капчу через CapMonster.")

                    input_box = page.query_selector("input[name='rep']")  # поле для ввода капчи
                    input_box.fill(text)
                    page.click("button[type='submit']")
                    time.sleep(3)
                except Exception as e:
                    print(f"⚠️ Ошибка: {e}")
                    continue

            # Пробуем найти сайты конкурентов
            page.wait_for_selector("li.serp-item", timeout=10000)
            items = page.query_selector_all("li.serp-item")
            results = []
            for item in items[:3]:  # только 3 конкурента
                link = item.query_selector("a.Link")
                href = link.get_attribute("href") if link else None
                if href:
                    results.append(href)

            browser.close()
            print(json.dumps(results, ensure_ascii=False))
            sys.exit(0)

    except PlaywrightTimeoutError:
        print("⏱️ Превышено время ожидания.")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")

print(json.dumps({"error": "🛑 Все прокси дали сбой или Яндекс выдал капчу."}, ensure_ascii=False))
