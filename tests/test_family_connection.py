"""Consent, role separation, and delivery for the Family Connection demo."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import server
from astra_core import checkins, family_connection, pvt
from hal2030.downlink import DownlinkService


OWNER = "/api/private/family"
FAMILY = "/api/family"
ORIGIN = {"Origin": "http://testserver"}
PASSWORD = "safe-local-test-password"
NOW = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def link(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRA_PRIVATE_DATA_DIR", str(tmp_path / "private"))
    monkeypatch.setattr(pvt, "_PATH", tmp_path / "pvt.json")
    monkeypatch.setattr(pvt, "utc_now", lambda: NOW)
    simulated = DownlinkService(tmp_path / "public-downlink")
    simulated.latency_s = 3
    simulated.set_connected(False)
    monkeypatch.setattr(server, "get_downlink", lambda: simulated)
    monkeypatch.setattr(family_connection, "get_downlink", lambda: simulated)
    return simulated


def _client(crew_id):
    checkins.provision_crew(crew_id, PASSWORD)
    client = TestClient(server.app)
    login = client.post(
        "/api/private/login", json={"crew_id": crew_id, "password": PASSWORD}, headers=ORIGIN
    )
    assert login.status_code == 200
    return client


def _post(client, suffix, **body):
    return client.post(f"{OWNER}{suffix}", json=body, headers=ORIGIN)


def _enable(client, recipient):
    response = _post(client, "/enable", recipient=recipient)
    assert response.is_success, response.text
    code = response.json()["pairing_code"]
    assert code and code not in client.get(OWNER).text
    return {"Authorization": f"Bearer {code}", **ORIGIN}


def _preview(client, *fields):
    response = _post(client, "/preview", fields=fields)
    assert response.is_success, response.text
    return response.json()


def _approve(client, preview):
    response = _post(client, "/reports", preview_id=preview["preview_id"])
    assert response.is_success, response.text
    return response.json()


def _add_checkin(client, mood):
    response = client.post(
        "/api/private/checkins",
        json={"mood": mood, "stress": 5, "note": "owner-only reflection"},
        headers=ORIGIN,
    )
    assert response.is_success, response.text


def test_family_roles_are_isolated_and_owner_mutations_require_same_origin(link):
    anonymous = TestClient(server.app)
    assert anonymous.get(OWNER).status_code == 401
    assert anonymous.get(FAMILY).status_code == 401
    assert anonymous.get(FAMILY, headers={"Authorization": "Bearer invalid"}).status_code == 401

    anton = _client("anton")
    emily = _client("emily")
    assert not anton.get(OWNER).json()["enabled"]
    assert _post(anton, "/preview", fields=["mood"]).status_code == 409
    assert anton.post(f"{OWNER}/enable", json={"recipient": "Alex"}).status_code == 403
    anton_family = _enable(anton, "Alex")
    emily_family = _enable(emily, "Morgan")
    assert anton.get(FAMILY).status_code == 401
    assert anonymous.get(OWNER, headers=anton_family).status_code == 401
    assert anonymous.get(FAMILY, headers=anton_family).json()["recipient"] == "Alex"
    assert anonymous.get(FAMILY, headers=emily_family).json()["recipient"] == "Morgan"

    preview = _preview(anton, "mood")
    assert _post(emily, "/reports", preview_id=preview["preview_id"]).status_code == 404
    packet = _approve(anton, preview)
    assert _post(emily, f"/reports/{packet['id']}/cancel").status_code == 404
    assert emily.get(OWNER).json()["reports"] == []


def test_preview_and_report_send_only_approved_server_values(link):
    anton = _client("anton")
    family = TestClient(server.app)
    family_headers = _enable(anton, "Alex")
    assert anton.post("/api/private/demo", headers=ORIGIN).is_success
    empty = _preview(anton, "mood", "sleep")
    assert empty["content"] == {"mood": None, "sleep_minutes": None}
    _add_checkin(anton, mood=2)
    pvt.add_sleep_log(
        "anton",
        [{"start_utc": (NOW - timedelta(hours=8)).isoformat(),
          "end_utc": (NOW - timedelta(hours=3)).isoformat()}],
        complete=True,
    )
    assert _preview(anton, "sleep")["content"] == {"sleep_minutes": 300}
    preview = _preview(anton, "mood", "sleep")
    assert preview["content"] == {"mood": 2, "sleep_minutes": 300}
    _add_checkin(anton, mood=5)
    tampered = _post(anton, "/reports", preview_id=preview["preview_id"], content={"mood": 5})
    assert tampered.status_code == 422
    packet = _approve(anton, preview)
    assert packet["content"] == preview["content"]
    assert _post(anton, "/reports", preview_id=preview["preview_id"]).status_code == 404
    assert family.get(FAMILY, headers=family_headers).json()["reports"] == []

    link.set_connected(True)
    assert _post(anton, "/advance", seconds=2).json()["delivered"] == 0
    assert _post(anton, "/advance", seconds=1).json()["delivered"] == 1
    reports = family.get(FAMILY, headers=family_headers).json()["reports"]
    assert len(reports) == 1
    assert reports[0]["content"] == {"mood": 2, "sleep_minutes": 300}
    assert reports[0]["status"] == "sent"
    assert _post(anton, f"/reports/{packet['id']}/cancel").status_code == 409
    public = family.get("/api/hal/downlink")
    assert public.is_success
    assert public.json()["queue"] == []
    assert family.get(f"/api/hal/downlink/packet/{packet['id']}").status_code == 404


def test_offline_cancellation_and_revocation_invalidate_pending_shares(link):
    anton = _client("anton")
    family = TestClient(server.app)
    family_headers = _enable(anton, "Alex")
    first = _approve(anton, _preview(anton, "mood"))
    second = _approve(anton, _preview(anton, "sleep"))
    pending_preview = _preview(anton, "mood")
    assert _post(anton, "/advance", seconds=30).json()["delivered"] == 0
    assert first["status"] == second["status"] == "queued"
    canceled = _post(anton, f"/reports/{first['id']}/cancel")
    assert canceled.is_success and canceled.json()["status"] == "canceled"
    assert _post(anton, "/revoke").json() == {"enabled": False}
    assert family.get(FAMILY, headers=family_headers).status_code == 401

    link.set_connected(True)
    new_family_headers = _enable(anton, "Alex")
    assert new_family_headers != family_headers
    assert _post(anton, "/reports", preview_id=pending_preview["preview_id"]).status_code == 404
    assert _post(anton, "/advance", seconds=30).json()["delivered"] == 0
    assert family.get(FAMILY, headers=new_family_headers).json()["reports"] == []


def test_family_reply_waits_for_link_and_arrives_only_in_owner_inbox(link):
    anton = _client("anton")
    emily = _client("emily")
    family = TestClient(server.app)
    credentials = _enable(anton, "Alex")
    _enable(emily, "Morgan")
    reply_text = "Thinking of you from the garden."
    reply = family.post(f"{FAMILY}/replies", json={"text": reply_text}, headers=credentials)
    assert reply.is_success, reply.text
    sent = reply.json()
    assert sent["status"] == "queued"
    assert anton.get(OWNER).json()["inbox"] == []
    assert _post(anton, "/advance", seconds=10).json()["delivered"] == 0
    link.set_connected(True)
    assert _post(emily, "/advance", seconds=10).json()["delivered"] == 0
    assert _post(anton, "/advance", seconds=3).json()["delivered"] == 1

    messages = anton.get(OWNER).json()["inbox"]
    assert [(entry["id"], entry["text"]) for entry in messages] == [(sent["id"], reply_text)]
    assert emily.get(OWNER).json()["inbox"] == []
    assert family.get(FAMILY, headers=credentials).json()["replies"][0]["status"] == "sent"
    assert reply_text not in family.get("/api/hal/downlink").text
    assert _post(anton, "/advance", seconds=3).json()["delivered"] == 0
