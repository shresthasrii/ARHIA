import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agent.router import router
from backend.tools.registry import registry

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.mark.asyncio
async def test_emergency_protocol_brake_failure():
    res = await registry.execute("get_emergency_protocol", {"emergency_type": "brake_failure"})
    assert res.get("success") is True
    data = res.get("result", {})
    assert data["severity"] == "CRITICAL"
    assert "BRAKE FAILURE" in data["title"]
    assert len(data["steps"]) >= 4
    assert any("engine" in s.lower() for s in data["steps"])
    assert any("handbrake" in s.lower() for s in data["steps"])

@pytest.mark.asyncio
async def test_emergency_protocol_cpr():
    res = await registry.execute("get_emergency_protocol", {"emergency_type": "cpr"})
    assert res.get("success") is True
    data = res.get("result", {})
    assert "CPR" in data["title"]
    assert data.get("metronome_bpm") == 110
    assert any("30" in s for s in data["steps"])
    assert any("100" in s or "120" in s for s in data["steps"])

@pytest.mark.asyncio
async def test_emergency_protocol_aquaplaning_and_blowout():
    res_aqua = await registry.execute("get_emergency_protocol", {"emergency_type": "aquaplaning"})
    assert res_aqua.get("success") is True
    assert "AQUAPLANING" in res_aqua["result"]["title"]
    assert any("brake" in s.lower() for s in res_aqua["result"]["steps"])

    res_blow = await registry.execute("get_emergency_protocol", {"emergency_type": "tyre_blowout"})
    assert res_blow.get("success") is True
    assert "BLOWOUT" in res_blow["result"]["title"]
    assert any("wheel" in s.lower() for s in res_blow["result"]["steps"])

@pytest.mark.asyncio
async def test_trigger_emergency_sos():
    res = await registry.execute("trigger_emergency_sos", {
        "incident_description": "Vehicle stalled on highway with brake smoke",
        "severity": "CRITICAL"
    })
    assert res.get("success") is True
    data = res.get("result", {})
    assert data["status"] == "SOS_DISPATCHED"
    assert "location" in data
    assert "emergency_hotlines" in data
    assert "112" in str(data["emergency_hotlines"])

@pytest.mark.asyncio
async def test_router_emergency_fast_path():
    # 1. Brake failure trigger
    res_brake = await router.route_and_execute("My car brakes failed on the highway!")
    assert res_brake is not None
    assert res_brake.get("action") == "emergency_alert"
    assert "BRAKE FAILURE" in res_brake["response"]
    assert res_brake["verified"] is True

    # 2. CPR trigger
    res_cpr = await router.route_and_execute("Help someone collapsed how to do CPR?")
    assert res_cpr is not None
    assert res_cpr.get("action") == "emergency_alert"
    assert "CPR" in res_cpr["response"]
    assert res_cpr["verified"] is True

    # 3. Choking trigger
    res_choke = await router.route_and_execute("Someone is choking on food help!")
    assert res_choke is not None
    assert res_choke.get("action") == "emergency_alert"
    assert "HEIMLICH" in res_choke["response"]
    assert res_choke["verified"] is True

    # 4. Immediate SOS trigger
    res_sos = await router.route_and_execute("Emergency SOS send help immediately")
    assert res_sos is not None
    assert res_sos.get("action") == "emergency_alert"
    assert "EMERGENCY SOS DISPATCH" in res_sos["response"]
    assert res_sos["verified"] is True

def test_emergency_rest_endpoints(client):
    # Hotlines
    resp_hot = client.get("/api/emergency/hotlines")
    assert resp_hot.status_code == 200
    assert "112" in str(resp_hot.json())

    # Protocol
    resp_proto = client.get("/api/emergency/protocol/brake_failure")
    assert resp_proto.status_code == 200
    assert "BRAKE FAILURE" in resp_proto.json().get("title", "")

    # SOS trigger
    resp_sos = client.post("/api/emergency/sos", json={"incident_description": "Test collision alert"})
    assert resp_sos.status_code == 200
    assert resp_sos.json().get("status") == "SOS_DISPATCHED"

    # Medical profile
    resp_med = client.get("/api/emergency/medical-profile")
    assert resp_med.status_code == 200
    assert "profile" in resp_med.json()
