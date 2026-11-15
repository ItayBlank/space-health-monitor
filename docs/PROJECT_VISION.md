# Web roadmap and implementation status

Reviewed against main after PRs #14, #15, and #18 on 2026-11-15. The active application
is the FastAPI web console (`server.py`, `astra_core/`, `static/`). The PySide6
application and its Windows executable remain available as a legacy prototype.
The feature guides below describe setup and verification scope.

| Feature / issue | Current status | Remaining work |
| --- | --- | --- |
| [#4 Guided near-vision](https://github.com/ItayBlank/space-health-monitor/issues/4) | Closed/completed; desktop implementation is merged and a calibrated web flow plus report APIs exist. | Keep browser calibration, microphone and report-parity testing separate from desktop verification. |
| [#2 Individual radiation exposure](https://github.com/ItayBlank/space-health-monitor/issues/2) | Partial: cabin schedules, module ratios, orbital profile, vessel-average comparison and scenario controls. | Reconcile the model with the original synchronized module-rate baseline; demonstrate two schedules and coverage/estimated labels. |
| [#3 CO2 and hatch events](https://github.com/ItayBlank/space-health-monitor/issues/3) | Partial: one cabin CO2 trace, a simulated hatch spike, and ventilation guidance. | Two module traces, hatch-event alignment, before/after comparison and simulated-event labels. |
| [#1 Combined vigilance/check-in proposal](https://github.com/ItayBlank/space-health-monitor/issues/1) | Superseded, not completed. | Replaced by the two independently scoped features below. |
| [#11 Private mood/stress check-ins](https://github.com/ItayBlank/space-health-monitor/issues/11) | Implemented in #14 with sign-in, owner history, an illustrative trend rule, and consent-based local consult requests. | Consult delivery is outside the [local demo](PRIVATE_CHECKINS.md). |
| [#12 Pre-task three-minute PVT](https://github.com/ItayBlank/space-health-monitor/issues/12) | Implemented in #15 with sleep and event logs, a timed check, and results against a personal baseline when available. | [Timing and thresholds](PVT.md) are illustrative. |
| [Family messages](FAMILY_MESSAGE_DEMO.md) | Implemented in #18. The simulated link sends audio and motion. The receiver rebuilds full-frame video from a preloaded portrait. | The app plays pre-rendered examples. |

## Demo boundaries

The Check-ins feature uses its own local account and keeps entries out of shared
readiness and routine downlink. Consult requests require explicit consent and
record only the entries the user selected.

The pre-task PVT shows **Sleep unknown** for missing, incomplete, or stale logs.
Its under-six-hour threshold and two-hour window support crew review. Only
completed three-minute sessions count toward the PVT history and personal baseline.

## Data and evidence

Fictional telemetry and research replay must remain distinguishable. The web
migration adds PhysioNet and radiation CSVs; their complete version/license/import
history still needs reconciliation with the existing registry. A file's presence
does not establish a live astronaut measurement or validated threshold.

OpenNeuro ds004902 is assessed, not imported into the running app. Its 30 complete
published summary pairs yield a mean paired median-RT increase of 41.2167 ms;
only 29 participants have both raw trial files. See [provenance](DATA_PROVENANCE.md).

[Source registry](../data/sources.json) · [Attribution](../THIRD_PARTY_NOTICES.md)
· [Contributing](../CONTRIBUTING.md) · [Evidence](SOURCES.md)
