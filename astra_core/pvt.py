"""Mission-aware measured PVT service; demo data is never stored with measured records."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json, os, secrets, threading
from pathlib import Path
from typing import Any
from hal2030.config import CREW_BY_ID

PROTOCOL_VERSION = "pvt-b-180s-v1"
DURATION_SECONDS = 180
LAPSE_THRESHOLD_MS = 500  # Illustrative, not a clinical limit.
UTC = timezone.utc
_LOCK = threading.RLock()
_PATH = Path(os.environ.get("ASTRA_PVT_STORE", Path(__file__).resolve().parents[1] / "runtime" / "pvt_records.json"))


class PVTError(ValueError):
    """Invalid PVT record or state transition."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_utc(value: str | datetime) -> datetime:
    """Parse ISO-8601 time with an explicit UTC offset."""
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PVTError("timestamp must be ISO 8601 with a UTC offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PVTError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _empty() -> dict[str, Any]:
    return {"version": 1, "sleep_logs": [], "events": [], "sessions": []}


def _load() -> dict[str, Any]:
    try:
        value = json.loads(_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty()
    except (OSError, json.JSONDecodeError) as exc:
        raise PVTError("PVT store cannot be read; history was not changed") from exc
    if not isinstance(value, dict) or value.get("version") != 1 or any(not isinstance(value.get(k), list) for k in ("sleep_logs", "events", "sessions")):
        raise PVTError("PVT store schema is invalid; history was not changed")
    return value


def _save(value: dict[str, Any]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = _PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(_PATH)


def _crew(crew_id: str) -> None:
    if crew_id not in CREW_BY_ID:
        raise PVTError("unknown crew_id")


def add_sleep_log(crew_id: str, intervals: list[dict[str, str]], complete: bool, now: datetime | None = None) -> dict:
    """Save a current snapshot asserting the prior 24h was completely logged."""
    _crew(crew_id)
    now = (now or utc_now()).astimezone(UTC)
    if not isinstance(complete, bool) or not isinstance(intervals, list) or len(intervals) > 100:
        raise PVTError("sleep log must include completeness and at most 100 intervals")
    normalized = []
    for span in intervals:
        start, end = parse_utc(span["start_utc"]), parse_utc(span["end_utc"])
        if start >= end or end > now + timedelta(minutes=1) or end - start > timedelta(hours=24):
            raise PVTError("sleep interval must be positive, at most 24h, and not in the future")
        normalized.append({"start_utc": _iso(start), "end_utc": _iso(end)})
    row = {"id": secrets.token_urlsafe(16), "crew_id": crew_id, "recorded_at_utc": _iso(now),
           "coverage_start_utc": _iso(now-timedelta(hours=24)), "coverage_end_utc": _iso(now),
           "complete": complete, "intervals": normalized, "provenance": "measured"}
    with _LOCK:
        data = _load()
        data["sleep_logs"].append(row)
        _save(data)
    return row


def add_event(crew_id: str, title: str, event_utc: str, critical: bool = True, now: datetime | None = None) -> dict:
    """Save an assigned event at an absolute UTC time."""
    _crew(crew_id)
    now = (now or utc_now()).astimezone(UTC)
    at = parse_utc(event_utc)
    if not isinstance(title, str) or not title.strip() or len(title) > 160 or not isinstance(critical, bool):
        raise PVTError("event title or critical flag is invalid")
    if at < now-timedelta(days=30) or at > now+timedelta(days=365):
        raise PVTError("event is outside the accepted scheduling horizon")
    row = {"id": secrets.token_urlsafe(16), "crew_id": crew_id, "title": title.strip(),
           "event_utc": _iso(at), "critical": critical, "assigned": True,
           "created_at_utc": _iso(now), "provenance": "measured"}
    with _LOCK:
        data = _load()
        data["events"].append(row)
        _save(data)
    return row


def reschedule_event(event_id: str, event_utc: str, now: datetime | None = None) -> dict:
    """Update an event's UTC time; recommendations are recomputed on the next status read."""
    now = (now or utc_now()).astimezone(UTC)
    at = parse_utc(event_utc)
    if at < now-timedelta(days=30) or at > now+timedelta(days=365):
        raise PVTError("event is outside the accepted scheduling horizon")
    with _LOCK:
        data = _load()
        row = next((e for e in data["events"] if e["id"] == event_id), None)
        if not row:
            raise PVTError("unknown event")
        row["event_utc"] = _iso(at)
        _save(data)
        return row


def _in_window(event: dict, now: datetime) -> bool:
    at = parse_utc(event["event_utc"])
    return at-timedelta(hours=2) <= now < at


def _sleep(logs: list[dict], now: datetime) -> tuple[float | None, bool, str | None]:
    cutoff = now-timedelta(hours=24)
    recent = [r for r in logs if parse_utc(r["recorded_at_utc"]) >= now-timedelta(hours=2)]
    if not recent:
        return None, False, None
    row = recent[-1]
    age = now-parse_utc(row["recorded_at_utc"])
    if not row["complete"] or age < timedelta(0) or age > timedelta(hours=2) or parse_utc(row["coverage_start_utc"]) > cutoff:
        return None, False, None
    spans = []
    for interval in row["intervals"]:
        start, end = max(parse_utc(interval["start_utc"]), cutoff), min(parse_utc(interval["end_utc"]), now)
        if start < end:
            spans.append((start, end))
    spans.sort()
    seconds = 0.0
    if spans:
        start, end = spans[0]
        for a, b in spans[1:]:
            if a <= end:
                end = max(end, b)
            else:
                seconds += (end-start).total_seconds()
                start, end = a, b
        seconds += (end-start).total_seconds()
    return seconds/60, True, row["recorded_at_utc"]


def _baseline(prior: list[dict]) -> dict:
    prior = [r for r in prior if isinstance(r.get("median_rt_ms"), (int, float))]
    if len(prior) < 3:
        return {"status": "establishing" if prior else "unavailable", "sample_count": len(prior), "median_rt_ms": None, "median_lapses": None}
    rts = sorted(r["median_rt_ms"] for r in prior)
    lapses = sorted(r["lapses"] for r in prior)
    mid = len(prior)//2
    median = lambda values: values[mid] if len(values)%2 else (values[mid-1]+values[mid])/2
    return {"status": "available", "sample_count": len(prior), "median_rt_ms": round(median(rts), 1), "median_lapses": round(median(lapses), 1)}


def get_status(crew_id: str, now: datetime | None = None, scenario: str | None = None) -> dict:
    """Recompute eligibility and measured same-protocol personal baseline."""
    _crew(crew_id)
    now = (now or utc_now()).astimezone(UTC)
    if scenario:
        if scenario not in {"short-sleep", "already-tested", "missing-log"}:
            raise PVTError("unknown synthetic scenario")
        return _demo_status(crew_id, now, scenario)
    with _LOCK:
        data = _load()
    events = [e for e in data["events"] if e["crew_id"] == crew_id and e["assigned"] and e["critical"] and parse_utc(e["event_utc"]) > now]
    event = min(events, key=lambda e: e["event_utc"]) if events else None
    event_window = bool(event and _in_window(event, now))
    minutes, known, sleep_logged_at = _sleep([r for r in data["sleep_logs"] if r["crew_id"] == crew_id], now)
    tested = bool(event_window and any(
        s["crew_id"] == crew_id and s.get("valid") and s.get("protocol_version") == PROTOCOL_VERSION and
        s.get("provenance") == "measured" and parse_utc(event["event_utc"])-timedelta(hours=2) <= parse_utc(s["completed_at_utc"]) < parse_utc(event["event_utc"])
        for s in data["sessions"]))
    recommend = bool(event_window and known and minutes is not None and minutes < 360 and not tested)
    reason = ("No upcoming assigned critical event is recorded." if not event else
              "The assigned event is outside its two-hour pre-task window." if not event_window else
              "Sleep unknown: no fresh complete sleep log covers the preceding 24 hours." if not known else
              "A valid same-protocol PVT is already recorded in this event window." if tested else
              "Sleep is at least 6 hours; no pre-task PVT is indicated." if minutes >= 360 else
              "Sleep is under 6 hours and no valid PVT is recorded in this event window.")
    records = sorted((s for s in data["sessions"] if s["crew_id"] == crew_id and s.get("valid") and s.get("provenance") == "measured" and s.get("protocol_version") == PROTOCOL_VERSION), key=lambda s: s["completed_at_utc"])
    baseline = _baseline(records[:-1] if records else [])
    return {"crew_id": crew_id, "now_utc": _iso(now), "protocol_version": PROTOCOL_VERSION,
            "duration_seconds": DURATION_SECONDS, "event": event,
            "sleep": {"status": "known" if known else "unknown", "total_minutes": None if minutes is None else int(minutes), "logged_at_utc": sleep_logged_at},
            "recommend": recommend, "reason": reason, "personal_baseline": baseline, "records": records}


def start_session(crew_id: str, now: datetime | None = None) -> dict:
    """Create a server-timed randomized 2–5 second stimulus schedule."""
    now = (now or utc_now()).astimezone(UTC)
    status = get_status(crew_id, now)
    if not status["recommend"]:
        raise PVTError("PVT is not currently indicated")
    intervals, elapsed = [], 0
    while True:
        interval = 2000+secrets.randbelow(3001)
        if elapsed+interval > (DURATION_SECONDS-2)*1000:
            break
        intervals.append(interval)
        elapsed += interval
    row = {"id": secrets.token_urlsafe(24), "crew_id": crew_id, "event_id": status["event"]["id"],
           "started_at_utc": _iso(now), "stimulus_intervals_ms": intervals,
           "protocol_version": PROTOCOL_VERSION, "duration_seconds": DURATION_SECONDS,
           "valid": False, "aborted": False, "provenance": "measured"}
    with _LOCK:
        data = _load()
        data["sessions"].append(row)
        _save(data)
    return {"session_id": row["id"], "protocol_version": PROTOCOL_VERSION, "duration_seconds": DURATION_SECONDS,
            "stimulus_intervals_ms": intervals, "started_at_utc": row["started_at_utc"]}


def abort_session(session_id: str) -> dict:
    """Invalidate an interrupted/false-started run."""
    with _LOCK:
        data = _load()
        row = next((s for s in data["sessions"] if secrets.compare_digest(s["id"], session_id)), None)
        if not row:
            raise PVTError("unknown PVT session")
        if not row.get("valid"):
            row["aborted"] = True
            _save(data)
        return {"session_id": session_id, "aborted": bool(row.get("aborted"))}


def complete_session(session_id: str, reaction_times_ms: list[int | None], now: datetime | None = None) -> dict:
    """Validate session timing and raw responses; derive all metrics on the server."""
    now = (now or utc_now()).astimezone(UTC)
    if not isinstance(reaction_times_ms, list) or len(reaction_times_ms) > 100:
        raise PVTError("reaction_times_ms must be a bounded list")
    with _LOCK:
        data = _load()
        row = next((s for s in data["sessions"] if secrets.compare_digest(s["id"], session_id)), None)
        if not row:
            raise PVTError("unknown PVT session")
        if row.get("aborted"):
            raise PVTError("aborted PVT session cannot complete")
        if row.get("valid"):
            return {k: row[k] for k in ("id", "valid", "median_rt_ms", "lapses", "trial_count", "completed_at_utc", "protocol_version")}
        started = parse_utc(row["started_at_utc"])
        elapsed = (now-started).total_seconds()
        if elapsed < DURATION_SECONDS:
            raise PVTError("PVT session cannot complete before 180 seconds")
        if elapsed > DURATION_SECONDS+30:
            row["aborted"] = True
            row["abort_reason"] = "completion timeout"
            _save(data)
            raise PVTError("PVT session expired; it must finish within 30 seconds of 180 seconds")
        schedule = row["stimulus_intervals_ms"]
        if not schedule or len(reaction_times_ms) != len(schedule):
            raise PVTError("response count does not match this session's complete stimulus schedule")
        if sum(schedule) > (DURATION_SECONDS-2)*1000:
            raise PVTError("session schedule leaves less than two seconds for the final response")
        clean = []
        for rt in reaction_times_ms:
            if rt is None:
                clean.append(None)
            elif isinstance(rt, bool) or not isinstance(rt, int) or not 100 <= rt <= 2000:
                raise PVTError("reaction times must be null or integer milliseconds in [100, 2000]")
            else:
                clean.append(rt)
        measured = sorted(rt for rt in clean if rt is not None)
        event = next((e for e in data["events"] if e["id"] == row["event_id"] and e["crew_id"] == row["crew_id"]), None)
        if not event or not _in_window(event, now):
            raise PVTError("assigned event is no longer in its pre-task window")
        n = len(measured)
        median = (measured[n//2] if n%2 else (measured[n//2-1]+measured[n//2])/2) if n else None
        row.update({"valid": True, "completed_at_utc": _iso(now), "elapsed_seconds": round(elapsed, 3),
                    "reaction_times_ms": clean, "median_rt_ms": None if median is None else round(median, 1),
                    "lapses": sum(rt is None or rt >= LAPSE_THRESHOLD_MS for rt in clean),
                    "trial_count": len(clean), "measured_trial_count": n})
        _save(data)
        return {k: row[k] for k in ("id", "valid", "median_rt_ms", "lapses", "trial_count", "completed_at_utc", "protocol_version")}


def _demo_status(crew_id: str, now: datetime, scenario: str) -> dict:
    event = {"id": f"synthetic-{scenario}", "crew_id": crew_id, "title": "Illustrative EVA prep",
             "event_utc": _iso(now+timedelta(minutes=45)), "critical": True, "assigned": True, "provenance": "synthetic"}
    known, tested = scenario != "missing-log", scenario == "already-tested"
    records = [{"provenance": "synthetic", "protocol_version": PROTOCOL_VERSION, "valid": True, "median_rt_ms": 288,
                "lapses": 1, "completed_at_utc": _iso(now-timedelta(minutes=30))}] if tested else []
    reason = ("Sleep unknown: synthetic scenario has no sleep log." if not known else
              "A valid same-protocol PVT is already recorded for this event." if tested else
              "Synthetic demonstration: sleep is under 6 hours and no PVT is recorded.")
    return {"crew_id": crew_id, "now_utc": _iso(now), "protocol_version": PROTOCOL_VERSION, "duration_seconds": DURATION_SECONDS,
            "event": event, "sleep": {"status": "known" if known else "unknown", "total_minutes": 330 if known else None},
            "recommend": scenario == "short-sleep", "reason": reason,
            "personal_baseline": {"status": "unavailable", "median_rt_ms": None, "median_lapses": None, "sample_count": 0},
            "records": records}

