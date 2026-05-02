Chat AI — кратко
Цель: минимальный бэкенд FastAPI + фронтенд для чата.

1. Установить Python 3.11 и зависимости:
```
pip install -r backend/requirements.txt
```
2. Установить переменную окружения:
- Linux/macOS: `export OPENAI_API_KEY=your_key`
- Windows (PowerShell): `$env:OPENAI_API_KEY="your_key"`
3. Запустить сервер:
```
uvicorn backend.app.main:app --reload --port 8000
```
4. Пример запроса:
```
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"session_id":"s1","message":"Привет"}'
```

### Что сделано
- backend/app/main.py — FastAPI /chat
- backend/requirements.txt
- backend/Dockerfile
- .github/workflows/ci-backend.yml

### Дальше
- Создать простой фронтенд (одна HTML-страница).
- Настроить деплой (GitHub Actions → Render/Heroku).
