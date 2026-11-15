# ASTRA-Core · HAL2030 — Space Health Monitor

A local Python web console (with a companion PySide6 desktop prototype) for the **NASA Space Apps Challenge 2026: Create Health Monitoring Software for Astronauts on Space Missions**.

**ASTRA-Core + HAL2030** pairs a FastAPI telemetry engine (`server.py`, `astra_core/`, `hal2030/`) with a Liquid Glass web interface (`static/`) featuring Day/Night mission themes, crew vitals, PhysioNet BIDMC/PTT physiological replay, ISS REM/DOSTEL space-radiation shielding analysis, guided near-vision testing, pre-task three-minute PVT, and private mood and stress check-ins, delayed Mars/Earth telemetry downlink simulation, and an offline CPU natural voice engine (**Kokoro-82M INT8** TTS + **Faster-Whisper tiny.en** STT).

**Everything in the application is in English.** Supplied scenario telemetry, portraits, and crew communications are synthetic/educational or derived from research datasets. The source registry (`data/sources.json`) covers the earlier assets; provenance for the new PhysioNet/radiation data and natural-voice models still needs reconciliation. Voice inference can run locally after installing its dependencies and weights. The current HTML still loads Chart.js and fonts from external CDNs; a fresh fully offline browser session is not yet guaranteed.

---

## Quick Start — Web Console (Recommended)

1. **Clone the repository** (64-bit **Python 3.11–3.14**):

```powershell
git clone https://github.com/ItayBlank/space-health-monitor.git
cd space-health-monitor
```

2. **Create a virtual environment and install dependencies:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

*(macOS / Linux: `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt`)*

