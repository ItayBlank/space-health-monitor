"""
HAL2030 Core Bridge for ASTRA-Core FastAPI Server.

Connects the team's deterministic 10-minute 6-crew telemetry replay,
activity-aware AlertEngine, 42-channel sensor status matrix, store-and-forward
DownlinkService queue, and honest HAL2030 cabin companion replies into the
VisionOS web tablet API.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from hal2030.alerts import AlertEngine, crew_status, sensor_status
from hal2030.config import CREW, METRICS, SCENARIOS, SENSORS
from hal2030.downlink import DownlinkService, _snapshot
from hal2030.paths import resource_root, runtime_root
from hal2030.telemetry import CsvReplaySource
from hal2030.vision import Calibration, EyeTest, levels_for, make_report

BASE_DIR = resource_root()
RUNTIME_DOWNLINK_DIR = runtime_root() / "downlink"

_SOURCE: Optional[CsvReplaySource] = None
_ENGINE: Optional[AlertEngine] = None
_DOWNLINK: Optional[DownlinkService] = None


def get_source() -> CsvReplaySource:
    """Return cached 10-minute 6-crew CsvReplaySource singleton."""
    global _SOURCE
    if _SOURCE is None:
        _SOURCE = CsvReplaySource(BASE_DIR / "data" / "telemetry_10min.csv")
    return _SOURCE


def get_alert_engine() -> AlertEngine:
    """Return cached activity-aware AlertEngine singleton."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = AlertEngine()
    return _ENGINE


def get_downlink(output_dir: Path | None = None) -> DownlinkService:
    """Return cached store-and-forward DownlinkService singleton (or custom dir for tests)."""
    global _DOWNLINK
    if output_dir is not None:
        return DownlinkService(output_dir)
    if _DOWNLINK is None:
        _DOWNLINK = DownlinkService(RUNTIME_DOWNLINK_DIR)
    return _DOWNLINK


def _clean_float(val: Any, decimals: int = 3) -> Optional[float]:
    if val is None:
        return None
    f = float(val)
    if not math.isfinite(f):
        return None
    return round(f, decimals)


def _clean_series(arr: np.ndarray, decimals: int = 2, stride: int = 1) -> List[Optional[float]]:
    sliced = arr[::stride] if stride > 1 else arr
    return [None if not math.isfinite(float(v)) else round(float(v), decimals) for v in sliced]


