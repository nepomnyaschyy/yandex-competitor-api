from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

class SearchRequest(BaseModel):
    keyword: str
    region: str

# 🟢 Красивая метка запуска
print("=" * 50)
print("🚀 Yandex Competitor API запущен!")
print("📡 Ожидание запросов на /api/yandex-competitors")
print("=" * 50)

@app.post("/api/yandex-competitors")
def get_competitors(data: SearchRequest):
    region = data.region
    keyword = data.keyword

    print("📥 Запрос получен:")
    print(f"🌍 Регион: {region}")
    print(f"🔍 Ключевое слово: {keyword}")

    try:
        result = subprocess.run(
            ["python", "yandex_parser.py", region, keyword],
            capture_output=True,
            text=True,
            timeout=180
        )

        print("🟢 STDOUT:")
        print(result.stdout)
        print("🔴 STDERR:")
        print(result.stderr)

        # Попытка декодировать JSON
        try:
            parsed = json.loads(result.stdout)
            return {"results": parsed} if isinstance(parsed, list) else parsed
        except json.JSONDecodeError:
            return {
                "error": "❌ Скрипт не вернул корректный JSON",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    except Exception as e:
        return {"error": f"💥 Ошибка при запуске внешнего парсера: {str(e)}"}
