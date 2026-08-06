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
            "scope_statement": "Authorized local lab only",
            "allowed_hosts": ["training.portal.local", "localhost", "127.0.0.1"],
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
    assert "training.portal.local" in fetched.json()["allowed_hosts"]

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
    assert launched.json()["runtime"] == "camoufox"
    assert launched.json()["launch_options"]["user_data_dir"].endswith(str(profile["id"]))

    running = client.get(f"/profiles/{profile['id']}")
    assert running.json()["is_running"] is True

    session = client.get(f"/profiles/{profile['id']}/session")
    assert session.status_code == 200
    assert session.json()["profile_id"] == profile["id"]

    proxy = client.get(f"/profiles/{profile['id']}/proxy")
    assert proxy.status_code == 200
    assert proxy.json()["profile_id"] == profile["id"]
    assert proxy.json()["port"] == launched.json()["proxy_port"]

    browser = client.get(f"/profiles/{profile['id']}/browser")
    assert browser.status_code == 200
    assert browser.json()["profile_id"] == profile["id"]

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

    decision = client.post(
        f"/interceptor/flows/{flow['id']}/decision",
        json={"decision": "drop", "operator": "tester", "reason": "controlled test"},
    )
    assert decision.status_code == 200
    assert decision.json()["decision"] == "drop"

    decisions = client.get(f"/interceptor/flows/{flow['id']}/decisions")
    assert decisions.status_code == 200
    assert decisions.json()[0]["operator"] == "tester"

    blocked_replay = client.post(f"/interceptor/flows/{flow['id']}/replay")
    assert blocked_replay.status_code == 200
    assert blocked_replay.json()["status"] == "blocked"


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
            "in_scope": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["in_scope"] is False
    assert created.json()["replayable"] is False

    replay = client.post(f"/interceptor/flows/{created.json()['id']}/replay")
    assert replay.status_code == 200
    assert replay.json()["status"] == "blocked"


def test_intercept_rule_pauses_matching_flow() -> None:
    profile = create_profile("Rule profile")
    rule = client.post(
        "/interceptor/rules",
        json={
            "profile_id": profile["id"],
            "name": "Pause login posts",
            "method": "POST",
            "host_pattern": "*.portal.local",
            "path_pattern": "/login*",
            "decision": "paused",
        },
    )
    assert rule.status_code == 201
    assert rule.json()["decision"] == "paused"

    listed = client.get(f"/interceptor/rules?profile_id={profile['id']}")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Pause login posts"

    flow = client.post(
        "/interceptor/flows",
        json={
            "profile_id": profile["id"],
            "method": "POST",
            "host": "training.portal.local",
            "path": "/login/session",
            "status_code": 200,
        },
    )
    assert flow.status_code == 201
    assert flow.json()["intercept_decision"] == "paused"

    deleted = client.delete(f"/interceptor/rules/{rule.json()['id']}")
    assert deleted.status_code == 204


def test_flow_websocket_streams_created_flows() -> None:
    profile = create_profile("Realtime profile")
    with client.websocket_connect(f"/ws/flows/{profile['id']}") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connected"
        assert connected["profile_id"] == profile["id"]

        created = client.post(
            "/interceptor/flows",
            json={
                "profile_id": profile["id"],
                "method": "GET",
                "host": "training.portal.local",
                "path": "/realtime",
                "status_code": 200,
            },
        )
        assert created.status_code == 201

        event = websocket.receive_json()
        assert event["type"] == "flow.created"
        assert event["profile_id"] == profile["id"]
        assert event["payload"]["path"] == "/realtime"
