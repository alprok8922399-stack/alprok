from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_smoke_chat():
    resp = client.post("/chat", json={"session_id": "s1", "message": "ping"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # допускаем варианты поля ответа: "reply" или "message"
    assert "reply" in data or "message" in data
  
