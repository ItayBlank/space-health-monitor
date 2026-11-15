"""Private, owner-authenticated local check-in store and API.

The local demo protects each crew account from other web clients. It is not an
encrypted store: the machine owner, server operator, and anyone with filesystem
access can read the SQLite database. Do not expose this demo to a network.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from hal2030.paths import runtime_root

router = APIRouter(prefix="/api/private", tags=["private check-ins"])
COOKIE_NAME = "astra_private_session"
SESSION_SECONDS = 8 * 60 * 60
BASELINE_SIZE = 5
PBKDF2_ROUNDS = 310_000


def store_path() -> Path:
    """Return the private runtime database path (override for local tests)."""
    import tempfile

    configured = os.environ.get("ASTRA_PRIVATE_DATA_DIR")
    if configured:
        candidates = [Path(configured)]
    elif os.environ.get("VERCEL") == "1":
        candidates = [runtime_root() / "private"]
    else:
        candidates = [
            Path.home() / ".astra-core" / "private",
            Path(tempfile.gettempdir()) / ".astra-core" / "private",
        ]
    for base in candidates:
        try:
            base.mkdir(parents=True, exist_ok=True)
            probe = base / ".write_test"
            probe.touch()
            probe.unlink(missing_ok=True)
            try:
                base.chmod(0o700)
            except OSError:
                pass
            return base / "checkins.sqlite3"
        except OSError:
            continue
    return Path(tempfile.gettempdir()) / "checkins.sqlite3"


@contextmanager
def _db():
    conn = sqlite3.connect(store_path(), timeout=10, isolation_level="IMMEDIATE")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS credentials (
            crew_id TEXT PRIMARY KEY, salt BLOB NOT NULL, password_hash BLOB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash BLOB PRIMARY KEY, crew_id TEXT NOT NULL REFERENCES credentials(crew_id),
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY, crew_id TEXT NOT NULL, created_at TEXT NOT NULL,
            mood INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5),
            stress INTEGER NOT NULL CHECK(stress BETWEEN 1 AND 5),
            note TEXT NOT NULL DEFAULT '', synthetic INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS entries_owner_time ON entries(crew_id, created_at);
        CREATE TABLE IF NOT EXISTS dismissals (
            crew_id TEXT NOT NULL, triplet_key TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY(crew_id, triplet_key)
        );
        CREATE TABLE IF NOT EXISTS consult_requests (
            id TEXT PRIMARY KEY, crew_id TEXT NOT NULL, created_at TEXT NOT NULL,
            recipient TEXT NOT NULL, consent INTEGER NOT NULL CHECK(consent=1),
            selected_entries TEXT NOT NULL, status TEXT NOT NULL
        );
        """
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def provision_crew(crew_id: str, password: str) -> None:
    """Provision one local account; credential creation is CLI-only."""
    crew_id = crew_id.strip()
    if not crew_id or len(crew_id) > 64 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in crew_id):
        raise ValueError("crew ID must contain 1–64 letters, digits, underscore, or hyphen")
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    with _db() as db:
        db.execute("INSERT INTO credentials(crew_id,salt,password_hash) VALUES(?,?,?)", (crew_id, salt, digest))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _csrf(request: Request) -> None:
    origin = request.headers.get("origin")
    host = request.headers.get("host", "")
    if not origin or urlsplit(origin).netloc.lower() != host.lower() or urlsplit(origin).scheme not in {"http", "https"}:
        raise HTTPException(403, "Same-origin request required")
    if request.headers.get("sec-fetch-site", "same-origin") not in {"same-origin", "none"}:
        raise HTTPException(403, "Same-origin request required")


def _owner(token: str | None) -> str:
    if not token:
        raise HTTPException(401, "Sign in to your private check-ins")
    digest = hashlib.sha256(token.encode("ascii", "ignore")).digest()
    now = int(time.time())
    with _db() as db:
        row = db.execute("SELECT crew_id,expires_at FROM sessions WHERE token_hash=?", (digest,)).fetchone()
        if row is None or row["expires_at"] <= now:
            if row:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (digest,))
            raise HTTPException(401, "Sign in to your private check-ins")
        return str(row["crew_id"])


class LoginRequest(BaseModel):
    crew_id: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class CheckinRequest(BaseModel):
    mood: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    note: str = Field(default="", max_length=280)


class DismissRequest(BaseModel):
    triplet_key: str = Field(min_length=1, max_length=300)


