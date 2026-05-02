mkdir -p backend
cat > backend/.github-smoke-test.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# Экспорт тестового ключа из .env если есть
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Запускаем uvicorn в фоне
uvicorn app.main:app --host 127.0.0.1 --port 8000 --loop asyncio --workers 1 &
PID=$!
# Ждём пока сервис станет доступен
for i in {1..10}; do
  if curl -sS -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message":"hello"}' >/dev/null 2>&1; then
    echo "smoke test passed"
    kill $PID || true
    exit 0
  fi
  sleep 1
done

echo "smoke test failed"
kill $PID || true
exit 1
EOF
