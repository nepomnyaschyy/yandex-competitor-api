from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

class SearchRequest(BaseModel):
    keyword: str
    region: str

@app.post("/api/yandex-competitors")
def get_competitors(data: SearchRequest):
    try:
        # Получаем данные из тела запроса
        region = data.region
        keyword = data.keyword
        print(f"📦 Получены данные: region={region}, keyword={keyword}")


        # Запуск внешнего скрипта
        result = subprocess.run(
            ["python", "yandex_parser.py", region, keyword],
            capture_output=True,
            text=True,
            timeout=60
        )

        # 🔍 Отладка (можно потом убрать)
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
