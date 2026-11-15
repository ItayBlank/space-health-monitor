"""
Unified ISS Bio-Medical Silo Integrator & Coupled-Risk Early-Warning Engine.

Breaks down the data silos across ISS Point-of-Care labs (Abbott i-STAT,
HemoCue, Urinalysis, Saliva), Medical Imaging (Butterfly iQ+ / Ultrasound 2,
OCT, Tono-Pen), Cardio/Wearables (Bio-Monitor/Astroskin), Pulmonary/Exercise
(PFS, eNO, ARED, SLAMMD), Neuro/Sleep (WinSCAT/PVT, Radar/CSI, OAE), and
Cabin Environment (CAD/RAM radiation, DONKI SEP, ppCO2, Noise).

Grounds clinical biomarker comparisons in real NASA Open Science Data Repository
(OSDR) Inspiration4 datasets:
  - OSD-569: Complete Blood Count (LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv)
  - OSD-575: Comprehensive Metabolic Panel & Multiplex Cardio/Immune Panels
  - CCMC DONKI: May 2024 Solar Energetic Particle (SEP) archive
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OSDR_DIR = DATA_DIR / "nasa_osdr"

# Pre-analytical + biological variation Reference Change Values (RCV = 2.77 * sqrt(CVa^2 + CVi^2))
# Derived from EFLM Biological Variation database & NASA HRP Clinical Chemistry references.
BIOMARKER_RCV_PCT: Dict[str, float] = {
    "hemoglobin": 7.9,
    "hematocrit": 8.1,
    "wbc": 31.2,
    "platelets": 25.2,
    "sodium": 2.3,
    "potassium": 13.0,
    "chloride": 3.5,
    "calcium": 5.9,
    "creatinine": 14.2,
    "bun": 33.8,
    "glucose": 15.1,
    "crp": 118.0,
    "fibrinogen": 29.8,
}


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.upper() in {"NA", "N/A", "NAN", "NULL"}:
        return None
    try:
        num = float(s)
        return num if math.isfinite(num) else None
    except ValueError:
        return None


def _phase_from_sample_name(name: str) -> str:
    upper = name.upper()
    if "_L-" in upper:
        return "preflight"
    if "_R+1_" in upper or upper.endswith("_R+1"):
        return "postflight_r1"
    return "recovery"


def load_osdr_reference_stats() -> Dict[str, Any]:
    """Compute real preflight vs R+1 cohort benchmarks from NASA OSDR OSD-569 & OSD-575."""
    benchmarks: Dict[str, Dict[str, Any]] = {}
    files_loaded: List[str] = []

    cbc_path = OSDR_DIR / "OSD-569_CBC_TRANSFORMED.csv"
    cmp_path = OSDR_DIR / "OSD-575_CMP_TRANSFORMED.csv"
    cardio_path = OSDR_DIR / "OSD-575_Cardio_EvePanel_TRANSFORMED.csv"

    def _summarize_csv(path: Path, metrics: Dict[str, tuple[str, str, str]]) -> None:
        if not path.exists():
            return
        files_loaded.append(path.name)
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        for key, (col, label, unit) in metrics.items():
            pre_vals: List[float] = []
            r1_vals: List[float] = []
            all_vals: List[float] = []
            for row in rows:
                v = _safe_float(row.get(col))
                if v is None:
                    continue
                all_vals.append(v)
                phase = _phase_from_sample_name(row.get("Sample Name", ""))
                if phase == "preflight":
                    pre_vals.append(v)
                elif phase == "postflight_r1":
                    r1_vals.append(v)
            if not pre_vals:
                continue
            pre_med = statistics.median(pre_vals)
            r1_med = statistics.median(r1_vals) if r1_vals else pre_med
            shift_pct = ((r1_med - pre_med) / pre_med * 100.0) if pre_med else 0.0
            benchmarks[key] = {
                "label": label,
                "unit": unit,
                "source_study": "OSD-569" if "OSD-569" in path.name else "OSD-575",
                "preflight_median": round(pre_med, 2),
                "preflight_min": round(min(pre_vals), 2),
                "preflight_max": round(max(pre_vals), 2),
                "r1_postflight_median": round(r1_med, 2),
                "cohort_shift_pct": round(shift_pct, 1),
                "rcv_pct": BIOMARKER_RCV_PCT.get(key, 15.0),
                "n_samples": len(all_vals),
            }

    _summarize_csv(
        cbc_path,
        {
            "hemoglobin": ("hemoglobin_value_percent", "Hemoglobin (Hb)", "g/dL"),
            "hematocrit": ("hematocrit_value_percent", "Hematocrit (Hct)", "%"),
            "wbc": ("white_blood_cell_count_value_thousand_per_microliter", "WBC Count", "K/uL"),
            "platelets": ("platelet_count_value_thousand_per_microliter", "Platelets", "K/uL"),
            "neutrophils_pct": ("neutrophils_value_percent", "Neutrophils", "%"),
            "lymphocytes_pct": ("lymphocytes_value_percent", "Lymphocytes", "%"),
        },
    )
    _summarize_csv(
        cmp_path,
        {
            "sodium": ("sodium_value_millimol_per_liter", "Sodium (Na+)", "mmol/L"),
            "potassium": ("potassium_value_millimol_per_liter", "Potassium (K+)", "mmol/L"),
            "chloride": ("chloride_value_millimol_per_liter", "Chloride (Cl-)", "mmol/L"),
            "calcium": ("calcium_value_milligram_per_deciliter", "Serum Calcium", "mg/dL"),
            "co2_hco3": ("carbon_dioxide_value_millimol_per_liter", "Serum CO2 / HCO3-", "mmol/L"),
            "creatinine": ("creatinine_value_milligram_per_deciliter", "Creatinine", "mg/dL"),
            "bun": ("urea_nitrogen_bun_value_milligram_per_deciliter", "BUN", "mg/dL"),
            "glucose": ("glucose_value_milligram_per_deciliter", "Glucose", "mg/dL"),
            "albumin": ("albumin_value_gram_per_deciliter", "Albumin", "g/dL"),
        },
    )
    _summarize_csv(
        cardio_path,
        {
            "crp_pg_ml": ("crp_concentration_picogram_per_milliliter", "CRP (Multiplex)", "pg/mL"),
            "fibrinogen": ("fibrinogen_concentration_nanogram_per_milliliter", "Fibrinogen", "ng/mL"),
            "haptoglobin": ("haptoglobin_concentration_nanogram_per_milliliter", "Haptoglobin", "ng/mL"),
        },
    )

    return {
        "provenance": "NASA OSDR Inspiration4 Cohort (OSD-569 CBC & OSD-575 CMP/Multiplex)",
        "files_loaded": files_loaded,
        "benchmarks": benchmarks,
    }


def load_donki_sep_events() -> List[Dict[str, Any]]:
    """Load cached May 2024 NASA CCMC DONKI Solar Energetic Particle (SEP) events."""
    path = OSDR_DIR / "DONKI_SEP_2024_05.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:6]:
        instruments = [i.get("displayName", "") for i in item.get("instruments", [])]
        out.append(
            {
                "sep_id": item.get("sepID"),
                "event_time": item.get("eventTime"),
                "instruments": instruments,
                "linked_count": len(item.get("linkedEvents") or []),
                "link": item.get("link"),
            }
        )
    return out


CLINICAL_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "nominal_iss": {
        "label": "Nominal ISS Flight Day 90",
        "description": "Balanced fluids, nominal ARED load, clean CDRA air, steady OSDR-aligned labs.",
        "poc_labs": {
            "na_mmol_l": 140.0,
            "k_mmol_l": 4.1,
            "cl_mmol_l": 102.0,
            "ica_mmol_l": 1.21,
            "calcium_mg_dl": 9.6,
            "glucose_mg_dl": 86.0,
            "lactate_mmol_l": 1.1,
            "bun_mg_dl": 16.0,
            "creatinine_mg_dl": 1.02,
            "ph": 7.39,
            "pco2_mmhg": 40.0,
            "hco3_mmol_l": 24.0,
            "hb_g_dl": 14.3,
            "hct_pct": 42.8,
            "wbc_k_ul": 6.4,
            "nlr": 1.9,
            "crp_mg_l": 1.4,
            "ctni_ng_ml": 0.01,
            "urine_sg": 1.015,
            "urine_ketones": False,
            "urine_blood": False,
            "saliva_cortisol_nmol_l": 9.5,
            "ebv_cmv_reactivation": False,
        },
        "imaging": {
            "onsd_mm": 4.6,
            "globe_flattening": False,
            "oct_rnfl_delta_um": 3.0,
            "iop_mmhg": 14.5,
            "jugular_flow_grade": "normal",
            "renal_calculi_or_hydro": False,
            "ef_pct": 61.0,
        },
        "pulmonary_exercise": {
            "vo2_peak_ml_kg_min": 42.0,
            "eno_ppb": 14.0,
            "ared_load_pct": 100.0,
            "ared_velocity_loss_pct": 16.0,
            "body_mass_delta_pct": -0.8,
            "hydration_l_day": 2.5,
        },
        "neuro_sleep": {
            "sleep_hours": 7.1,
            "sleep_efficiency_pct": 86.0,
            "apnea_events": 1,
            "pvt_mean_rt_ms": 248.0,
            "audiometry_shift_db": 2.0,
            "headache_score": 0,
        },
        "environment": {
            "ppco2_mmhg": 1.9,
            "daily_msv": 0.56,
            "noise_dba": 61.0,
            "water_cfu_ml": 8.0,
        },
    },
    "sans_hypercapnia": {
        "label": "Pre-Symptomatic SANS + CDRA CO2 Creep",
        "description": "Asymptomatic crew: subclinical ONSD + RNFL swelling amplified by 3.4 mmHg cabin ppCO2 before visual blur starts.",
        "poc_labs": {
            "na_mmol_l": 139.0,
            "k_mmol_l": 4.0,
            "cl_mmol_l": 101.0,
            "ica_mmol_l": 1.23,
            "calcium_mg_dl": 9.8,
            "glucose_mg_dl": 91.0,
            "lactate_mmol_l": 1.2,
            "bun_mg_dl": 18.0,
            "creatinine_mg_dl": 1.05,
            "ph": 7.34,
            "pco2_mmhg": 46.5,
            "hco3_mmol_l": 26.8,
            "hb_g_dl": 14.8,
            "hct_pct": 44.2,
            "wbc_k_ul": 6.8,
            "nlr": 2.1,
            "crp_mg_l": 2.1,
            "ctni_ng_ml": 0.01,
            "urine_sg": 1.019,
            "urine_ketones": False,
            "urine_blood": False,
            "saliva_cortisol_nmol_l": 12.2,
            "ebv_cmv_reactivation": False,
        },
        "imaging": {
            "onsd_mm": 5.7,
            "globe_flattening": True,
            "oct_rnfl_delta_um": 24.0,
            "iop_mmhg": 19.2,
            "jugular_flow_grade": "normal",
            "renal_calculi_or_hydro": False,
            "ef_pct": 60.0,
        },
        "pulmonary_exercise": {
            "vo2_peak_ml_kg_min": 39.5,
            "eno_ppb": 16.0,
            "ared_load_pct": 94.0,
            "ared_velocity_loss_pct": 21.0,
            "body_mass_delta_pct": -1.4,
            "hydration_l_day": 2.2,
        },
        "neuro_sleep": {
            "sleep_hours": 6.1,
            "sleep_efficiency_pct": 76.0,
            "apnea_events": 3,
            "pvt_mean_rt_ms": 292.0,
            "audiometry_shift_db": 4.0,
            "headache_score": 4,
        },
        "environment": {
            "ppco2_mmhg": 3.4,
            "daily_msv": 0.62,
            "noise_dba": 64.0,
            "water_cfu_ml": 10.0,
        },
    },
    "renal_stone_pre": {
        "label": "Pre-Symptomatic Renal Stone & Bone-Loss Cascade",
        "description": "Missed ARED resistive loading + low hydration drives hypercalciuria & concentrated urine days before acute renal colic.",
        "poc_labs": {
            "na_mmol_l": 146.0,
            "k_mmol_l": 3.8,
            "cl_mmol_l": 106.0,
            "ica_mmol_l": 1.37,
            "calcium_mg_dl": 10.6,
            "glucose_mg_dl": 94.0,
            "lactate_mmol_l": 1.4,
            "bun_mg_dl": 25.0,
            "creatinine_mg_dl": 1.36,
            "ph": 7.36,
            "pco2_mmhg": 41.0,
            "hco3_mmol_l": 23.0,
            "hb_g_dl": 15.6,
            "hct_pct": 46.8,
            "wbc_k_ul": 7.1,
            "nlr": 2.3,
            "crp_mg_l": 3.0,
            "ctni_ng_ml": 0.01,
            "urine_sg": 1.029,
            "urine_ketones": True,
            "urine_blood": True,
            "saliva_cortisol_nmol_l": 14.0,
            "ebv_cmv_reactivation": False,
        },
        "imaging": {
            "onsd_mm": 4.8,
            "globe_flattening": False,
            "oct_rnfl_delta_um": 5.0,
            "iop_mmhg": 15.0,
            "jugular_flow_grade": "normal",
            "renal_calculi_or_hydro": True,
            "ef_pct": 59.0,
        },
        "pulmonary_exercise": {
            "vo2_peak_ml_kg_min": 37.0,
            "eno_ppb": 15.0,
            "ared_load_pct": 68.0,
            "ared_velocity_loss_pct": 33.0,
            "body_mass_delta_pct": -3.6,
            "hydration_l_day": 1.25,
        },
        "neuro_sleep": {
            "sleep_hours": 6.4,
            "sleep_efficiency_pct": 80.0,
            "apnea_events": 2,
            "pvt_mean_rt_ms": 268.0,
            "audiometry_shift_db": 3.0,
            "headache_score": 2,
        },
        "environment": {
            "ppco2_mmhg": 2.1,
            "daily_msv": 0.58,
            "noise_dba": 62.0,
            "water_cfu_ml": 12.0,
        },
    },
    "ij_vte_immune": {
        "label": "Jugular Vein Stasis (IJ-VTE) + Immune Reactivation",
        "description": "Cephalad venous stasis + hemoconcentration + latent EBV/cortisol reactivation caught prior to occlusive DVT or clinical sepsis.",
        "poc_labs": {
            "na_mmol_l": 144.0,
            "k_mmol_l": 3.9,
            "cl_mmol_l": 104.0,
            "ica_mmol_l": 1.24,
            "calcium_mg_dl": 9.9,
            "glucose_mg_dl": 108.0,
            "lactate_mmol_l": 2.3,
            "bun_mg_dl": 22.0,
            "creatinine_mg_dl": 1.18,
            "ph": 7.37,
            "pco2_mmhg": 39.0,
            "hco3_mmol_l": 22.5,
            "hb_g_dl": 16.4,
            "hct_pct": 49.6,
            "wbc_k_ul": 10.9,
            "nlr": 4.4,
            "crp_mg_l": 18.5,
            "ctni_ng_ml": 0.02,
            "urine_sg": 1.024,
            "urine_ketones": False,
            "urine_blood": False,
            "saliva_cortisol_nmol_l": 24.5,
            "ebv_cmv_reactivation": True,
        },
        "imaging": {
            "onsd_mm": 5.3,
            "globe_flattening": False,
            "oct_rnfl_delta_um": 14.0,
            "iop_mmhg": 17.5,
            "jugular_flow_grade": "stagnant",
            "renal_calculi_or_hydro": False,
            "ef_pct": 57.0,
        },
        "pulmonary_exercise": {
            "vo2_peak_ml_kg_min": 35.5,
            "eno_ppb": 29.0,
            "ared_load_pct": 78.0,
            "ared_velocity_loss_pct": 38.0,
            "body_mass_delta_pct": -2.7,
            "hydration_l_day": 1.65,
        },
        "neuro_sleep": {
            "sleep_hours": 5.2,
            "sleep_efficiency_pct": 68.0,
            "apnea_events": 7,
            "pvt_mean_rt_ms": 324.0,
            "audiometry_shift_db": 7.0,
            "headache_score": 5,
        },
        "environment": {
            "ppco2_mmhg": 2.6,
            "daily_msv": 0.88,
            "noise_dba": 71.0,
            "water_cfu_ml": 45.0,
        },
    },
}


def _risk_tier(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "ELEVATED"
    if score >= 25:
        return "WATCH"
    return "LOW"


def _deep_merge(base: Dict[str, Any], patch: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = json.loads(json.dumps(base))
    if not patch:
        return out
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def evaluate_clinical_hub(
    scenario_id: str = "nominal_iss",
    overrides: Optional[Dict[str, Any]] = None,
    live_radiation: Optional[Dict[str, Any]] = None,
    live_vitals: Optional[Dict[str, Any]] = None,
    live_sleep: Optional[Dict[str, Any]] = None,
    live_exercise: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fuse all 6 ISS medical silos + real NASA OSDR benchmarks + live ASTRA-Core modules
    to detect pre-symptomatic coupled-system cascades before clinical onset.
    """
    base = CLINICAL_SCENARIOS.get(scenario_id, CLINICAL_SCENARIOS["nominal_iss"])
    state = _deep_merge(base, overrides)

    poc = state["poc_labs"]
    img = state["imaging"]
    pex = state["pulmonary_exercise"]
    ns = state["neuro_sleep"]
    env = state["environment"]

    # Overlay live telemetry from ASTRA-Core engines when scenario is nominal_iss or explicit live data exists
    live_links: List[str] = []
    if live_radiation and scenario_id == "nominal_iss":
        env["daily_msv"] = round(float(live_radiation.get("daily_cabin_msv", env["daily_msv"])), 3)
        live_links.append("ISS RadLab Radiation")
    if live_sleep and scenario_id == "nominal_iss":
        summary = live_sleep.get("summary") or live_sleep
        if "sleep_efficiency_pct" in summary:
            ns["sleep_efficiency_pct"] = float(summary["sleep_efficiency_pct"])
        if "apnea_events" in summary:
            ns["apnea_events"] = int(summary["apnea_events"])
        live_links.append("Radar/CSI Sleep")
    if live_exercise and scenario_id == "nominal_iss":
        if "max_velocity_loss_pct" in live_exercise:
            pex["ared_velocity_loss_pct"] = float(live_exercise["max_velocity_loss_pct"])
        live_links.append("ARED Pose CV")

    vitals_summary = (live_vitals or {}).get("summary", {})
    hr_bpm = float(vitals_summary.get("hr_bpm", 66.0))
    rmssd_ms = float(vitals_summary.get("rmssd_ms", 42.0))
    prsa_dc_ms = float(vitals_summary.get("deceleration_capacity_ms", 6.2))
    spo2_pct = float(vitals_summary.get("spo2_pct", 98.0))
    if live_vitals:
        live_links.append("PhysioNet Bio-Monitor DSP")

    osdr = load_osdr_reference_stats()
    bmarks = osdr["benchmarks"]

    # Compare key POC labs against real NASA OSDR Inspiration4 preflight medians & RCV
    osdr_comparisons: List[Dict[str, Any]] = []
    lab_map = [
        ("hemoglobin", poc["hb_g_dl"], "HemoCue / i-STAT"),
        ("hematocrit", poc["hct_pct"], "i-STAT"),
        ("wbc", poc["wbc_k_ul"], "HemoCue WBC"),
        ("sodium", poc["na_mmol_l"], "i-STAT CHEM8+"),
        ("potassium", poc["k_mmol_l"], "i-STAT CHEM8+"),
        ("calcium", poc["calcium_mg_dl"], "i-STAT / CMP"),
        ("creatinine", poc["creatinine_mg_dl"], "i-STAT CHEM8+"),
        ("bun", poc["bun_mg_dl"], "i-STAT CHEM8+"),
        ("glucose", poc["glucose_mg_dl"], "i-STAT CHEM8+"),
    ]
    for key, current_val, device in lab_map:
        ref = bmarks.get(key)
        if not ref:
            continue
        pre_med = ref["preflight_median"]
        delta_pct = ((current_val - pre_med) / pre_med * 100.0) if pre_med else 0.0
        rcv = ref["rcv_pct"]
        exceeds_rcv = abs(delta_pct) >= rcv
        osdr_comparisons.append(
            {
                "biomarker": key,
                "label": ref["label"],
                "device": device,
                "current": round(float(current_val), 2),
                "unit": ref["unit"],
                "osdr_preflight_median": pre_med,
                "osdr_r1_postflight_median": ref["r1_postflight_median"],
                "delta_vs_osdr_pct": round(delta_pct, 1),
                "rcv_threshold_pct": rcv,
                "exceeds_rcv": exceeds_rcv,
                "study": ref["source_study"],
            }
        )

    # ==================== 6 DEEP COUPLED PRE-SYMPTOMATIC PATHWAYS ====================
    pathways: List[Dict[str, Any]] = []

    # 1. SANS Pre-Symptomatic Neuro-Ocular Cascade
    sans_signals: List[str] = []
    sans_score = 0.0
    if img["onsd_mm"] >= 5.5:
        sans_score += 34
        sans_signals.append(f"Ultrasound ONSD {img['onsd_mm']:.1f} mm (>=5.5 mm)")
    elif img["onsd_mm"] >= 5.0:
        sans_score += 18
        sans_signals.append(f"Borderline ONSD {img['onsd_mm']:.1f} mm")
    if img["oct_rnfl_delta_um"] >= 15.0:
        sans_score += 24
        sans_signals.append(f"OCT RNFL +{img['oct_rnfl_delta_um']:.0f} um")
    if img["globe_flattening"]:
        sans_score += 20
        sans_signals.append("Posterior globe flattening (Ultrasound 2)")
    if env["ppco2_mmhg"] >= 2.5:
        sans_score += 16 if env["ppco2_mmhg"] < 3.0 else 22
        sans_signals.append(f"Cabin ppCO2 {env['ppco2_mmhg']:.1f} mmHg cerebral vasodilation cofactor")
    if img["iop_mmhg"] >= 18.0:
        sans_score += 10
        sans_signals.append(f"Tono-Pen IOP {img['iop_mmhg']:.1f} mmHg")
    pathways.append(
        {
            "id": "sans_cascade",
            "title": "SANS Pre-Symptomatic Neuro-Ocular Cascade",
            "silos_linked": ["Medical Imaging (US/OCT/Tono-Pen)", "Cabin Air (ppCO2)", "Neuro/Vision"],
            "score": round(min(100.0, sans_score)),
            "tier": _risk_tier(sans_score),
            "converging_signals": sans_signals or ["No neuro-ocular convergence"],
            "science_basis": "Kramer et al. Radiology 2012 (ONSD >=5.5 mm); NASA HRP SANS Evidence Report; Laurie et al. (ppCO2-SANS cerebral blood flow coupling).",
            "pre_symptomatic_action": (
                "Initiate Chibis/LBNP fluid-redistribution protocol, drop CDRA ppCO2 <2.0 mmHg, and repeat OCT + Tumbling-E within 48h before visual acuity degrades."
                if sans_score >= 25
                else "Continue routine 30-day OCT + Ultrasound ONSD surveillance."
            ),
        }
    )

    # 2. Renal Stone & Bone-Resorption Cascade
    renal_signals: List[str] = []
    renal_score = 0.0
    if poc["ica_mmol_l"] >= 1.32 or poc["calcium_mg_dl"] >= 10.3:
        renal_score += 28
        renal_signals.append(f"i-STAT iCa {poc['ica_mmol_l']:.2f} mmol/L / Ca {poc['calcium_mg_dl']:.1f} mg/dL")
    if poc["urine_sg"] >= 1.025:
        renal_score += 24
        renal_signals.append(f"Urine SG {poc['urine_sg']:.3f} (concentrated)")
    if pex["hydration_l_day"] < 2.0:
        renal_score += 18
        renal_signals.append(f"Low hydration {pex['hydration_l_day']:.2f} L/day")
    if pex["ared_load_pct"] < 80.0:
        renal_score += 16
        renal_signals.append(f"ARED resistive loading {pex['ared_load_pct']:.0f}% (accelerates bone Ca2+ efflux)")
    if img["renal_calculi_or_hydro"] or poc["urine_blood"]:
        renal_score += 24
        renal_signals.append("Renal Ultrasound/microhematuria pre-colic finding")
    pathways.append(
        {
            "id": "renal_stone",
            "title": "Renal Stone & Bone-Resorption Cascade",
            "silos_linked": ["Point-of-Care (i-STAT Ca + Urinalysis)", "Exercise/Hydration (ARED)", "Renal Ultrasound"],
            "score": round(min(100.0, renal_score)),
            "tier": _risk_tier(renal_score),
            "converging_signals": renal_signals or ["Bone-renal calcium balance nominal"],
            "science_basis": "Whitson et al. / NASA HRP Renal Stone Risk: microgravity osteoclastic resorption + low urine volume spikes supersaturation weeks prior to colic.",
            "pre_symptomatic_action": (
                "Escalate fluid intake to >=2.5 L/day, start potassium citrate prophylaxis per CMO protocol, and restore 100% ARED axial loading."
                if renal_score >= 25
                else "Maintain >=2.2 L/day hydration and scheduled ARED load."
            ),
        }
    )

    # 3. Internal Jugular Vein Thrombosis (IJ-VTE) Stasis Cascade
    vte_signals: List[str] = []
    vte_score = 0.0
    if img["jugular_flow_grade"] == "reversed_thrombus":
        vte_score += 55
        vte_signals.append("Butterfly Doppler: reversed/occlusive IJ flow")
    elif img["jugular_flow_grade"] == "stagnant":
        vte_score += 36
        vte_signals.append("Butterfly Doppler: stagnant/sluggish IJ venous flow")
    if poc["hct_pct"] >= 48.0:
        vte_score += 20
        vte_signals.append(f"Hemoconcentration Hct {poc['hct_pct']:.1f}% (i-STAT)")
    if pex["hydration_l_day"] < 1.8:
        vte_score += 14
        vte_signals.append(f"Plasma volume contraction ({pex['hydration_l_day']:.2f} L/day)")
    if img["onsd_mm"] >= 5.2:
        vte_score += 12
        vte_signals.append("Concurrent cephalad venous congestion (ONSD elevated)")
    pathways.append(
        {
            "id": "ij_vte_stasis",
            "title": "Jugular Vein Stasis (IJ-VTE / DVT) Cascade",
            "silos_linked": ["Vascular Doppler Ultrasound", "i-STAT Hematology (Hct)", "Fluid Balance"],
            "score": round(min(100.0, vte_score)),
            "tier": _risk_tier(vte_score),
            "converging_signals": vte_signals or ["Jugular venous flow brisk & compressible"],
            "science_basis": "Marshall-Goebel et al. JAMA Netw Open 2019 & Aunon-Chancellor NEJM 2020: stagnant internal jugular flow in microgravity precedes thrombosis.",
            "pre_symptomatic_action": (
                "Perform bilateral compression/Doppler re-scan, initiate LBNP venous-return countermeasure + oral rehydration, and prepare Flight Surgeon SBAR for anticoagulation review."
                if vte_score >= 25
                else "Routine periodic Butterfly iQ+ neck Doppler check."
            ),
        }
    )

    # 4. Subclinical Immune Reactivation & Sepsis Pre-Warning
    imm_signals: List[str] = []
    imm_score = 0.0
    if poc["ebv_cmv_reactivation"]:
        imm_score += 24
        imm_signals.append("Saliva/MinION latent viral reactivation (EBV/CMV)")
    if poc["saliva_cortisol_nmol_l"] >= 20.0:
        imm_score += 18
        imm_signals.append(f"Saliva Cortisol {poc['saliva_cortisol_nmol_l']:.1f} nmol/L")
    if poc["nlr"] >= 3.5 or poc["wbc_k_ul"] >= 10.0:
        imm_score += 20
        imm_signals.append(f"HemoCue WBC {poc['wbc_k_ul']:.1f} K/uL, NLR {poc['nlr']:.1f}")
    if poc["crp_mg_l"] >= 10.0 or poc["lactate_mmol_l"] >= 2.0:
        imm_score += 20
        imm_signals.append(f"CRP {poc['crp_mg_l']:.1f} mg/L, Lactate {poc['lactate_mmol_l']:.1f} mmol/L")
    if ns["sleep_efficiency_pct"] < 75.0 or prsa_dc_ms < 4.5 or rmssd_ms < 20.0:
        imm_score += 14
        imm_signals.append(f"Autonomic/sleep stress (Eff {ns['sleep_efficiency_pct']:.0f}%, PRSA DC {prsa_dc_ms:.1f} ms)")
    pathways.append(
        {
            "id": "immune_sepsis",
            "title": "Immune Reactivation & Subclinical Infection Cascade",
            "silos_linked": ["Saliva/MinION", "HemoCue/i-STAT (NLR/CRP/Lactate)", "Sleep & HRV Autonomic"],
            "score": round(min(100.0, imm_score)),
            "tier": _risk_tier(imm_score),
            "converging_signals": imm_signals or ["Immune & vagal markers within baseline"],
            "science_basis": "Crucian et al. (NASA HRP Immune Risk) & Bauer PRSA DC: cortisol + sleep loss triggers EBV/CMV shedding and vagal withdrawal 24-72h before overt fever.",
            "pre_symptomatic_action": (
                "Isolate sleep schedule recovery, repeat 6h i-STAT lactate/CRP + core temperature, and run MinION pathogen swab if NLR/CRP climbs."
                if imm_score >= 25
                else "No infectious or viral reactivation flags."
            ),
        }
    )

    # 5. Space Anemia & Cardiopulmonary Deconditioning
    anemia_signals: List[str] = []
    anemia_score = 0.0
    hb_ref = bmarks.get("hemoglobin", {}).get("preflight_median", 14.4)
    hb_drop_pct = (poc["hb_g_dl"] - hb_ref) / hb_ref * 100.0 if hb_ref else 0.0
    if hb_drop_pct <= -8.0 or poc["hb_g_dl"] < 12.0:
        anemia_score += 34
        anemia_signals.append(f"Hb {poc['hb_g_dl']:.1f} g/dL ({hb_drop_pct:+.1f}% vs OSDR preflight, exceeds RCV)")
    if pex["ared_velocity_loss_pct"] >= 30.0:
        anemia_score += 22
        anemia_signals.append(f"ARED velocity loss {pex['ared_velocity_loss_pct']:.0f}% (neuromuscular fatigue)")
    if pex["vo2_peak_ml_kg_min"] < 37.0:
        anemia_score += 18
        anemia_signals.append(f"PFS VO2 peak {pex['vo2_peak_ml_kg_min']:.1f} mL/kg/min")
    if spo2_pct < 95.0 or hr_bpm > 90.0:
        anemia_score += 15
        anemia_signals.append(f"Cardio strain (HR {hr_bpm:.0f} bpm, SpO2 {spo2_pct:.1f}%)")
    pathways.append(
        {
            "id": "space_anemia_decond",
            "title": "Space Anemia & Cardiopulmonary Deconditioning",
            "silos_linked": ["HemoCue/OSDR Hb", "PFS VO2 & ARED Velocity Loss", "Bio-Monitor SpO2/HR"],
            "score": round(min(100.0, anemia_score)),
            "tier": _risk_tier(anemia_score),
            "converging_signals": anemia_signals or ["Oxygen delivery & muscular power nominal"],
            "science_basis": "Trudel et al. Nature Medicine 2022 (Space Anemia 54% hemolysis increase) + NASA SPRINT ARED/VO2 aerobic countermeasure tracking.",
            "pre_symptomatic_action": (
                "Check reticulocytes/haptoglobin/ferritin, reduce ARED set volume before >35% velocity loss, and adjust CEVIS aerobic zone."
                if anemia_score >= 25
                else "Oxygen-carrying capacity and SPRINT fitness on target."
            ),
        }
    )

    # 6. Environmental Attribution Gate (CO2 / Dust eNO / Noise / Microbial)
    env_signals: List[str] = []
    env_score = 0.0
    if env["ppco2_mmhg"] >= 2.5:
        env_score += 32 if env["ppco2_mmhg"] < 3.0 else 44
        env_signals.append(f"Cabin ppCO2 {env['ppco2_mmhg']:.1f} mmHg (headache {ns['headache_score']}/10, PVT {ns['pvt_mean_rt_ms']:.0f} ms)")
    if pex["eno_ppb"] >= 25.0:
        env_score += 24
        env_signals.append(f"Exhaled NO {pex['eno_ppb']:.0f} ppb (airway/dust inflammation)")
    if env["noise_dba"] >= 68.0 or ns["audiometry_shift_db"] >= 10.0:
        env_score += 18
        env_signals.append(f"Acoustic load {env['noise_dba']:.0f} dBA / OAE shift {ns['audiometry_shift_db']:.0f} dB")
    if env["water_cfu_ml"] >= 50.0:
        env_score += 18
        env_signals.append(f"Potable water microbial {env['water_cfu_ml']:.0f} CFU/mL")
    pathways.append(
        {
            "id": "env_attribution",
            "title": "Environmental Exposure & Symptom Attribution Gate",
            "silos_linked": ["ECLSS ppCO2/Noise/Microbial", "Pulmonary eNO", "WinSCAT PVT & Audiometry"],
            "score": round(min(100.0, env_score)),
            "tier": _risk_tier(env_score),
            "converging_signals": env_signals or ["Cabin atmosphere, acoustics & airway eNO nominal"],
            "science_basis": "NASA-STD-3001 Vol 2 & LSAH CO2 headache study: separates ECLSS hypercapnia/dust/noise effects from primary crew illness.",
            "pre_symptomatic_action": (
                "Treat as ECLSS/environmental exposure first: boost CDRA CO2 scrubbing, inspect particulate/HEPA filters, enforce hearing protection before escalating pharmacotherapy."
                if env_score >= 25
                else "Cabin environment is not driving physiological drift."
            ),
        }
    )

    # Sort highest-risk coupled pathways first
    pathways.sort(key=lambda p: p["score"], reverse=True)
    top_score = pathways[0]["score"] if pathways else 0

    silos = [
        {
            "id": "poc_labs",
            "name": "1. Point-of-Care Labs & Frozen Archive",
            "devices": "Abbott i-STAT · HemoCue · Urinalysis · Saliva · MinION · MELFI (-80 C)",
            "key_metrics": f"Hb {poc['hb_g_dl']:.1f} g/dL · iCa {poc['ica_mmol_l']:.2f} mmol/L · K+ {poc['k_mmol_l']:.1f} · Cr {poc['creatinine_mg_dl']:.2f} · USG {poc['urine_sg']:.3f} · Cortisol {poc['saliva_cortisol_nmol_l']:.1f}",
            "status": "WATCH" if (poc["urine_sg"] >= 1.025 or poc["ica_mmol_l"] >= 1.32 or poc["ebv_cmv_reactivation"] or poc["nlr"] >= 3.5) else "NOMINAL",
        },
        {
            "id": "imaging",
            "name": "2. Medical Imaging & Ocular",
            "devices": "Ultrasound 2 / Butterfly iQ+ · Spectralis OCT · Fundoscope · Tono-Pen",
            "key_metrics": f"ONSD {img['onsd_mm']:.1f} mm · RNFL +{img['oct_rnfl_delta_um']:.0f} um · IOP {img['iop_mmhg']:.1f} mmHg · IJ Flow: {img['jugular_flow_grade']}",
            "status": "CRITICAL" if img["jugular_flow_grade"] == "reversed_thrombus" else ("WATCH" if (img["onsd_mm"] >= 5.5 or img["jugular_flow_grade"] == "stagnant" or img["renal_calculi_or_hydro"]) else "NOMINAL"),
        },
        {
            "id": "cardio",
            "name": "3. Cardio & Wearables",
            "devices": "12-Lead CMRS ECG · Bio-Monitor / Astroskin · Finapres",
            "key_metrics": f"HR {hr_bpm:.0f} bpm · RMSSD {rmssd_ms:.0f} ms · PRSA DC {prsa_dc_ms:.1f} ms · SpO2 {spo2_pct:.1f}%",
            "status": "WATCH" if (prsa_dc_ms < 4.5 or rmssd_ms < 20.0 or spo2_pct < 94.0) else "NOMINAL",
        },
        {
            "id": "pulm_ex",
            "name": "4. Pulmonary, Metabolism & Fitness",
            "devices": "PFS (VO2/VCO2) · eNO · ARED + Pose CV · SLAMMD Mass",
            "key_metrics": f"VO2 {pex['vo2_peak_ml_kg_min']:.1f} · eNO {pex['eno_ppb']:.0f} ppb · ARED {pex['ared_load_pct']:.0f}% (VL {pex['ared_velocity_loss_pct']:.0f}%) · Hydr {pex['hydration_l_day']:.2f} L",
            "status": "WATCH" if (pex["ared_velocity_loss_pct"] >= 30.0 or pex["ared_load_pct"] < 80.0 or pex["eno_ppb"] >= 25.0) else "NOMINAL",
        },
        {
            "id": "neuro_sleep",
            "name": "5. Neuro, Sleep & Audiometry",
            "devices": "WinSCAT / PVT · Actiwatch / Radar / ESP32 CSI · OAE Audiometry",
            "key_metrics": f"Sleep {ns['sleep_hours']:.1f}h ({ns['sleep_efficiency_pct']:.0f}%) · Apnea {ns['apnea_events']} · PVT {ns['pvt_mean_rt_ms']:.0f} ms · OAE {ns['audiometry_shift_db']:+.0f} dB",
            "status": "WATCH" if (ns["sleep_efficiency_pct"] < 75.0 or ns["pvt_mean_rt_ms"] >= 300.0 or ns["audiometry_shift_db"] >= 10.0) else "NOMINAL",
        },
        {
            "id": "environment",
            "name": "6. Cabin Environment & Space Weather",
            "devices": "CAD/RAM Dosimeters · CCMC DONKI · ECLSS CO2 · Acoustic/Microbial",
            "key_metrics": f"ppCO2 {env['ppco2_mmhg']:.1f} mmHg · Rad {env['daily_msv']:.2f} mSv/d · Noise {env['noise_dba']:.0f} dBA · Water {env['water_cfu_ml']:.0f} CFU/mL",
            "status": "WATCH" if (env["ppco2_mmhg"] >= 2.5 or env["noise_dba"] >= 68.0 or env["daily_msv"] >= 1.0) else "NOMINAL",
        },
    ]

    return {
        "scenario_id": scenario_id,
        "scenario_label": base["label"],
        "scenario_description": base["description"],
        "provenance_note": "Benchmarks from real NASA OSDR Inspiration4 (OSD-569/575) & May 2024 CCMC DONKI SEP; crew scenario values are labeled clinical simulations fused with live ASTRA-Core engines.",
        "live_links": live_links,
        "overall_coupled_risk_score": top_score,
        "overall_coupled_tier": _risk_tier(top_score),
        "silos": silos,
        "pathways": pathways,
        "osdr_comparisons": osdr_comparisons,
        "osdr_files_loaded": osdr["files_loaded"],
        "donki_sep_events": load_donki_sep_events(),
        "raw_state": state,
        "available_scenarios": {
            k: {"label": v["label"], "description": v["description"]}
            for k, v in CLINICAL_SCENARIOS.items()
        },
    }
