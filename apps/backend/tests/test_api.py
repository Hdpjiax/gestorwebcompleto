from collections.abc import Generator

from fastapi.testclient import TestClient

from app.main import app, get_store
from app.storage import SQLiteStore


TEST_STORE = SQLiteStore(":memory:")


def override_store() -> Generator[SQLiteStore, None, None]:
    yield TEST_STORE


app.dependency_overrides[get_store] = override_store
client = TestClient(app)


def create_profile(name: str = "Training Profile") -> dict:
    response = client.post(
        "/profiles",
        json={
            "name": name,
            "description": "Profile for controlled exercises",
            "anonymity_level": "medium",
            "camoufox_config": {"headless": True},
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_profile_crud_and_anonymity_level() -> None:
    profile = create_profile()

    fetched = client.get(f"/profiles/{profile['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Training Profile"

    updated = client.put(
        f"/profiles/{profile['id']}/anonymity-level",
        json={"anonymity_level": "high"},
    )
    assert updated.status_code == 200
    assert updated.json()["anonymity_level"] == "high"

    deleted = client.delete(f"/profiles/{profile['id']}")
    assert deleted.status_code == 204

    missing = client.get(f"/profiles/{profile['id']}")
    assert missing.status_code == 404


def test_launch_stop_stubs() -> None:
    profile = create_profile("Launchable")

    launched = client.post(f"/profiles/{profile['id']}/launch")
    assert launched.status_code == 200
    assert launched.json()["status"] in {"stubbed", "prepared"}
    assert launched.json()["proxy_port"] >= 9100 + profile["id"]

    running = client.get(f"/profiles/{profile['id']}")
    assert running.json()["is_running"] is True

    session = client.get(f"/profiles/{profile['id']}/session")
    assert session.status_code == 200
    assert session.json()["profile_id"] == profile["id"]

    proxy = client.get(f"/profiles/{profile['id']}/proxy")
    assert proxy.status_code == 200
    assert proxy.json()["profile_id"] == profile["id"]
    assert proxy.json()["port"] == launched.json()["proxy_port"]

    stopped = client.post(f"/profiles/{profile['id']}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopped"

    not_running = client.get(f"/profiles/{profile['id']}")
    assert not_running.json()["is_running"] is False


def test_flows_and_replay_stub() -> None:
    flows = client.get("/flows")
    assert flows.status_code == 200
    assert len(flows.json()) >= 1

    flow_id = flows.json()[0]["id"]
    replay = client.post(f"/flows/{flow_id}/replay")
    assert replay.status_code == 200
    assert replay.json()["status"] == "stubbed"


def test_anonymity_presets() -> None:
    response = client.get("/anonymity/presets")
    assert response.status_code == 200
    presets = response.json()
    assert {preset["level"] for preset in presets} == {"low", "medium", "high"}


def test_frontend_compatibility_endpoints() -> None:
    requests = client.get("/interceptor/requests")
    assert requests.status_code == 200
    assert requests.json()[0]["host"] == "training.portal.local"

    browser = client.post(
        "/browser/open",
        json={"profileId": "1", "url": "https://training.portal.local/login"},
    )
    assert browser.status_code == 200
    assert browser.json()["status"] == "stubbed"


def test_record_http_flow_redacts_sensitive_headers_and_replays() -> None:
    profile = create_profile("Intercepted")
    created = client.post(
        "/interceptor/flows",
        json={
            "profile_id": profile["id"],
            "method": "GET",
            "scheme": "https",
            "host": "training.portal.local",
            "path": "/account",
            "status_code": 200,
            "request_headers": {"Authorization": "Bearer secret", "Accept": "application/json"},
            "response_headers": {"Set-Cookie": "sid=secret", "Content-Type": "application/json"},
            "resource_type": "xhr",
        },
    )
    assert created.status_code == 201
    flow = created.json()
    assert flow["request_headers"]["Authorization"] == "[redacted]"
    assert flow["response_headers"]["Set-Cookie"] == "[redacted]"

    listed = client.get(f"/interceptor/flows?profile_id={profile['id']}")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == flow["id"]

    requests = client.get(f"/interceptor/requests?profile_id={profile['id']}")
    assert requests.status_code == 200
    assert requests.json()[0]["host"] == "training.portal.local"

    replay = client.post(f"/interceptor/flows/{flow['id']}/replay", json={"headers": {"X-Lab": "ok"}})
    assert replay.status_code == 200
    assert replay.json()["status"] == "stubbed"


def test_out_of_scope_flow_blocks_replay() -> None:
    profile = create_profile("Out of scope")
    created = client.post(
        "/interceptor/flows",
        json={
            "profile_id": profile["id"],
            "method": "POST",
            "host": "external.example",
            "path": "/login",
            "status_code": 200,
            "in_scope": False,
        },
    )
    assert created.status_code == 201
    assert created.json()["replayable"] is False

    replay = client.post(f"/interceptor/flows/{created.json()['id']}/replay")
    assert replay.status_code == 200
    assert replay.json()["status"] == "blocked"


def test_flow_websocket_echo() -> None:
    with client.websocket_connect("/ws/flows/123") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connected"
        assert connected["profile_id"] == 123

        websocket.send_text("ping")
        echo = websocket.receive_json()
        assert echo["type"] == "echo"
        assert echo["message"] == "ping"
