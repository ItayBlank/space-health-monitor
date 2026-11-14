"""Display-calibrated, single-optotype near-vision demo; not a clinical protocol."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
import random
from uuid import uuid4

DIRECTIONS = ('up', 'down', 'left', 'right')
PROTOCOL = 'hal2030.tumbling_e.demo.v1'


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def symbol_mm(logmar: float, distance_mm: float = 400) -> float:
    """Return full E height in mm for a five-arcminute × 10**logMAR angle."""
    if not math.isfinite(logmar) or not math.isfinite(distance_mm) or distance_mm <= 0:
        raise ValueError('Finite logMAR and positive viewing distance required.')
    return 2 * distance_mm * math.tan(math.radians(5 * 10**logmar / 60) / 2)


@dataclass(frozen=True)
class Calibration:
    """User-measured logical pixels/mm and display signature; distance is self-confirmed."""
    px_per_mm_x: float
    px_per_mm_y: float
    device_pixel_ratio: float
    display_signature: str
    distance_mm: float = 400

    def __post_init__(self):
        values = (self.px_per_mm_x, self.px_per_mm_y, self.device_pixel_ratio, self.distance_mm)
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError('Calibration values must be finite and positive.')


def levels_for(calibration: Calibration) -> list[dict]:
    """Build distinct integer-device-pixel levels, rejecting strokes below 2 px.

    Rounding is recorded as actual angular size on both axes, never hidden as
    the nominal 0.1-logMAR step. The 2 px floor is an engineering limit only.
    """
    c = calibration
    levels, seen = [], set()
    for tenth in range(10, -1, -1):
        nominal = tenth / 10
        mm = symbol_mm(nominal, c.distance_mm)
        strokes = tuple(int(math.floor(mm / 5 * ppm * c.device_pixel_ratio + .5))
                        for ppm in (c.px_per_mm_x, c.px_per_mm_y))
        if min(strokes) < 2 or strokes in seen:
            continue
        sizes = [5 * s / (ppm * c.device_pixel_ratio)
                 for s, ppm in zip(strokes, (c.px_per_mm_x, c.px_per_mm_y))]
        if max(sizes) / min(sizes) > 1.1:
            continue
        angular = [math.log10(math.degrees(2 * math.atan(size / (2 * c.distance_mm))) * 60 / 5)
                   for size in sizes]
        levels.append(dict(nominal_logmar=nominal, stroke_device_px=list(strokes),
                           actual_size_mm=sizes, actual_logmar_xy=angular))
        seen.add(strokes)
    if not levels:
        raise ValueError('This display cannot render the test range. Recheck calibration.')
    return levels


class EyeTest:
    """Own one eye's confirmed trials and bounded 4/5-pass descending protocol.

    submit accepts a direction or 'unable'; unknown speech must never reach it.
    First failure repeats the previous pass; result is range/consistency-aware.
    """
    def __init__(self, levels: list[dict], rng=None):
        if not levels:
            raise ValueError('At least one renderable level is required.')
        self.levels = levels
        self.rng = rng or random.SystemRandom()
        self.index = 0
        self.confirming = False
        self.batch = []
        self.trials = []
        self.result = None
        self.direction = self.rng.choice(DIRECTIONS)

    @property
    def level(self):
        return self.levels[self.index]

    def submit(self, response: str):
        """Score one explicitly confirmed response; reject invalid or finished input."""
        if self.result is not None or response not in (*DIRECTIONS, 'unable'):
            raise ValueError('Invalid response or completed test.')
        correct = response == self.direction
        self.trials.append(dict(timestamp_utc=utcnow(), level=self.level.copy(),
                                expected=self.direction, response=response, correct=correct,
                                confirmation_block=self.confirming))
        self.batch.append(correct)
        if len(self.batch) == 5:
            passed = sum(self.batch) >= 4
            self.batch = []
            if self.confirming:
                self.result = dict(status='confirmed' if passed else 'inconsistent',
                                   level=self.level.copy() if passed else None)
            elif not passed:
                if self.index == 0:
                    self.result = dict(status='outside_range', level=None)
                else:
                    self.index -= 1
                    self.confirming = True
            elif self.index == len(self.levels) - 1:
                self.result = dict(status='display_limit', level=self.level.copy())
            else:
                self.index += 1
        if self.result is None:
            self.direction = self.rng.choice(DIRECTIONS)
        return self.result


def make_report(crew_id, symptom, conditions, calibration, attempts, practice):
    """Return a JSON-safe report, with observed input and synthetic baseline separated."""
    if not attempts or any(set(attempt['eyes']) != {'right', 'left'} for attempt in attempts):
        raise ValueError('Both eyes must be completed before saving.')
    return dict(schema='hal2030.vision_report.v1', report_id='VISION-' + uuid4().hex[:12].upper(),
                recorded_at_utc=utcnow(), crew_id=crew_id, symptom=symptom,
                protocol=PROTOCOL, data_kind='user_performed_demo', clinical_validation=False,
                conditions=conditions, calibration=asdict(calibration),
                distance_verification='user_confirmed_not_tracked',
                baseline=dict(kind='simulated_preflight', right_logmar=0.0, left_logmar=0.0,
                              comparable=False, reason='Illustrative baseline; no matched prior measurement.'),
                attempts=attempts, practice=practice,
                interpretation='Functional near-vision demo for review; not a diagnosis or standard chart score.')
