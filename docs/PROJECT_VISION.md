# Web roadmap and implementation status

Reviewed against main after PRs #9 and #10 on 2026-11-14. The active application
is the FastAPI web console (`server.py`, `astra_core/`, `static/`). The PySide6
application and its Windows executable remain available as a legacy prototype.
This inventory is based on code inspection; it is not a new browser acceptance test.

| Feature / issue | Current status | Remaining work |
| --- | --- | --- |
| [#4 Guided near-vision](https://github.com/ItayBlank/space-health-monitor/issues/4) | Closed/completed; desktop implementation is merged and a calibrated web flow plus report APIs exist. | Keep browser calibration, microphone and report-parity testing separate from desktop verification. |
| [#2 Individual radiation exposure](https://github.com/ItayBlank/space-health-monitor/issues/2) | Partial: cabin schedules, module ratios, orbital profile, vessel-average comparison and scenario controls. | Reconcile the model with the original synchronized module-rate baseline; demonstrate two schedules and coverage/estimated labels. |
| [#3 CO2 and hatch events](https://github.com/ItayBlank/space-health-monitor/issues/3) | Open: cabin readings and ventilation guidance exist. | Two module traces, hatch-event alignment, before/after comparison and simulated-event labels. |
| [#1 Combined vigilance/check-in proposal](https://github.com/ItayBlank/space-health-monitor/issues/1) | Superseded, not completed. | Replaced by the two independently scoped features below. |
| [#11 Private mood/stress check-ins](https://github.com/ItayBlank/space-health-monitor/issues/11) | Planned. | Timestamped private history, personal baseline establishment, illustrative three-consecutive-check-in follow-up, dismissal and consent-based selected-entry sharing. |
| [#12 Pre-task three-minute PVT](https://github.com/ItayBlank/space-health-monitor/issues/12) | Planned; current web reaction demo is only five trials and reports a mean. | Sleep logs including naps, assigned critical events, two-hour window, <6 h sleep flag, completed-test suppression, median/lapses and same-protocol baseline. |

## Next feature boundaries

Private mood/stress entries belong to the crew member. Keep them out of shared
readiness cards and routine downlink unless explicitly selected for sharing.
Crew selection in a shared demo is not authenticated private storage. Define the
usual-range calculation and baseline establishment before implementing #11.

For #12, missing sleep logs must display **Sleep unknown**. The under-six-hour
and two-hour thresholds are illustrative. The planned result supports crew review;
it does not grant operational clearance. Do not count the existing five-trial
demo as a completed three-minute PVT or reuse its fixed cutoff as a personal baseline.
The issues contain the acceptance criteria and evidence links.

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
