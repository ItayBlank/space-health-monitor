"""Transparent, activity-aware demonstration rules; no AI diagnosis.

Limits deliberately live in config.py. A real mission requires individually
validated baselines, quality assessment, and clinician-approved protocols.
"""
from __future__ import annotations

import math

from .config import DEMO_LIMITS as L, SENSORS
from .models import Alert, Sample


def _valid(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


class AlertEngine:
    def evaluate(self, frame: dict[str, Sample]) -> list[Alert]:
        alerts: list[Alert] = []
        for crew_id, sample in frame.items():
            current_values = dict(sample.values)
            for sensor in SENSORS:
                sensor_id = sensor["id"]
                missing = (sample.sensor_status.get(sensor_id) != "online"
                           or any(not _valid(sample.values.get(key)) for key in sensor["metrics"]))
                if missing:
                    # A receiver may briefly retain a stale numeric reading.
                    # Never treat it as current physiology after signal loss.
                    for metric in sensor["metrics"]:
                        current_values[metric] = None
                    alerts.append(Alert(
                        key=f"{crew_id}:signal:{sensor_id}", crew_id=crew_id,
                        severity="warning", title=f"{sensor['name']}: no signal",
                        metric=sensor["metrics"][0], value=None, sensor_id=sensor_id,
                        recommendation="Check the device connection and electrode contact. Missing data cannot establish that the crew member is well or unwell.",
                        steps=[
                            "Ask the crew member whether they have any symptoms.",
                            "Inspect placement, power, contact quality, and the wireless link.",
                            "Use a verified backup measurement if monitoring is needed now.",
                            "Escalate symptoms or persistent signal loss to the crew medical officer.",
                        ],
                    ))

            def add(metric: str, sensor_id: str, severity: str, title: str,
                    recommendation: str, steps: list[str]) -> None:
                alerts.append(Alert(f"{crew_id}:{metric}:{severity}", crew_id,
                                    severity, title, metric, current_values[metric],
                                    recommendation, steps, sensor_id))

            oxygen = current_values.get("spo2")
            if _valid(oxygen) and oxygen < L["spo2_warning_low"]:
                critical = oxygen <= L["spo2_critical_low"]
                add("spo2", "oximeter", "critical" if critical else "warning",
                    "Low oxygen saturation" if critical else "Oxygen reading needs review",
                    "Notify the crew medical officer and confirm oxygen saturation with a verified measurement. Assess breathing and cabin conditions.",
                    [
                        "Pause exertion and ask about breathlessness, chest discomfort, or confusion.",
                        "Check oximeter placement and confirm the reading with a backup device.",
                        "Have the medical officer assess lung ventilation and the cabin atmosphere.",
                        "Use supplemental oxygen only under the approved onboard protocol and medical direction.",
                    ])

            exercise = sample.activity.lower() == "exercise"
            asleep = sample.activity.lower() == "sleeping"
            high_critical = L["heart_rate_critical_high_exercise" if exercise else "heart_rate_critical_high_rest"]
            high_warning = L["heart_rate_warning_high_exercise" if exercise else "heart_rate_warning_high_rest"]
            low_critical = L["heart_rate_critical_low_asleep" if asleep else "heart_rate_critical_low_awake"]
            hr = current_values.get("heart_rate")
            if _valid(hr) and (hr >= high_warning or hr < low_critical):
                severity = "critical" if hr >= high_critical or hr < low_critical else "warning"
                add("heart_rate", "ecg", severity,
                    "Heart rate outside demo limits",
                    "Review activity and ECG signal quality with the crew medical officer; a rate alone does not identify a rhythm or diagnosis.",
                    [
                        "Pause exertion and assess symptoms with the crew medical officer.",
                        "Verify ECG contact and confirm the pulse using a second measurement.",
                        "Review the trace, recent activity, hydration, and prescribed medications.",
                        "The medical officer may request an ECG assessment or blood tests if indicated.",
                    ])

            rr = current_values.get("resp_rate")
            rr_critical = L["resp_rate_critical_high_exercise" if exercise else "resp_rate_critical_high_rest"]
            rr_warning = L["resp_rate_warning_high_exercise" if exercise else "resp_rate_warning_high_rest"]
            if _valid(rr) and (rr >= rr_warning or rr < L["resp_rate_critical_low"]):
                severity = "critical" if rr >= rr_critical or rr < L["resp_rate_critical_low"] else "warning"
                add("resp_rate", "respiration", severity,
                    "Breathing pattern needs assessment",
                    "Ask the crew medical officer to assess breathing, confirm the belt signal, and review ventilation and oxygen readings.",
                    [
                        "Check the astronaut's breathing directly and ask about symptoms.",
                        "Check belt position and compare with another measurement.",
                        "Review oxygen saturation and the environmental control system.",
                        "Follow the onboard medical procedure selected by the crew medical officer.",
                    ])

            temp = current_values.get("skin_temp")
            if _valid(temp) and temp >= L["skin_temp_warning_high"]:
                add("skin_temp", "temperature", "warning",
                    "Skin temperature trend elevated",
                    "Confirm with an approved body-temperature measurement. Skin temperature alone cannot establish fever or infection.",
                    [
                        "Check patch contact, recent exercise, and ambient temperature.",
                        "Measure body temperature with an approved clinical thermometer.",
                        "Discuss symptoms and the trend with the crew medical officer.",
                        "A blood panel may be requested by the medical officer if clinically indicated.",
                    ])

            for metric, high_warning, high_critical, low_critical in [
                ("systolic", L["systolic_warning_high"], L["systolic_critical_high"], L["systolic_critical_low"]),
                ("diastolic", L["diastolic_warning_high"], L["diastolic_critical_high"], 0.0),
            ]:
                value = current_values.get(metric)
                if _valid(value) and (value >= high_warning or value < low_critical):
                    severity = "critical" if value >= high_critical or value < low_critical else "warning"
                    add(metric, "bp", severity, "Blood pressure needs review",
                        "Repeat the measurement with correct technique and ask the crew medical officer to interpret the result with symptoms and recent activity.",
                        [
                            "Check cuff placement and measurement quality.",
                            "Repeat after the rest period specified by the onboard procedure.",
                            "Report symptoms and repeat values to the crew medical officer.",
                        ])
        return sorted(alerts, key=lambda alert: 0 if alert.severity == "critical" else 1)


def crew_status(crew_id: str, alerts: list[Alert]) -> str:
    severities = {alert.severity for alert in alerts if alert.crew_id == crew_id}
    if "critical" in severities:
        return "critical"
    if "warning" in severities:
        return "warning"
    return "nominal"


def sensor_status(crew_id: str, sensor_id: str, frame: dict[str, Sample],
                  alerts: list[Alert]) -> str:
    severities = {alert.severity for alert in alerts
                  if alert.crew_id == crew_id and alert.sensor_id == sensor_id}
    if "critical" in severities:
        return "critical"
    sample = frame.get(crew_id)
    if sample is None or sample.sensor_status.get(sensor_id) != "online" or "warning" in severities:
        return "warning"
    return "nominal"
