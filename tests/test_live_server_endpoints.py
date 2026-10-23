import pytest
import os
import io
import wave
import json
import asyncio
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_root_serves_frontend(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ARHIEA" in response.text or "html" in response.text.lower()

def test_api_status_endpoint(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "ARHIEA" in data["app_name"]
    assert "clock" in data
    assert "date" in data
    assert "system_info" in data

def test_chat_math_fast_route(client):
    response = client.post("/api/chat", json={"text": "calculate 45 * 20", "is_voice": False})
    assert response.status_code == 200
    data = response.json()
    assert "900" in data["response"]
    assert data["verified"] is True

def test_chat_flight_booking_multi_turn(client):
    response = client.post("/api/chat", json={"text": "Book flight from Delhi to Mumbai tomorrow", "is_voice": False})
    assert response.status_code == 200
    data = response.json()
    assert data.get("booking_data") is not None
    assert data["booking_data"]["origin"] == "Delhi"
    assert data["booking_data"]["destination"] == "Mumbai"

def test_chat_flight_booking_one_shot(client):
    response = client.post("/api/chat", json={"text": "Book flight from Delhi to Mumbai tomorrow on Google Flights", "is_voice": False})
    assert response.status_code == 200
    data = response.json()
    assert data.get("booking_data") is not None
    assert data["booking_data"]["origin_code"] == "DEL"
    assert data["booking_data"]["dest_code"] == "BOM"

def test_chat_general_ai_knowledge(client):
    response = client.post("/api/chat", json={"text": "Who was Marie Curie?", "is_voice": False})
    assert response.status_code == 200
    data = response.json()
    assert len(data["response"]) > 20
    assert any(term in data["response"].lower() for term in ["curie", "physicist", "chemist", "nobel", "radioactivity", "radium", "science", "marie"])

def test_tts_endpoint(client):
    response = client.post("/api/tts", data={"text": "System is fully operational."})
    assert response.status_code == 200
    data = response.json()
    assert "audio_base64" in data
    assert data["audio_base64"] is not None
    assert len(data["audio_base64"]) > 50

def test_stt_endpoint_with_wav_audio(client):
    # Synthesize small silent WAV
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b'\x00' * 32000) # 1 sec of silence
    buffer.seek(0)

    files = {"file": ("test.wav", buffer, "audio/wav")}
    response = client.post("/api/stt", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data

def test_websocket_ping_pong(client):
    with client.websocket_connect("/ws") as websocket:
        init_msg = websocket.receive_json()
        assert init_msg.get("type") == "init"
        assert "clock" in init_msg

        websocket.send_text(json.dumps({"type": "ping"}))
        pong_msg = websocket.receive_json()
        assert pong_msg.get("type") == "pong"
        assert "clock" in pong_msg
