"""Portable, JSON-friendly telemetry objects; no GUI dependency."""
from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass
class Sample:
    t: int
    crew_id: str
    activity: str
    values: dict[str, float | None]
    sensor_status: dict[str, str]
    cabin_co2: float = 900.0
    cabin_temp: float = 22.0
    signal_quality: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Alert:
    key: str
    crew_id: str
    severity: str
    title: str
    metric: str
    value: float | None
    recommendation: str
    steps: list[str] = field(default_factory=list)
    sensor_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class TelemetrySource(Protocol):
    """Boundary for a future receiver using serial, BLE, MQTT, or another link.

    A real adapter must timestamp and validate packets, map device IDs to crew,
    expire stale readings, and supply None plus no_signal when a channel is lost.
    Acquiring real hardware data is intentionally outside this demonstration.
    """

    def frame(self, t: int) -> dict[str, Sample]: ...
