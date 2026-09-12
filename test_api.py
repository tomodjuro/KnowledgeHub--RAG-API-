import os
import pytest
from fastapi.testclient import TestClient

# Uvozimo FastAPI app iz glavne skripte
from main import app

# Inicijalizacija TestClienta
client = TestClient(app)

def test_healthcheck():
    """Provjera radi li osnovni root / healthcheck endpoint."""
    response = client.get("/")
    assert response.status_code == 200

def test_upload_endpoints():
    """Provjera slanja datoteke na upload endpoint."""
    file_path = "./test_docs/test_info.txt"
    
    # Provjera postoji li datoteka prije slanja
    assert os.path.exists(file_path), f"Testna datoteka ne postoji na putanji: {file_path}"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/v1/upload", 
            files={"file": ("test_info.txt", f, "text/plain")}
        )
    
    assert response.status_code == 200

def test_reindex_endpoint():
    """Provjera okidanja reindeksiranja baze."""
    response = client.post("/api/v1/reindex")
    assert response.status_code == 200

def test_query_rag():
    """Provjera RAG upita i komunikacije s LLM-om."""
    payload = {
        "question": "Što se nalazi u testnim dokumentima?"
    }
    response = client.post("/api/query", json=payload)
    
    assert response.status_code == 200
    assert "answer" in response.json() or "response" in response.json()