3. **Optional. Install local voice dependencies and download the CPU voice models (Kokoro-82M INT8 TTS + Faster-Whisper tiny.en STT):**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
.\.venv\Scripts\python.exe tools/download_voice_model.py --engine natural
```

*(Voice weights are stored in `runtime/voice-model/`. If omitted, Kokoro files can also auto-download on first demand when online.)*

4. **Launch the website and open it in your browser:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in Chrome, Edge, or Firefox.

---

## Web Console Views

| View | Implemented behavior |
|---|---|
| **Glance & Readiness** | Left-anchored mission timeline & crew cards alongside an expanded **Station Readiness** panel with priority watch, recent events, cabin environment context, and Day/Night Liquid Glass styling. |
| **Actions** | Crew-filtered operational & medical check-off protocols reactive to live alert severity. |
| **Heart (Cardiovascular)** | Individual 1 Hz vitals, activity-aware rules, synthetic ECG/PPG strips, and **PhysioNet BIDMC / PTT** dataset replay. |
| **RadLab (Radiation)** | **ISS REM 2024 & DOSTEL** orbital dose-rate timeline, module shielding simulation, and Solar Particle Event (SPE) / GCR presets. |
| **Sensors & SANS** | All 42 sensor channels with filters, [mission-aware three-minute PVT](docs/PVT.md) and a separate five-trial reaction demo, **SANS** optical/Amsler exam with voice readout, and Guided Near-Vision check. |
| **Check-ins** | [Local sign-in, personal mood/stress history, illustrative trend follow-up, and consent-based consult requests](docs/PRIVATE_CHECKINS.md). |
| **Downlink (Mission Link)** | Durable local JSON snapshot queue (`runtime/downlink/`) with offline toggle and **Local · 3 s** / **Mars · 22 min** latency presets. |
| **HAL2030 Companion** | Six isolated crew chat sessions with local **Kokoro-82M INT8** natural speech output, **Faster-Whisper tiny.en** microphone transcription, and IEC 60601-1-8 / NASA-STD-3001 gentle marimba chimes + anti-overload critical callouts (`Voice` / `Chime` / `Muted`). |

---

## Feature status and next work

See [the web roadmap](docs/PROJECT_VISION.md) for implemented, partial, and
superseded work. The [private check-ins](docs/PRIVATE_CHECKINS.md) and
[pre-task PVT](docs/PVT.md) replaced the earlier combined issue #1. Radiation #2
and hatch/CO2 #3 remain open.

The Check-ins view requires its own sign-in. The HAL companion separates demo
chat sessions by crew selection and does not authenticate users.
The CI executable and screenshot smoke test target the legacy desktop app;
they do not establish browser workflow or web microphone correctness.

## Legacy Desktop Prototype & CI Executable (`main.py`)

This repository also retains the original **PySide6 desktop prototype** (`main.py`) and CI Windows executable build (`HAL2030.exe`):

```powershell
.\.venv\Scripts\python.exe main.py
```

Or double-click `start_windows.bat` (`./start_unix.sh` on macOS/Linux). Prebuilt desktop workflow artifacts are available under **Actions → Test and build** (`HAL2030-windows-x64-<commit>`). See `.github/workflows/tests.yml` for the automated CI packaging and `--engine vosk` smoke checks.

The main alert banner appears on every view. An affected astronaut's portrait is enlarged in **Priority watch**. Click that portrait or **Review recommended actions** to open predefined guidance. Opening an action card does not clear a physiological alert: its state follows the current telemetry.

### Status language

- **Green — Nominal / Online:** connected sensor and values within the demonstration rules.
- **Amber — Attention / No signal:** a missing signal or a noncritical measurement needing review. The table states the reason explicitly.
- **Red — Critical:** a measured value outside a critical demonstration threshold.

Missing data becomes `—` and an actual gap in the plotted signal. A disconnected sensor is not portrayed as a valid normal measurement. Activity appears as a small portrait badge and a readable label, including Working, Sleeping, Moving, Resting, Maintenance and Exercise.

## The fictional crew

| Name | Role | Profile |
|---|---|---|
| Idan | Mission commander | Male; international crew |
| Itay | Flight engineer | Male; international crew |
| Anton | Payload specialist | Male; international crew |
| Emily Carter | Crew medical officer | Female; United States |
| Sofia Almeida | Life sciences specialist | Female; Brazil |
| Camila Santos | Mission scientist | Female; Brazil |

All six portraits are generated fictional people. Edit the roster, metric labels, sensor metadata and rule limits in **`hal2030/config.py`**. Keep crew IDs consistent with the recording, or regenerate the data after changing the generator.

## Replay and demonstration scenarios

The bundled `data/telemetry_10min.csv` contains **3,600 records: 600 seconds × six crew members**. Summaries are sampled once per second. Playback advances in real time by default, with Pause/Resume, Restart, 1×/5×/10× speed, a seek slider, Loop, and a scenario selector. It ends after ten minutes unless Loop is enabled. A 10× demonstration takes approximately one minute.

| Jump point | What to show |
|---|---|
| **00:00** | Nominal crew, different activities, all devices connected. |
| **00:40** | Anton: low oxygen saturation and increased breathing rate; red portrait and action card. |
| **02:00** | Itay: oximeter signal loss; amber state and missing saturation value. |
| **03:05** | Emily: exercise with expected higher heart/respiration rates; activity-aware rules keep her nominal. |
| **04:25** | Idan: elevated resting heart and respiratory rates; critical review. |
| **05:55** | Sofia: elevated skin-temperature trend; confirm with an appropriate clinical temperature measurement. |
| **07:15** | Camila: missing EEG signal; check the research headband. |
| **08:50** | Recovery; all six return to nominal. |

The scalar dataset includes heart rate, SpO₂, respiratory rate, skin temperature, systolic/diastolic blood pressure, HRV (RMSSD), relative EEG alpha/beta powers, motion index and wearable battery, with cabin CO₂ and air temperature as context. EEG powers and activity states are scenario features. Raw waveform strips are separate deterministic illustrations; they are not reconstructed physiological measurements from the 1 Hz CSV.

To regenerate the identical dataset with seed 2030:

```powershell
.\.venv\Scripts\python.exe tools/generate_telemetry.py
```

## Ground-link demonstration

1. Open **Mission control** and keep **Local demonstration · 3 s** selected.
2. Click **Send current telemetry**. A JSON packet is written immediately, enters the simulated link, and shows **Received · Sim.** after the selected delay.
3. Turn off **Ground link available** and send again. The next packet remains queued.
4. Restore the link; that same packet resumes. It is not duplicated.
5. Select **Mars scenario · 22 min** to illustrate delayed delivery. This is a configurable scenario, not a claim that Earth–Mars latency is always 22 minutes.

Latency runs on elapsed wall time, independently of replay speed or seeking. It continues while replay is paused. **Auto-send every 30 seconds** emits one packet per 30 seconds of active playback in wall-clock time; paused playback does not repeatedly send the same frame. Changing the selected delay applies to new packets. Pending packets retain their existing countdown. The queue and packet files are preserved between application launches in `runtime/downlink/`.

This build has **no NASA network endpoint**. Receipt is simulated locally. **Export snapshot** writes a real, inspectable JSON file. Health packets contain sensor summaries, activity, availability and alerts; companion messages are excluded.

## HAL2030 Voice Engine & Family Archive

- **Family Message Demo:** Compare original CREMA-D recordings with calibrated LivePortrait reconstructions that reuse one portrait. The demo includes a low-bitrate video benchmark and offline rendering commands. See the [demo and benchmark guide](docs/FAMILY_MESSAGE_DEMO.md).

- **Web Console (`server.py`):** Provides isolated six-crew companion sessions backed by real local CPU voice inference via `/api/hal/voice/status`, `/api/hal/voice/speak` (**Kokoro-82M INT8** WAV synthesis), and `/api/hal/voice/transcribe` (**Faster-Whisper tiny.en** speech-to-text). Crew health packets remain excluded from private companion chat, and family-archive replies are clearly labeled as simulations.
- **Legacy Desktop Prototype (`main.py`):** Retains simulated voice-state preview and offline Vosk vision-check recognition.

## Project layout

```text
space-health-monitor/
  server.py                     FastAPI web console entrypoint & APIs
  main.py                       Legacy PySide6 desktop prototype entrypoint
  requirements.txt              Web runtime dependencies
  requirements-desktop.txt      Desktop and local voice dependencies
  requirements-voice.txt        CPU voice dependencies (Kokoro-82M INT8 + Faster-Whisper)
  requirements-dev.txt          Optional test dependencies
  astra_core/
    hal_bridge.py               Telemetry bridge, crew vitals & alert rules
    radiation.py                ISS REM/DOSTEL orbital radiation & shielding model
    vitals.py                   Cardiovascular telemetry & PhysioNet dataset replay
    readiness.py                Station Readiness scoring & summary engine
    standards.py                IEC 60601-1-8 / NASA-STD-3001 alert & operational limits
  static/
    index.html                  Liquid Glass web dashboard markup
    styles.css                  Day/Night Liquid Glass styling & fluid layout transitions
    app.js                      Interactive web console, Web Audio chimes & voice client
    assets/                     Crew portraits & spacecraft body visualizations
  hal2030/
    config.py                   Crew, sensor metadata, metrics, demo limits
    paths.py                    Unified source & runtime path resolution
    voice_engine.py             Kokoro-82M INT8 TTS + Faster-Whisper tiny.en STT engine
    models.py                   Sample, Alert, and data-source protocol
    telemetry.py                CSV replay, generation, synthetic waveforms
    alerts.py                   Transparent predefined rules and actions
    downlink.py                 Durable local packet queue and simulated link
    ui/                         Legacy PySide6 desktop views
  data/
    telemetry_10min.csv         Complete ten-minute synthetic scenario recording
    iss_modules_rem_2024.csv    ISS REM module dose rates
    iss_dostel_orbital_2024_01_25.csv  Orbital DOSTEL radiation time-series
    physionet_bidmc/            PhysioNet BIDMC physiological dataset slices
    physionet_ptt/              PhysioNet pulse-transit-time dataset slices
    sources.json                Data & model provenance registry
  tools/
    download_voice_model.py     Atomic voice model downloader (natural / vosk)
    build_resources.py          Tracked resource verification for CI
    generate_telemetry.py       Reproducible telemetry dataset generator
  tests/                        Pytest suite (ASTRA-Core APIs, voice, radiation, vitals, desktop)
  docs/                         Architecture, schema, provenance, and demo guides
