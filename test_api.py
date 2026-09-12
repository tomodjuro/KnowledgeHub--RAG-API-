import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/")
    assert response.status_code == 200

def test_upload_endpoints():
    file_path = "./test_docs/test_info.txt"
    assert os.path.exists(file_path), f"Testna datoteka ne postoji: {file_path}"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/v1/upload", 
            files={"file": ("test_info.txt", f, "text/plain")}
        )
    
    # Prihvaćamo 202 Accepted jer se obrada izvodi u pozadini
    assert response.status_code in (200, 202)

def test_reindex_endpoint():
    response = client.post("/api/v1/reindex")
    assert response.status_code in (200, 202)

def test_query_rag():
    payload = {"question": "Što se nalazi u testnim dokumentima?"}
    response = client.post("/api/query", json=payload)
    
    assert response.status_code == 200
    assert "answer" in response.json() or "response" in response.json()