def get_hal_frame(
    t: float = 0.0,
    window_s: int = 90,
    trend_crew_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build complete 6-crew frame, alerts, 42-channel matrix, and optional waveforms."""
    src = get_source()
    engine = get_alert_engine()
    clamped_t = max(0.0, min(float(t), float(src.duration - 1)))
    frame = src.frame(clamped_t)
    alerts = engine.evaluate(frame)

    crew_meta = [
        {
            **person,
            "avatar": f"/static/assets/portraits/{person['id']}.png",
        }
        for person in CREW
    ]

    samples_out: Dict[str, Any] = {}
    for cid, sample in frame.items():
        connected_count = sum(1 for v in sample.sensor_status.values() if v == "online")
        samples_out[cid] = {
            "t": sample.t,
            "activity": sample.activity,
            "values": {k: _clean_float(v, METRICS.get(k, {}).get("decimals", 1)) for k, v in sample.values.items()},
            "sensor_status": dict(sample.sensor_status),
            "connected_sensors": connected_count,
            "total_sensors": len(SENSORS),
            "cabin_co2": _clean_float(sample.cabin_co2, 0),
            "cabin_temp": _clean_float(sample.cabin_temp, 1),
            "signal_quality": _clean_float(sample.signal_quality, 3),
            "status": crew_status(cid, alerts),
        }

    alerts_out = [
        {
            "key": a.key,
            "crew_id": a.crew_id,
            "severity": a.severity,
            "title": a.title,
            "metric": a.metric,
            "value": _clean_float(a.value, 2),
            "recommendation": a.recommendation,
            "steps": list(a.steps),
            "sensor_id": a.sensor_id,
        }
        for a in alerts
    ]

    sensor_matrix: List[Dict[str, Any]] = []
    for person in CREW:
        cid = person["id"]
        sample = frame.get(cid)
        if sample is None:
            continue
        for sensor in SENSORS:
            sid = sensor["id"]
            link_state = sample.sensor_status.get(sid, "no_signal")
            connected = link_state == "online"
            state = sensor_status(cid, sid, frame, alerts)
            parts: List[str] = []
            for mkey in sensor["metrics"]:
                val = sample.values.get(mkey) if connected else None
                if val is not None and math.isfinite(float(val)):
                    mdef = METRICS.get(mkey, {})
                    dec = int(mdef.get("decimals", 0))
                    unit = mdef.get("unit", "")
                    short = {"eeg_alpha": "α", "eeg_beta": "β", "hrv": "HRV", "systolic": "SYS", "diastolic": "DIA"}.get(mkey, "")
                    parts.append(f"{short + ' ' if short else ''}{float(val):.{dec}f} {unit}".strip())
            sensor_matrix.append(
                {
                    "crew_id": cid,
                    "crew_name": person["name"],
                    "sensor_id": sid,
                    "sensor_name": sensor["name"],
                    "placement": sensor["placement"],
                    "sample_rate": sensor["sample_rate"],
                    "link_state": link_state,
                    "state": state,
                    "reading_display": "  /  ".join(parts) if parts else "—",
                    "quality_pct": round(float(sample.signal_quality) * 100.0) if connected else None,
                    "battery_pct": _clean_float(sample.values.get("battery"), 0),
                }
            )

    selected_crew = trend_crew_id if trend_crew_id in frame else CREW[0]["id"]
    hist_secs = max(30, min(int(window_s), 240))
    end_sec = int(clamped_t)
    start_sec = max(0, end_sec - hist_secs + 1)
    co2_t = list(range(start_sec, end_sec + 1))
    co2_vals = [_clean_float(src.frame(sec)[selected_crew].cabin_co2, 0) for sec in co2_t]

    payload: Dict[str, Any] = {
        "simulation": True,
        "t": round(clamped_t, 2),
        "duration": src.duration,
        "crew": crew_meta,
        "scenarios": list(SCENARIOS),
        "sensors_meta": list(SENSORS),
        "metrics_meta": dict(METRICS),
        "samples": samples_out,
        "alerts": alerts_out,
        "sensor_matrix": sensor_matrix,
        "cabin_co2_history": {
            "t": co2_t,
            "values": co2_vals,
        },
    }

    if trend_crew_id and trend_crew_id in frame:
        trends: Dict[str, Any] = {}
        for metric in ("heart_rate", "spo2", "resp_rate", "skin_temp", "hrv"):
            mt, mv = src.history(trend_crew_id, metric, clamped_t, seconds=hist_secs)
            trends[metric] = {"t": [int(x) for x in mt], "values": _clean_series(mv, 1)}
        waveforms: Dict[str, Any] = {}
        for kind in ("ecg", "respiration", "eeg"):
            wx, wy = src.waveform(trend_crew_id, kind, clamped_t, seconds=6.0)
            waveforms[kind] = {
                "t": _clean_series(wx, 3, stride=4),
                "values": _clean_series(wy, 3, stride=4),
            }
        payload["detail_crew_id"] = trend_crew_id
        payload["trends"] = trends
        payload["waveforms"] = waveforms

    return payload


def serialize_downlink(service: DownlinkService) -> Dict[str, Any]:
    """Serialize DownlinkService queue and transport configuration."""
    q = [dict(p) for p in service.queue]
    delivered = sum(1 for p in q if p.get("status") == "delivered")
    in_transit = sum(1 for p in q if p.get("status") == "in_transit")
    queued = sum(1 for p in q if p.get("status") == "queued")
    return {
        "simulation": True,
        "connected": bool(service.connected),
        "latency_s": int(service.latency_s),
        "auto_send": bool(service.auto_send),
        "status_text": service.status_text,
        "recovery_warning": service.recovery_warning,
        "total_packets": len(q),
        "delivered_count": delivered,
        "in_transit_count": in_transit,
        "queued_count": queued,
        "queue": list(reversed(q)),  # newest first for tablet display
    }


def read_downlink_packet(service: DownlinkService, packet_id: str) -> Optional[Dict[str, Any]]:
    """Read stored JSON payload for a packet id, or None if not found."""
    match = next((p for p in service.queue if p.get("id") == packet_id), None)
    if match is None:
        return None
    fpath = service.output_dir / str(match["filename"])
    if not fpath.exists():
        return None
    return json.loads(fpath.read_text(encoding="utf-8"))


def build_snapshot_payload(frame: Any, alerts: Any, mission_time: float) -> Dict[str, Any]:
    """Build exportable JSON snapshot preserving missing values as JSON null."""
    return _snapshot(frame, alerts, mission_time)


def build_companion_reply(
    crew_id: str,
    text: str,
    family_mode: bool = False,
    t: float = 0.0,
) -> Dict[str, Any]:
    """Return honest HAL2030 scripted preview or simulated family archive reply."""
    src = get_source()
    clamped_t = max(0.0, min(float(t), float(src.duration - 1)))
    frame = src.frame(clamped_t)
    person = next((c for c in CREW if c["id"] == crew_id), CREW[0])
    cid = person["id"]
    first_name = person["name"].split()[0]
    lower = text.strip().lower()

    if family_mode:
        if any(word in lower for word in ("sleep", "rest", "tired")):
            reply = (
                "A fictional message from the archive: Take a quiet moment and tell me about one good thing from your day. "
                "We can turn that into a message for home when you are ready."
            )
        else:
            reply = (
                f"This is a simulated family conversation, {first_name}. Imagine a familiar voice asking: "
                "what was the most interesting part of your day? We can keep a thought ready for your next real message to Earth."
            )
        speaker = "Family archive · simulated sample"
        kind = "family"
    else:
        speaker = "HAL2030 · scripted preview"
        kind = "assistant"
        if any(word in lower for word in ("reading", "health", "oxygen", "heart", "sensor", "status")):
            sample = frame.get(cid)
            if sample is None:
                reply = "I am waiting for the demonstration telemetry frame. Open Glance or Body HUD once replay starts."
            else:
                def fmt(metric: str, unit: str) -> str:
                    val = sample.values.get(metric)
                    return "no signal" if val is None or not math.isfinite(float(val)) else f"{float(val):.0f} {unit}"

                reply = (
                    f"Your current simulated readings at T+{int(clamped_t)//60:02d}:{int(clamped_t)%60:02d} are: "
                    f"heart rate {fmt('heart_rate', 'bpm')}, blood oxygen {fmt('spo2', '%')}, "
                    f"and breathing rate {fmt('resp_rate', 'breaths/min')}. "
                    "Open Body Action HUD or Heart Lab for action checklists; this scripted chat cannot diagnose medical conditions."
                )
        elif any(word in lower for word in ("miss", "home", "family", "lonely")):
            reply = (
                f"Being far from familiar people can feel difficult, {first_name}. What would you most like them to hear today? "
                "You can put that into words here. Family archive mode is a clearly marked simulation, and real messages wait for the communication link."
            )
        elif any(word in lower for word in ("sleep", "tired", "rest")):
            reply = (
                "We can make space for a short pause. Check your scheduled rest window, reduce distractions where practical, "
                "and try the 3-minute PVT focus check in Sensors / Head. If fatigue affects tasks, alert your crew medical officer."
            )
        elif any(word in lower for word in ("unwind", "stress", "worry", "anxious", "break", "calm")):
            reply = (
                "Let us pause for a moment. Settle into a comfortable position, relax your shoulders, and breathe slowly at your own pace. "
                "What is one thing on your mind you want to offload right now?"
            )
        elif any(word in lower for word in ("privacy", "private", "send", "ground")):
            reply = (
                "This private cabin session is excluded from telemetry downlink packets. Mission Control packets only contain "
                "health telemetry and alert states, stored locally while Earth communication is offline."
            )
        elif any(word in lower for word in ("hello", "hi", "hey")):
            reply = (
                f"Hello, {first_name}. We can check your simulated readings or take a quiet break. "
                "Prepared responses are active locally while Earth-Mars delay prevents real-time ground coaching."
            )
        else:
            reply = (
                "I am listening through this scripted onboard preview. Ask to review your readings, unwind, "
                "talk about home, plan rest, or verify downlink privacy."
            )

    return {
        "crew_id": cid,
        "speaker": speaker,
        "kind": kind,
        "reply": reply,
        "simulation": True,
        "excluded_from_downlink": True,
    }


def compute_vision_levels(
    px_per_mm_x: float,
    px_per_mm_y: float,
    device_pixel_ratio: float = 1.0,
    display_signature: str = "Web Display · Calibrated 50mm",
    distance_mm: float = 400.0,
) -> Dict[str, Any]:
    """Build display-calibrated Tumbling-E logMAR levels via Itay's hal2030.vision geometry."""
    cal = Calibration(
        px_per_mm_x=float(px_per_mm_x),
        px_per_mm_y=float(px_per_mm_y),
        device_pixel_ratio=float(device_pixel_ratio),
        display_signature=str(display_signature),
        distance_mm=float(distance_mm),
    )
    levels = levels_for(cal)
    return {
        "calibration": {
            "px_per_mm_x": cal.px_per_mm_x,
            "px_per_mm_y": cal.px_per_mm_y,
            "device_pixel_ratio": cal.device_pixel_ratio,
            "display_signature": cal.display_signature,
            "distance_mm": cal.distance_mm,
        },
        "levels": levels,
        "count": len(levels),
    }


def submit_vision_exam(
    crew_id: str,
    symptom: str,
    conditions: Dict[str, Any],
    calibration_dict: Dict[str, Any],
    attempts: List[Dict[str, Any]],
    practice: List[Dict[str, Any]],
    mission_time: float,
    dl: Optional[DownlinkService] = None,
) -> Dict[str, Any]:
    """Validate and queue a completed two-eye near-vision report onto DownlinkService."""
    cal = Calibration(
        px_per_mm_x=float(calibration_dict["px_per_mm_x"]),
        px_per_mm_y=float(calibration_dict["px_per_mm_y"]),
        device_pixel_ratio=float(calibration_dict.get("device_pixel_ratio", 1.0)),
        display_signature=str(calibration_dict.get("display_signature", "Web Display")),
        distance_mm=float(calibration_dict.get("distance_mm", 400.0)),
    )
    report = make_report(
        crew_id=crew_id,
        symptom=symptom,
        conditions=conditions,
        calibration=cal,
        attempts=attempts,
        practice=practice,
    )
    service = dl or get_downlink()
    packet = service.enqueue_report(report, float(mission_time))
    return {"report": report, "packet": packet, "state": serialize_downlink(service)}

