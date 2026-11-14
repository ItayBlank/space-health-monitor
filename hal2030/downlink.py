"""Persistent store-and-forward downlink simulator.

No socket, HTTP client, NASA endpoint, microphone, or chat archive is used here.
"Delivered" is a local simulated acknowledgement. Timing uses elapsed wall time
provided by the GUI; replay seeking and speed never accelerate the link.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
from uuid import uuid4

from .paths import runtime_root
from .models import Alert, Sample


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, content: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(content, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    temp.replace(path)


def _snapshot(frame: dict[str, Sample], alerts: list[Alert], mission_time: float) -> dict:
    return {
        "schema": "hal2030.health_snapshot.v1",
        "simulation": True,
        "notice": "Fictional demonstration telemetry. No NASA transmission or medical diagnosis.",
        "recorded_at_utc": _utcnow(),
        "mission_time_s": round(float(mission_time), 3),
        "crew": [sample.to_dict() for sample in frame.values()],
        "alerts": [alert.to_dict() for alert in alerts],
    }


class DownlinkService:
    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir) if output_dir is not None else runtime_root() / "downlink"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.connected = True
        self.auto_send = False
        self.latency_s = 3
        self.queue: list[dict] = []
        self.recovery_warning = ""
        self._path = self.output_dir / "queue.json"
        self._last_persist_elapsed = 0.0
        if self._path.exists():
            try:
                loaded = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(loaded, list):
                    raise ValueError("Queue must be a list")
                seen = set()
                for packet in loaded:
                    required = {"id", "created_at", "mission_time", "status", "filename", "eta_s", "crew_count"}
                    if not isinstance(packet, dict) or not required <= packet.keys():
                        raise ValueError("Invalid queue entry")
                    if packet["id"] in seen or packet["status"] not in {"queued", "in_transit", "delivered"}:
                        raise ValueError("Duplicate packet or invalid status")
                    if Path(packet["filename"]).name != packet["filename"]:
                        raise ValueError("Packet filename must be local")
                    if not math.isfinite(float(packet["eta_s"])) or packet["eta_s"] < 0:
                        raise ValueError("Invalid time remaining")
                    if not (self.output_dir / packet["filename"]).exists():
                        raise ValueError(f"Missing packet payload: {packet['filename']}")
                    seen.add(packet["id"])
                self.queue = loaded
            except (OSError, ValueError, TypeError, KeyError) as error:
                # Preserve a corrupt queue for inspection; never silently erase it.
                backup = self._path.with_name(f"queue_recovery_{uuid4().hex[:8]}.json")
                self._path.replace(backup)
                self.recovery_warning = f"Could not restore the saved queue: {error}. Original preserved as {backup.name}."

    @property
    def status_text(self) -> str:
        pending = sum(packet["status"] != "delivered" for packet in self.queue)
        if not self.connected:
            return f"SIMULATED LINK OFFLINE · {pending} queued"
        in_transit = sum(packet["status"] == "in_transit" for packet in self.queue)
        if in_transit:
            return f"SIMULATED DOWNLINK · {in_transit} in transit"
        if pending:
            return f"SIMULATED LINK READY · {pending} queued"
        return "SIMULATED LINK READY"

    def _save(self) -> None:
        _write_json(self._path, self.queue)

    def enqueue(self, frame: dict[str, Sample], alerts: list[Alert],
                mission_time: float) -> dict:
        if not frame:
            raise ValueError("Cannot queue an empty health snapshot.")
        identifier = f"HAL-{uuid4().hex[:12].upper()}"
        filename = f"{identifier}.json"
        content = _snapshot(frame, alerts, mission_time)
        content["packet_id"] = identifier
        content["destination"] = "NASA Mission Control simulator (local only)"
        _write_json(self.output_dir / filename, content)
        packet = {
            "id": identifier,
            "created_at": _utcnow(),
            "mission_time": float(mission_time),
            "status": "in_transit" if self.connected else "queued",
            "filename": filename,
            "eta_s": max(0.0, float(self.latency_s)),
            "crew_count": len(frame),
            "simulated": True,
        }
        self.queue.append(packet)
        self._save()
        return packet

    def tick(self, elapsed_seconds: float) -> None:
        """Advance simulated link by a nonnegative wall-clock delta."""
        delta = float(elapsed_seconds)
        if not math.isfinite(delta) or delta < 0:
            raise ValueError("Elapsed seconds must be finite and nonnegative.")
        state_changed = False
        has_pending = False
        for packet in self.queue:
            if packet["status"] == "delivered":
                continue
            has_pending = True
            if not self.connected:
                if packet["status"] != "queued":
                    packet["status"] = "queued"
                    state_changed = True
                continue
            if packet["status"] == "queued":
                packet["status"] = "in_transit"
                state_changed = True
            packet["eta_s"] = max(0.0, float(packet["eta_s"]) - delta)
            if packet["eta_s"] <= 0:
                packet["status"] = "delivered"
                packet["delivered_at"] = _utcnow()
                state_changed = True
        self._last_persist_elapsed += delta
        # Persist at most once per second during transit, and immediately on
        # state changes; a restart conservatively replays <=1 extra second.
        if state_changed or (has_pending and self._last_persist_elapsed >= 1.0):
            self._save()
            self._last_persist_elapsed = 0.0

    def set_connected(self, connected: bool) -> None:
        self.connected = bool(connected)
        self.tick(0.0)

    def export_snapshot(self, frame: dict[str, Sample], alerts: list[Alert],
                        path: str | Path) -> None:
        mission_time = max((sample.t for sample in frame.values()), default=0)
        _write_json(Path(path), _snapshot(frame, alerts, mission_time))

    def flush(self) -> None:
        """Persist exact remaining times when the application closes."""
        self._save()
