"""Deterministic CSV replay and explicitly illustrative synthetic waveforms.

The CSV stores one summary per person per second. Waveform drawings are separate
synthetic illustrations; no raw ECG or EEG is claimed to be recovered from these
low-rate summaries.
"""
from __future__ import annotations

import csv
import math
from copy import deepcopy
from pathlib import Path

import numpy as np

from .config import CREW, DATA_PATH, DEMO_DURATION, DEMO_SEED, METRICS, SENSORS
from .models import Sample

_BASELINES = {
    "idan": (72, 98.2, 15.0, 33.7, 118, 76, 52),
    "itay": (69, 98.0, 14.0, 33.8, 116, 74, 58),
    "anton": (73, 98.3, 15.0, 33.6, 120, 78, 49),
    "emily": (70, 98.6, 14.0, 33.8, 112, 72, 62),
    "sofia": (67, 98.4, 14.0, 33.5, 110, 71, 65),
    "camila": (76, 98.0, 16.0, 33.7, 114, 73, 56),
}


def _episode(t: int, start: int, plateau: int, recovery: int, end: int) -> float:
    """Smooth event envelope, zero outside the event."""
    if t < start or t >= end:
        return 0.0
    if t < plateau:
        return (t - start) / max(1, plateau - start)
    if t < recovery:
        return 1.0
    return (end - t) / max(1, end - recovery)


