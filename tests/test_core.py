"""Behavioral checks for the offline recording, alert rules, and link queue."""
import csv
import json
import math
from pathlib import Path

import numpy as np
import pytest

from hal2030.alerts import AlertEngine, crew_status, sensor_status
from hal2030.config import CREW, SCENARIOS, SENSORS
from hal2030.downlink import DownlinkService
from hal2030.telemetry import CsvReplaySource, generate_dataset


@pytest.fixture(scope="module")
def source():
    return CsvReplaySource()


def test_recording_has_exactly_ten_minutes_and_six_people(source):
    assert source.duration == 600
    with source.path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3600
    assert {row["crew_id"] for row in rows} == {crew["id"] for crew in CREW}
    assert len(source.frame(0)) == len(source.frame(599)) == 6
    assert all(sample.t == 0 for sample in source.frame(-10).values())
    assert all(sample.t == 599 for sample in source.frame(6000).values())


def test_generator_is_deterministic_and_replay_preserves_file(tmp_path):
    first = generate_dataset(tmp_path / "a.csv")
    second = generate_dataset(tmp_path / "b.csv")
    assert first.read_bytes() == second.read_bytes()
    before = first.stat().st_mtime_ns
    CsvReplaySource(first)
    assert first.stat().st_mtime_ns == before


def test_missing_signal_has_no_fake_value_and_history_breaks(source):
    frame = source.frame(120)
    assert frame["itay"].sensor_status["oximeter"] == "no_signal"
    assert frame["itay"].values["spo2"] is None
    engine = AlertEngine()
    alerts = engine.evaluate(frame)
    itay_alerts = [alert for alert in alerts if alert.crew_id == "itay"]
    assert len(itay_alerts) == 1
    assert itay_alerts[0].severity == "warning"
    assert itay_alerts[0].value is None
    assert sensor_status("itay", "oximeter", frame, alerts) == "warning"
    times, values = source.history("itay", "spo2", 125, seconds=30)
    assert max(times) == 125
    assert math.isnan(values[-1]) and math.isfinite(values[0])
    assert source.frame(150)["itay"].values["spo2"] is not None


def test_critical_episode_and_normal_exercise_are_distinct(source):
    engine = AlertEngine()
    critical_frame = source.frame(40)
    critical_alerts = engine.evaluate(critical_frame)
    assert crew_status("anton", critical_alerts) == "critical"
    assert sensor_status("anton", "oximeter", critical_frame, critical_alerts) == "critical"
    exercise_frame = source.frame(185)
    assert exercise_frame["emily"].activity == "Exercise"
    assert exercise_frame["emily"].values["heart_rate"] > 120
    assert crew_status("emily", engine.evaluate(exercise_frame)) == "nominal"
    # Identical high heart rate at rest must not retain exercise tolerance.
    exercise_frame["emily"].activity = "Resting"
    assert crew_status("emily", engine.evaluate(exercise_frame)) == "critical"


def test_nominal_start_and_full_recovery_and_scenario_targets(source):
    engine = AlertEngine()
    for second in [0, 530, 599]:
        assert engine.evaluate(source.frame(second)) == []
    assert crew_status("idan", engine.evaluate(source.frame(265))) == "critical"
    assert crew_status("sofia", engine.evaluate(source.frame(355))) == "warning"
    assert crew_status("camila", engine.evaluate(source.frame(435))) == "warning"
    assert all(0 <= entry["t"] < source.duration for entry in SCENARIOS)


def test_mutating_returned_frame_does_not_change_recording(source):
    frame = source.frame(0)
    original = frame["idan"].values["heart_rate"]
    frame["idan"].values["heart_rate"] = -999
    assert source.frame(0)["idan"].values["heart_rate"] == original


def test_eeg_waveform_has_gap_and_fractional_time_is_supported(source):
    x, y = source.waveform("camila", "eeg", 435.3)
    assert np.isclose(x[-1], 435.3)
    assert len(x) == len(y) and len(x) > 100
    assert np.isnan(y).all()
    x2, y2 = source.waveform("camila", "eeg", 415.6)
    assert np.isfinite(y2).all()
    assert np.isclose(x2[-1], 415.6)
    with pytest.raises(ValueError):
        source.waveform("camila", "unknown", 10)


