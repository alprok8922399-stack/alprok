import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def test_smoke():
    resp = requests.post(f"{BASE_URL}/chat", json={"message": "Привет"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    
