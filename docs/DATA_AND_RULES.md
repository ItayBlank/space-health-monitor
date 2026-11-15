# Legacy telemetry data and rules

Scope: the original synthetic replay and shared HAL2030 rules. The web app also
uses `astra_core` research replay/model inputs; this document does not describe
all of them. See [web architecture](ARCHITECTURE.md) and [status](PROJECT_VISION.md).

## What the recording represents

`data/telemetry_10min.csv` is a deterministic, fictional recording containing
**3,600 rows: six crew members × 600 one-second frames**. Mission time runs from
`t = 0` through `t = 599`; the final sample represents the last second of the
ten-minute replay. This is a demonstration dataset, not a NASA data feed.

The UI reads one frame at a time from this recording. Playback speed changes how
quickly frames become visible; pausing holds the current sample. Seeking changes
the replay position. Trend queries end at the selected time and never return
later samples.

The six fictional identities are Idan, Itay, Anton, Emily Carter, Sofia Almeida,
and Camila Santos. The first three are male; the remaining three are female.
Names, roles, portraits, metadata, units, and demonstration thresholds are editable
in `hal2030/config.py`.

## CSV schema

Each row is one person's summary at one mission second. Empty numeric cells
become Python `None`, are exported as JSON `null`, and produce visible gaps in
plots. Missing values are never replaced by zero or by the preceding measurement.

| Column | Meaning | Unit or encoding |
|---|---|---|
| `t` | Mission elapsed time | Integer seconds |
| `crew_id` | Assigned person | `idan`, `itay`, `anton`, `emily`, `sofia`, `camila` |
| `activity` | Scripted activity context | Working, Resting, Maintenance, Exercise, Sleeping, Moving |
| `heart_rate` | Heart-rate summary | bpm |
| `spo2` | Simulated oxygen-saturation summary | % |
| `resp_rate` | Respiratory-rate summary | breaths/min |
| `skin_temp` | Skin-temperature summary | °C |
| `systolic` | Systolic blood-pressure summary | mmHg |
| `diastolic` | Diastolic blood-pressure summary | mmHg |
| `hrv` | Illustrative HRV/RMSSD summary | ms |
| `eeg_alpha` | Illustrative relative EEG alpha power | % |
| `eeg_beta` | Illustrative relative EEG beta power | % |
| `motion` | Dimensionless scenario motion level | Arbitrary units, not acceleration in g |
| `battery` | Fictional wearable battery estimate | % |
| `sensor_ecg` | ECG patch availability | `online` / `no_signal` |
| `sensor_oximeter` | Oximeter availability | `online` / `no_signal` |
| `sensor_respiration` | Respiration belt availability | `online` / `no_signal` |
| `sensor_temperature` | Skin-temperature patch availability | `online` / `no_signal` |
| `sensor_bp` | Blood-pressure monitor availability | `online` / `no_signal` |
| `sensor_eeg` | EEG headband availability | `online` / `no_signal` |
| `sensor_imu` | Motion-tracker availability | `online` / `no_signal` |
| `cabin_co2` | Fictional cabin CO₂ level | ppm |
| `cabin_temp` | Fictional cabin temperature | °C |
| `signal_quality` | Scenario quality estimate for this crew summary | Fraction from 0 to 1 |

There are seven assigned sensor modules per person, making 42 inventory rows.
`signal_quality` is a crew-level scenario estimate; the prototype does not claim
that it is an independently measured quality score for each sensor. The two EEG
features are not a complete band-power spectrum and do not diagnose mental state.

The blood-pressure values are continuously varying fictional summaries for the
interface demonstration. They do not imply that a physical cuff obtains a fresh
measurement each second. A real integration must preserve each device's actual
measurement time and cadence.

`CsvReplaySource` validates required columns, crew IDs, complete contiguous
frames, duplicate rows, finite values, recognized sensor states, and quality
range. A disconnected sensor has all its associated metrics set to `None` even
if a supplied CSV row contains stale numbers.

## Regenerate the recording

From the project directory:

```powershell
python tools/generate_telemetry.py
```

An optional alternative output is supported:

```powershell
python tools/generate_telemetry.py --output data/another_demo.csv
```

Generation uses NumPy seed `2030`, smooth baseline variation, small reproducible
noise, scripted activities, and explicit event envelopes. Running the generator
recreates the same bytes. Source construction generates a missing file, but does
not overwrite an existing recording.

## Demonstration timeline

The application provides jump points at the following times. Transitions occur
around these points, so replay can show onset, persistence, and recovery.

| Jump point | Person | Demonstrated behavior |
|---|---|---|
| 00:00 | All crew | Nominal baseline; Sofia is sleeping and Camila is moving |
| 00:40 | Anton | Reduced oxygen saturation with increased respiratory rate |
| 02:00 | Itay | Oximeter disconnected; oxygen reading disappears |
| 03:05 | Emily | Exercise increases heart and respiratory rates without a resting-state alarm |
| 04:25 | Idan | Elevated heart and respiratory rates while resting |
| 05:55 | Sofia | Elevated skin-temperature trend requests confirmation |
| 07:15 | Camila | EEG channel disconnected; power summaries and waveform disappear |
| 08:50 | All crew | Recovery to nominal availability and demonstration limits |

## Synthetic waveform contract

The CSV contains **1 Hz scalar summaries only**. It contains no raw ECG,
respiration, or EEG recordings.

`CsvReplaySource.waveform()` draws separate, explicitly illustrative signals:

- ECG: a mathematical P–QRS–T-like shape with rate driven by the fictional
  heart-rate summary.
