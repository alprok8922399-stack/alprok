## Chat AI — кратко
Цель: минимальный бэкенд FastAPI + фронтенд для чата.

### Быстрый запуск (локально)
1. Установить Python 3.11 и зависимости:
```
pip install -r backend/requirements.txt
```
2. Установить переменную окружения:
- Linux/macOS: `export OPENAI_API_KEY=your_key`
- Windows (PowerShell): `$env:OPENAI_API_KEY="your_key"`
- Или создайте файл .env в backend с содержимым:
```
OPENAI_API_KEY=your_key
```
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
- frontend/index.html
- .env.example

### Дальше
- Создать простой фронтенд (если требуется доработка).
- Настроить деплой (GitHub Actions → Render/Heroku).

Сохраните изменения — внизу в поле "Commit changes" укажите сообщение коммита (например «Replace README with full content») и нажмите «Commit changes».
