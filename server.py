"""
FastAPI backend for ASTRA-Core (Astronaut Health & Readiness Backbone).

Run with:
    uvicorn server:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import copy
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from astra_core.radiation import (
    DEFAULT_HOURLY_SCHEDULE,
    ISS_CABINS,
    load_rem_summary,
    simulate_astronaut_radiation,
)
from astra_core.readiness import compute_holistic_readiness
from astra_core.standards import (
    NASA_CARDIO_VITALS_STANDARDS,
    NASA_ENVIRONMENT_STANDARDS,
    NASA_RADIATION_STANDARDS,
)
from astra_core.vitals import PHYSIONET_RECORDS, analyze_vitals_stream
from astra_core.checkins import router as private_checkins_router
from astra_core.family_connection import router as family_connection_router
from hal2030.paths import resource_root

STATIC_DIR = resource_root() / "static"

_VITALS_CACHE: Dict[Tuple[str, str, float, float, Optional[float]], dict] = {}


def _get_cached_vitals(
    record_id: str,
    atmosphere_profile: str = "iss_nominal",
    window_sec: float = 60.0,
    step_sec: float = 30.0,
    cabin_ppco2_mmhg: Optional[float] = None,
) -> dict:
    """Memoize deterministic Bio-Monitor DSP runs across identical parameters."""
    co2_key = round(float(cabin_ppco2_mmhg), 2) if cabin_ppco2_mmhg is not None else None
    key = (record_id, atmosphere_profile, float(window_sec), float(step_sec), co2_key)
    if key not in _VITALS_CACHE:
        _VITALS_CACHE[key] = analyze_vitals_stream(
            record_id=record_id,
            atmosphere_profile=atmosphere_profile,
            window_sec=window_sec,
            step_sec=step_sec,
            cabin_ppco2_mmhg=cabin_ppco2_mmhg,
        )
    return copy.deepcopy(_VITALS_CACHE[key])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Pre-warm default crew PhysioNet records and background Kokoro voice engine."""
    for rec_id, co2 in [("ptt_s3_sit", 1.9), ("ptt_s3_sit", 3.1), ("bidmc_19", 2.0), ("bidmc_16", 2.4)]:
        _get_cached_vitals(rec_id, "iss_nominal", 60.0, 30.0, co2)
    _get_cached_vitals("ptt_s3_sit", "iss_nominal", 60.0, 30.0, None)
    if "PYTEST_CURRENT_TEST" not in os.environ:
        threading.Thread(target=warmup_voice_engine, daemon=True).start()
    yield


