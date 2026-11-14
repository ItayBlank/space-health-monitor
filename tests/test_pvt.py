from datetime import datetime, timedelta, timezone
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from astra_core import pvt
from astra_core.pvt_api import router

UTC = timezone.utc
NOW = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(pvt, "_PATH", tmp_path / "runtime" / "pvt.json")
    monkeypatch.setattr(pvt, "utc_now", lambda: NOW)
    monkeypatch.setattr(pvt.secrets, "randbelow", lambda _limit: 0)
    return pvt._PATH


def event_at(at=NOW + timedelta(hours=1)):
    return pvt.add_event("anton", "EVA prep", at.isoformat(), now=NOW)


def sleep_at(now=NOW, intervals=None, complete=True):
    intervals = intervals if intervals is not None else [
        {"start_utc": (now-timedelta(hours=8)).isoformat(), "end_utc": (now-timedelta(hours=3)).isoformat()}
    ]
    return pvt.add_sleep_log("anton", intervals, complete, now=now)


def test_event_window_includes_exactly_two_hours_but_excludes_event_start(store):
    event_at(NOW + timedelta(hours=2))
    sleep_at()
    assert pvt.get_status("anton", NOW)["recommend"] is True
    before_window = pvt.get_status("anton", NOW-timedelta(seconds=1))
    assert not before_window["recommend"]
    assert before_window["reason"].startswith("The assigned event")
    assert pvt.get_status("anton", NOW + timedelta(hours=2))["event"] is None


def test_event_trigger_boundaries_and_unknown_sleep(store):
    event_at(NOW + timedelta(hours=1))
    status = pvt.get_status("anton", NOW)
    assert status["event"]["title"] == "EVA prep"
    assert status["sleep"] == {"status": "unknown", "total_minutes": None, "logged_at_utc": None}
    assert not status["recommend"]
    assert "Sleep unknown" in status["reason"]


def test_sleep_union_is_clipped_and_uses_exact_six_hour_threshold(store):
    event_at()
    sleep_at(intervals=[
        {"start_utc": (NOW-timedelta(hours=8)).isoformat(), "end_utc": (NOW-timedelta(hours=5)).isoformat()},
        {"start_utc": (NOW-timedelta(hours=6)).isoformat(), "end_utc": (NOW-timedelta(hours=2)).isoformat()},
        {"start_utc": (NOW-timedelta(hours=25)).isoformat(), "end_utc": (NOW-timedelta(hours=24)).isoformat()},
    ])
    status = pvt.get_status("anton", NOW)
    assert status["sleep"]["total_minutes"] == 360
    assert not status["recommend"]
    store.unlink()
    event_at()

    sleep_at(intervals=[
        {"start_utc": (NOW-timedelta(hours=8)).isoformat(), "end_utc": (NOW-timedelta(hours=2, seconds=1)).isoformat()}
    ])
    status = pvt.get_status("anton", NOW)
    assert status["sleep"]["total_minutes"] == 359
    assert status["recommend"]
    assert pvt.get_status("anton", NOW+timedelta(minutes=5))["sleep"]["status"] == "known"


def test_incomplete_and_expired_sleep_snapshots_are_unknown(store):
    event_at()
    sleep_at(complete=False)
    assert pvt.get_status("anton", NOW)["sleep"]["status"] == "unknown"
    store.unlink()
    sleep_at(now=NOW-timedelta(minutes=121))
    assert pvt.get_status("anton", NOW)["sleep"]["status"] == "unknown"


def test_pvt_is_server_timed_metrics_are_derived_and_result_suppresses(store):
    event_at()
    sleep_at()
    session = pvt.start_session("anton", NOW)
    assert len(session["stimulus_intervals_ms"]) == 89
    with pytest.raises(pvt.PVTError, match="before 180"):
        pvt.complete_session(session["session_id"], [400] * 89, NOW+timedelta(seconds=179, milliseconds=999))
    result = pvt.complete_session(session["session_id"], [400] * 88+[None], NOW+timedelta(seconds=180))
    assert result["median_rt_ms"] == 400
    assert result["lapses"] == 1
    assert pvt.get_status("anton", NOW+timedelta(seconds=180))["recommend"] is False


def test_aborted_expired_and_malformed_sessions_never_qualify(store):
    event_at()
    sleep_at()
    aborted = pvt.start_session("anton", NOW)
    pvt.abort_session(aborted["session_id"])
    with pytest.raises(pvt.PVTError, match="aborted"):
        pvt.complete_session(aborted["session_id"], [400]*89, NOW+timedelta(seconds=180))
    expired = pvt.start_session("anton", NOW)
    with pytest.raises(pvt.PVTError, match="expired"):
        pvt.complete_session(expired["session_id"], [400]*89, NOW+timedelta(seconds=211))
    malformed = pvt.start_session("anton", NOW)
    with pytest.raises(pvt.PVTError, match="response count"):
        pvt.complete_session(malformed["session_id"], [400], NOW+timedelta(seconds=180))


def test_event_reschedule_recomputes_recommendation(store):
    row = event_at(NOW+timedelta(hours=1))
    sleep_at()
    assert pvt.get_status("anton", NOW)["recommend"]
    moved = pvt.reschedule_event(row["id"], (NOW+timedelta(hours=3)).isoformat(), now=NOW)
    assert moved["event_utc"] == "2030-01-01T15:00:00Z"
    status = pvt.get_status("anton", NOW)
    assert not status["recommend"]
    assert status["event"]["event_utc"] == moved["event_utc"]


