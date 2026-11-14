"""
NASA-STD-3001 (Vol 1 & Vol 2) crew health thresholds and ISS dosimetry constants.

All radiation limits follow NASA-STD-3001 Vol 1 (600 mSv universal career
effective dose limit, ALARA principle, and non-cancer organ limits).
DOSTEL quality factors follow DLR/NASA DOSIS 3D ISS measurements separating
Galactic Cosmic Rays (GCR) and South Atlantic Anomaly (SAA) trapped protons.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class OrganLimit:
    """Short-term and career non-cancer tissue limits in mGy-Eq (or mGy)."""

    name: str
    unit: str
    limit_30d: float
    limit_1yr: float
    limit_career: float | None


NASA_RADIATION_STANDARDS = {
    "career_effective_dose_msv": 600.0,
    "spe_short_term_msv": 250.0,
    "iss_baseline_msv_per_day_min": 0.4,
    "iss_baseline_msv_per_day_max": 1.0,
    "iss_eva_msv_per_day": 1.3,
    "alara_daily_watch_msv": 0.65,
    "alara_daily_alert_msv": 1.0,
    # DLR DOSTEL / DOSIS 3D mean quality factors on ISS
    "quality_factor_gcr": 3.20,
    "quality_factor_saa": 1.22,
    # NASA-STD-3001 Vol 1 organ-specific non-cancer limits
    "organs": {
        "bfo": OrganLimit("Blood-Forming Organs (BFO)", "mGy-Eq", 250.0, 500.0, None),
        "circulatory": OrganLimit("Circulatory System", "mGy-Eq", 250.0, 500.0, 1000.0),
        "cns": OrganLimit("Central Nervous System (CNS)", "mGy", 500.0, 1000.0, None),
        "eye_lens": OrganLimit("Eye Lens", "mGy-Eq", 1000.0, 2000.0, 4000.0),
        "skin": OrganLimit("Skin", "mGy-Eq", 1500.0, 3000.0, 6000.0),
    },
}

# NASA-STD-3001 Vol 2 cabin environment limits (ready for Air Quality module)
NASA_ENVIRONMENT_STANDARDS: Dict[str, Dict[str, float | str]] = {
    "ppco2_mmhg": {"nominal": 2.0, "warn": 2.5, "limit_1hr": 3.0, "eva_limit": 2.0, "unit": "mmHg"},
    "ppo2_kpa": {"min": 20.7, "nominal": 21.3, "max": 50.6, "unit": "kPa"},
    "pressure_kpa": {"min": 26.2, "nominal": 101.3, "max": 103.0, "unit": "kPa"},
    "temperature_c": {"min": 18.0, "nominal": 22.0, "max": 27.0, "unit": "degC"},
    "humidity_pct": {"min": 25.0, "nominal": 45.0, "max": 75.0, "unit": "%RH"},
}

# NASA-STD-3001, NASA HRP Cardiac Rhythm Risk, Bio-Monitor/Astroskin &
# peer-reviewed pre-event cardiovascular early-warning thresholds.
NASA_CARDIO_VITALS_STANDARDS: Dict[str, object] = {
    "hardware_reference": {
        "system": "CSA Bio-Monitor / Astroskin (Hexoskin)",
        "ecg_hz": 250.0,
        "resp_hz": 125.0,
        "ppg_hz": 75.0,
        "accel_hz": 50.0,
        "skin_temp_hz": 1.0,
        "physionet_proxy_hz": 125.0,
    },
    "heart_rate_bpm": {
        "brady_critical": 38.0,
        "brady_watch": 45.0,
        "nominal_min": 45.0,
        "nominal_max": 90.0,
        "tachy_watch": 95.0,
        "tachy_critical": 115.0,
        # NASA post-spaceflight orthostatic intolerance / POTS diagnostic rise
        "orthostatic_delta_bpm": 30.0,
    },
    "hrv_autonomic": {
        # Malik ESC/NASPE Task Force & Kleiger et al.: SDNN < 50 ms high cardiac risk
        "sdnn_watch_ms": 50.0,
        "sdnn_critical_ms": 30.0,
        # Parasympathetic (vagal) withdrawal markers
        "rmssd_watch_ms": 20.0,
        "rmssd_critical_ms": 12.0,
        "rmssd_drop_watch_pct": -25.0,
        "rmssd_drop_critical_pct": -40.0,
        "lf_hf_watch": 3.5,
        "lf_hf_critical": 5.0,
        # Bauer et al. (Lancet 2006) PRSA Deceleration Capacity
        "deceleration_capacity_watch_ms": 4.5,
        "deceleration_capacity_critical_ms": 2.5,
        # Short-term fractal scaling exponent (DFA alpha-1 healthy ~0.85..1.15)
        "dfa_alpha1_min": 0.75,
        "dfa_alpha1_max": 1.35,
    },
    "repolarization_electrical": {
        # D'Aunno et al. (2003) & Fritsch-Yelle et al.: long-duration spaceflight QTcF
        "qtcf_watch_ms": 450.0,
        "qtcf_female_watch_ms": 460.0,
        "qtcf_critical_ms": 500.0,
        "qtcf_delta_critical_ms": 60.0,
        # Premature beat / PVC burden & mechanical pulse deficit
        "ectopy_watch_pct": 1.0,
        "ectopy_critical_pct": 5.0,
        "pulse_deficit_watch_bpm": 5.0,
        "pulse_deficit_critical_bpm": 10.0,
        # Beat-to-beat T-wave alternans normalized ratio
        "twa_watch_ratio": 0.15,
        "twa_critical_ratio": 0.25,
    },
    "hemodynamics": {
        "pat_drop_watch_ms": -18.0,
        "pat_rise_watch_ms": 25.0,
        "shock_index_watch": 0.85,
        "shock_index_critical": 1.0,
    },
    "respiration": {
        "rr_critical_low": 8.0,
        "rr_nominal_min": 10.0,
        "rr_nominal_max": 20.0,
        "rr_watch_high": 22.0,
        "rr_critical_high": 26.0,
        "apnea_pause_sec": 10.0,
    },
    "atmosphere_spo2": {
        "iss_nominal": {
            "label": "ISS Sea-Level Equivalent (14.7 psia / 21% O2)",
            "nominal_min": 96.0,
            "watch_min": 93.0,
            "critical_below": 92.0,
            "odi3_watch_per_hr": 5.0,
            "odi3_critical_per_hr": 15.0,
        },
        "exploration_8_2": {
            "label": "NASA Exploration Atmosphere (8.2 psia / 34% O2, ~1,220 m eq.)",
            "nominal_min": 94.0,
            "watch_min": 91.0,
            "critical_below": 90.0,
            "odi3_watch_per_hr": 5.0,
            "odi3_critical_per_hr": 15.0,
        },
    },
}

# Weighting for the holistic Astronaut Readiness Score (sums to 1.0)
READINESS_WEIGHTS: Dict[str, float] = {
    "radiation": 0.20,
    "air_quality": 0.15,
    "sleep_vigilance": 0.25,
    "cardio_vitals": 0.25,
    "exercise_nutrition": 0.15,
}
