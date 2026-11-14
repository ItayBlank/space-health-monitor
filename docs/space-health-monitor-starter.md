# Space Health Monitor

A 2026 NASA Space Apps Challenge prototype for crew health monitoring on long-duration missions. The demo follows a simulated crew through a mission timeline and shows how environmental readings and self-reports can lead to a concrete follow-up check.

## Features

| Feature | Demo |
| --- | --- |
| Mission-aware vigilance | Explain why a three-minute vigilance check is suggested after disrupted sleep or before a critical task. |
| Personal radiation exposure | Compare cumulative dose estimated from each astronaut's module schedule with a shared station-wide estimate. |
| Cabin CO₂ and mission events | Compare module readings around a hatch or ventilation event. |
| Guided near-vision exam | Record each eye's result under consistent conditions and queue the comparison with baseline for review. |

## Collaborating

Claim a feature in its issue before starting. Work on one branch per issue, open a small PR, and write `Closes #N` in the PR description. Agree on a shared timeline with UTC timestamps and stable crew and module IDs. Keep observed, simulated, and estimated values labeled in the UI.

[Challenge](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/)

## GitHub issue drafts

### 1. Build a mission-aware vigilance check

#### Goal

Use sleep, self-reported alertness, mood and mission context to recommend a three-minute Psychomotor Vigilance Task (PVT) when it would add information.

#### Demo acceptance

- [ ] Log a check-in against a simulated personal baseline.
- [ ] Following a simulated maneuver that extended duty and shortened sleep, explain why a PVT is recommended before a planned task.
- [ ] Show a routine or already-tested case that produces no duplicate prompt.
- [ ] Treat the prompt as a recommendation and keep demo thresholds labeled as illustrative.

OpenNeuro can test whether mood adds information about same-session lapses. The questionnaires followed the PVT. Later work can use HERA or ISS to evaluate a forward prediction.

