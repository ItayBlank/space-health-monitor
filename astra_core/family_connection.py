"""Private, simulated message exchange between a crew account and one recipient."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import secrets
import time
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Cookie, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from astra_core.checkins import COOKIE_NAME, _csrf, _db, _owner, _utc_now
from astra_core.hal_bridge import get_downlink
from astra_core.pvt import PVTError, get_status as pvt_status

router = APIRouter(tags=["family connection"])

PRIVATE = "/api/private/family"
FAMILY = "/api/family"
PREVIEW_LIFETIME_SECONDS = 900
PRELOADED_VIDEO = "/static/family-media/two-reconstruction.mp4"
OwnerCookie = Annotated[str | None, Cookie(alias=COOKIE_NAME)]
Authorization = Annotated[str | None, Header()]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
ReplyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class FamilyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EnableSharing(FamilyRequest):
    recipient: Label


class PreviewReport(FamilyRequest):
    fields: list[Literal["mood", "sleep"]] = Field(min_length=1, max_length=2)


class SendReport(FamilyRequest):
    preview_id: str = Field(min_length=1, max_length=64)


class AdvanceLink(FamilyRequest):
    seconds: int = Field(strict=True, ge=1, le=86_400)


class SendReply(FamilyRequest):
    text: ReplyText


@contextmanager
def _family_db(*, write: bool = False):
    with _db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS family_sharing (
                owner TEXT PRIMARY KEY REFERENCES credentials(crew_id),
                grant_id TEXT NOT NULL UNIQUE,
                recipient TEXT NOT NULL,
                code_hash BLOB NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS family_previews (
                id TEXT PRIMARY KEY,
                grant_id TEXT NOT NULL REFERENCES family_sharing(grant_id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS family_messages (
                id TEXT PRIMARY KEY,
                owner TEXT NOT NULL REFERENCES credentials(crew_id),
                grant_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('report', 'reply')),
                content TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('queued', 'sent', 'canceled')),
                created_at TEXT NOT NULL,
                remaining_s INTEGER
            );
            CREATE INDEX IF NOT EXISTS family_messages_owner_time
                ON family_messages(owner, created_at);
            CREATE INDEX IF NOT EXISTS family_messages_grant_time
                ON family_messages(grant_id, created_at);
            """
        )
        if write:
            # Serialize grant checks, preview consumption, cancellation, and delivery.
            db.execute("BEGIN IMMEDIATE")
        yield db


def _link() -> dict:
    downlink = get_downlink()
    return {"connected": bool(downlink.connected), "latency_s": int(downlink.latency_s)}


def _sharing(db, owner: str, *, required: bool = False):
    grant = db.execute("SELECT * FROM family_sharing WHERE owner=?", (owner,)).fetchone()
    if grant is None and required:
        raise HTTPException(409, "Enable family sharing before preparing a report")
    return grant


def _recipient(db, authorization: str | None):
    scheme, _, code = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or len(code) != 43 or not code.isascii():
        raise HTTPException(401, "Enter the active family pairing code")
    digest = hashlib.sha256(code.encode("ascii")).digest()
    grant = db.execute("SELECT * FROM family_sharing WHERE code_hash=?", (digest,)).fetchone()
    if grant is None:
        raise HTTPException(401, "Enter the active family pairing code")
    return grant


def _message(row) -> dict:
    message = {"id": row["id"], "status": row["status"], "created_at": row["created_at"]}
    if row["kind"] == "report":
        message["content"] = json.loads(row["content"])
    else:
        message["text"] = row["content"]
    return message


def _queue(db, grant, kind: Literal["report", "reply"], content: str) -> dict:
    message_id = uuid4().hex
    db.execute(
        "INSERT INTO family_messages (id, owner, grant_id, kind, content, status, created_at) "
        "VALUES (?,?,?,?,?,'queued',?)",
        (message_id, grant["owner"], grant["grant_id"], kind, content, _utc_now()),
    )
    return _message(db.execute("SELECT * FROM family_messages WHERE id=?", (message_id,)).fetchone())


@router.get(PRIVATE)
def owner_view(token: OwnerCookie = None) -> dict:
    owner = _owner(token)
    with _family_db() as db:
        grant = _sharing(db, owner)
        rows = db.execute(
            "SELECT * FROM family_messages WHERE owner=? AND (kind='report' OR status='sent') "
            "ORDER BY created_at DESC, rowid DESC", (owner,)
        ).fetchall()
    return {
        "enabled": grant is not None,
        "recipient": grant["recipient"] if grant else None,
        "link": _link(),
        "reports": [_message(row) for row in rows if row["kind"] == "report"],
        "inbox": [_message(row) for row in rows if row["kind"] == "reply"],
        "video_url": PRELOADED_VIDEO,
    }