def generate_dataset(path: str | Path = DATA_PATH) -> Path:
    """Write exactly 600 × 6 fictional 1 Hz summaries with fixed seed 2030."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(DEMO_SEED)
    sensor_fields = [f"sensor_{sensor['id']}" for sensor in SENSORS]
    fields = ["t", "crew_id", "activity", *METRICS, *sensor_fields,
              "cabin_co2", "cabin_temp", "signal_quality"]
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for t in range(DEMO_DURATION):
            for i, crew in enumerate(CREW):
                crew_id = crew["id"]
                hr, oxygen, breath, skin, systolic, diastolic, hrv = _BASELINES[crew_id]
                slow = math.sin(t / 18.0 + i)
                values = {
                    "heart_rate": hr + 2.5 * slow + rng.normal(0, 0.7),
                    "spo2": oxygen + 0.18 * math.sin(t / 24 + i) + rng.normal(0, 0.06),
                    "resp_rate": breath + 0.7 * math.sin(t / 20 + i) + rng.normal(0, 0.13),
                    "skin_temp": skin + 0.12 * math.sin(t / 70 + i),
                    "systolic": systolic + 2.5 * math.sin(t / 36 + i),
                    "diastolic": diastolic + 1.6 * math.sin(t / 35 + i),
                    "hrv": hrv + 4.0 * math.sin(t / 42 + i) + rng.normal(0, 0.5),
                    "eeg_alpha": 34 + i + 3.0 * math.sin(t / 23 + i),
                    "eeg_beta": 23 - i / 2 + 2.2 * math.sin(t / 16 + i),
                    "motion": max(0.0, 0.17 + 0.05 * math.sin(t / 7 + i)),
                    "battery": 98.0 - i * 2.0 - t / 500.0,
                }
                status = {sensor["id"]: "online" for sensor in SENSORS}
                activity = "Working"
                if crew_id == "anton":
                    activity = "Resting"
                    event = _episode(t, 25, 35, 75, 95)
                    values["spo2"] -= 10.2 * event
                    values["resp_rate"] += 14.5 * event
                    values["heart_rate"] += 24.0 * event
                elif crew_id == "itay":
                    activity = "Maintenance"
                    if 110 <= t < 150:
                        status["oximeter"] = "no_signal"
                elif crew_id == "emily":
                    event = _episode(t, 165, 180, 210, 235)
                    if event > 0:
                        activity = "Exercise"
                        values["heart_rate"] += 65 * event
                        values["resp_rate"] += 14 * event
                        values["hrv"] -= 29 * event
                        values["motion"] += 0.65 * event
                        values["skin_temp"] += 0.9 * event
                elif crew_id == "idan":
                    event = _episode(t, 250, 260, 285, 310)
                    if event > 0:
                        activity = "Resting"
                        values["heart_rate"] += 70 * event
                        values["resp_rate"] += 15.0 * event
                        values["systolic"] += 38.0 * event
                        values["hrv"] -= 28.0 * event
                elif crew_id == "sofia":
                    if t < 150:
                        activity = "Sleeping"
                        values["heart_rate"] -= 13
                        values["resp_rate"] -= 2.5
                        values["motion"] = 0.01 + 0.005 * math.sin(t / 12)
                        values["eeg_alpha"] -= 18
                        values["eeg_beta"] -= 12
                    event = _episode(t, 325, 345, 380, 405)
                    values["skin_temp"] += 4.0 * event
                    values["heart_rate"] += 30 * event
                elif crew_id == "camila":
                    if t < 90:
                        activity = "Moving"
                        values["motion"] += 0.25
                        values["heart_rate"] += 8
                    if 420 <= t < 470:
                        status["eeg"] = "no_signal"
                for sensor in SENSORS:
                    if status[sensor["id"]] == "no_signal":
                        for metric in sensor["metrics"]:
                            values[metric] = None
                row = {"t": t, "crew_id": crew_id, "activity": activity}
                row.update({key: "" if value is None else round(value, 3)
                            for key, value in values.items()})
                row.update({f"sensor_{key}": value for key, value in status.items()})
                row.update({
                    "cabin_co2": round(910 + 45 * math.sin(t / 61), 1),
                    "cabin_temp": round(22.1 + 0.18 * math.sin(t / 120), 2),
                    "signal_quality": 0.82 if "no_signal" in status.values() else round(0.98 + 0.01 * math.sin(t / 16 + i), 3),
                })
                writer.writerow(row)
    return destination


class CsvReplaySource:
    """Validated, read-only frame access to the shipped ten-minute recording."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else DATA_PATH
        if not self.path.exists():
            generate_dataset(self.path)
        self._frames: dict[int, dict[str, Sample]] = {}
        expected_ids = {person["id"] for person in CREW}
        with self.path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            required = {"t", "crew_id", "activity", *METRICS,
                        *(f"sensor_{sensor['id']}" for sensor in SENSORS),
                        "cabin_co2", "cabin_temp", "signal_quality"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"Missing telemetry columns: {', '.join(sorted(missing))}")
            for row in reader:
                t, crew_id = int(row["t"]), row["crew_id"]
                if crew_id not in expected_ids or t < 0:
                    raise ValueError(f"Invalid telemetry identity or time: {crew_id}, {t}")
                values = {metric: float(row[metric]) if row[metric] else None for metric in METRICS}
                if any(value is not None and not math.isfinite(value) for value in values.values()):
                    raise ValueError(f"Non-finite telemetry value at t={t}, crew={crew_id}")
                statuses = {sensor["id"]: row[f"sensor_{sensor['id']}"] for sensor in SENSORS}
                if any(status not in {"online", "no_signal"} for status in statuses.values()):
                    raise ValueError(f"Unknown sensor state at t={t}, crew={crew_id}")
                for sensor in SENSORS:
                    if statuses[sensor["id"]] == "no_signal":
                        for metric in sensor["metrics"]:
                            values[metric] = None
                environment = [float(row[key]) for key in ("cabin_co2", "cabin_temp", "signal_quality")]
                if not all(math.isfinite(value) for value in environment):
                    raise ValueError(f"Non-finite cabin or signal-quality metadata at t={t}, crew={crew_id}")
                if not 0.0 <= environment[2] <= 1.0:
                    raise ValueError(f"Signal quality must be between 0 and 1 at t={t}, crew={crew_id}")
                sample = Sample(t, crew_id, row["activity"], values, statuses, *environment)
                people = self._frames.setdefault(t, {})
                if crew_id in people:
                    raise ValueError(f"Duplicate telemetry row: t={t}, crew={crew_id}")
                people[crew_id] = sample
        self.duration = max(self._frames, default=-1) + 1
        if self.duration == 0 or set(self._frames) != set(range(self.duration)):
            raise ValueError("Telemetry must contain a contiguous recording starting at zero.")
        for t, people in self._frames.items():
            if set(people) != expected_ids:
                raise ValueError(f"Incomplete crew frame at second {t}.")
        self._wave_phases = {}
        for crew_id in expected_ids:
            for kind, metric, fallback in [
                ("ecg", "heart_rate", _BASELINES[crew_id][0]),
                ("respiration", "resp_rate", _BASELINES[crew_id][2]),
                ("eeg", None, None),
            ]:
                if kind == "eeg":
                    rates = np.array([3.0 if self._frames[t][crew_id].activity == "Sleeping" else 10.0
                                      for t in range(self.duration)])
                else:
                    rates = np.array([(self._frames[t][crew_id].values[metric] or fallback) / 60.0
                                      for t in range(self.duration)])
                # Each phase prefix depends only on earlier samples. The same
                # mission timestamp always produces the same drawing, even
                # after seeking or changing the visible window length.
                self._wave_phases[crew_id, kind] = (rates, np.r_[0.0, np.cumsum(rates)])

    def _time(self, t: int | float) -> int:
        return max(0, min(int(t), self.duration - 1))

    def frame(self, t: int) -> dict[str, Sample]:
        return deepcopy(self._frames[self._time(t)])

    def history(self, crew_id: str, metric: str, end_t: int,
                seconds: int = 60) -> tuple[list[float], list[float]]:
        if seconds <= 0:
            return [], []
        end = self._time(end_t)
        start = max(0, end - int(seconds) + 1)
        times = list(range(start, end + 1))
        values = [self._frames[t][crew_id].values[metric] for t in times]
        return [float(t) for t in times], [float("nan") if value is None else float(value) for value in values]

    def waveform(self, crew_id: str, kind: str, end_t: float,
                 seconds: float = 8, fs: int = 100) -> tuple[np.ndarray, np.ndarray]:
        """Draw a model signal, never a measurement or a reconstructed waveform.

        Missing sensor intervals are NaN so plots visibly break; data never look
        physiologically normal while a device has lost its signal.
        """
        sensor_for_kind = {"ecg": "ecg", "respiration": "respiration", "eeg": "eeg"}
        if kind not in sensor_for_kind:
            raise ValueError(f"Unknown waveform kind: {kind}")
        if fs <= 0 or seconds <= 0:
            return np.array([], dtype=float), np.array([], dtype=float)
        end = max(0.0, min(float(end_t), float(self.duration - 1)))
        start = max(0.0, end - seconds)
        x = np.linspace(start, end, max(2, int((end - start) * fs) + 1))
        idx = np.clip(x.astype(int), 0, self.duration - 1)
        phases = {crew["id"]: i * 0.21 for i, crew in enumerate(CREW)}
        offset = phases[crew_id]
        rates, accumulated = self._wave_phases[crew_id, kind]
        cycles = accumulated[idx] + rates[idx] * (x - idx)
        if kind == "ecg":
            # P-QRS-T-like shape: educational plotting model only.
            phase = (cycles + offset) % 1.0
            y = (0.10 * np.exp(-((phase - 0.16) / 0.05) ** 2)
                 - 0.14 * np.exp(-((phase - 0.37) / 0.018) ** 2)
                 + 1.0 * np.exp(-((phase - 0.40) / 0.016) ** 2)
                 - 0.23 * np.exp(-((phase - 0.44) / 0.022) ** 2)
                 + 0.24 * np.exp(-((phase - 0.67) / 0.10) ** 2)
                 + 0.018 * np.sin(2 * np.pi * 0.33 * x))
        elif kind == "respiration":
            y = 0.8 * np.sin(2 * np.pi * cycles + offset)
            y += 0.12 * np.sin(4 * np.pi * cycles + offset)
        else:
            y = (13 * np.sin(2 * np.pi * cycles + offset)
                 + 7 * np.sin(2 * np.pi * 18 * x + offset)
                 + 3 * np.sin(2 * np.pi * 31 * x + offset * 2)
                 + 2 * np.sin(2 * np.pi * 1.3 * x))
        channel = sensor_for_kind[kind]
        available = np.array([self._frames[int(t)][crew_id].sensor_status[channel] == "online" for t in idx])
        y = np.where(available, y, np.nan)
        return x, y
