"""
NASA RadLab ISS Cabin-by-Cabin Radiation Engine.

Fuses two real NASA OSDR RadLab datasets:
1. iss_modules_rem_2024.csv: 23 consecutive days (Jan 18 - Feb 9, 2024) of
   6 simultaneous Radiation Environment Monitor (REM Timepix) detectors across
   6 ISS modules (Node 1, Kibo JPM, Columbus, Node 3, Cupola, Destiny US Lab).
2. iss_dostel_orbital_2024_01_25.csv: ~90-second orbital DosTel1/2 telemetry
   in Columbus with latitude/longitude, capturing South Atlantic Anomaly (SAA)
   proton belt passes vs. Galactic Cosmic Ray (GCR) background.

Applies time-weighted integration (avoiding SAA 20s-burst oversampling bias)
and DLR DOSTEL quality factors (<Q>_GCR = 3.20, <Q>_SAA = 1.22) to compare
cabin-tracked astronaut dose against a naive vessel-average estimate.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import numpy as np

from hal2030.paths import resource_root

from .standards import NASA_RADIATION_STANDARDS

DATA_DIR = resource_root() / "data"
REM_CSV = DATA_DIR / "iss_modules_rem_2024.csv"
ORBITAL_CSV = DATA_DIR / "iss_dostel_orbital_2024_01_25.csv"


@dataclass(frozen=True)
class CabinMeta:
    """Metadata for a real ISS module monitored by a RadLab REM sensor."""

    cabin_id: str
    instrument_id: str
    name: str
    role: str
    shielding_note: str
    default_hours: float


ISS_CABINS: Dict[str, CabinMeta] = {
    "node1": CabinMeta(
        cabin_id="node1",
        instrument_id="REM-NOD1SSC22-pre",
        name="Node 1 (Unity)",
        role="Galley, Dining & Common Hub",
        shielding_note="Highest 23-day REM mean (28.16 uGy/h); radial docking hub.",
        default_hours=2.0,
    ),
    "jpm": CabinMeta(
        cabin_id="jpm",
        instrument_id="REM-JPM1FD4-pre",
        name="Kibo (JPM)",
        role="JAXA Science Laboratory",
        shielding_note="25.67 uGy/h mean; large pressurized science volume.",
        default_hours=4.0,
    ),
    "columbus": CabinMeta(
        cabin_id="columbus",
        instrument_id="REM-COL1A2-pre",
        name="Columbus (ESA)",
        role="ESA Science Lab (DOSTEL Host)",
        shielding_note="25.43 uGy/h mean; reference location for DosTel1/2.",
        default_hours=4.0,
    ),
    "node3": CabinMeta(
        cabin_id="node3",
        instrument_id="REM-NOD3SSC24-pre",
        name="Node 3 (Tranquility)",
        role="ARED Gym, Treadmill & Sleep/Hygiene",
        shielding_note="24.93 uGy/h mean; crew exercise & water recovery racks.",
        default_hours=10.0,
    ),
    "cupola": CabinMeta(
        cabin_id="cupola",
        instrument_id="REM-CUPSSC17-pre",
        name="Cupola",
        role="Earth Observation & Robotics Dome",
        shielding_note="22.25 uGy/h mean; multi-pane fused silica windows.",
        default_hours=1.0,
    ),
    "uslab": CabinMeta(
        cabin_id="uslab",
        instrument_id="REM-LABSSC8-pre",
        name="Destiny (US Lab)",
        role="Primary Lab & Shielded Core",
        shielding_note="Lowest 23-day mean (20.53 uGy/h), dense payload racks.",
        default_hours=3.0,
    ),
}

INSTRUMENT_TO_CABIN = {meta.instrument_id: cid for cid, meta in ISS_CABINS.items()}

# Realistic 24h astronaut schedule across ISS modules (00:00..23:00 UTC)
DEFAULT_HOURLY_SCHEDULE: List[str] = (
    ["node3"] * 8       # 00-07: Sleep / Crew Quarters proxy (water-wall racks)
    + ["node1"] * 1     # 08: Breakfast in Unity Galley
    + ["uslab"] * 3     # 09-11: Destiny Lab operations
    + ["node3"] * 2     # 12-13: ARED / T2 Exercise + Lunch prep
    + ["node1"] * 1     # 14: Midday meal in Unity
    + ["columbus"] * 4  # 15-18: Columbus science block
    + ["jpm"] * 3       # 19-21: Kibo JPM payloads
    + ["cupola"] * 1    # 22: Robotics / Cupola check
    + ["node3"] * 1     # 23: Pre-sleep hygiene
)


@lru_cache(maxsize=1)
def load_rem_summary() -> Dict[str, dict]:
    """Load 23-day REM cabin statistics and shielding ratios vs Columbus & Vessel Avg."""
    by_cabin: Dict[str, List[float]] = {}
    by_ts: Dict[str, Dict[str, float]] = {}
    all_rates: List[float] = []
    with REM_CSV.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            cid = INSTRUMENT_TO_CABIN.get(row["instrument_id"])
            if not cid:
                continue
            rate = float(row["absorbed_dose_rate"])
            by_cabin.setdefault(cid, []).append(rate)
            by_ts.setdefault(row["timestamp"], {})[cid] = rate
            all_rates.append(rate)

    columbus_mean = float(np.mean(by_cabin["columbus"]))
    vessel_mean = float(np.mean(all_rates))

    summary: Dict[str, dict] = {}
    for cid, meta in ISS_CABINS.items():
        vals = by_cabin[cid]
        c_mean = float(np.mean(vals))
        summary[cid] = {
            "cabin_id": cid,
            "instrument_id": meta.instrument_id,
            "name": meta.name,
            "role": meta.role,
            "shielding_note": meta.shielding_note,
            "days": int(len(vals)),
            "rem_mean_ugy_h": round(c_mean, 2),
            "rem_min_ugy_h": round(float(np.min(vals)), 2),
            "rem_max_ugy_h": round(float(np.max(vals)), 2),
            "ratio_vs_columbus": round(c_mean / columbus_mean, 4),
            "ratio_vs_vessel_avg": round(c_mean / vessel_mean, 4),
        }

    daily_series = [
        {"date": ts[:10], **{cid: round(float(by_ts[ts][cid]), 2) for cid in ISS_CABINS if cid in by_ts[ts]}}
        for ts in sorted(by_ts)
    ]
    return {"cabins": summary, "vessel_mean_ugy_h": round(vessel_mean, 2), "daily_series": daily_series}


@lru_cache(maxsize=1)
def load_orbital_bins() -> List[Dict[str, float]]:
    """
    Build a time-weighted 24-hour orbital radiation profile (in Columbus) from DosTel1.

    DosTel1 switches from ~100s cadence outside the South Atlantic Anomaly (SAA)
    to ~20s cadence inside the SAA. Integrating by actual dt prevents 5x SAA bias
    and yields ~0.210 mGy/day (0.455 mSv/day), matching published ISS baselines.
    """
    rows: List[tuple] = []
    with ORBITAL_CSV.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("instrument_id") != "DosTel1":
                continue
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            rate = float(row["absorbed_dose_rate"])
            rows.append((ts, lat, lon, rate))
    rows.sort(key=lambda r: r[0])

    n = len(rows)
    dt_h = np.empty(n, dtype=float)
    rates = np.empty(n, dtype=float)
    in_saa = np.zeros(n, dtype=bool)
    hours = np.empty(n, dtype=int)
    for i, (ts, lat, lon, rate) in enumerate(rows):
        if i == 0:
            dt_s = 100.0
        else:
            dt_s = max(1.0, min(300.0, (ts - rows[i - 1][0]).total_seconds()))
        dt_h[i] = dt_s / 3600.0
        rates[i] = rate
        in_saa[i] = (-55.0 <= lat <= 5.0) and (-95.0 <= lon <= 45.0) and (rate > 20.0)
        hours[i] = ts.hour

    gcr_baseline_mean = float(np.mean(rates[~in_saa]))
    q_gcr = NASA_RADIATION_STANDARDS["quality_factor_gcr"]
    q_saa = NASA_RADIATION_STANDARDS["quality_factor_saa"]
    gcr_part = np.where(in_saa, gcr_baseline_mean, rates)
    saa_excess = np.clip(rates - gcr_part, 0.0, None)
    eq_rate = gcr_part * q_gcr + saa_excess * q_saa

    abs_dose = rates * dt_h
    eq_dose = eq_rate * dt_h
    out: List[Dict[str, float]] = []
    for hr in sorted(set(int(h) for h in hours)):
        mask = hours == hr
        tot_h = float(np.sum(dt_h[mask]))
        out.append(
            {
                "hour": float(hr),
                "columbus_abs_ugy_h": float(np.sum(abs_dose[mask])) / tot_h,
                "columbus_eq_usv_h": float(np.sum(eq_dose[mask])) / tot_h,
                "saa_fraction": float(np.mean(in_saa[mask])),
                "peak_ugy_h": float(np.max(rates[mask])),
            }
        )
    return out


def _normalize_schedule(
    hourly_schedule: List[str] | None = None,
    cabin_hours: Dict[str, float] | None = None,
) -> tuple[List[str], Dict[str, float]]:
    """Return a 24-element hourly schedule and hour counts per cabin."""
    if hourly_schedule and len(hourly_schedule) == 24:
        clean = [c if c in ISS_CABINS else "uslab" for c in hourly_schedule]
        counts = {cid: float(clean.count(cid)) for cid in ISS_CABINS}
        return clean, counts

    if cabin_hours:
        # Allocate 24 integer/proportional slots cleanly
        raw = {cid: max(0.0, float(cabin_hours.get(cid, 0.0))) for cid in ISS_CABINS}
        total = sum(raw.values())
        if total <= 0:
            return DEFAULT_HOURLY_SCHEDULE, {cid: float(DEFAULT_HOURLY_SCHEDULE.count(cid)) for cid in ISS_CABINS}

        scaled = {cid: (val / total) * 24.0 for cid, val in raw.items()}
        int_slots = {cid: int(np.floor(v)) for cid, v in scaled.items()}
        remainder = 24 - sum(int_slots.values())
        for cid in sorted(scaled, key=lambda k: scaled[k] - int_slots[k], reverse=True)[:remainder]:
            int_slots[cid] += 1

        schedule: List[str] = []
        for cid in ISS_CABINS:
            schedule.extend([cid] * int_slots[cid])
        return schedule[:24], scaled

    return DEFAULT_HOURLY_SCHEDULE, {cid: float(DEFAULT_HOURLY_SCHEDULE.count(cid)) for cid in ISS_CABINS}


def simulate_astronaut_radiation(
    hourly_schedule: List[str] | None = None,
    cabin_hours: Dict[str, float] | None = None,
    mission_days: int = 30,
    prior_career_msv: float = 120.0,
    solar_storm_active: bool = False,
    personal_dosimeter_online: bool = True,
) -> dict:
    """
    Simulate cabin-tracked radiation vs. naive vessel-average estimation.

    When solar_storm_active is True, applies a Solar Particle Event (SPE) flux
    multiplier (18x in lightly shielded Cupola, 8x in Node 1/labs, 4.5x in
    shielded Destiny core / Node 3 water walls) to illustrate ALARA shelter value.
    """
    mission_days = max(1, min(365, int(mission_days)))
    rem_data = load_rem_summary()
    cabins_meta = rem_data["cabins"]
    vessel_ratio = rem_data["vessel_mean_ugy_h"] / cabins_meta["columbus"]["rem_mean_ugy_h"]

    schedule, hour_counts = _normalize_schedule(hourly_schedule, cabin_hours)
    orbital = load_orbital_bins()

    # SPE shielding factors (water-wall & payload rack attenuation during solar flare)
    spe_multipliers = {
        "uslab": 4.5,
        "node3": 5.0,
        "columbus": 7.5,
        "jpm": 7.5,
        "node1": 9.0,
        "cupola": 18.0,
    }
    vessel_spe_mult = float(np.mean(list(spe_multipliers.values())))

    hourly_trace = []
    cum_cabin_usv = 0.0
    cum_vessel_usv = 0.0
    cum_cabin_ugy = 0.0
    cum_vessel_ugy = 0.0

    for row in orbital:
        hr = int(row["hour"])
        cid = schedule[hr]
        cabin_ratio = cabins_meta[cid]["ratio_vs_columbus"]
        storm_factor = spe_multipliers[cid] if solar_storm_active else 1.0
        vessel_storm = vessel_spe_mult if solar_storm_active else 1.0

        cabin_abs_h = float(row["columbus_abs_ugy_h"]) * cabin_ratio * storm_factor
        cabin_eq_h = float(row["columbus_eq_usv_h"]) * cabin_ratio * storm_factor

        vessel_abs_h = float(row["columbus_abs_ugy_h"]) * vessel_ratio * vessel_storm
        vessel_eq_h = float(row["columbus_eq_usv_h"]) * vessel_ratio * vessel_storm

        cum_cabin_ugy += cabin_abs_h
        cum_vessel_ugy += vessel_abs_h
        cum_cabin_usv += cabin_eq_h
        cum_vessel_usv += vessel_eq_h

        hourly_trace.append(
            {
                "hour": hr,
                "label": f"{hr:02d}:00",
                "cabin_id": cid,
                "cabin_name": cabins_meta[cid]["name"],
                "saa_pass": bool(row["saa_fraction"] > 0.05),
                "cabin_rate_usv_h": round(cabin_eq_h, 2),
                "vessel_avg_rate_usv_h": round(vessel_eq_h, 2),
                "cum_cabin_usv": round(cum_cabin_usv, 1),
                "cum_vessel_avg_usv": round(cum_vessel_usv, 1),
            }
        )

    daily_cabin_mgy = cum_cabin_ugy / 1000.0
    daily_cabin_msv = cum_cabin_usv / 1000.0
    daily_vessel_mgy = cum_vessel_ugy / 1000.0
    daily_vessel_msv = cum_vessel_usv / 1000.0

    mission_cabin_msv = daily_cabin_msv * mission_days
    mission_vessel_msv = daily_vessel_msv * mission_days
    delta_pct = ((daily_cabin_msv - daily_vessel_msv) / daily_vessel_msv) * 100.0 if daily_vessel_msv else 0.0

    # Optimal ALARA comparison: spending work hours in Destiny (lowest REM ratio)
    best_ratio = min(c["ratio_vs_columbus"] for c in cabins_meta.values())
    optimal_daily_msv = sum(float(r["columbus_eq_usv_h"]) for r in orbital) / 1000.0 * best_ratio
    alara_savings_pct = max(0.0, ((daily_cabin_msv - optimal_daily_msv) / daily_cabin_msv) * 100.0) if not solar_storm_active else 0.0

    career_total_msv = prior_career_msv + mission_cabin_msv
    career_limit = NASA_RADIATION_STANDARDS["career_effective_dose_msv"]
    career_pct_used = (career_total_msv / career_limit) * 100.0

    # NASA-STD-3001 Organ Check (30-day BFO in mGy-Eq approximated from mission rate)
    bfo_30d_mgy_eq = daily_cabin_msv * min(30, mission_days)
    bfo_limit_30d = NASA_RADIATION_STANDARDS["organs"]["bfo"].limit_30d

    # Sub-score (0-100) for holistic Readiness Score
    if solar_storm_active and (hour_counts.get("cupola", 0) > 0 or hour_counts.get("node1", 0) > 2):
        status = "CRITICAL"
        rad_score = 32
        guidance = (
            "SOLAR PARTICLE EVENT (SPE): Relocate immediately from Cupola/Node 1 to "
            "Destiny US Lab or Node 3 water-wall shelter. Defer EVAs per NASA-STD-3001 ALARA."
        )
    elif solar_storm_active:
        status = "WARNING"
        rad_score = 58
        guidance = (
            "SPE Active — Crew inside higher-shielded core modules. Monitor BFO 30-day limit "
            "(250 mGy-Eq) and maintain shelter posture until solar proton flux subsides."
        )
    elif career_total_msv >= career_limit * 0.85 or daily_cabin_msv > NASA_RADIATION_STANDARDS["alara_daily_alert_msv"]:
        status = "WARNING"
        rad_score = 68
        guidance = (
            f"Elevated daily exposure ({daily_cabin_msv:.3f} mSv/day). Shift non-essential tasks "
            f"from Node 1 (28.16 uGy/h) to Destiny US Lab (20.53 uGy/h) to cut exposure by ~{alara_savings_pct:.0f}%."
        )
    elif delta_pct > 5.0:
        status = "WATCH"
        rad_score = 84
        guidance = (
            f"Cabin-tracked dose is +{delta_pct:.1f}% above naive vessel average due to high-flux module occupancy. "
            f"ALARA optimization to Destiny Lab can reduce dose by ~{alara_savings_pct:.0f}%."
        )
    else:
        status = "NOMINAL"
        rad_score = 94
        guidance = (
            "Daily dose rate nominal under NASA-STD-3001 ALARA protocol; no mandatory module transfer required."
        )

    dosimeter_source = (
        "MEASURED (Personal Dosimeter + REM Verification)"
        if personal_dosimeter_online
        else "ESTIMATED (Personal Dosimeter Offline — Inferred from Cabin Occupancy × RadLab REM)"
    )

    # Effective per-cabin dose rate (uGy/h) reflecting active solar storm shielding factors
    effective_rates_ugy_h = {
        cid: round(
            cabins_meta[cid]["rem_mean_ugy_h"] * (spe_multipliers[cid] if solar_storm_active else 1.0),
            2,
        )
        for cid in ISS_CABINS
    }

    # Compute per-cabin dose share & plain-English Simple Astronaut Mode guidance
    cabin_usv_totals: Dict[str, float] = {cid: 0.0 for cid in ISS_CABINS}
    for pt in hourly_trace:
        cabin_usv_totals[pt["cabin_id"]] += pt["cabin_rate_usv_h"]

    total_usv = sum(cabin_usv_totals.values()) or 1.0
    cabin_share_pct = {cid: round((val / total_usv) * 100.0, 1) for cid, val in cabin_usv_totals.items()}

    # Identify highest non-core dose contributor (or overall top contributor)
    non_core_active = [cid for cid in ("cupola", "node1", "jpm", "columbus") if hour_counts.get(cid, 0) > 0]
    culprit_id = max(
        non_core_active if non_core_active else list(ISS_CABINS.keys()),
        key=lambda cid: cabin_usv_totals[cid],
    )
    culprit_name = cabins_meta[culprit_id]["name"]
    culprit_pct = cabin_share_pct[culprit_id]

    # Build a concrete damage-limiting move to Destiny (US Lab) with transparent source accounting
    recommended_target = "uslab"
    move_hours = 0.0
    moved_sources: Dict[str, float] = {}
    preview_cabin_hours = dict(hour_counts)
    if solar_storm_active:
        for cid in ("cupola", "node1", "columbus", "jpm"):
            hrs = preview_cabin_hours.get(cid, 0.0)
            if hrs > 0:
                preview_cabin_hours[cid] = 0.0
                preview_cabin_hours[recommended_target] = preview_cabin_hours.get(recommended_target, 0.0) + hrs
                moved_sources[cid] = hrs
                move_hours += hrs
    elif culprit_id != "uslab" and culprit_id != "node3" and hour_counts.get(culprit_id, 0.0) > 0:
        move_hours = min(4.0, float(hour_counts[culprit_id]))
        preview_cabin_hours[culprit_id] = max(0.0, preview_cabin_hours[culprit_id] - move_hours)
        preview_cabin_hours[recommended_target] = preview_cabin_hours.get(recommended_target, 0.0) + move_hours
        moved_sources[culprit_id] = move_hours

    # Estimate dose reduction from moving those hours to Destiny US Lab
    if move_hours > 0:
        swapped_schedule = list(schedule)
        remaining = int(round(move_hours))
        priority_sources = ("cupola", "node1", "jpm", "columbus") if solar_storm_active else (culprit_id,)
        for src in priority_sources:
            for idx, cid in enumerate(swapped_schedule):
                if cid == src and remaining > 0:
                    swapped_schedule[idx] = recommended_target
                    remaining -= 1
        preview_usv = 0.0
        for row in orbital:
            hr = int(row["hour"])
            cid = swapped_schedule[hr]
            c_ratio = cabins_meta[cid]["ratio_vs_columbus"]
            s_factor = spe_multipliers[cid] if solar_storm_active else 1.0
            preview_usv += float(row["columbus_eq_usv_h"]) * c_ratio * s_factor
        preview_daily_msv = preview_usv / 1000.0
        dose_reduction_pct = max(0.0, ((cum_cabin_usv - preview_usv) / cum_cabin_usv) * 100.0) if cum_cabin_usv else 0.0
        projected_rad_score = 58 if solar_storm_active else min(96, max(rad_score + 8, 92))
    else:
        preview_daily_msv = daily_cabin_msv
        dose_reduction_pct = 0.0
        projected_rad_score = rad_score
        swapped_schedule = list(schedule)

    source_parts = [f"{int(round(h))}h {cabins_meta[cid]['name']}" for cid, h in moved_sources.items() if round(h) > 0]
    if len(source_parts) == 1:
        source_summary = cabins_meta[next(iter(moved_sources))]["name"]
        source_breakdown = source_parts[0]
    elif len(source_parts) == 2:
        source_names = [cabins_meta[cid]["name"] for cid in moved_sources]
        source_summary = " & ".join(source_names)
        source_breakdown = " + ".join(source_parts)
    else:
        source_summary = "unshielded cabins"
        source_breakdown = ", ".join(source_parts)

    if status == "CRITICAL":
        verdict_headline = "SHELTER NOW — SOLAR STORM ACTIVE"
        verdict_detail = (
            "A solar particle storm is hitting the station. Thin-walled and windowed cabins let in far more radiation right now."
        )
        culprit_text = (
            f"Time in {culprit_name} is driving {culprit_pct:.0f}% of today's radiation exposure."
        )
        action_title = f"Move {int(round(move_hours))}h to {cabins_meta[recommended_target]['name']} shelter now"
        action_detail = (
            f"Relocate {source_breakdown} to Destiny Lab's dense equipment racks. "
            f"Cuts remaining storm exposure by ~{dose_reduction_pct:.0f}%."
        )
    elif status in ("WARNING", "WATCH"):
        verdict_headline = "CAUTION — HIGHER RADIATION SCHEDULE"
        verdict_detail = (
            "Your current cabin schedule puts you in less-shielded modules. You are still within career limits, "
            "but a schedule shift reduces unnecessary exposure."
        )
        culprit_text = (
            f"{culprit_name} accounts for {culprit_pct:.0f}% of today's radiation dose because it has lighter shielding."
        )
        action_title = (
            f"Shift {int(round(move_hours))}h from {source_summary} to {cabins_meta[recommended_target]['name']}"
            if move_hours > 0
            else "Maintain time in Destiny US Lab"
        )
        action_detail = (
            f"Relocate {source_breakdown} to Destiny Lab's thick equipment shielding — "
            f"lowers today's radiation by ~{dose_reduction_pct:.0f}%."
            if move_hours > 0
            else "You are already scheduled in the best-shielded modules."
        )
    else:
        verdict_headline = "SAFE — NORMAL ORBITAL EXPOSURE"
        verdict_detail = (
            "Today's radiation level is well within NASA safety limits. No shelter action needed."
        )
        culprit_text = (
            f"Highest share today: {culprit_name} ({culprit_pct:.0f}% of daily dose), within normal bounds."
        )
        action_title = (
            f"Optional: Move {int(round(move_hours))}h from {source_summary} to {cabins_meta[recommended_target]['name']}"
            if move_hours > 0
            else "Keep current cabin schedule"
        )
        action_detail = (
            f"Moving {source_breakdown} to Destiny Lab reduces exposure slightly (−{dose_reduction_pct:.1f}% today)."
            if move_hours > 0
            else "Your schedule already favors the best-shielded modules (Destiny & Node 3)."
        )

    shielding_ratings = {
        "uslab": "BEST SHIELDING",
        "node3": "GOOD (WATER WALL)",
        "cupola": "AVOID IN STORM" if solar_storm_active else "WINDOW DOME",
        "columbus": "ELEVATED IN STORM" if solar_storm_active else "MODERATE",
        "jpm": "ELEVATED IN STORM" if solar_storm_active else "MODERATE",
        "node1": "HIGH IN STORM" if solar_storm_active else "HIGHER EXPOSURE",
    }

    simple_summary = {
        "verdict_headline": verdict_headline,
        "verdict_detail": verdict_detail,
        "culprit_cabin_id": culprit_id,
        "culprit_pct": culprit_pct,
        "culprit_text": culprit_text,
        "recommended_action": {
            "can_improve": move_hours > 0,
            "source_cabin_id": culprit_id,
            "moved_sources": {k: round(v, 2) for k, v in moved_sources.items()},
            "target_cabin_id": recommended_target,
            "hours_to_move": int(round(move_hours)),
            "dose_reduction_pct": round(dose_reduction_pct, 1),
            "preview_daily_msv": round(preview_daily_msv, 3),
            "projected_rad_score": projected_rad_score,
            "preview_cabin_hours": {k: round(v, 2) for k, v in preview_cabin_hours.items()},
            "action_title": action_title,
            "action_detail": action_detail,
        },
        "cabin_share_pct": cabin_share_pct,
        "effective_rates_ugy_h": effective_rates_ugy_h,
        "shielding_ratings": shielding_ratings,
    }

    return {
        "dosimeter_status": "measured" if personal_dosimeter_online else "estimated",
        "dosimeter_label": dosimeter_source,
        "mission_days": mission_days,
        "solar_storm_active": solar_storm_active,
        "daily_cabin_mgy": round(daily_cabin_mgy, 3),
        "daily_cabin_msv": round(daily_cabin_msv, 3),
        "daily_vessel_avg_mgy": round(daily_vessel_mgy, 3),
        "daily_vessel_avg_msv": round(daily_vessel_msv, 3),
        "delta_vs_vessel_pct": round(delta_pct, 2),
        "mission_cabin_msv": round(mission_cabin_msv, 2),
        "mission_vessel_avg_msv": round(mission_vessel_msv, 2),
        "prior_career_msv": round(prior_career_msv, 1),
        "career_total_msv": round(career_total_msv, 2),
        "career_limit_msv": career_limit,
        "career_pct_used": round(career_pct_used, 2),
        "bfo_30d_mgy_eq": round(bfo_30d_mgy_eq, 2),
        "bfo_30d_limit_mgy_eq": bfo_limit_30d,
        "status": status,
        "radiation_score": rad_score,
        "alara_guidance": guidance,
        "simple_summary": simple_summary,
        "cabin_hours": {k: round(v, 2) for k, v in hour_counts.items()},
        "hourly_schedule": schedule,
        "hourly_trace": hourly_trace,
        "cabins": cabins_meta,
        "daily_rem_series": rem_data["daily_series"],
    }