- Respiration: combined sinusoids with rate driven by the fictional breathing
  summary.
- EEG: combined mathematical oscillations with a scripted sleep/awake change.

These graphics are not reconstructed physiological signals, a clinically
calibrated ECG, or spectra from which the CSV's EEG summaries were computed.
Axis units describe the illustrative model. The 100 Hz plotting resolution is
independent of the hypothetical raw sensor rates shown in inventory tooltips.

Phase is integrated across earlier one-second summaries. Consequently, a given
mission timestamp has a consistent waveform value; updating the latest sample
does not redraw historical beats. Fractional replay time provides smooth motion.
Disconnected time intervals are represented by NaN gaps.

## Rule behavior

`AlertEngine` is deterministic and rule based. It does not use an AI model,
diagnose disease, or prescribe treatment. The following constants are chosen to
exercise interface behavior. They are **not NASA-approved limits, universal
medical guidance, or personalized crew baselines**.

| Metric / context | Attention condition | Critical condition |
|---|---|---|
| Oxygen saturation | Below 94%, above 90% | At or below 90% |
| Heart rate, awake/resting | At least 110 bpm, below 130 bpm | At least 130 bpm or below 40 bpm |
| Heart rate, sleeping | At least 110 bpm, below 130 bpm | At least 130 bpm or below 35 bpm |
| Heart rate, exercise | At least 165 bpm, below 180 bpm | At least 180 bpm or below 40 bpm |
| Respiration, non-exercise | At least 23, below 28 breaths/min | At least 28 or below 7 breaths/min |
| Respiration, exercise | At least 36, below 42 breaths/min | At least 42 or below 7 breaths/min |
| Skin temperature | At least 37 °C | No temperature-only critical rule |
| Systolic pressure | At least 150, below 180 mmHg | At least 180 or below 85 mmHg |
| Diastolic pressure | At least 95, below 120 mmHg | At least 120 mmHg |
| Sensor availability | Disconnected or missing required metrics | No physiological inference from missing data |

The prototype has no rule for low skin temperature, EEG pathology, HRV
diagnosis, radiation exposure, blood chemistry, or cabin-environment hazards.
Those capabilities must not be inferred from a green card. Green means that
available demo metrics have not triggered the implemented rules.

Every current frame is evaluated immediately. There is no diagnostic persistence
window, hysteresis, artifact classifier, or escalation policy in this first
version. Production behavior needs all of these to be designed and validated.

A person's overall status is the highest current severity: red for critical,
amber for attention or missing signal, otherwise green. Sensor availability is
separate from measurement severity: an online oximeter may produce a critical
value, while a disconnected one produces a missing-signal warning. The engine
ignores retained numeric values from a channel marked disconnected.

Recommendations are prewritten prompts to verify the signal, check symptoms,
and involve the crew medical officer. Skin temperature is explicitly separated
from core/body temperature and does not establish fever. Requests for a blood
panel or supplemental oxygen are conditional on the medical officer and the
approved onboard procedure; the software neither orders tests nor administers
treatment.

## Local downlink simulation

`DownlinkService` writes JSON health snapshots and `queue.json` under
`runtime/downlink/` by default. A snapshot includes readings, activity, sensor
states, environment summaries, and current alerts. Companion conversations and
family archives are not included.

Each packet has a unique ID and moves through `queued`, `in_transit`, and
`delivered`. These are local simulation states. No network request, NASA
endpoint, or actual ground acknowledgement exists in this implementation.

`tick(delta_seconds)` uses elapsed wall time. Pausing or speeding the telemetry
replay does not pause or accelerate a packet already in transit. Link loss holds
the remaining delay; reconnection resumes the same packet without duplication.
The selected delay applies when a packet is created. A 22-minute setting is a
demonstration scenario, not a fixed Earth–Mars propagation time.

Pending packets and their remaining delays survive restart. Delivery does not
advance while the application is closed. Writes use an atomic temporary-file
replacement; graceful application close calls `flush()`. A malformed saved
queue is preserved in a recovery file and the GUI receives a recovery warning.

## Connecting real equipment later

The intended extension boundaries are deliberately small:

1. Implement a receiver behind `TelemetrySource`, then map its validated
   measurements into `Sample` objects. Keep hardware I/O outside the GUI thread.
2. Preserve measurement timestamps and sample rates; handle out-of-order data,
   packet loss, sensor placement, calibration, and per-channel quality.
3. Expire stale observations to `None` plus `no_signal`. Do not silently reuse
   a last good value as a current measurement.
4. Replace waveform illustration with actual raw waveform buffers before
   describing any trace as a measured signal.
5. Replace demonstration thresholds with versioned, individualized, clinically
   reviewed rules and record their provenance and validation.
6. Implement an authenticated transport behind the downlink boundary before
   enabling an external destination. Preserve IDs, encryption, retry semantics,
   audit records, and separation of medical telemetry from private conversations.

AI text, speech recognition, speech synthesis, voice identity, and family-memory
processing belong in separate adapters. Engine availability must be stated
accurately. A generated family conversation must remain identified as a
simulation even after a local AI engine is connected.

## Behavioral verification

Run:

```powershell
python -m pytest tests/test_core.py -q
```

The tests cover the complete recording, repeatable generation, source
immutability, signal loss, activity context, scenario recovery, waveform gaps
and overlap consistency, missing/nonfinite columns, stale disconnected readings,
JSON nulls, offline queueing, wall-clock delivery, restart recovery, and corrupt
queue preservation.
