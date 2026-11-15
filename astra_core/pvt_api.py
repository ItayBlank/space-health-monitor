"""FastAPI endpoints for the measured, event-linked pre-task PVT."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from . import pvt

router = APIRouter(prefix="/api/pvt", tags=["pre-task PVT"])


class SleepInterval(BaseModel):
    start_utc: str
    end_utc: str


class SleepLogRequest(BaseModel):
    crew_id: str = Field(min_length=1, max_length=40)
    complete: bool
    intervals: list[SleepInterval] = Field(max_length=100)


class EventRequest(BaseModel):
    crew_id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=160)
    event_utc: str
    critical: bool = True


class StartRequest(BaseModel):
    crew_id: str = Field(min_length=1, max_length=40)


class CompletionRequest(BaseModel):
    reaction_times_ms: list[int | None] = Field(max_length=100)


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except pvt.PVTError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/crew")
def crew() -> dict:
    """List supported stable crew IDs."""
    from hal2030.config import CREW
    return {"crew": [{"id": row["id"], "name": row["name"]} for row in CREW]}


@router.get("/status/{crew_id}")
def status(crew_id: str, scenario: str | None = None) -> dict:
    """Re-evaluate eligibility; scenario data is synthetic and isolated."""
    return _call(pvt.get_status, crew_id, scenario=scenario)


@router.post("/sleep")
def sleep_log(request: SleepLogRequest) -> dict:
    """Save one measured sleep-log snapshot."""
    return _call(pvt.add_sleep_log, request.crew_id, [x.model_dump() for x in request.intervals], request.complete)


@router.post("/events")
def event(request: EventRequest) -> dict:
    """Assign a mission event to a crew member."""
    return _call(pvt.add_event, request.crew_id, request.title, request.event_utc, request.critical)


@router.put("/events/{event_id}")
def reschedule(event_id: str, event_utc: str) -> dict:
    """Reschedule the event; the eligibility rule is recalculated on status refresh."""
    return _call(pvt.reschedule_event, event_id, event_utc)


@router.post("/sessions/start")
def start(request: StartRequest) -> dict:
    """Start a server-timed session only when current status recommends it."""
    return _call(pvt.start_session, request.crew_id)


@router.post("/sessions/{session_id}/complete")
def complete(session_id: str, request: CompletionRequest) -> dict:
    """Validate 180 seconds and derive metrics from raw trial responses."""
    return _call(pvt.complete_session, session_id, request.reaction_times_ms)


@router.post("/sessions/{session_id}/abort")
def abort(session_id: str) -> dict:
    """Invalidate an interrupted run so it cannot suppress a recommendation."""
    return _call(pvt.abort_session, session_id)

