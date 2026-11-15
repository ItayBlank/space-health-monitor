"""Owner isolation and consent boundaries for local private check-ins."""

import sqlite3

from fastapi.testclient import TestClient

from astra_core import checkins
from server import app


def _client(tmp_path, monkeypatch, crew_id="crew-a", password="safe-demo-password"):
    monkeypatch.setenv("ASTRA_PRIVATE_DATA_DIR", str(tmp_path))
    checkins.provision_crew(crew_id, password)
    client = TestClient(app)
    return client, crew_id, password


def _login(client, crew_id, password):
    return client.post("/api/private/login", json={"crew_id": crew_id, "password": password}, headers={"Origin": "http://testserver"})


def _add(client, mood=4, stress=1, note=""):
    return client.post("/api/private/checkins", json={"mood": mood, "stress": stress, "note": note}, headers={"Origin": "http://testserver"})


def test_authentication_owner_scope_and_session_expiry(tmp_path, monkeypatch):
    first, crew_a, password_a = _client(tmp_path, monkeypatch)
    assert first.get("/api/private/checkins").status_code == 401
    assert first.post("/api/private/checkins", json={"mood": 1, "stress": 5}, headers={"Origin": "http://testserver"}).status_code == 401
    assert first.post("/api/private/login", json={"crew_id": crew_a, "password": password_a}).status_code == 403
    assert _login(first, crew_a, password_a).status_code == 200
    assert first.post("/api/private/checkins", json={"mood": 1, "stress": 5}, headers={"Origin": "http://evil.test"}).status_code == 403
    assert first.post("/api/private/dismiss", json={"triplet_key": "x"}, headers={"Origin": "http://testserver", "Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert first.post("/api/private/logout", json={}, headers={"Origin": "http://evil.test"}).status_code == 403
    assert _login(first, crew_a, "wrong-password").status_code == 200
    assert first.get("/api/private/checkins").headers["cache-control"] == "no-store, private"
    assert _add(first).status_code == 200

    checkins.provision_crew("crew-b", "another-demo-password")
    second = TestClient(app)
    assert _login(second, "crew-b", "another-demo-password").status_code == 200
    assert second.get("/api/private/checkins").json()["entries"] == []
    foreign_id = _add(second, mood=3, stress=2).json()["id"]
    assert first.post("/api/private/consult-requests", json={"entry_ids": [foreign_id], "recipient": "Flight surgeon (local demo)", "consent": True}, headers={"Origin": "http://testserver"}).status_code == 404
    assert second.post("/api/private/dismiss", json={"triplet_key": "foreign"}, headers={"Origin": "http://testserver"}).status_code == 409

    assert first.get("/api/private/checkins", params={"crew_id": "crew-b"}).json()["entries"][0]["mood"] == 4

    token = first.cookies.get(checkins.COOKIE_NAME)
    with checkins._db() as db:
        db.execute("UPDATE sessions SET expires_at=0 WHERE token_hash=?", (checkins.hashlib.sha256(token.encode()).digest(),))
    assert first.get("/api/private/checkins").status_code == 401

    fresh = TestClient(app)
    assert _login(fresh, crew_a, password_a).status_code == 200
    assert fresh.post("/api/private/logout", json={}, headers={"Origin": "http://testserver"}).status_code == 200
    assert fresh.get("/api/private/checkins").status_code == 401


def test_baseline_fixed_dismissal_and_three_consecutive_rule(tmp_path, monkeypatch):
    client, crew_id, password = _client(tmp_path, monkeypatch)
    assert _login(client, crew_id, password).status_code == 200
    for _ in range(3):
        _add(client, mood=4, stress=1)
    current = client.get("/api/private/checkins").json()
    assert current["trend"]["baseline_ready"] is False
    assert current["trend"]["baseline_count"] == 3
    assert len(current["entries"]) == 3

    for _ in range(2):
        _add(client, mood=4, stress=1)
    # An isolated dip is not enough.
    _add(client, mood=2, stress=1)
    _add(client, mood=4, stress=1)
    _add(client, mood=4, stress=1)
    current = client.get("/api/private/checkins").json()
    assert current["trend"]["baseline_ready"] is True
    assert current["trend"]["baseline_count"] == 5
    assert current["trend"]["prompt"] is False

    # A dimension-mixed triplet is not a 3-consecutive trend in either dimension.
    measured = [dict(id=str(i), mood=4, stress=1, synthetic=False) for i in range(5)]
    measured += [dict(id="m1", mood=2, stress=1, synthetic=False),
                 dict(id="s", mood=4, stress=3, synthetic=False),
                 dict(id="m2", mood=2, stress=1, synthetic=False)]
    assert checkins._trend(measured, set())["prompt"] is False

    _add(client, mood=1, stress=1)
    _add(client, mood=1, stress=1)
    _add(client, mood=1, stress=1)
    current = client.get("/api/private/checkins").json()
    assert current["trend"]["prompt"] is True
    key = current["trend"]["triplet_key"]
    assert client.post("/api/private/dismiss", json={"triplet_key": key}, headers={"Origin": "http://testserver"}).status_code == 200
    assert client.get("/api/private/checkins").json()["trend"]["prompt"] is False
    _add(client, mood=1, stress=1)
    assert client.get("/api/private/checkins").json()["trend"]["prompt"] is True


def test_consent_selected_entries_and_synthetic_demos_are_isolated(tmp_path, monkeypatch):
    client, crew_id, password = _client(tmp_path, monkeypatch)
    assert _login(client, crew_id, password).status_code == 200
    assert _add(client, mood=0, stress=1).status_code == 422
    assert _add(client, mood=4, stress=6).status_code == 422
    for _ in range(5):
        _add(client, mood=4, stress=1, note="personal")
    one = _add(client, mood=3, stress=2, note="selected-only").json()["id"]
    two = _add(client, mood=2, stress=3, note="not-selected").json()["id"]
    assert client.post("/api/private/consult-requests", json={"entry_ids": [one], "recipient": "Flight surgeon (local demo)", "consent": False}, headers={"Origin": "http://testserver"}).status_code == 400
    assert client.post("/api/private/consult-requests", json={"entry_ids": [two], "recipient": "Flight surgeon (local demo)", "consent": True}, headers={"Origin": "http://testserver"}).status_code == 200
    assert client.post("/api/private/consult-requests", json={"entry_ids": ["foreign-id"], "recipient": "Flight surgeon (local demo)", "consent": True}, headers={"Origin": "http://testserver"}).status_code == 404

    with checkins._db() as db:
        selected = db.execute("SELECT selected_entries,status FROM consult_requests").fetchone()
        assert selected["selected_entries"] == two
        assert selected["status"] == "locally_recorded_not_delivered"
    original_count = len(client.get("/api/private/checkins").json()["entries"])
    assert client.post("/api/private/demo", json={}, headers={"Origin": "http://testserver"}).status_code == 200
    data = client.get("/api/private/checkins").json()
    assert len(data["entries"]) == original_count
    assert len(data["demo_entries"]) == 16
    assert [case["trend"]["prompt"] for case in data["demo_cases"]] == [False, True]
    assert all(entry["synthetic"] for entry in data["demo_entries"])


def test_high_stress_trend_and_history_survive_store_reopen(tmp_path, monkeypatch):
    client, crew_id, password = _client(tmp_path, monkeypatch)
    assert _login(client, crew_id, password).status_code == 200
    for _ in range(5):
        _add(client, mood=4, stress=1)
    for _ in range(3):
        _add(client, mood=4, stress=3)
    assert client.get("/api/private/checkins").json()["trend"]["stress_streak"] is True

    token = client.cookies.get(checkins.COOKIE_NAME)
    reopened = TestClient(app)
    reopened.cookies.set(checkins.COOKIE_NAME, token, path="/api/private")
    result = reopened.get("/api/private/checkins")
    assert result.status_code == 200
    assert len(result.json()["entries"]) == 8
    assert result.json()["trend"]["prompt"] is True
