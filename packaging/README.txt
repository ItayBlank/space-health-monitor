HAL2030 Windows x64 demo

Extract the downloaded artifact ZIP, then open HAL2030.exe. Keep the voice-model folder beside it.
Python is bundled; no Python installation or network connection is required.
The executable is unsigned. It is a hackathon prototype, not a signed installer.

The offline English Vosk model is included and detected automatically.
In Crew detail, open Start vision check and click Enable microphone.
Allow microphone access if Windows prompts. No model download or selection is needed.
See THIRD_PARTY_NOTICES.md, SOURCES.json and Apache-2.0.txt for attribution and terms.
OpenNeuro is an assessed PVT source; its participant data is not included.

Telemetry and portraits are bundled. All crew readings are synthetic.
Ground-link delivery is simulated locally, not transmitted to NASA.
Persistent outbox: %LOCALAPPDATA%\HAL2030\runtime\downlink
Optional override: HAL2030.exe --runtime-dir C:\path\to\runtime

The first launch can take several seconds while the one-file bundle extracts.
See the repository README for usage and the included LICENSE for project terms.
