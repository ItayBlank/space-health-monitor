"""
Holistic Astronaut Readiness Score Backbone.

Combines 5 NASA-aligned health & environment pillars into a single 0-100
Readiness Score with Green/Yellow/Red triage status and actionable guidance.

Right now, `radiation` is powered by live NASA RadLab simulation. The other
4 pillar slots (`air_quality`, `sleep_vigilance`, `cardio_vitals`,
`exercise_nutrition`) expose clean plug-in contracts so teammates can drop in
NASA EDA CO2, OpenNeuro PVT, PhysioNet ECG/HRV, and Edge AI ARED modules.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .standards import READINESS_WEIGHTS


def compute_holistic_readiness(
    radiation_result: Dict[str, Any],
    pillar_overrides: Dict[str, Dict[str, Any]] | None = None,
    vitals_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Fuse all 5 pillars into the unified Astronaut Readiness Score (0-100)."""
    overrides = dict(pillar_overrides or {})
    if vitals_result is not None and "cardio_vitals" not in overrides:
        overrides["cardio_vitals"] = vitals_result["readiness_patch"]

    pillars: Dict[str, Dict[str, Any]] = {
        "radiation": {
            "label": "Radiation & Shielding",
            "weight": READINESS_WEIGHTS["radiation"],
            "score": radiation_result["radiation_score"],
            "status": radiation_result["status"],
            "source": f"NASA RadLab ({radiation_result['dosimeter_status'].upper()})",
            "summary": (
                f"{radiation_result['daily_cabin_msv']:.3f} mSv/day "
                f"({radiation_result['delta_vs_vessel_pct']:+.1f}% vs vessel avg)"
            ),
            "crew_summary": radiation_result["simple_summary"]["verdict_headline"],
            "crew_action": radiation_result["simple_summary"]["recommended_action"]["action_title"],
            "action": radiation_result["alara_guidance"],
            "is_live_module": True,
        },
        "air_quality": {
            "label": "Cabin Air Quality",
            "weight": READINESS_WEIGHTS["air_quality"],
            "score": 92,
            "status": "NOMINAL",
            "source": "NASA EDA + Cabin CO2 Slot",
            "summary": "ppCO2 1.9 mmHg (< 3.0 mmHg NASA-STD-3001 limit), 21.8 °C",
            "crew_summary": "Cabin air is clean and fresh (CO2 & oxygen normal).",
            "crew_action": "No ventilation changes needed.",
            "action": "ECLSS nominal. Ready to wire NASA EDA CSV + hatch/EVA triggers.",
            "is_live_module": False,
        },
        "sleep_vigilance": {
            "label": "Sleep & Alertness",
            "weight": READINESS_WEIGHTS["sleep_vigilance"],
            "score": 88,
            "status": "NOMINAL",
            "source": "OpenNeuro ds004902 PVT Slot",
            "summary": "7.2h sleep, nominal PANAS mood, 3-min PVT not triggered",
            "crew_summary": "7.2 hrs sleep logged · Focus & mood steady.",
            "crew_action": "No reaction check required today.",
            "action": "Ready to wire OpenNeuro mood/sleep -> 3-min vigilance trigger.",
            "is_live_module": False,
        },
        "cardio_vitals": {
            "label": "Heart & Blood Flow",
            "weight": READINESS_WEIGHTS["cardio_vitals"],
            "score": 90,
            "status": "NOMINAL",
            "source": "Bio-Monitor / PhysioNet ECG Slot",
            "summary": "HR 64 bpm, HRV 52 ms, SpO2 98%, Fluid Shift baseline",
            "crew_summary": "Resting heart rate 64 bpm · Blood oxygen 98%.",
            "crew_action": "Hydration and fluid balance look steady.",
            "action": "Ready to wire PhysioNet 250Hz ECG/PPG DSP & ESP32 feed.",
            "is_live_module": False,
        },
        "exercise_nutrition": {
            "label": "Strength & Nutrition",
            "weight": READINESS_WEIGHTS["exercise_nutrition"],
            "score": 86,
            "status": "NOMINAL",
            "source": "ARED Pose Tracker + Meal Log Slot",
            "summary": "ARED resistive load 100%, 2,750 kcal, 2.4L hydration",
            "crew_summary": "Daily strength workout complete · 2.4 L water logged.",
            "crew_action": "Stay on track with evening meal & Vitamin D.",
            "action": "Ready to wire MediaPipe webcam rep counter & OSDR nutrition.",
            "is_live_module": False,
        },
    }

    for key, patch in overrides.items():
        if key in pillars:
            pillars[key].update(patch)
            pillars[key]["is_live_module"] = True

    weighted_score = sum(p["score"] * p["weight"] for p in pillars.values())
    # Critical safety override: if any life-critical pillar drops < 40, cap readiness
    min_pillar = min(p["score"] for p in pillars.values())
    if min_pillar < 40:
        weighted_score = min(weighted_score, 49.0)

    overall_score = round(weighted_score)
    if overall_score >= 80 and min_pillar >= 65:
        overall_status = "GREEN — EVA CLEARED"
        tier = "nominal"
    elif overall_score >= 60 and min_pillar >= 40:
        overall_status = "YELLOW — COUNTERMEASURE REQUIRED"
        tier = "warning"
    else:
        overall_status = "RED — RESTRICT EVA / ESCALATE"
        tier = "critical"

    # Collect prioritized active actions (non-nominal first)
    actions: List[dict] = [
        {"pillar": p["label"], "status": p["status"], "action": p["action"]}
        for p in pillars.values()
        if p["status"] != "NOMINAL"
    ]
    if not actions:
        actions.append(
            {
                "pillar": "All Systems",
                "status": "NOMINAL",
                "action": "All telemetry within NASA-STD-3001 bounds. Continue nominal routine.",
            }
        )

    return {
        "overall_score": overall_score,
        "overall_status": overall_status,
        "tier": tier,
        "pillars": pillars,
        "priority_actions": actions,
    }