[OpenNeuro ds004902](https://openneuro.org/datasets/ds004902/versions/1.0.8) · [HERA fatigue study](https://doi.org/10.1038/s41598-020-71929-4) · [ISS Reaction Self-Test](https://ntrs.nasa.gov/citations/20210022966)

[Open prefilled GitHub issue after the repo exists](https://github.com/ItayBlank/space-health-monitor/issues/new?title=Build%20a%20mission-aware%20vigilance%20check&body=%23%23%20Goal%0A%0AUse%20sleep%2C%20self-reported%20alertness%2C%20mood%20and%20mission%20context%20to%20recommend%20a%20three-minute%20Psychomotor%20Vigilance%20Task%20(PVT)%20when%20it%20would%20add%20information.%0A%0A%23%23%20Demo%20acceptance%0A%0A-%20%5B%20%5D%20Log%20a%20check-in%20against%20a%20simulated%20personal%20baseline.%0A-%20%5B%20%5D%20Following%20a%20simulated%20maneuver%20that%20extended%20duty%20and%20shortened%20sleep%2C%20explain%20why%20a%20PVT%20is%20recommended%20before%20a%20planned%20task.%0A-%20%5B%20%5D%20Show%20a%20routine%20or%20already-tested%20case%20that%20produces%20no%20duplicate%20prompt.%0A-%20%5B%20%5D%20Treat%20the%20prompt%20as%20a%20recommendation%20and%20keep%20demo%20thresholds%20labeled%20as%20illustrative.%0A%0AOpenNeuro%20can%20test%20whether%20mood%20adds%20information%20about%20same-session%20lapses.%20The%20questionnaires%20followed%20the%20PVT.%20Later%20work%20can%20use%20HERA%20or%20ISS%20to%20evaluate%20a%20forward%20prediction.%0A%0A%5BOpenNeuro%20ds004902%5D(https%3A%2F%2Fopenneuro.org%2Fdatasets%2Fds004902%2Fversions%2F1.0.8)%20%C2%B7%20%5BHERA%20fatigue%20study%5D(https%3A%2F%2Fdoi.org%2F10.1038%2Fs41598-020-71929-4)%20%C2%B7%20%5BISS%20Reaction%20Self-Test%5D(https%3A%2F%2Fntrs.nasa.gov%2Fcitations%2F20210022966))

### 2. Compare individual radiation exposure with a station-wide average

#### Goal

Estimate cumulative exposure from time spent in monitored modules and compare it with the same station-wide baseline for every astronaut.

#### Demo acceptance

- [ ] Replay a period with overlapping RadLab dose-rate measurements in at least two modules, or label any simulated module series.
- [ ] Show two simulated crew schedules and calculate dose as the sum of each module's rate times time spent there.
- [ ] Plot both individual estimates and a shared baseline computed as the mean across the monitored modules at each time step.
- [ ] Document units, time resolution and missing coverage. Label schedule-based dose as estimated.

[NASA RadLab](https://visualization.osdr.nasa.gov/radlab/gui/overview/) · [RadLab API](https://visualization.osdr.nasa.gov/radlab/gui/data-api/)

[Open prefilled GitHub issue after the repo exists](https://github.com/ItayBlank/space-health-monitor/issues/new?title=Compare%20individual%20radiation%20exposure%20with%20a%20station-wide%20average&body=%23%23%20Goal%0A%0AEstimate%20cumulative%20exposure%20from%20time%20spent%20in%20monitored%20modules%20and%20compare%20it%20with%20the%20same%20station-wide%20baseline%20for%20every%20astronaut.%0A%0A%23%23%20Demo%20acceptance%0A%0A-%20%5B%20%5D%20Replay%20a%20period%20with%20overlapping%20RadLab%20dose-rate%20measurements%20in%20at%20least%20two%20modules%2C%20or%20label%20any%20simulated%20module%20series.%0A-%20%5B%20%5D%20Show%20two%20simulated%20crew%20schedules%20and%20calculate%20dose%20as%20the%20sum%20of%20each%20module's%20rate%20times%20time%20spent%20there.%0A-%20%5B%20%5D%20Plot%20both%20individual%20estimates%20and%20a%20shared%20baseline%20computed%20as%20the%20mean%20across%20the%20monitored%20modules%20at%20each%20time%20step.%0A-%20%5B%20%5D%20Document%20units%2C%20time%20resolution%20and%20missing%20coverage.%20Label%20schedule-based%20dose%20as%20estimated.%0A%0A%5BNASA%20RadLab%5D(https%3A%2F%2Fvisualization.osdr.nasa.gov%2Fradlab%2Fgui%2Foverview%2F)%20%C2%B7%20%5BRadLab%20API%5D(https%3A%2F%2Fvisualization.osdr.nasa.gov%2Fradlab%2Fgui%2Fdata-api%2F))

### 3. Connect cabin CO₂ readings to hatch and ventilation events

#### Goal

Show how module CO₂ readings change around a hatch event, alongside ventilation status and crew occupancy where available.

#### Demo acceptance

- [ ] Plot two module traces on a common time axis and mark an example hatch event.
- [ ] Show before-and-after readings and a prompt to check ventilation in a scenario with a sustained rise.
- [ ] Label simulated traces and events. Show timing as an association.

Real ISS background telemetry is available. A synchronized public record covering both sides of a specific hatch event remains unverified.

[NASA Environmental Data App](https://visualization.osdr.nasa.gov/eda/) · [Example hatch-opening log](https://www.nasa.gov/blogs/spacestation/2019/03/03/spacex-crew-dragon-hatch-open/)

[Open prefilled GitHub issue after the repo exists](https://github.com/ItayBlank/space-health-monitor/issues/new?title=Connect%20cabin%20CO%E2%82%82%20readings%20to%20hatch%20and%20ventilation%20events&body=%23%23%20Goal%0A%0AShow%20how%20module%20CO%E2%82%82%20readings%20change%20around%20a%20hatch%20event%2C%20alongside%20ventilation%20status%20and%20crew%20occupancy%20where%20available.%0A%0A%23%23%20Demo%20acceptance%0A%0A-%20%5B%20%5D%20Plot%20two%20module%20traces%20on%20a%20common%20time%20axis%20and%20mark%20an%20example%20hatch%20event.%0A-%20%5B%20%5D%20Show%20before-and-after%20readings%20and%20a%20prompt%20to%20check%20ventilation%20in%20a%20scenario%20with%20a%20sustained%20rise.%0A-%20%5B%20%5D%20Label%20simulated%20traces%20and%20events.%20Show%20timing%20as%20an%20association.%0A%0AReal%20ISS%20background%20telemetry%20is%20available.%20A%20synchronized%20public%20record%20covering%20both%20sides%20of%20a%20specific%20hatch%20event%20remains%20unverified.%0A%0A%5BNASA%20Environmental%20Data%20App%5D(https%3A%2F%2Fvisualization.osdr.nasa.gov%2Feda%2F)%20%C2%B7%20%5BExample%20hatch-opening%20log%5D(https%3A%2F%2Fwww.nasa.gov%2Fblogs%2Fspacestation%2F2019%2F03%2F03%2Fspacex-crew-dragon-hatch-open%2F))

### 4. Build an offline guided near-vision exam

#### Goal

Turn a reported vision change into a consistent measurement and a reviewable handoff.

#### Demo acceptance

- [ ] Guide one eye at a time using a chart and controlled viewing distance. Record correction worn and the smallest line read.
- [ ] Compare each eye with a labeled simulated preflight baseline and offer a repeat check under the same conditions.
- [ ] Queue an offline report with the symptom, both results, baseline, timestamp and test conditions.
- [ ] Present it as a functional vision measurement for review.

[NASA SANS technical brief](https://www.nasa.gov/wp-content/uploads/2024/02/ochmo-mtb-001-sans.pdf)

[Open prefilled GitHub issue after the repo exists](https://github.com/ItayBlank/space-health-monitor/issues/new?title=Build%20an%20offline%20guided%20near-vision%20exam&body=%23%23%20Goal%0A%0ATurn%20a%20reported%20vision%20change%20into%20a%20consistent%20measurement%20and%20a%20reviewable%20handoff.%0A%0A%23%23%20Demo%20acceptance%0A%0A-%20%5B%20%5D%20Guide%20one%20eye%20at%20a%20time%20using%20a%20chart%20and%20controlled%20viewing%20distance.%20Record%20correction%20worn%20and%20the%20smallest%20line%20read.%0A-%20%5B%20%5D%20Compare%20each%20eye%20with%20a%20labeled%20simulated%20preflight%20baseline%20and%20offer%20a%20repeat%20check%20under%20the%20same%20conditions.%0A-%20%5B%20%5D%20Queue%20an%20offline%20report%20with%20the%20symptom%2C%20both%20results%2C%20baseline%2C%20timestamp%20and%20test%20conditions.%0A-%20%5B%20%5D%20Present%20it%20as%20a%20functional%20vision%20measurement%20for%20review.%0A%0A%5BNASA%20SANS%20technical%20brief%5D(https%3A%2F%2Fwww.nasa.gov%2Fwp-content%2Fuploads%2F2024%2F02%2Fochmo-mtb-001-sans.pdf))
