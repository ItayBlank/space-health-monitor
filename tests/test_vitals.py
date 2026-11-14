"""DSP accuracy, NASA-STD-3001 compliance, early-warning, and API tests for Wearable Vitals."""

from fastapi.testclient import TestClient

from astra_core.radiation import simulate_astronaut_radiation
from astra_core.readiness import compute_holistic_readiness
from astra_core.vitals import PHYSIONET_RECORDS, analyze_vitals_stream
from server import app


def test_healthy_physionet_baseline_matches_ground_truth() -> None:
    res = analyze_vitals_stream("ptt_s3_sit")
    m = res["summary_metrics"]
    ew = res["early_warning"]

    # Ground-truth R-peak count in s3_sit.csv is 603 beats
    assert 595 <= m["total_beats"] <= 610
    assert 70.0 <= m["mean_hr_bpm"] <= 77.0
    assert m["sdnn_ms"] > 50.0
    assert m["rmssd_ms"] > 25.0
    assert m["deceleration_capacity_ms"] > 4.5
    assert 0.75 <= m["dfa_alpha1"] <= 1.35
    assert m["qtcf_ms"] < 450.0
    assert m["pat_ms"] is not None and 120.0 <= m["pat_ms"] <= 400.0
    assert m["ectopy_burden_pct"] < 1.0
    assert ew["status"] == "NOMINAL"
    assert ew["cardio_score"] >= 85


def test_ecg_hr_accuracy_across_bidmc_recordings() -> None:
    for rid in ("bidmc_19", "bidmc_12", "bidmc_17", "bidmc_16"):
        res = analyze_vitals_stream(rid)
        m = res["summary_metrics"]
        assert abs(m["mean_hr_bpm"] - m["ref_hr_mean_bpm"]) <= 3.5


def test_early_warning_discriminates_pre_event_signatures() -> None:
    # BIDMC #12: real SpO2 desaturation (92%, ODI3 > 5/hr) + vagal collapse
    r12 = analyze_vitals_stream("bidmc_12")
    metrics_12 = {s["metric"] for s in r12["early_warning"]["signals"]}
    assert r12["summary_metrics"]["spo2_min_pct"] == 92.0
    assert "Min SpO2" in metrics_12
    assert "ODI3 Desaturations" in metrics_12
    assert "RMSSD" in metrics_12
    assert r12["early_warning"]["status"] == "CRITICAL"

    # BIDMC #17: high premature beat / ectopy burden + desaturation
    r17 = analyze_vitals_stream("bidmc_17")
    metrics_17 = {s["metric"] for s in r17["early_warning"]["signals"]}
    assert r17["summary_metrics"]["ectopy_burden_pct"] >= 5.0
    assert "Ectopy Burden" in metrics_17

    # BIDMC #16: sustained tachycardia + severe SDNN/DC autonomic suppression
    r16 = analyze_vitals_stream("bidmc_16")
    metrics_16 = {s["metric"] for s in r16["early_warning"]["signals"]}
    assert r16["summary_metrics"]["mean_hr_bpm"] > 100.0
    assert "Resting HR" in metrics_16
    assert "SDNN" in metrics_16
    assert "Deceleration Capacity" in metrics_16

    # BIDMC #19: borderline QTcF prolongation (>=450 ms) + low HRV
    r19 = analyze_vitals_stream("bidmc_19")
    metrics_19 = {s["metric"] for s in r19["early_warning"]["signals"]}
    assert r19["summary_metrics"]["qtcf_ms"] >= 450.0
    assert "QTcF" in metrics_19


def test_exploration_atmosphere_and_hypercapnia_link() -> None:
    iss = analyze_vitals_stream("bidmc_12", atmosphere_profile="iss_nominal")
    exp = analyze_vitals_stream("bidmc_12", atmosphere_profile="exploration_8_2", cabin_ppco2_mmhg=3.6)

    assert iss["summary_metrics"]["atmosphere_profile"] == "iss_nominal"
    assert exp["summary_metrics"]["atmosphere_profile"] == "exploration_8_2"
    exp_metrics = {s["metric"] for s in exp["early_warning"]["signals"]}
    assert "Hypercapnic Cardiopulmonary Link" in exp_metrics


def test_readiness_integration_and_fastapi_vitals_endpoints() -> None:
    rad = simulate_astronaut_radiation()
    vit = analyze_vitals_stream("ptt_s3_sit")
    readiness = compute_holistic_readiness(rad, vitals_result=vit)
    assert readiness["pillars"]["cardio_vitals"]["is_live_module"] is True
    assert readiness["pillars"]["cardio_vitals"]["score"] == vit["early_warning"]["cardio_score"]

    client = TestClient(app)
    recs = client.get("/api/vitals/records")
    assert recs.status_code == 200
    assert set(recs.json()["records"].keys()) == set(PHYSIONET_RECORDS.keys())

    base = client.get("/api/vitals/baseline")
    assert base.status_code == 200
    assert base.json()["vitals"]["record"]["record_id"] == "ptt_s3_sit"

    post = client.post(
        "/api/vitals/analyze",
        json={"record_id": "bidmc_17", "atmosphere_profile": "iss_nominal"},
    )
    assert post.status_code == 200
    assert post.json()["vitals"]["early_warning"]["status"] == "CRITICAL"
    assert post.json()["readiness"]["pillars"]["cardio_vitals"]["is_live_module"] is True
