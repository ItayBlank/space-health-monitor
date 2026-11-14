# Architecture and extension guide

## Data flow

`main.py` creates the Qt application, opens a `CsvReplaySource`, and constructs `MainWindow`. A single 100 ms GUI timer advances the replay clock. The source releases six 1 Hz `Sample` summaries for the current mission second; no UI code invents a fresh reading independently.

`AlertEngine.evaluate(frame)` turns those samples into transparent `Alert` objects. The same alerts determine portrait rings, sensor-row colors, the global banner, priority watch and individual action cards. Severity uses critical-before-warning precedence. Missing signals are handled separately from physiological threshold violations.

The current view receives `update_frame(frame, alerts, mission_time)`. Scalar values refresh when the second changes. The individual signal strips can redraw at 10 Hz using fractional mission time. Those traces are deterministic illustrations with their own synthetic sampling, explicitly separate from the CSV summaries.

`DownlinkService` receives snapshots only through a manual action or enabled 30-second auto-send. It serializes the frame and alerts to a local packet, updates a persistent queue, and advances a simulated delivery clock. Its wall-clock delta is independent of the telemetry clock, so a seek or 10× replay does not shorten a 22-minute link scenario. No chat history is accepted by this service.

## Module responsibilities

| Module | Owns | Does not own |
|---|---|---|
| `config.py` | Crew identities, sensors, metric metadata, demo limits and event jumps | Actual measurements |
| `models.py` | Shared `Sample`, `Alert`, `TelemetrySource` contracts | GUI rendering |
| `telemetry.py` | Validated CSV replay and deterministic synthetic signals | Clinical diagnosis |
| `alerts.py` | Predefined rules and explanation/action text | Treatment execution |
| `downlink.py` | Atomic local JSON writes and queue state | NASA transport or chat storage |
| `ui/window.py` | Navigation, shared selected crew, clocks and top-level commands | Sensor acquisition drivers |
| `ui/dashboard.py` | Fleet cards, priority watch and recommendation dialog | An independent alert policy |
| `ui/detail.py` | Selected astronaut's plots, metrics and guidance | Classification of EEG into disease or emotions |
| `ui/sensors.py` | Assignment/availability registry and filters | Automatic hardware discovery |
| `ui/mission_control.py` | Link settings, outbox view and packet inspection | Internet transmission |
| `ui/companion.py` | Per-person scripted chats and setup previews | LLM inference, speech or archive ingestion |

## Adding real hardware

The `TelemetrySource` protocol is the starting boundary. A real adapter should timestamp incoming packets, map each device to a crew ID and sensor ID, and normalize measured quantities into the same documented units. BLE, serial, TCP, laboratory DAQ and file streams can be separate adapters.

Implement acquisition in a worker thread or asynchronous bridge. Use Qt signals to pass completed frames to the GUI thread; do not block the update timer on device I/O. A real stream needs a bounded history buffer, sequence numbers, device timestamps, sampling metadata and explicit freshness limits. Mark an expired reading unavailable and emit `None`, rather than allowing an old normal number to look current.

Raw ECG/EEG/respiration should have independent timestamped arrays and their actual sampling rates. Replace the illustrative `waveform()` method with a real buffer-backed source. Do not infer raw high-frequency data from low-rate vital summaries. Blood-pressure cuff updates are usually intermittent; their age and measurement state need explicit handling rather than the demonstration's 1 Hz scalar convention.

Crew identity and binding belong in a configuration layer. The present 42-row roster is predefined, not discovered hardware. Before connecting real devices, add validation for impossible values, quality flags, unit conversions, alignment of sample clocks, missing packets and reconnect behavior.

## Replacing the rule engine

`AlertEngine` is intentionally readable. Actual deployment would require mission-approved thresholds, individualized baselines, signal-quality gating, persistence/hysteresis, activity-specific logic, human acknowledgement and audit records. The current immediate frame rules are useful for demonstrating the interface. They are not validated medical criteria.

Use the existing `Alert` fields to keep decisions explainable: the metric, measured value, sensor, severity, title, reason and reviewable steps are explicit. Clinical recommendations should remain under the applicable crew medical procedure.

## Replacing simulated transport

Keep `DownlinkService`'s serialization and store-and-forward boundary, then implement the mission's approved authenticated transport. Real networking needs access control, encryption, integrity, packet IDs, acknowledgement/retry semantics and a ground endpoint supplied by the operator. The demo deliberately contains no destination credentials or NASA API address.

The present delay models one-way arrival with a local simulated receipt. It does not implement round-trip propagation, bandwidth contention, packet loss, orbital coverage or a real acknowledgement returning from Earth. The adjustable 22-minute setting is an illustration, not a universal communications delay.

## Adding offline AI and voice

The companion's `_reply()` method is a scripted boundary. Replace it with a local engine client or worker that can stream text without blocking Qt. Add separate offline speech recognition and speech synthesis components. The current local-model dialog stores a selected path only and explicitly does not load it.

Keep one history/context per crew member. Make any future archive import explicit and distinguish generated replies from messages received from real relatives. Archive content must not become medical instructions. Send telemetry through its dedicated service; private conversations are excluded by construction in this prototype. Current chat histories live only in memory and are not encrypted persistent records.

## Runtime and reproducibility

The recording and portraits ship in the ZIP. Replay needs no network. The generator uses a fixed seed. Local packets live beneath `runtime/downlink/` by default, with an override from `--runtime-dir`. Packet payloads are written before the queue records them. A pending packet resumes with its original ID after a normal restart. A corrupt queue is preserved for inspection and a warning is exposed.

Development screenshots can be generated with `python main.py --paused --start-at 40 --screenshot output.png`; Linux uses the offscreen Qt platform automatically if no display is available. Do not confuse a software-rendered preview with native deployment validation.
