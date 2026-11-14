HAL2030 Windows x64 demo

Extract the downloaded artifact ZIP, then open dist/HAL2030.exe.
Python is bundled; no Python installation or network connection is required.
The executable is unsigned. It is a hackathon prototype, not a signed installer.

Telemetry and portraits are bundled. All crew readings are synthetic.
Ground-link delivery is simulated locally, not transmitted to NASA.
Persistent outbox: %LOCALAPPDATA%\HAL2030\runtime\downlink
Optional override: HAL2030.exe --runtime-dir C:\path\to\runtime

The first launch can take several seconds while the one-file bundle extracts.
See the repository README for usage and the included LICENSE for project terms.