def test_queue_survives_disconnect_and_restart_without_duplicate(source, tmp_path):
    service = DownlinkService(tmp_path)
    service.latency_s = 22 * 60
    service.set_connected(False)
    frame = source.frame(40)
    packet = service.enqueue(frame, AlertEngine().evaluate(frame), 40)
    assert packet["status"] == "queued"
    service.tick(10)
    assert packet["eta_s"] == 1320
    payload = json.loads((tmp_path / packet["filename"]).read_text(encoding="utf-8"))
    assert payload["simulation"] is True
    assert len(payload["crew"]) == 6
    assert "chat" not in payload and "family" not in payload
    restored = DownlinkService(tmp_path)
    assert len(restored.queue) == 1
    assert restored.queue[0]["id"] == packet["id"]
    restored.tick(2.0)
    assert restored.queue[0]["status"] == "in_transit"
    assert restored.queue[0]["eta_s"] == 1318
    restored.set_connected(False)
    restored.tick(5000)
    assert restored.queue[0]["eta_s"] == 1318
    restored.set_connected(True)
    restored.tick(1318)
    assert restored.queue[0]["status"] == "delivered"
    assert restored.queue[0]["eta_s"] == 0
    assert len(restored.queue) == 1


def test_direct_connection_flag_change_and_invalid_time(source, tmp_path):
    service = DownlinkService(tmp_path)
    packet = service.enqueue(source.frame(0), [], 0)
    service.connected = False
    service.tick(0.1)
    assert packet["status"] == "queued"
    service.connected = True
    service.tick(3)
    assert packet["status"] == "delivered"
    with pytest.raises(ValueError):
        service.tick(-1)
    with pytest.raises(ValueError):
        service.tick(float("nan"))


def test_export_json_preserves_missing_values_as_null(source, tmp_path):
    frame = source.frame(120)
    service = DownlinkService(tmp_path / "downlink")
    export_path = tmp_path / "snapshot.json"
    service.export_snapshot(frame, AlertEngine().evaluate(frame), export_path)
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    itay = next(person for person in payload["crew"] if person["crew_id"] == "itay")
    assert itay["values"]["spo2"] is None
    assert payload["mission_time_s"] == 120


def test_corrupt_saved_queue_is_preserved(tmp_path):
    path = tmp_path / "queue.json"
    path.write_text("not valid json", encoding="utf-8")
    service = DownlinkService(tmp_path)
    assert service.queue == []
    assert service.recovery_warning
    saved = list(tmp_path.glob("queue_recovery_*.json"))
    assert len(saved) == 1 and saved[0].read_text() == "not valid json"


def test_waveform_overlap_does_not_redraw_past_beats(source):
    # The second window crosses a rate-changing event. Its overlapping history
    # must remain identical rather than adopting the newest heart/breath rate.
    for kind in ("ecg", "respiration", "eeg"):
        x_before, y_before = source.waveform("idan", kind, 260.3, seconds=8)
        x_after, y_after = source.waveform("idan", kind, 261.3, seconds=8)
        np.testing.assert_allclose(x_before[100:], x_after[:-100], atol=1e-12)
        np.testing.assert_allclose(y_before[100:], y_after[:-100], atol=1e-10)
    times, _ = source.history("idan", "heart_rate", 260.9)
    assert max(times) == 260
    assert x_before.max() <= 260.3


def test_stale_unsafe_number_on_disconnected_sensor_is_not_a_new_physiology_alert(source):
    frame = source.frame(0)
    frame["itay"].sensor_status["oximeter"] = "no_signal"
    frame["itay"].values["spo2"] = 82.0
    alerts = AlertEngine().evaluate(frame)
    own = [alert for alert in alerts if alert.crew_id == "itay"]
    assert len(own) == 1 and own[0].value is None
    assert own[0].severity == "warning"
    assert "no signal" in own[0].title.lower()


def test_csv_rejects_nonfinite_metadata_and_missing_columns(source, tmp_path):
    with source.path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    rows[0]["cabin_temp"] = "inf"
    bad = tmp_path / "bad.csv"
    with bad.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="Non-finite cabin"):
        CsvReplaySource(bad)
    incomplete = tmp_path / "incomplete.csv"
    incomplete.write_text("t,crew_id\n0,idan\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing telemetry columns"):
        CsvReplaySource(incomplete)
