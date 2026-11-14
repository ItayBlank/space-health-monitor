"""FastAPI integration tests for HAL2030 replay, sensor matrix, downlink & companion."""

from fastapi.testclient import TestClient

from server import app


def test_hal_frame_replay_missing_signal_and_exercise_suppression() -> None:
    client = TestClient(app)

    # t=40: Anton oxygen saturation critical alert
    res_anton = client.get("/api/hal/frame", params={"t": 40, "crew_id": "anton"})
    assert res_anton.status_code == 200
    body = res_anton.json()
    assert len(body["crew"]) == 6
    assert len(body["sensor_matrix"]) == 42
    assert body["samples"]["anton"]["status"] == "critical"
    assert body["samples"]["anton"]["values"]["spo2"] < 90.0
    assert "waveforms" in body and len(body["waveforms"]["ecg"]["values"]) > 50

    # t=120: Itay oximeter signal lost -> null value, warning status
    res_itay = client.get("/api/hal/frame", params={"t": 120, "crew_id": "itay"})
    assert res_itay.status_code == 200
    itay_data = res_itay.json()
    assert itay_data["samples"]["itay"]["sensor_status"]["oximeter"] == "no_signal"
    assert itay_data["samples"]["itay"]["values"]["spo2"] is None
    assert itay_data["samples"]["itay"]["status"] == "warning"

    # t=185: Emily exercising -> elevated HR does NOT create false alarm
    res_emily = client.get("/api/hal/frame", params={"t": 185})
    assert res_emily.status_code == 200
    emily_data = res_emily.json()
    assert emily_data["samples"]["emily"]["activity"] == "Exercise"
    assert emily_data["samples"]["emily"]["values"]["heart_rate"] > 120
    assert emily_data["samples"]["emily"]["status"] == "nominal"


def test_hal_downlink_queue_tick_export_and_companion() -> None:
    client = TestClient(app)

    cfg = client.post("/api/hal/downlink/config", json={"connected": False, "latency_s": 1320})
    assert cfg.status_code == 200
    assert cfg.json()["connected"] is False
    assert cfg.json()["latency_s"] == 1320

    enq = client.post("/api/hal/downlink/enqueue", json={"t": 120})
    assert enq.status_code == 200
    pkt_id = enq.json()["packet"]["id"]
    assert enq.json()["packet"]["status"] == "queued"

    pkt = client.get(f"/api/hal/downlink/packet/{pkt_id}")
    assert pkt.status_code == 200
    pkt_json = pkt.json()
    itay_row = next(row for row in pkt_json["crew"] if row["crew_id"] == "itay")
    assert itay_row["values"]["spo2"] is None

    exp = client.get("/api/hal/downlink/export", params={"t": 120})
    assert exp.status_code == 200
    assert "attachment" in exp.headers.get("content-disposition", "")

    # Companion scripted vs family archive
    c1 = client.post(
        "/api/hal/companion/reply",
        json={"crew_id": "anton", "text": "Check my oxygen readings", "family_mode": False, "t": 40},
    )
    assert c1.status_code == 200
    assert c1.json()["kind"] == "assistant"
    assert "cannot diagnose" in c1.json()["reply"].lower()

    c2 = client.post(
        "/api/hal/companion/reply",
        json={"crew_id": "anton", "text": "I miss home", "family_mode": True, "t": 40},
    )
    assert c2.status_code == 200
    assert c2.json()["kind"] == "family"
    assert "simulated" in c2.json()["reply"].lower()

    # Restore clean default online/3s config
    client.post("/api/hal/downlink/config", json={"connected": True, "latency_s": 3})


def test_calibrated_vision_and_natural_voice_api():
    client = TestClient(app)
    lvl_res = client.post(
        "/api/hal/vision/levels",
        json={
            "px_per_mm_x": 4.0,
            "px_per_mm_y": 4.0,
            "device_pixel_ratio": 1.0,
            "display_signature": "Pytest Virtual Display",
            "distance_mm": 400.0,
        },
    )
    assert lvl_res.status_code == 200
    lvl_data = lvl_res.json()
    assert lvl_data["count"] >= 4
    first_lvl = lvl_data["levels"][0]

    v_status = client.get("/api/hal/voice/status")
    assert v_status.status_code == 200
    vst = v_status.json()
    assert vst["tts_engine"] in ("kokoro-82m-int8", "browser-fallback")

    speak_res = client.post("/api/hal/voice/speak", json={"text": "Pointing left. Check Anton heart view."})
    assert speak_res.status_code in (200, 204)
    if speak_res.status_code == 200 and vst["stt_ready"]:
        tr_res = client.post(
            "/api/hal/voice/transcribe",
            files={"file": ("speech.wav", speak_res.content, "audio/wav")},
        )
        assert tr_res.status_code == 200
        tr_data = tr_res.json()
        assert tr_data["vision_command"] == "left"
        assert tr_data["crew_id"] == "anton"

    # Submit calibrated two-eye exam to store-and-forward queue
    trial = {
        "timestamp_utc": "2026-11-14T15:00:00+00:00",
        "level": first_lvl,
        "expected": "right",
        "response": "right",
        "correct": True,
        "confirmation_block": False,
    }
    sub_res = client.post(
        "/api/hal/vision/submit",
        json={
            "crew_id": "anton",
            "symptom": "Routine scheduled check",
            "conditions": {"lighting": "Nominal cabin"},
            "calibration": lvl_data["calibration"],
            "attempts": [
                {
                    "attempt": 1,
                    "eyes": {
                        "right": {"result": {"status": "confirmed", "level": first_lvl}, "trials": [trial]},
                        "left": {"result": {"status": "confirmed", "level": first_lvl}, "trials": [trial]},
                    },
                }
            ],
            "practice": [],
            "mission_time": 40.0,
        },
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["packet"]["id"].startswith("VISION-")
    assert sub_data["packet"]["kind"] == "vision_report"