class ConsultRequest(BaseModel):
    entry_ids: list[str] = Field(min_length=1, max_length=20)
    recipient: str = Field(min_length=1, max_length=120)
    consent: bool


def _entry(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "created_at": row["created_at"], "mood": row["mood"], "stress": row["stress"], "note": row["note"], "synthetic": bool(row["synthetic"])}


def _trend(entries: list[dict], dismissed: set[str], *, include_synthetic: bool = False) -> dict:
    measured = [e for e in entries if include_synthetic or not e["synthetic"]]
    baseline = measured[:BASELINE_SIZE]
    result = {"baseline_ready": len(baseline) >= BASELINE_SIZE, "baseline_count": len(baseline), "baseline_required": BASELINE_SIZE,
              "usual_mood": None, "usual_stress": None, "prompt": False, "triplet_key": None,
              "worse_ids": [], "threshold": "Illustrative rule: 3 consecutive measured check-ins outside the personal usual range."}
    if len(baseline) < BASELINE_SIZE:
        return result
    mood_avg = sum(e["mood"] for e in baseline) / BASELINE_SIZE
    stress_avg = sum(e["stress"] for e in baseline) / BASELINE_SIZE
    mood_low, mood_high = max(1, mood_avg - 1), min(5, mood_avg + 1)
    stress_low, stress_high = max(1, stress_avg - 1), min(5, stress_avg + 1)
    result["usual_mood"] = [round(mood_low, 1), round(mood_high, 1)]
    result["usual_stress"] = [round(stress_low, 1), round(stress_high, 1)]
    later = measured[BASELINE_SIZE:]
    if len(later) < 3:
        return result
    triplet = later[-3:]
    key = ":".join(e["id"] for e in triplet)
    low_mood = all(e["mood"] < mood_low for e in triplet)
    high_stress = all(e["stress"] > stress_high for e in triplet)
    result.update({"triplet_key": key,
                   "worse_ids": [e["id"] for e in triplet] if low_mood or high_stress else [],
                   "mood_streak": low_mood, "stress_streak": high_stress,
                   "prompt": (low_mood or high_stress) and key not in dismissed})
    return result


@router.get("/session")
def session_status(token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    try:
        _owner(token)
        return {"authenticated": True}
    except HTTPException:
        return {"authenticated": False}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response) -> dict:
    _csrf(request)
    with _db() as db:
        row = db.execute("SELECT salt,password_hash FROM credentials WHERE crew_id=?", (payload.crew_id,)).fetchone()
    # Run the same KDF for unknown users to reduce account enumeration by timing.
    salt = row["salt"] if row else b"astra-local-demo-salt"
    candidate = hashlib.pbkdf2_hmac("sha256", payload.password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    if row is None or not hmac.compare_digest(candidate, row["password_hash"]):
        raise HTTPException(401, "Crew ID or password is incorrect")
    token = secrets.token_urlsafe(32)
    expires = int(time.time()) + SESSION_SECONDS
    with _db() as db:
        db.execute("INSERT INTO sessions(token_hash,crew_id,expires_at) VALUES(?,?,?)", (hashlib.sha256(token.encode()).digest(), payload.crew_id, expires))
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True, secure=request.url.scheme == "https",
                        samesite="strict", path="/api/private")
    return {"authenticated": True, "expires_in": SESSION_SECONDS}


@router.post("/logout")
def logout(request: Request, response: Response, token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    _csrf(request)
    if token:
        with _db() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).digest(),))
    response.delete_cookie(COOKIE_NAME, path="/api/private", httponly=True, samesite="strict")
    return {"authenticated": False}


