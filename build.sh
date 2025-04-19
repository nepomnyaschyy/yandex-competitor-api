#!/bin/bash

echo "📦 Установка зависимостей..."
pip install -r requirements.txt

echo "🌐 Установка браузеров Playwright..."
playwright install --with-deps
