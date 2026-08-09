from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_health_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_investigate_empty_query():
    response = client.post("/api/v1/investigate", json={"query": ""})
    assert response.status_code == 400

def test_investigate_missing_query():
    response = client.post("/api/v1/investigate", json={"incident_id": "INC-123"})
    assert response.status_code == 422  # Pydantic validation error