```

## Useful launch options

```powershell
# Open Anton's detail view at the oxygen event, paused.
.\.venv\Scripts\python.exe main.py --start-at 40 --page 1 --crew anton --paused

# Use another CSV with the same schema.
.\.venv\Scripts\python.exe main.py --data path\to\telemetry.csv

# Put runtime packets in a chosen folder.
.\.venv\Scripts\python.exe main.py --runtime-dir path\to\runtime
```

Page indices: `0` overview, `1` detail, `2` sensors, `3` mission control, `4` companion. Keyboard shortcuts: **Ctrl+1…5** switch views; **Ctrl+Space** pauses/resumes; arrow keys seek when the timeline has focus.

## Validation

GitHub Actions runs the core tests on Python 3.13 on Windows and Linux. These tests exercise synthetic replay and simulated downlink behavior; they do not validate medical decisions or physical sensors.

The supplied archive's validation notes report that the core was exercised with automated tests for dataset size and reproducibility, source immutability, absence of future observations, missing-signal gaps, waveform continuity, activity-aware alerts, recovery, queue persistence, offline/reconnect behavior, and JSON exports. GUI checks exercised all five pages, crew selection, recommendations, filtered sensor views, chat isolation, voice placeholders, playback controls and simulated packet delivery. Layout was inspected at 1540×1000 and 1280×720 using an offscreen Linux Qt session. **A native Windows execution was not available in the build environment.**

Run the optional core tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

For the data schema and exact rule settings, see [docs/DATA_AND_RULES.md](docs/DATA_AND_RULES.md). For the component boundaries and real-sensor integration path, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Source grounding and scope are in [docs/SOURCES.md](docs/SOURCES.md). A short presentation walkthrough is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

**Scope:** a demonstrable software prototype with rule-based decision support. The synthetic limits are not NASA medical criteria, and clinical actions require an appropriate crew medical protocol. Real sensors, real mission-control networking, raw physiological acquisition, local AI inference and speech engines remain integration work. NASA does not endorse this project.

## Project direction and collaboration

The original project overview and planned feature demos are preserved in [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md). They describe project direction; the implemented HAL2030 views are listed above.

Claim a feature in the [issue tracker](https://github.com/ItayBlank/space-health-monitor/issues) before starting. Work on one branch per issue, open a small PR, and write `Closes #N` in the PR description. Agree on a shared timeline with UTC timestamps and stable crew and module IDs. Keep observed, simulated, and estimated values labeled in the UI.

[Challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)

## Data and license

The [MIT License](LICENSE) covers this project's code and documentation. External
data and models retain their own licenses. Current telemetry is synthetic; the
Windows download bundles the Vosk English model. OpenNeuro ds004902 v1.0.8 has been
assessed for future PVT reference records but is **not imported into the app**.

- [Source registry](data/sources.json): versions, licenses, file hashes and usage status.
- [Third-party attribution](THIRD_PARTY_NOTICES.md): dataset/model authors and terms.
- [Provenance policy and PVT assessment](docs/DATA_PROVENANCE.md): coverage, limitations,
  and the distinction between measured results, dataset replay and synthetic data.

## CI maintenance contract

Every pull request (including drafts and fork PRs) runs the same tests and Windows
build against GitHub's proposed merge with `main`. Pushes to `main` build the merged
app. Manual runs are available. New pushes to a PR cancel its outdated run; feature
branch pushes do not duplicate the PR build. Existing PRs created before a CI change
may need their branch updated from `main` to adopt it.

CI installs the checked-out requirements, discovers tests with pytest, and asks the
packaged app to smoke-test every current navigation page. No page count, crew name,
or telemetry filename is hard-coded in the workflow or smoke runner. The build
includes all tracked files under `assets/` and `data/`, plus non-Python package
resources under `hal2030/`. Untracked downloads, runtime output and virtual
environments are excluded. Commit only distributable resources in those locations.

For ordinary features, add runtime dependencies to `requirements.txt` (or included
requirements files), put resources in those directories, and add behavioral tests.
Application submodules are collected even when imported dynamically. New dialogs
and hardware integrations still need feature-specific tests; navigation screenshots
do not exercise every interaction. Native dependencies, unusual dynamic imports,
external model downloads or additional distribution formats may need packaging
hooks or CI changes. An arbitrary future feature cannot be guaranteed to package
without any maintenance.

PR executable artifacts include the PR number and tested commit SHA. Smoke artifacts
include `manifest.json`, which lists the captured pages, alongside screenshots.
The existing read-only Actions permissions and secret-free build also apply to forks.
