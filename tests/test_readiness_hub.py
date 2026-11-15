"""Tests for unified readiness state hub, /api/exercise/set, and /api/sleep/* endpoints."""

from __future__ import annotations

import sys
import types

from fastapi.testclient import TestClient

import server


def _reset_hub() -> None:
    with server._READINESS_LOCK:
        for k in server._READINESS_STATE:
            server._READINESS_STATE[k] = None


def test_readiness_hub_preserves_live_pillars_across_endpoints() -> None:
    _reset_hub()
    client = TestClient(server.app)

    r_vit = client.post("/api/vitals/analyze", json={"record_id": "ptt_s3_sit"})
    assert r_vit.status_code == 200
    assert r_vit.json()["readiness"]["pillars"]["cardio_vitals"]["is_live_module"] is True

    # Running radiation simulation must preserve live cardio_vitals
    r_rad = client.post("/api/radiation/simulate", json={"mission_days": 14, "solar_storm_active": False})
    assert r_rad.status_code == 200
    pillars = r_rad.json()["readiness"]["pillars"]
    assert pillars["radiation"]["is_live_module"] is True
    assert pillars["cardio_vitals"]["is_live_module"] is True


def test_exercise_set_updates_readiness_and_detects_velocity_loss_fatigue() -> None:
    _reset_hub()
    client = TestClient(server.app)

    # Nominal set
    res_ok = client.post(
        "/api/exercise/set",
        json={
            "exercise": "squat",
            "camera_mode": "frontal",
            "reps": [
                {"rep": 1, "rom_deg": 92.0, "concentric_vel_norm": 1.0, "velocity_loss_pct": 0.0, "quality_score": 95.0},
                {"rep": 2, "rom_deg": 91.0, "concentric_vel_norm": 0.94, "velocity_loss_pct": 6.0, "quality_score": 92.0},
            ],
        },
    )
    assert res_ok.status_code == 200
    data_ok = res_ok.json()
    assert data_ok["exercise"]["status"] == "NOMINAL"
    assert data_ok["readiness"]["pillars"]["exercise_nutrition"]["is_live_module"] is True

    # High fatigue set (>35% velocity loss)
    res_fat = client.post(
        "/api/exercise/set",
        json={
            "exercise": "squat",
            "camera_mode": "side",
            "reps": [
                {"rep": 1, "rom_deg": 92.0, "concentric_vel_norm": 1.0, "velocity_loss_pct": 0.0, "quality_score": 90.0},
                {"rep": 8, "rom_deg": 108.0, "concentric_vel_norm": 0.61, "velocity_loss_pct": 39.0, "trunk_lean_deg": 18.0, "quality_score": 68.0, "flags": ["lumbar"]},
            ],
        },
    )
    assert res_fat.status_code == 200
    assert res_fat.json()["exercise"]["status"] in ("WARNING", "CRITICAL")


def test_sleep_and_csi_reach_85_percent_live_readiness(monkeypatch) -> None:
    _reset_hub()
    fake_mod = types.ModuleType("astra_core.radar_sleep")
    fake_patch = {
        "label": "Sleep & Alertness",
        "score": 84,
        "status": "NOMINAL",
        "source": "Contactless Radar Sleep ML",
        "summary": "7.1h TST, 88% eff, AHI 1.2/hr",
        "crew_summary": "7.1 hrs sleep · Restorative stages nominal.",
        "crew_action": "No sleep countermeasure needed.",
        "action": "Sleep nominal.",
        "is_live_module": True,
    }
    fake_mod.analyze_radar_sleep = lambda **kwargs: {"sleep_summary": {"tst_h": 7.1}, "readiness_patch": fake_patch}
    fake_mod.analyze_csi_window = lambda **kwargs: {"resp_rate_bpm": 14.5, "readiness_patch": fake_patch}
    monkeypatch.setitem(sys.modules, "astra_core.radar_sleep", fake_mod)

    client = TestClient(server.app)
    client.post("/api/vitals/analyze", json={"record_id": "ptt_s3_sit"})
    client.post(
        "/api/exercise/set",
        json={
            "exercise": "squat",
            "reps": [{"rep": 1, "rom_deg": 90.0, "concentric_vel_norm": 1.0, "velocity_loss_pct": 4.0, "quality_score": 94.0}],
        },
    )
    r_sleep = client.post("/api/sleep/analyze", json={"record_id": "nominal_rest"})
    assert r_sleep.status_code == 200
    r_csi = client.post("/api/sleep/csi", json={"csi_frames": [[1.0] * 52 for _ in range(12)]})
    assert r_csi.status_code == 200

    pillars = r_csi.json()["readiness"]["pillars"]
    live_weight = sum(p["weight"] for p in pillars.values() if p["is_live_module"])
    assert abs(live_weight - 0.85) < 1e-6