@router.get("/checkins")
def list_checkins(token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    owner = _owner(token)
    with _db() as db:
        rows = db.execute("SELECT * FROM entries WHERE crew_id=? AND synthetic=0 ORDER BY rowid", (owner,)).fetchall()
        demos = db.execute("SELECT * FROM entries WHERE crew_id=? AND synthetic=1 ORDER BY rowid", (owner,)).fetchall()
        dismissed = {r[0] for r in db.execute("SELECT triplet_key FROM dismissals WHERE crew_id=?", (owner,))}
    history = [_entry(r) for r in rows]
    demo_history = [_entry(r) for r in demos]
    cases = []
    if demo_history:
        for label, case_entries in (("isolated", demo_history[:8]), ("sustained", demo_history[8:16])):
            demo_trend = _trend(case_entries, set(), include_synthetic=True)
            cases.append({"case": label, "entries": case_entries, "trend": demo_trend})
    return {"entries": history, "demo_entries": demo_history, "demo_cases": cases, "trend": _trend(history, dismissed)}


@router.post("/checkins")
def create_checkin(payload: CheckinRequest, request: Request, token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    item_id = secrets.token_urlsafe(12)
    with _db() as db:
        db.execute("INSERT INTO entries(id,crew_id,created_at,mood,stress,note) VALUES(?,?,?,?,?,?)",
                   (item_id, owner, _utc_now(), payload.mood, payload.stress, payload.note.strip()))
    return {"created": True, "id": item_id}


@router.post("/dismiss")
def dismiss_prompt(payload: DismissRequest, request: Request, token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    with _db() as db:
        # Only the current server-computed candidate may be dismissed.
        rows = db.execute("SELECT * FROM entries WHERE crew_id=? AND synthetic=0 ORDER BY rowid", (owner,)).fetchall()
        dismissed = {r[0] for r in db.execute("SELECT triplet_key FROM dismissals WHERE crew_id=?", (owner,))}
        trend = _trend([_entry(r) for r in rows], dismissed)
        if not trend["prompt"] or trend["triplet_key"] != payload.triplet_key:
            raise HTTPException(409, "That follow-up is no longer available")
        db.execute("INSERT OR IGNORE INTO dismissals VALUES(?,?,?)", (owner, payload.triplet_key, _utc_now()))
    return {"dismissed": True}


@router.post("/consult-requests")
def request_consult(payload: ConsultRequest, request: Request, token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    if payload.consent is not True:
        raise HTTPException(400, "Explicit consent is required")
    if payload.recipient != "Flight surgeon (local demo)":
        raise HTTPException(400, "Unknown local demo recipient")
    with _db() as db:
        wanted = set(payload.entry_ids)
        placeholders = ",".join("?" for _ in wanted)
        rows = db.execute(f"SELECT * FROM entries WHERE crew_id=? AND synthetic=0 AND id IN ({placeholders})", (owner, *wanted)).fetchall()
        if len(rows) != len(wanted):
            raise HTTPException(404, "One or more selected entries are unavailable")
        # Only the explicit selection is snapshotted. No message or delivery is sent.
        ids = [r["id"] for r in rows]
        request_id = secrets.token_urlsafe(12)
        db.execute("INSERT INTO consult_requests VALUES(?,?,?,?,?,?,?)",
                   (request_id, owner, _utc_now(), payload.recipient, 1, ",".join(ids), "locally_recorded_not_delivered"))
    return {"request_id": request_id, "status": "locally_recorded_not_delivered", "selected_count": len(ids), "recipient": payload.recipient}


@router.post("/demo")
def seed_synthetic_demo(request: Request, token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None) -> dict:
    """Add isolated synthetic examples to a separate demo-only timeline."""
    _csrf(request)
    owner = _owner(token)
    with _db() as db:
        existing = db.execute("SELECT COUNT(*) FROM entries WHERE crew_id=? AND synthetic=1", (owner,)).fetchone()[0]
        if existing:
            db.execute("DELETE FROM entries WHERE crew_id=? AND synthetic=1", (owner,))
        now = time.time()
        samples = [("isolated", [(4, 1)] * 5 + [(2, 1), (4, 1), (4, 1)]),
                   ("sustained", [(4, 1)] * 5 + [(2, 1), (2, 1), (2, 1)])]
        offset = 0
        for case, values in samples:
            for mood, stress in values:
                created = datetime.fromtimestamp(now + offset, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                db.execute("INSERT INTO entries(id,crew_id,created_at,mood,stress,note,synthetic) VALUES(?,?,?,?,?,?,1)",
                           (secrets.token_urlsafe(10), owner, created, mood, stress, f"Synthetic demo · {case}"))
                offset += 1
    return {"seeded": True}


def main() -> int:
    """Local-only account provisioning; no HTTP enrollment/reset endpoint exists."""
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description="Provision an ASTRA local private-check-in account")
    commands = parser.add_subparsers(dest="command", required=True)
    provision = commands.add_parser("provision", help="create a new crew credential (does not reset accounts)")
    provision.add_argument("crew_id")
    args = parser.parse_args()
    first = getpass.getpass("New password (12+ characters): ")
    second = getpass.getpass("Repeat password: ")
    if first != second:
        parser.error("passwords did not match")
    try:
        provision_crew(args.crew_id, first)
    except (ValueError, sqlite3.IntegrityError) as exc:
        parser.error(str(exc))
    print(f"Provisioned local crew account {args.crew_id!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
