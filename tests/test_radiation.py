"""Physics, NASA-STD-3001 compliance, and API tests for ASTRA-Core backbone."""

from fastapi.testclient import TestClient

from astra_core.radiation import load_rem_summary, simulate_astronaut_radiation
from astra_core.readiness import compute_holistic_readiness
from server import app


def test_rem_summary_has_all_six_iss_cabins() -> None:
    rem = load_rem_summary()
    assert len(rem["cabins"]) == 6
    assert rem["cabins"]["node1"]["rem_mean_ugy_h"] > rem["cabins"]["uslab"]["rem_mean_ugy_h"]
    assert len(rem["daily_series"]) == 23


def test_cabin_tracking_vs_vessel_average_physics() -> None:
    high_flux = simulate_astronaut_radiation(
        cabin_hours={"node1": 24, "uslab": 0, "columbus": 0, "jpm": 0, "node3": 0, "cupola": 0}
    )
    low_flux = simulate_astronaut_radiation(
        cabin_hours={"uslab": 24, "node1": 0, "columbus": 0, "jpm": 0, "node3": 0, "cupola": 0}
    )
    # Baseline ISS equivalent dose must lie within realistic LEO range (0.2..1.0 mSv/day)
    assert 0.2 <= low_flux["daily_cabin_msv"] <= 1.0
    assert 0.2 <= high_flux["daily_cabin_msv"] <= 1.0
    # Node 1 (~28.16 uGy/h) must exceed Destiny (~20.53 uGy/h) and exceed vessel average
    assert high_flux["daily_cabin_msv"] > low_flux["daily_cabin_msv"]
    assert high_flux["delta_vs_vessel_pct"] > 5.0
    assert low_flux["delta_vs_vessel_pct"] < -5.0


def test_solar_storm_and_missing_dosimeter_flags() -> None:
    sim = simulate_astronaut_radiation(
        cabin_hours={"cupola": 6, "node1": 6, "node3": 12, "uslab": 0, "columbus": 0, "jpm": 0},
        solar_storm_active=True,
        personal_dosimeter_online=False,
    )
    assert sim["dosimeter_status"] == "estimated"
    assert "ESTIMATED" in sim["dosimeter_label"]
    assert sim["status"] == "CRITICAL"
    assert sim["simple_summary"]["recommended_action"]["can_improve"] is True
    assert sim["simple_summary"]["recommended_action"]["dose_reduction_pct"] > 0
    rates = sim["simple_summary"]["effective_rates_ugy_h"]
    assert rates["cupola"] > rates["node3"] > rates["uslab"]

    # Multi-source storm action must disclose all moved cabins transparently
    alara_storm = simulate_astronaut_radiation(
        cabin_hours={"uslab": 14, "node3": 8, "columbus": 1, "jpm": 1, "node1": 0, "cupola": 0},
        solar_storm_active=True,
    )
    rec = alara_storm["simple_summary"]["recommended_action"]
    assert set(rec["moved_sources"].keys()) == {"columbus", "jpm"}
    assert "Columbus" in rec["action_title"] and "Kibo" in rec["action_title"]

    readiness = compute_holistic_readiness(sim)
    assert readiness["overall_score"] <= 49
    assert readiness["tier"] in ("warning", "critical")
    assert "crew_summary" in readiness["pillars"]["radiation"]


def test_fastapi_endpoints() -> None:
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/standards").status_code == 200
    base = client.get("/api/radiation/baseline")
    assert base.status_code == 200
    assert "readiness" in base.json()

    post = client.post(
        "/api/radiation/simulate",
        json={"cabin_hours": {"node1": 12, "uslab": 12}, "mission_days": 60, "solar_storm_active": False},
    )
    assert post.status_code == 200
    assert post.json()["radiation"]["mission_days"] == 60
