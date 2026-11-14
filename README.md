# Space Health Monitor — HAL2030

A local Python desktop prototype for the **NASA Space Apps Challenge 2026: Create Health Monitoring Software for Astronauts on Space Missions**.

HAL2030 combines a live crew overview, individual telemetry, a sensor registry, a simulated ground link, and six private companion sessions. Its dark spacecraft-console design uses cyan signal traces, clear green/amber/red status indicators, fictional flight-suit portraits, and an original red optical lens inspired by classic science-fiction interfaces.

**Everything in the application is in English.** The supplied recording, people, events, and physiological signals are synthetic. After installing its dependencies, the application runs locally without an internet connection.

## Download the Windows executable

Open this repository's **Actions → Test and build**, select a successful run,
and download the **HAL2030-windows-x64-<commit>** artifact. Extract the ZIP and
launch `dist/HAL2030.exe`. GitHub requires sign-in to download workflow artifacts.
No Python installation is needed. Artifacts are retained for 14 days; builds run
on pushes and pull requests and can also be started with **Run workflow**.

The executable bundles the synthetic recording and portraits. It is unsigned,
and the first launch takes a few seconds to extract its dependencies. Packaged
runs preserve their outbox in `%LOCALAPPDATA%\HAL2030\runtime\downlink`;
`--runtime-dir` overrides that location. Source runs keep `runtime/downlink/`.

To build locally on Windows using the development environment below:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging/HAL2030.spec
.\.venv\Scripts\python.exe tools/smoke_executable.py dist/HAL2030.exe --output-dir build/smoke
```

CI runs the core tests before packaging and launches all five packaged pages
offscreen from a separate working directory. This is a startup/resource-loading
check, not a complete interactive Windows test.

## Quick start on Windows / VS Code

1. Clone this repository and open `space-health-monitor` in VS Code; this folder contains `main.py`.

   ```powershell
   git clone https://github.com/ItayBlank/space-health-monitor.git
   cd space-health-monitor
   ```
2. Use **64-bit Python 3.11–3.14**. Python 3.12 or 3.13 is a convenient choice.
3. Open a VS Code terminal and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

There is no need to activate the environment, so PowerShell execution-policy settings do not block these commands. The first dependency installation needs internet access; the app itself does not.

Alternatively, double-click **`start_windows.bat`**. It creates the local environment, installs missing packages, and launches the app. Subsequent launches use the installed packages.

For debugging, select the `.venv` interpreter with **Python: Select Interpreter**, then press **F5**. Included launch profiles open either the standard demonstration or Anton's oxygen-alert scenario. Install the VS Code Python extension if it is not already available.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

The `start_unix.sh` helper performs those steps when needed. A graphical desktop and Qt's platform dependencies are required. If a minimal Linux installation reports a missing `xcb` library, use the distribution's Qt/X11 runtime packages; Windows wheels include the required Qt libraries.

## The five views

| View | Implemented behavior |
|---|---|
| **Crew overview** | Six live cards; heart rate, oxygen saturation and respiration; 60-second sparklines; activity labels; status rings; crew/sensor counts; cabin context; recent events; manual snapshot sending. |
| **Crew detail** | Select a person, inspect additional values, view synthetic ECG/respiration/EEG strips and trailing trends, read the current recommendation cards, and open that person's companion session. |
| **Sensor network** | All 42 assignments with sensor name, owner, placement, state, current values, quality and latest observation. Filters select an astronaut or signal state. Double-click a sensor to open its owner's detail page. |
| **Mission control** | Manual or automatic health snapshots, a durable local JSON outbox, an offline-link switch, selectable delay, packet inspection, export, and simulated receipt. |
| **HAL2030** | Six separate conversations; scripted English replies; private per-person history; visual voice-chat preview; local-model setup placeholder; clearly labeled family-archive simulation. |

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

## HAL2030 and family archive

The companion has working navigation, isolated conversation histories, text entry, prepared responses, quick prompts and a visual voice-state animation. **Start voice demo** cycles through simulated listening, transcription and reply states; it does not access the microphone or produce speech.

**Connect local model** opens a setup preview for a local model path. No inference engine is installed. **Preview archive setup** offers a file-selection preview; selected archive contents are not read. Family mode always identifies its replies as a **simulation**, with fictional examples. It is not presented as a live call with a relative. Session histories remain in memory and clear when the application closes.

## Project layout

```text
space-health-monitor/
  main.py                       Entry point and command-line options
  requirements.txt              Runtime dependencies
  requirements-dev.txt          Optional test dependency
  start_windows.bat             Windows setup / launch helper
  start_unix.sh                 macOS / Linux setup / launch helper
  hal2030/
    config.py                   Crew, sensor metadata, metrics, demo limits
    models.py                   Sample, Alert, and data-source protocol
    telemetry.py                CSV replay, generation, synthetic waveforms
    alerts.py                   Transparent predefined rules and actions
    downlink.py                 Durable local packet queue and simulated link
    ui/
      window.py                 Navigation, replay clock, global alert banner
      theme.py                  Shared colors and styling
      widgets.py                Portraits, HAL lens, metrics, reusable panels
      dashboard.py              Crew overview and recommendation dialog
      detail.py                 Individual vitals, plots and guidance
      sensors.py                Sensor registry and filters
      mission_control.py        Link controls, queue and packet inspection
      companion.py              Per-crew chat and voice / AI placeholders
  assets/portraits/              Six generated PNG portraits
  data/telemetry_10min.csv       Complete ten-minute recording
  tools/generate_telemetry.py    Reproducible dataset generator
  tests/test_core.py             Core behavioral tests
  docs/                         Architecture, schema, sources, demo guide
  .vscode/                      Debug profiles and interpreter settings
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

Claim a feature in the [issue tracker](../../issues) before starting. Work on one branch per issue, open a small PR, and write `Closes #N` in the PR description. Agree on a shared timeline with UTC timestamps and stable crew and module IDs. Keep observed, simulated, and estimated values labeled in the UI.

[Challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)

## Data and license

The [MIT License](LICENSE) covers this project's code and documentation. Linked datasets retain their original terms. The demo uses public source data where available and labels simulated crew records.
