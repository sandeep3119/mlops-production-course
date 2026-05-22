
import sys
from fastapi.testclient import TestClient
from app.main import app

def test_embed():
    client = TestClient(app)
    response = client.post("/embed", json={"text": "test sentence"})
    assert response.status_code == 200
    data = response.json()
    assert "embedding" in data
    assert isinstance(data["embedding"], list)
    assert len(data["embedding"]) > 0
