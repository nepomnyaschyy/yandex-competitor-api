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
            return {"error": "❌ Скрипт не вернул корректный JSON"}

    except Exception as e:
        return {"error": f"💥 Ошибка при запуске внешнего парсера: {str(e)}"}
