# tests/test_api.py
from unittest.mock import patch
from fastapi.testclient import TestClient
import numpy as np

# Import and mock before app initialization
# Patch model load before importing app
with patch("app.model.load_model"):
    import app.main
    import app.model
    app.model.model_ready = True

client = TestClient(app.main.app)


def test_embed_returns_200():
    with patch("app.model.embed_text", return_value=np.array([0.1] * 384)):
        response = client.post("/embed", json={"text": "hello world"})
        assert response.status_code == 200


def test_embed_returns_correct_shape():
    with patch("app.model.embed_text", return_value=np.array([0.1] * 384)):
        response = client.post("/embed", json={"text": "hello world"})
        assert len(response.json()["embedding"]) == 384


def test_embed_empty_text_returns_400():
    response = client.post("/embed", json={"text": ""})
    assert response.status_code == 400


def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
