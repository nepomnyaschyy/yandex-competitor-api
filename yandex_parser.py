import sys
import json
from playwright.sync_api import sync_playwright

# Получаем аргументы
region = sys.argv[1]
keyword = sys.argv[2]

print(f"📦 Получены данные: region={region}, keyword={keyword}")

# Прокси-конфигурация
proxy_config = {
    "server": "http://95.181.157.185:8000",
    "username": "z8m9cu",
    "password": "zMmuCv"
}

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=proxy_config)
        page = browser.new_page()
        page.goto(f"https://yandex.ru/search/?text={keyword}+{region}", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # Проверка на капчу по URL
        if "showcaptcha" in page.url:
            print(json.dumps({"error": "🛑 Яндекс выдал капчу (визуальную). Попробуй позже или используй другой прокси."}, ensure_ascii=False))
            browser.close()
            sys.exit()

        try:
            page.wait_for_selector("li.serp-item", timeout=10000)
        except:
            # Сохраняем HTML для отладки
            html = page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)

            print(json.dumps({
                "error": "⏱ Не удалось найти блоки с результатами. Возможно, Яндекс изменил структуру или выдал капчу.",
                "hint": "HTML сохранён в debug.html"
            }, ensure_ascii=False))
            browser.close()
            sys.exit()

        # Сбор результатов
        items = page.query_selector_all("li.serp-item")
        results = []

        for item in items[:10]:
            link = item.query_selector("a.Link")
            if link:
                href = link.get_attribute("href")
                title = link.inner_text()
                results.append({"title": title, "url": href})

        print(json.dumps(results, ensure_ascii=False))
        browser.close()

except Exception as e:
    print(json.dumps({
        "error": f"🛑 Не удалось получить результаты: {str(e)}"
    }, ensure_ascii=False))