@router.post(PRIVATE + "/enable")
def enable(payload: EnableSharing, request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    code = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code.encode("ascii")).digest()
    with _family_db(write=True) as db:
        if _sharing(db, owner):
            raise HTTPException(409, "Turn off the current family connection before pairing a new recipient")
        db.execute(
            "INSERT INTO family_sharing (owner, grant_id, recipient, code_hash) VALUES (?,?,?,?)",
            (owner, uuid4().hex, payload.recipient, digest),
        )
    return {"recipient": payload.recipient, "pairing_code": code}


@router.post(PRIVATE + "/revoke")
def revoke(request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    with _family_db(write=True) as db:
        db.execute("UPDATE family_messages SET status='canceled' WHERE owner=? AND status='queued'", (owner,))
        db.execute("DELETE FROM family_sharing WHERE owner=?", (owner,))
    return {"enabled": False}


@router.post(PRIVATE + "/preview")
def preview(payload: PreviewReport, request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    content = {}
    preview_id = uuid4().hex
    expires_at = int(time.time()) + PREVIEW_LIFETIME_SECONDS
    with _family_db(write=True) as db:
        grant = _sharing(db, owner, required=True)
        if "mood" in payload.fields:
            entry = db.execute(
                "SELECT mood FROM entries WHERE crew_id=? AND synthetic=0 "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1", (owner,)
            ).fetchone()
            content["mood"] = entry["mood"] if entry else None
        if "sleep" in payload.fields:
            try:
                sleep = pvt_status(owner)["sleep"]
                content["sleep_minutes"] = sleep["total_minutes"] if sleep["status"] == "known" else None
            except PVTError:
                # A provisioned check-in ID may have no matching PVT crew record.
                content["sleep_minutes"] = None
        db.execute("DELETE FROM family_previews WHERE grant_id=? AND expires_at<=?", (grant["grant_id"], int(time.time())))
        db.execute(
            "INSERT INTO family_previews (id, grant_id, content, expires_at) VALUES (?,?,?,?)",
            (preview_id, grant["grant_id"], json.dumps(content), expires_at),
        )
    return {"preview_id": preview_id, "content": content}


@router.post(PRIVATE + "/reports")
def send_report(payload: SendReport, request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    with _family_db(write=True) as db:
        grant = _sharing(db, owner, required=True)
        preview_row = db.execute(
            "SELECT content FROM family_previews WHERE id=? AND grant_id=? AND expires_at>?",
            (payload.preview_id, grant["grant_id"], int(time.time())),
        ).fetchone()
        if not preview_row:
            raise HTTPException(404, "Prepare a fresh report preview")
        db.execute("DELETE FROM family_previews WHERE id=?", (payload.preview_id,))
        return _queue(db, grant, "report", preview_row["content"])


@router.post(PRIVATE + "/reports/{message_id}/cancel")
def cancel_report(message_id: str, request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    with _family_db(write=True) as db:
        report = db.execute(
            "SELECT * FROM family_messages WHERE id=? AND owner=? AND kind='report'",
            (message_id, owner),
        ).fetchone()
        if not report:
            raise HTTPException(404, "Report not found")
        if report["status"] == "sent":
            raise HTTPException(409, "The report has already been sent")
        db.execute("UPDATE family_messages SET status='canceled' WHERE id=?", (message_id,))
        return {**_message(report), "status": "canceled"}


@router.post(PRIVATE + "/advance")
def advance(payload: AdvanceLink, request: Request, token: OwnerCookie = None) -> dict:
    _csrf(request)
    owner = _owner(token)
    with _family_db(write=True) as db:
        grant = _sharing(db, owner)
        link = _link()
        if grant is None or not link["connected"]:
            return {"delivered": 0}
        # Partial progress is saved so separate ticks can complete a transmission.
        db.execute(
            "UPDATE family_messages SET remaining_s=max(0,coalesce(remaining_s,?)-?) "
            "WHERE grant_id=? AND status='queued'",
            (link["latency_s"], payload.seconds, grant["grant_id"]),
        )
        result = db.execute(
            "UPDATE family_messages SET status='sent' WHERE grant_id=? AND status='queued' AND remaining_s=0",
            (grant["grant_id"],),
        )
        return {"delivered": result.rowcount}


@router.get(FAMILY)
def family_view(authorization: Authorization = None) -> dict:
    with _family_db() as db:
        grant = _recipient(db, authorization)
        rows = db.execute(
            "SELECT * FROM family_messages WHERE grant_id=? AND (kind='reply' OR status='sent') "
            "ORDER BY created_at DESC, rowid DESC", (grant["grant_id"],)
        ).fetchall()
    return {
        "recipient": grant["recipient"],
        "link": _link(),
        "reports": [_message(row) for row in rows if row["kind"] == "report"],
        "replies": [_message(row) for row in rows if row["kind"] == "reply"],
    }


@router.post(FAMILY + "/replies")
def reply(payload: SendReply, request: Request, authorization: Authorization = None) -> dict:
    _csrf(request)
    with _family_db(write=True) as db:
        grant = _recipient(db, authorization)
        return _queue(db, grant, "reply", payload.text)
