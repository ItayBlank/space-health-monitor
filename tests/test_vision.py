"""Geometry, bounded scoring and durable vision reports, independent of Qt/audio."""
import json
import math
import random

import pytest

from hal2030.vision import Calibration, EyeTest, levels_for, make_report, symbol_mm
from hal2030.downlink import DownlinkService


@pytest.fixture
def calibration():
    return Calibration(3.78, 3.78, 1, 'test-display')


def block(test, correct=5):
    for n in range(5):
        test.submit(test.direction if n < correct else 'unable')


def test_geometry_and_display_floor(calibration):
    assert symbol_mm(0) == pytest.approx(.5817765, rel=1e-6)
    assert symbol_mm(0, 800) == pytest.approx(2 * symbol_mm(0))
    levels = levels_for(calibration)
    assert len({tuple(level['stroke_device_px']) for level in levels}) == len(levels)
    assert all(min(level['stroke_device_px']) >= 2 for level in levels)
    assert levels[-1]['actual_logmar_xy'][0] > .6  # Laptop resolution cannot support 0.0 at 40 cm.
    for level in levels:
        actual = level['actual_logmar_xy'][0]
        assert symbol_mm(actual) == pytest.approx(level['actual_size_mm'][0])
    assert len(levels_for(Calibration(3.78, 3.78, 2, 'hidpi'))) > len(levels)


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf')])
def test_calibration_rejects_invalid_numbers(value):
    with pytest.raises(ValueError):
        Calibration(value, 3.78, 1, 'screen')


def test_threshold_requires_confirmation(calibration):
    test = EyeTest(levels_for(calibration), random.Random(4))
    block(test, 4)
    assert test.index == 1
    block(test, 3)
    assert test.confirming and test.index == 0 and test.result is None
    block(test, 4)
    assert test.result['status'] == 'confirmed'
    assert len(test.trials) == 15
    with pytest.raises(ValueError):
        test.submit('up')


def test_failed_confirmation_does_not_report_threshold(calibration):
    test = EyeTest(levels_for(calibration))
    block(test)
    block(test, 0)
    block(test, 3)
    assert test.result == {'status': 'inconsistent', 'level': None}


def test_floor_and_ceiling_are_censored(calibration):
    levels = levels_for(calibration)
    test = EyeTest(levels)
    for _ in levels:
        block(test)
    assert test.result['status'] == 'display_limit'
    assert len(test.trials) == len(levels) * 5 <= 55
    other = EyeTest(levels)
    block(other, 0)
    assert other.result == {'status': 'outside_range', 'level': None}


def test_unrecognized_speech_cannot_be_scored(calibration):
    test = EyeTest(levels_for(calibration))
    for invalid in ['', 'continue', 'up down', '[unk]']:
        with pytest.raises(ValueError):
            test.submit(invalid)
    assert test.trials == []


def report(calibration):
    eyes = {}
    for eye in ('right', 'left'):
        test = EyeTest(levels_for(calibration))
        block(test, 0)
        eyes[eye] = {'result': test.result, 'trials': test.trials}
    return make_report('anton', 'routine demo', {'correction': 'None'}, calibration,
                       [{'eyes': eyes}], [])


def test_report_queue_offline_restart_and_no_duplicate(calibration, tmp_path):
    service = DownlinkService(tmp_path)
    service.set_connected(False)
    content = report(calibration)
    packet = service.enqueue_report(content, 40)
    assert packet['status'] == 'queued'
    assert service.enqueue_report(content, 40) is packet
    payload = json.loads((tmp_path / packet['filename']).read_text())
    assert payload['data_kind'] == 'user_performed_demo'
    assert payload['baseline']['kind'] == 'simulated_preflight'
    assert payload['transport_simulated'] is True
    restored = DownlinkService(tmp_path)
    assert len(restored.queue) == 1
    restored.tick(3)
    assert restored.queue[0]['status'] == 'delivered'


def test_queue_failure_is_retryable(calibration, tmp_path, monkeypatch):
    service = DownlinkService(tmp_path)
    content = report(calibration)
    original_save = service._save
    def fail():
        raise OSError('disk unavailable')
    monkeypatch.setattr(service, '_save', fail)
    with pytest.raises(OSError):
        service.enqueue_report(content, 0)
    assert service.queue == []
    monkeypatch.setattr(service, '_save', original_save)
    service.enqueue_report(content, 0)
    assert len(service.queue) == 1


def test_incomplete_report_rejected(calibration, tmp_path):
    with pytest.raises(ValueError):
        make_report('anton', 'demo', {}, calibration, [{'eyes': {'left': {}}}], [])
    content = report(calibration)
    del content['attempts'][0]['eyes']['right']
    with pytest.raises(ValueError):
        DownlinkService(tmp_path).enqueue_report(content, 0)
