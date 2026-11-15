"""Unit tests for Contactless Radar & ESP32 Wi-Fi CSI Sleep/Respiration ML."""

import numpy as np

from astra_core.radar_sleep import (
    SLEEP_RECORDS,
    STAGES,
    analyze_csi_window,
    analyze_sleep_record,
    circle_fit_iq,
    detect_motion_arousals,
    extract_cardiac_bcg_hrv,
    extract_respiration_and_apnea,
    process_csi_frame,
    unwrap_iq_phase,
    viterbi_smooth,
)


def test_iq_circle_fit_and_phase_unwrapping():
    t = np.linspace(0.0, 30.0, 600)
    phi_true = 0.7 * np.sin(2.0 * np.pi * 0.25 * t)
    i_sig = 3.5 + 1.2 * np.cos(phi_true)
    q_sig = -2.1 + 0.9 * np.sin(phi_true)

    i_c, q_c = circle_fit_iq(i_sig, q_sig)
    assert np.isfinite(i_c).all() and np.isfinite(q_c).all()

    phi_est = unwrap_iq_phase(i_sig, q_sig)
    corr = np.corrcoef(phi_true, phi_est - np.mean(phi_est))[0, 1]
    assert corr > 0.95


def test_respiration_and_apnea_detection():
    fs = 20.0
    t = np.arange(0.0, 90.0, 1.0 / fs)
    phase = 0.8 * np.sin(2.0 * np.pi * 0.25 * t)  # 15 bpm
    # Inject a 14-second apnea pause
    phase[(t >= 30.0) & (t <= 44.0)] = 0.0

    motion = detect_motion_arousals(phase, fs_hz=fs)
    resp = extract_respiration_and_apnea(phase, fs_hz=fs, motion_mask_1s=motion["motion_mask_1s"])
    assert resp["resp_rate_bpm"] is not None
    assert 13.0 <= resp["resp_rate_bpm"] <= 17.0
    assert len(resp["apnea_events"]) >= 1
    assert resp["max_apnea_pause_s"] >= 10.0


def test_cardiac_bcg_hrv_reuse():
    fs = 20.0
    t = np.arange(0.0, 60.0, 1.0 / fs)
    phase = 0.6 * np.sin(2.0 * np.pi * 0.25 * t) + 0.12 * np.sin(2.0 * np.pi * 1.05 * t)
    hrv = extract_cardiac_bcg_hrv(phase, fs_hz=fs, resp_rate_bpm=15.0)
    assert hrv["mean_hr_bpm"] is not None
    assert 55.0 <= hrv["mean_hr_bpm"] <= 72.0


def test_viterbi_smooth_valid_stages():
    probs = np.array(
        [
            [0.8, 0.1, 0.05, 0.05],
            [0.1, 0.7, 0.1, 0.1],
            [0.05, 0.15, 0.75, 0.05],
            [0.05, 0.2, 0.1, 0.65],
        ]
    )
    path = viterbi_smooth(probs)
    assert len(path) == 4
    assert all(s in STAGES for s in path)


def test_esp32_csi_processing_and_window():
    fs = 20.0
    frames = []
    for k in range(int(40 * fs)):
        t = k / fs
        resp = 0.5 * np.sin(2.0 * np.pi * 0.25 * t)
        amps = (10.0 + resp + np.zeros(52)).tolist()
        phases = (0.1 * resp + np.zeros(52)).tolist()
        frames.append({"ts": t, "amplitudes": amps, "phases": phases})

    one = process_csi_frame(frames[0])
    assert one["subcarriers"] == 52

    res = analyze_csi_window(frames, fs_hz=fs)
    assert res["resp_rate_bpm"] is not None
    assert 13.0 <= res["resp_rate_bpm"] <= 17.0
    assert res["readiness_patch"]["is_live_module"] is True


def test_analyze_sleep_records_offline():
    for rec_id in SLEEP_RECORDS:
        out = analyze_sleep_record(rec_id)
        assert out["record"]["record_id"] == rec_id
        assert len(out["sleep_summary"]["hypnogram_epochs"]) >= 1
        assert out["readiness_patch"]["is_live_module"] is True
        if rec_id == "iss_sleep_apnea":
            assert out["sleep_summary"]["max_apnea_pause_s"] >= 10.0