def test_corrupt_store_fails_closed_without_overwrite(store):
    store.parent.mkdir(parents=True)
    store.write_text("{broken")
    with pytest.raises(pvt.PVTError, match="history was not changed"):
        pvt.get_status("anton", NOW)
    assert store.read_text() == "{broken"


def test_synthetic_scenarios_are_separate_and_cannot_start_or_write(store):
    demo = pvt.get_status("anton", NOW, "already-tested")
    assert demo["records"][0]["provenance"] == "synthetic"
    assert demo["personal_baseline"]["status"] == "unavailable"
    assert not store.exists()


def test_api_rejects_unknown_crew_and_early_completion(store):
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/pvt/status/no-one").status_code == 400
    assert client.get("/api/pvt/status/anton?scenario=missing-log").json()["sleep"]["status"] == "unknown"
    event_at()
    sleep_at()
    session = client.post("/api/pvt/sessions/start", json={"crew_id": "anton"}).json()
    res = client.post(f"/api/pvt/sessions/{session['session_id']}/complete",
                      json={"reaction_times_ms": [400]*89, "median_rt_ms": 1, "lapses": 0})
    assert res.status_code == 400
    assert "180 seconds" in res.json()["detail"]



def test_overlapping_naps_union_clips_at_rolling_24h_and_reports_asof(store):
    event_at()
    sleep_at(intervals=[
        {"start_utc": (NOW-timedelta(hours=25)).isoformat(), "end_utc": (NOW-timedelta(hours=23)).isoformat()},
        {"start_utc": (NOW-timedelta(hours=8)).isoformat(), "end_utc": (NOW-timedelta(hours=5)).isoformat()},
        {"start_utc": (NOW-timedelta(hours=6)).isoformat(), "end_utc": (NOW-timedelta(hours=2)).isoformat()},
    ])
    status = pvt.get_status("anton", NOW)
    assert status["sleep"]["total_minutes"] == 420
    assert status["sleep"]["logged_at_utc"] == "2030-01-01T12:00:00Z"


def test_other_crew_and_old_protocol_samples_do_not_suppress(store):
    event_at()
    sleep_at()
    pvt.add_event("itay", "EVA prep", (NOW+timedelta(hours=1)).isoformat(), now=NOW)
    pvt.add_sleep_log("itay", [
        {"start_utc": (NOW-timedelta(hours=8)).isoformat(), "end_utc": (NOW-timedelta(hours=3)).isoformat()}
    ], True, now=NOW)
    with pvt._LOCK:
        data = pvt._load()
        data["sessions"].append({
            "id": "old-protocol", "crew_id": "itay", "event_id": data["events"][-1]["id"],
            "valid": True, "provenance": "measured", "protocol_version": "pvt-b-old",
            "completed_at_utc": NOW.isoformat(), "median_rt_ms": 100, "lapses": 0,
        })
        pvt._save(data)
    assert pvt.get_status("anton", NOW)["recommend"]
    assert pvt.get_status("itay", NOW)["recommend"]
    assert pvt.get_status("itay", NOW)["personal_baseline"]["status"] == "unavailable"


def test_personal_baseline_uses_earlier_same_protocol_runs_and_lapses(store):
    started = []
    for offset, rt in ((15, 300), (12, 310), (9, 320), (6, 400)):
        at = NOW-timedelta(hours=offset)
        pvt.add_event("anton", "Prior EVA", (at+timedelta(hours=1)).isoformat(), now=at)
        pvt.add_sleep_log("anton", [
            {"start_utc": (at-timedelta(hours=8)).isoformat(), "end_utc": (at-timedelta(hours=3)).isoformat()}
        ], True, now=at)
        session = pvt.start_session("anton", at)
        trials = [rt]*(len(session["stimulus_intervals_ms"])-offset//3) + [None]*(offset//3)
        started.append(pvt.complete_session(session["session_id"], trials, at+timedelta(seconds=180)))
    event_at()
    sleep_at()
    status = pvt.get_status("anton", NOW)
    assert status["personal_baseline"] == {
        "status": "available", "sample_count": 3, "median_rt_ms": 310, "median_lapses": 4
    }
    assert status["records"][-1]["median_rt_ms"] == 400
    assert status["records"][-1]["lapses"] == 2


def test_same_protocol_completion_in_suppression_window_covers_overlapping_events(store):
    first = event_at(NOW+timedelta(hours=1))
    event2 = pvt.add_event("anton", "Second critical task", (NOW+timedelta(hours=2)).isoformat(), now=NOW)
    sleep_at()
    session = pvt.start_session("anton", NOW)
    pvt.complete_session(session["session_id"], [300]*89, NOW+timedelta(seconds=180))
    moved = pvt.reschedule_event(first["id"], (NOW+timedelta(hours=3)).isoformat(), now=NOW)
    status = pvt.get_status("anton", NOW+timedelta(minutes=4))
    assert status["event"]["id"] == event2["id"]
    assert moved["event_utc"] == "2030-01-01T15:00:00Z"
    assert not status["recommend"]
    assert "already recorded" in status["reason"]
