"""Tests for the ISS Unified Medical Hub & NASA OSDR/DONKI coupled-risk engine."""

from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient

from astra_core.clinical_hub import (
    evaluate_clinical_hub,
    load_donki_sep_events,
    load_osdr_reference_stats,
)
from server import app


def test_osdr_and_donki_datasets_loaded():
    osdr = load_osdr_reference_stats()
    assert "OSD-569_CBC_TRANSFORMED.csv" in osdr["files_loaded"]
    assert "OSD-575_CMP_TRANSFORMED.csv" in osdr["files_loaded"]
    bmarks = osdr["benchmarks"]
    assert "hemoglobin" in bmarks
    assert "calcium" in bmarks
    assert bmarks["hemoglobin"]["preflight_median"] > 10.0
    assert bmarks["hemoglobin"]["rcv_pct"] == 7.9

    sep_events = load_donki_sep_events()
    assert len(sep_events) >= 1
    assert sep_events[0]["sep_id"]


def test_clinical_scenarios_trigger_expected_pre_symptomatic_pathways():
    nominal = evaluate_clinical_hub("nominal_iss")
    assert len(nominal["silos"]) == 6
    assert len(nominal["pathways"]) == 6
    assert nominal["overall_coupled_risk_score"] < 25
    assert nominal["overall_coupled_tier"] == "LOW"

    sans = evaluate_clinical_hub("sans_hypercapnia")
    top_sans = sans["pathways"][0]
    assert top_sans["id"] == "sans_cascade"
    assert top_sans["score"] >= 75
    assert top_sans["tier"] == "CRITICAL"

    renal = evaluate_clinical_hub("renal_stone_pre")
    renal_map = {p["id"]: p for p in renal["pathways"]}
    assert renal_map["renal_stone"]["score"] >= 75

    ij_vte = evaluate_clinical_hub("ij_vte_immune")
    ij_map = {p["id"]: p for p in ij_vte["pathways"]}
    assert ij_map["ij_vte_stasis"]["score"] >= 75
    assert ij_map["immune_sepsis"]["score"] >= 50


def test_custom_overrides_and_api_endpoints():
    client = TestClient(app)

    r_get = client.get("/api/clinical/hub", params={"scenario_id": "sans_hypercapnia"})
    assert r_get.status_code == 200
    body_get = r_get.json()
    assert body_get["scenario_id"] == "sans_hypercapnia"
    assert body_get["overall_coupled_risk_score"] >= 75
    assert len(body_get["osdr_comparisons"]) >= 5
    assert len(body_get["donki_sep_events"]) >= 1

    r_post = client.post(
        "/api/clinical/evaluate",
        json={
            "scenario_id": "nominal_iss",
            "overrides": {
                "poc_labs": {"ica_mmol_l": 1.38, "urine_sg": 1.031, "hb_g_dl": 11.2},
                "pulmonary_exercise": {"hydration_l_day": 1.4, "ared_load_pct": 68.0},
            },
        },
    )
    assert r_post.status_code == 200
    body_post = r_post.json()
    p_map = {p["id"]: p for p in body_post["pathways"]}
    assert p_map["renal_stone"]["score"] >= 75
    osdr_hb = next(c for c in body_post["osdr_comparisons"] if c["biomarker"] == "hemoglobin")
    assert osdr_hb["exceeds_rcv"] is True


def test_api_scenario_switching_and_app_js_syntax():
    client = TestClient(app)
    expected_scenarios = (
        "nominal_iss",
        "sans_hypercapnia",
        "renal_stone_pre",
        "ij_vte_immune",
    )
    required_pathway_keys = {
        "id",
        "title",
        "score",
        "tier",
        "converging_signals",
        "silos_linked",
        "science_basis",
        "pre_symptomatic_action",
    }

    for scenario_id in expected_scenarios:
        resp = client.get("/api/clinical/hub", params={"scenario_id": scenario_id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["scenario_id"] == scenario_id
        for key in (
            "overall_coupled_risk_score",
            "overall_coupled_tier",
            "provenance_note",
            "live_links",
            "silos",
            "pathways",
            "osdr_comparisons",
            "donki_sep_events",
            "available_scenarios",
        ):
            assert key in body
        assert len(body["silos"]) == 6
        assert len(body["pathways"]) == 6
        for pathway in body["pathways"]:
            assert required_pathway_keys.issubset(pathway.keys())
        for sid in expected_scenarios:
            assert sid in body["available_scenarios"]
        if scenario_id == "nominal_iss":
            assert body["overall_coupled_tier"] == "LOW"
            assert body["overall_coupled_risk_score"] < 25
        else:
            assert body["overall_coupled_risk_score"] >= 75

    app_js = Path(__file__).resolve().parent.parent / "static" / "app.js"
    js_text = app_js.read_text(encoding="utf-8")
    for needle in ("medhubState", "setMedHubMode", 'newLevel === "biosense"', 'newLevel === "medhub"'):
        assert needle in js_text

    node_bin = shutil.which("node")
    if node_bin:
        proc = subprocess.run([node_bin, "--check", str(app_js)], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