app = FastAPI(
    title="ASTRA-Core: NASA Space Apps 2026 Backbone",
    version="0.1.0",
    description="NASA-STD-3001 aligned astronaut health & cabin radiation backbone.",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(private_checkins_router)
app.include_router(family_connection_router)


@app.middleware("http")
async def private_response_headers(request, call_next):
    """Prevent browser, proxy, or shared-cache storage of private API responses."""
    response = await call_next(request)
    path = request.url.path
    family_recipient = path == "/api/family" or path.startswith("/api/family/")
    if path.startswith("/api/private/") or family_recipient:
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Vary"] = "Authorization" if family_recipient else "Cookie"
    return response


class RadiationSimRequest(BaseModel):
    """Input payload for cabin-by-cabin radiation simulation."""

    hourly_schedule: Optional[List[str]] = Field(
        default=None,
        description="Optional 24-element list of ISS cabin_ids for hours 00..23 UTC.",
    )
    cabin_hours: Optional[Dict[str, float]] = Field(
        default=None,
        description="Hours spent per cabin in a 24h cycle (used if hourly_schedule omitted).",
    )
    mission_days: int = Field(default=30, ge=1, le=365)
    prior_career_msv: float = Field(default=120.0, ge=0.0, le=599.0)
    solar_storm_active: bool = Field(default=False)
    personal_dosimeter_online: bool = Field(default=True)
    pillar_overrides: Optional[Dict[str, Dict[str, Any]]] = Field(default=None)


class VitalsAnalyzeRequest(BaseModel):
    """Input payload for Bio-Monitor / PhysioNet ECG+PPG+RESP early-warning analysis."""

    record_id: str = Field(default="ptt_s3_sit")
    atmosphere_profile: str = Field(default="iss_nominal", pattern="^(iss_nominal|exploration_8_2)$")
    window_sec: float = Field(default=60.0, ge=30.0, le=180.0)
    step_sec: float = Field(default=30.0, ge=10.0, le=90.0)
    cabin_ppco2_mmhg: Optional[float] = Field(default=None, ge=0.0, le=20.0)


@app.get("/")
def root() -> FileResponse:
    """Serve the mission-control dashboard."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def api_health() -> dict:
    """Service health check."""
    return {"status": "ok", "service": "ASTRA-Core"}


@app.get("/api/standards")
def get_standards() -> dict:
    """Return NASA-STD-3001 Vol 1 & Vol 2 limits and ISS cabin metadata."""
    return {
        "radiation": {
            "career_effective_dose_msv": NASA_RADIATION_STANDARDS["career_effective_dose_msv"],
            "spe_short_term_msv": NASA_RADIATION_STANDARDS["spe_short_term_msv"],
            "iss_baseline_msv_per_day": [
                NASA_RADIATION_STANDARDS["iss_baseline_msv_per_day_min"],
                NASA_RADIATION_STANDARDS["iss_baseline_msv_per_day_max"],
            ],
            "quality_factor_gcr": NASA_RADIATION_STANDARDS["quality_factor_gcr"],
            "quality_factor_saa": NASA_RADIATION_STANDARDS["quality_factor_saa"],
            "organs": {
                k: {
                    "name": v.name,
                    "unit": v.unit,
                    "limit_30d": v.limit_30d,
                    "limit_1yr": v.limit_1yr,
                    "limit_career": v.limit_career,
                }
                for k, v in NASA_RADIATION_STANDARDS["organs"].items()
            },
        },
        "environment": NASA_ENVIRONMENT_STANDARDS,
        "cardio_vitals": NASA_CARDIO_VITALS_STANDARDS,
        "cabins": {k: vars(v) for k, v in ISS_CABINS.items()},
        "default_hourly_schedule": DEFAULT_HOURLY_SCHEDULE,
    }


@app.get("/api/radiation/baseline")
def get_radiation_baseline() -> dict:
    """Return default 24h schedule simulation + 23-day REM cabin data + live baseline vitals."""
    sim = simulate_astronaut_radiation()
    vitals = _get_cached_vitals("ptt_s3_sit")
    readiness = compute_holistic_readiness(sim, vitals_result=vitals)
    return {"radiation": sim, "vitals": vitals, "readiness": readiness, "rem_summary": load_rem_summary()}


@app.post("/api/radiation/simulate")
def run_radiation_simulation(req: RadiationSimRequest) -> dict:
    """Simulate cabin-tracked radiation vs. vessel average and update Readiness Score."""
    sim = simulate_astronaut_radiation(
        hourly_schedule=req.hourly_schedule,
        cabin_hours=req.cabin_hours,
        mission_days=req.mission_days,
        prior_career_msv=req.prior_career_msv,
        solar_storm_active=req.solar_storm_active,
        personal_dosimeter_online=req.personal_dosimeter_online,
    )
    readiness = compute_holistic_readiness(sim, pillar_overrides=req.pillar_overrides)
    return {"radiation": sim, "readiness": readiness}


@app.get("/api/vitals/records")
def list_vitals_records() -> dict:
    """List bundled PhysioNet records and NASA atmosphere SpO2 profiles."""
    return {
        "records": {k: vars(v) for k, v in PHYSIONET_RECORDS.items()},
        "atmosphere_profiles": NASA_CARDIO_VITALS_STANDARDS["atmosphere_spo2"],
    }


@app.get("/api/vitals/baseline")
def get_vitals_baseline(record_id: str = "ptt_s3_sit", atmosphere_profile: str = "iss_nominal") -> dict:
    """Analyze baseline PhysioNet stream and return updated holistic Readiness Score."""
    vitals = _get_cached_vitals(record_id=record_id, atmosphere_profile=atmosphere_profile)
    sim = simulate_astronaut_radiation()
    readiness = compute_holistic_readiness(sim, vitals_result=vitals)
    return {"vitals": vitals, "readiness": readiness}


@app.post("/api/vitals/analyze")
def run_vitals_analysis(req: VitalsAnalyzeRequest) -> dict:
    """Run Astroskin/Bio-Monitor DSP & early-warning analysis on a PhysioNet stream."""
    vitals = _get_cached_vitals(
        record_id=req.record_id,
        atmosphere_profile=req.atmosphere_profile,
        window_sec=req.window_sec,
        step_sec=req.step_sec,
        cabin_ppco2_mmhg=req.cabin_ppco2_mmhg,
    )
    sim = simulate_astronaut_radiation()
    readiness = compute_holistic_readiness(sim, vitals_result=vitals)
    return {"vitals": vitals, "readiness": readiness}


# ==================== HAL2030 TEAM TELEMETRY, DOWNLINK & COMPANION ====================

from fastapi import File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from astra_core.hal_bridge import (
    build_companion_reply,
    build_snapshot_payload,
    compute_vision_levels,
    get_alert_engine,
    get_downlink,
    get_hal_frame,
    get_source,
    read_downlink_packet,
    serialize_downlink,
    submit_vision_exam,
)
from hal2030.voice_engine import (
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    get_voice_status,
    synthesize_wav,
    transcribe_audio_bytes,
    warmup_voice_engine,
)


class HalEnqueueRequest(BaseModel):
    t: float = 0.0


class HalTickRequest(BaseModel):
    elapsed_s: float = Field(default=1.0, ge=0.0, le=3600.0)


class HalDownlinkConfigRequest(BaseModel):
    connected: Optional[bool] = None
    latency_s: Optional[int] = Field(default=None, ge=1, le=3600)
    auto_send: Optional[bool] = None


class HalCompanionRequest(BaseModel):
    crew_id: str = "anton"
    text: str = Field(min_length=1, max_length=1000)
    family_mode: bool = False
    t: float = 0.0


@app.get("/api/hal/frame")
def hal_frame(t: float = 0.0, window_s: int = 90, crew_id: Optional[str] = None) -> dict:
    """Return 6-crew HAL2030 replay frame, activity-aware alerts, 42-sensor matrix, and traces."""
    return get_hal_frame(t=t, window_s=window_s, trend_crew_id=crew_id)


@app.get("/api/hal/downlink")
def hal_downlink_status() -> dict:
    """Return Mission Control store-and-forward downlink queue and delay settings."""
    return serialize_downlink(get_downlink())


@app.post("/api/hal/downlink/enqueue")
def hal_downlink_enqueue(req: HalEnqueueRequest) -> dict:
    """Queue a 6-crew telemetry snapshot packet onto the durable store-and-forward link."""
    src = get_source()
    engine = get_alert_engine()
    dl = get_downlink()
    clamped_t = max(0.0, min(float(req.t), float(src.duration - 1)))
    frame = src.frame(clamped_t)
    alerts = engine.evaluate(frame)
    packet = dl.enqueue(frame, alerts, clamped_t)
    return {"packet": packet, "state": serialize_downlink(dl)}


@app.post("/api/hal/downlink/tick")
def hal_downlink_tick(req: HalTickRequest) -> dict:
    """Advance active downlink delivery countdown timers."""
    dl = get_downlink()
    dl.tick(req.elapsed_s)
    return serialize_downlink(dl)


@app.post("/api/hal/downlink/config")
def hal_downlink_config(req: HalDownlinkConfigRequest) -> dict:
    """Configure ground link availability and simulated one-way latency (3s / 30s / 1320s)."""
    dl = get_downlink()
    if req.connected is not None:
        dl.set_connected(req.connected)
    if req.latency_s is not None:
        dl.latency_s = int(req.latency_s)
    if req.auto_send is not None:
        dl.auto_send = bool(req.auto_send)
    return serialize_downlink(dl)


@app.get("/api/hal/downlink/packet/{packet_id}")
def hal_downlink_packet(packet_id: str) -> dict:
    """Inspect a queued or delivered packet JSON payload (null preserved for missing values)."""
    payload = read_downlink_packet(get_downlink(), packet_id)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"Packet '{packet_id}' not found")
    return payload


@app.get("/api/hal/downlink/export")
def hal_downlink_export(t: float = 0.0) -> JSONResponse:
    """Export one-off JSON telemetry snapshot at mission time t, preserving null missing signals."""
    src = get_source()
    engine = get_alert_engine()
    clamped_t = max(0.0, min(float(t), float(src.duration - 1)))
    frame = src.frame(clamped_t)
    alerts = engine.evaluate(frame)
    payload = build_snapshot_payload(frame, alerts, clamped_t)
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="hal2030_snapshot_t{int(clamped_t):03d}.json"'},
    )


@app.post("/api/hal/companion/reply")
def hal_companion_reply(req: HalCompanionRequest) -> dict:
    """Return honest HAL2030 scripted support or simulated family archive reply."""
    return build_companion_reply(
        crew_id=req.crew_id,
        text=req.text,
        family_mode=req.family_mode,
        t=req.t,
    )


class VisionCalibrationRequest(BaseModel):
    px_per_mm_x: float = Field(gt=0.1, le=100.0)
    px_per_mm_y: float = Field(gt=0.1, le=100.0)
    device_pixel_ratio: float = Field(default=1.0, gt=0.1, le=10.0)
    display_signature: str = Field(default="Web Display · Calibrated 50mm")
    distance_mm: float = Field(default=400.0, gt=50.0, le=5000.0)


class VisionSubmitRequest(BaseModel):
    crew_id: str
    symptom: str = "Routine scheduled check"
    conditions: Dict[str, Any] = Field(default_factory=dict)
    calibration: Dict[str, Any]
    attempts: List[Dict[str, Any]]
    practice: List[Dict[str, Any]] = Field(default_factory=list)
    mission_time: float = 0.0


class VoiceSpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=800)
    voice: str = DEFAULT_VOICE
    speed: float = Field(default=DEFAULT_SPEED, ge=0.7, le=1.3)


@app.post("/api/hal/vision/levels")
def hal_vision_levels(req: VisionCalibrationRequest) -> dict:
    """Calculate calibrated Tumbling-E test levels via hal2030.vision."""
    try:
        return compute_vision_levels(
            px_per_mm_x=req.px_per_mm_x,
            px_per_mm_y=req.px_per_mm_y,
            device_pixel_ratio=req.device_pixel_ratio,
            display_signature=req.display_signature,
            distance_mm=req.distance_mm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/hal/vision/submit")
def hal_vision_submit(req: VisionSubmitRequest) -> dict:
    """Persist and queue a completed calibrated two-eye SANS vision report onto Downlink."""
    try:
        return submit_vision_exam(
            crew_id=req.crew_id,
            symptom=req.symptom,
            conditions=req.conditions,
            calibration_dict=req.calibration,
            attempts=req.attempts,
            practice=req.practice,
            mission_time=req.mission_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/hal/voice/status")
def hal_voice_status() -> dict:
    """Return lightweight CPU voice TTS (Kokoro-82M INT8) & STT (Faster-Whisper) readiness."""
    return get_voice_status()


@app.post("/api/hal/voice/speak")
def hal_voice_speak(req: VoiceSpeakRequest) -> Response:
    """Synthesize natural human guidance speech as PCM WAV on CPU via Kokoro-ONNX."""
    try:
        wav = synthesize_wav(req.text, voice=req.voice, speed=req.speed)
    except Exception:
        wav = None
    if wav is None:
        return Response(status_code=204)
    return Response(content=wav, media_type="audio/wav")


@app.post("/api/hal/voice/transcribe")
async def hal_voice_transcribe(file: UploadFile = File(...)) -> dict:
    """Transcribe browser microphone clip on CPU via Faster-Whisper tiny.en & parse intent."""
    data = await file.read()
    suffix = Path(file.filename or "clip.webm").suffix or ".webm"
    try:
        return transcribe_audio_bytes(data, suffix=suffix)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

# Mission-aware, three-minute pre-task PVT. Kept at the tail to avoid import coupling.
from astra_core.pvt_api import router as pvt_router
app.include_router(pvt_router)
