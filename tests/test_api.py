import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.routes import get_vector_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    get_vector_store().reset()
    yield



def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "details" in response.json()

def test_query_empty_db():
    response = client.post("/query", json={"question": "Non-existent query data"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This information is not available in the provided documents."
    assert data["sources"] == []
    assert "latency_ms" in data

def test_ingestion_and_query_flow(tmp_path):
    # Write a temporary text file to ingest
    temp_file = tmp_path / "pricing.txt"
    content = "DocuMind AI Pricing Plan: The Enterprise Plan ($99/mo) includes API access."
    temp_file.write_text(content, encoding="utf-8")

    # Ingest the file
    with open(temp_file, "rb") as f:
        ingest_resp = client.post(
            "/ingest",
            files={"file": ("pricing.txt", f, "text/plain")}
        )
    
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["message"] == "Ingestion successful"
    assert ingest_resp.json()["filename"] == "pricing.txt"

    # Query the ingested data
    query_resp = client.post(
        "/query",
        json={"question": "Which plan includes API access?"}
    )
    
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert "pricing.txt" in data["sources"]
    assert "Enterprise Plan" in data["answer"]
