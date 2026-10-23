import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.knowledge_engine import knowledge_engine

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_teach_and_search_concept():
    res = knowledge_engine.teach_concept(
        topic="Mitochondria",
        content="Mitochondria are membrane-bound cell organelles that generate most of the chemical energy needed to power the cell's biochemical reactions.",
        category="Biology & Medicine",
        summary="The powerhouse of eukaryotic cells generating ATP.",
        keywords="mitochondria, atp, cell biology, powerhouse, organelle",
        source="user_taught"
    )
    assert res["status"] == "success"
    assert res["topic"] == "Mitochondria"

    # Search by topic
    results = knowledge_engine.search_knowledge("Tell me about Mitochondria", limit=1)
    assert len(results) > 0
    assert results[0]["topic"] == "Mitochondria"
    assert "powerhouse" in results[0]["summary"].lower() or "power" in results[0]["summary"].lower()

def test_detect_and_learn_from_chat():
    text = "Learn that the speed of sound in air is approximately 343 meters per second"
    ack = knowledge_engine.detect_and_learn_from_chat(text)
    assert ack is not None
    assert ack["tool"] == "teach_concept"
    assert "speed of sound" in ack["topic"].lower()
    assert ack["verified"] is True

    # Check search recall
    search_res = knowledge_engine.search_knowledge("speed of sound", limit=1)
    assert len(search_res) > 0
    assert "343" in search_res[0]["content"]

def test_train_from_text_multiple_concepts():
    training_data = """
# Rust Ownership Model
Rust uses an ownership system with rules that the compiler checks at compile time to ensure memory safety without a garbage collector.

# Golang Goroutines
Goroutines are lightweight threads managed by the Go runtime with a tiny initial stack of only 2KB.
"""
    train_res = knowledge_engine.train_from_text(training_data, category="Programming Languages")
    assert train_res["status"] == "success"
    assert train_res["concepts_learned"] >= 2
    assert any("Rust" in t for t in train_res["topics"])
    assert any("Golang" in t or "Goroutines" in t for t in train_res["topics"])

def test_knowledge_stats():
    stats = knowledge_engine.get_stats()
    assert stats["total_concepts"] >= 5
    assert "categories" in stats
    assert "sources" in stats

def test_knowledge_rest_api_lifecycle(client):
    # 1. Teach via API
    teach_payload = {
        "topic": "Newton's First Law of Motion",
        "content": "An object at rest stays at rest and an object in motion stays in motion with the same speed and direction unless acted upon by an unbalanced external force.",
        "category": "Physics & Mechanics",
        "summary": "Law of Inertia",
        "keywords": "inertia, newton, force, motion, physics"
    }
    post_res = client.post("/api/knowledge/teach", json=teach_payload)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "success"
    concept_id = data["id"]

    # 2. Get list via API
    get_res = client.get("/api/knowledge?category=Physics & Mechanics")
    assert get_res.status_code == 200
    concepts = get_res.json()["concepts"]
    assert any(c["id"] == concept_id for c in concepts)

    # 3. Get stats via API
    stats_res = client.get("/api/knowledge/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_concepts"] > 0

    # 4. Ingest document via API
    doc_payload = {
        "text": "# Redis In-Memory Store\nRedis is an open-source, in-memory data structure store used as a database, cache, streaming engine, and message broker.",
        "category": "Databases"
    }
    train_res = client.post("/api/knowledge/train", json=doc_payload)
    assert train_res.status_code == 200
    assert train_res.json()["concepts_learned"] >= 1

    # 5. Delete concept
    del_res = client.delete(f"/api/knowledge/{concept_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

def test_chat_with_brain_knowledge(client):
    # Query CPR - should retrieve directly from ARHIEA's brain
    chat_res = client.post("/api/chat", json={"text": "What are the steps for CPR?", "is_voice": False})
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "cpr" in data["response"].lower() or "chest compressions" in data["response"].lower()
    assert any(w in data["response"].lower() for w in ["compressions", "breaths", "30", "100-120"])
