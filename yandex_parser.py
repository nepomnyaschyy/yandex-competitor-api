import sys
import json
from playwright.sync_api import sync_playwright
from time import sleep

region = sys.argv[1]
keyword = sys.argv[2]

print(f"📦 Получены данные: region={region}, keyword={keyword}")

# Список прокси
proxies = [
    {"server": "http://46.174.196.141:9687", "username": "user283783", "password": "gz8nsj"},
    {"server": "http://46.174.196.76:9687", "username": "user283783", "password": "gz8nsj"},
]

success = False
results = []

with sync_playwright() as p:
    for proxy in proxies:
        try:
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": proxy["server"],
                    "username": proxy["username"],
                    "password": proxy["password"]
                }
            )
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
            page = context.new_page()

            page.goto(f"https://yandex.ru/search/?text={keyword}+{region}", timeout=20000)

            # Проверка на капчу
            if "showcaptcha" in page.url:
                print("🔁 Капча. Пробуем следующий прокси...")
                browser.close()
                continue

            page.wait_for_selector("li.serp-item", timeout=10000)
            items = page.query_selector_all("li.serp-item")

            for item in items[:10]:
                title_el = item.query_selector("h2 a")
                link = title_el.get_attribute("href") if title_el else ""
                title = title_el.inner_text().strip() if title_el else ""
                if title and link:
                    results.append({"title": title, "link": link})

            browser.close()
            success = True
            break

        except Exception as e:
            print(f"⚠️ Ошибка с прокси {proxy['server']}: {str(e)}")
            try:
                browser.close()
            except:
                pass
            continue

if success:
    print(json.dumps(results, ensure_ascii=False))
else:
    print(json.dumps({
        "error": "🛑 Все прокси дали сбой или Яндекс выдал капчу. Попробуй позже или добавь новые прокси."
    }, ensure_ascii=False))
