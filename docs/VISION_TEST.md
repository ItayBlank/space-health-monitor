# Self-administered near-vision demo

Open **Crew detail**, choose a crew member, and click **Start vision check**.
A separate window opens. Telemetry replay pauses, while the simulated downlink
continues. Closing the exam releases its microphone; replay stays paused.

## Setup

Record symptom/reason, correction worn, lighting and brightness. Measure the
horizontal and vertical bars with a physical ruler and adjust each until the
distance between its end ticks is **50 mm**. Confirm the tested eye is **40 cm**
from the screen, with a supported device, straight-on viewing and fixed screen
rotation. Both axes are calibrated independently. Changing displays, display
resolution, scaling or reported orientation invalidates an unfinished session.
Calibration is deliberately repeated for every new session.

Distance and head alignment are **user-confirmed**, not tracked. Recheck position
before each eye. If position changes during testing, use **Back** to restart that
eye with direction practice. The app cannot detect head motion or ambient light.

## Speech and controls

Qt TextToSpeech reads the visible instructions at a slow rate using an installed
English system voice. Narration can be disabled. If the system voice is unavailable,
text guidance remains usable. No LLM or cloud speech service is used.

The Windows artifact includes the English Vosk model beside `HAL2030.exe` in
`voice-model/`. Extract the entire ZIP and keep that folder beside the executable;
it is detected automatically, regardless of the working directory. No extra setup
or internet connection is needed. Click **Enable microphone** to start listening.

For source runs, install normal requirements (which include
`requirements-voice.txt`), then download the English Vosk model once:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/download_voice_model.py
```

The model is stored under `runtime/voice-model/` for source execution, next to the
downlink directory. Use **Model folder…** to select a model stored elsewhere.
Click **Enable microphone** in the fixed header; it stays visible without scrolling
through setup or during the test. Before testing, enable the microphone or explicitly
select **Use buttons instead of microphone**. The header light is red while the app
speaks, green only while commands are accepted, amber during startup/waiting or an
input error, and gray when the microphone is off. Text labels accompany every color. The app uses the operating system's default
input device; select the desired microphone in the OS before starting. The model
is [Vosk small English US 0.15](https://alphacephei.com/vosk/models), Apache 2.0.
Its files stay out of Git. CI downloads a checksum-pinned official archive and
ships the extracted model, original README, attribution and Apache 2.0 license
with the executable. Source installation/build downloads need internet; using
the bundled model does not. If the bundled folder is missing, setup falls back to
the runtime model path; **Model folder…** still allows a custom location.

Commands: **up, down, left, right, unable, continue, repeat, back, pause, resume**.
Buttons provide the same controls; arrow keys and Space work in the test panel.
Directions refer to screen edges, not the astronaut's body or gravity. Each eye
starts with four large labeled practice symbols; incorrect practice responses
receive correction and do not advance. Practice is never scored.

Each spoken answer is echoed. Say **continue** to confirm, or another direction
to correct it. Only the confirmed answer is scored. The recognizer ignores audio
while narration plays and for a short echo guard afterward; old recognition events
are discarded. Silence and unrecognized phrases never count as wrong answers.
Audio is neither recorded to disk nor transmitted. **Pause** suspends the exam;
**resume** returns to it. **Repeat** rereads the instruction. **Back** clears a
pending answer or restarts the current eye if no answer is pending.

## Geometry and stopping rules

The E is drawn on a five-by-five grid, with one-unit strokes and gaps. For distance
`d` in mm and nominal logMAR `L`, full size is
`2*d*tan(radians(5*10**L/60)/2)` mm. Nominal levels descend from 1.0 to 0.0 in 0.1
steps. Rendering rounds strokes to integer physical pixels, disables smoothing,
rejects strokes smaller than two physical pixels and rejects >10% axis distortion.
Duplicate rendered sizes are skipped. Every trial records the actual size and
angular logMAR on both axes, in addition to the nominal level.

The two-pixel floor and distortion bound are engineering limits, not validated
clinical tolerances. A typical laptop at 40 cm cannot render logMAR 0.0 accurately.
This single-optotype test is not equivalent to a crowded letter chart.

- Five independently randomized E directions per rendered size; at least four
  correct passes the level. Responses are untimed.
- A pass advances to the next smaller renderable level.
- The first failed level triggers five fresh symbols at the previous passing
  level. Passing that block gives a confirmed result; failing it gives an
  inconsistent result and an offer to repeat.
- Failure at the largest level is reported as outside the measurable range.
- Passing the smallest renderable level is reported as display-limited, not a
  measured acuity threshold. No smaller or unseen score is inferred.
- **Unable** is an explicitly confirmed unsuccessful response; speech recognition
  failures are not. Closing midway produces no complete report.

This is a bounded, illustrative demo protocol, not a validated clinical test.
The geometry follows the [five-unit E convention](https://aes.amegroups.org/article/view/6970/html).
The [NASA SANS brief](https://www.nasa.gov/wp-content/uploads/2024/02/ochmo-mtb-001-sans.pdf)
provides mission context, not validation of this implementation or stopping rule.

## Reports and repeat attempts

After both eyes, the summary shows results beside a **simulated preflight baseline**
of 0.00 logMAR per eye. Any numerical difference is descriptive only: the baseline
is not an actual matched measurement. Range-limited or inconsistent results are
explicitly identified. No diagnosis or medical alert is inferred.

**Repeat both eyes** retains the previous completed attempt and its conditions.
**Save and queue report** persists one JSON packet in the existing local outbox,
including symptom, correction, lighting, brightness, calibration/display signature,
UTC timestamps, practice, confirmed trials, both-eye results and the labeled
baseline. A stable report ID prevents duplicate queue entries. **Mission control →
Inspect selected packet** displays it. Transport is simulated; user-performed
responses are labeled separately from simulated baseline data.

Validation includes geometry, display limits, pass/fail/confirmation paths, both-eye
completion, display invalidation, stale voice events, repeated attempts and queue
restart/idempotency. Synthetic speech checks exercise decoding, not microphone,
accent, room-noise or human test-retest reliability. Those remain manual checks.
