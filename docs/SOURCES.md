# Sources and interpretation

Reviewed on **14 November 2026**. These sources informed the monitoring categories and challenge framing. They did not supply the synthetic data, rule thresholds, astronaut identities, or an operational NASA API.

## Challenge

**NASA Space Apps Challenge 2026 — Create Health Monitoring Software for Astronauts on Space Missions**

https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/

The official challenge description asks for software that gathers health indicators and helps astronauts evaluate and act on their condition during long missions. It discusses isolation, altered gravity, radiation and the closed spacecraft environment. HAL2030 addresses the gathering/evaluation/action interface and demonstrates onboard independence and delayed communication. It does not claim to assess every long-duration spaceflight risk.

The challenge description was confirmed through the indexed official page. Direct fetching of the dynamic page intermittently returned an error in the build environment. No claim is made that every challenge resource or eligibility rule was inspected.

## Vital-sign selection

**Canadian Space Agency — Bio-Monitor: Keeping an eye on astronauts' vital signs**

https://www.csa-asc.gc.ca/eng/sciences/bio-monitor.asp

CSA describes a wearable ISS system for pulse/cardiac electrical activity, blood pressure, breathing rate and volume, skin temperature, oxygen saturation, and physical activity. These categories informed the scalar channels and device assignments. HAL2030's exact devices, sampling assumptions and data are fictional. A 1 Hz blood-pressure field is a demo convention, not a claim that an actual cuff produces a new measurement every second.

**NASA — Wearable Tech for Space Station Research, 13 November 2024**

https://www.nasa.gov/missions/station/iss-research/wearable-tech-for-space-station-research/

NASA describes wearable studies covering sleep, cardiovascular signals, breathing and temperature, including motion/light monitoring, sensor garments and temperature research. This informed the activity labels and separate temperature/sleep context in the interface.

## EEG and sleep research

**NASA — Science in Space: Week of Sept. 15, 2023 — Sleep on Station, 18 September 2023**

https://www.nasa.gov/humans-in-space/science-in-space-week-of-sept-15-2023-sleep-on-station/

NASA describes the Sleep In Orbit ear-EEG study and the Dreams EEG headband investigation. The EEG channel in HAL2030 is therefore framed as a research channel. Its alpha/beta percentages are synthetic scenario features, and the app does not derive a medical or emotional diagnosis from them.

**NASA — ISS Daily Summary Report, 19 September 2023**

https://www.nasa.gov/blogs/stationreport/2023/09/19/iss-daily-summary-report-9-19-2023/

The report describes wearable collection of single-lead ECG, heart rate, HRV, respiration and skin temperature, together with an ear-EEG sleep session. It supports the choice of complementary cardiorespiratory and neurophysiological research views.

## Boundaries of the evidence

- These are publicly described ISS research capabilities, not a public live feed of private astronaut medical telemetry.
- HAL2030's six people, 10-minute time series, cabin readings, activity labels, portraits and events are synthetic.
- No threshold in `DEMO_LIMITS` is represented as an official NASA or CSA medical rule.
- NASA research on these categories does not validate this prototype or establish that all listed devices continuously monitor every current astronaut.
- The family-archive concept and local AI connection UI are project ideas, not claims about an operational NASA service.
- The 22-minute communication setting is a selectable simulation. Actual propagation delay depends on mission geometry and network operation.

## Asset provenance

See `assets/ASSETS.md` for fictional portrait provenance. The HAL2030 lens and other interface instruments are drawn by project code. The supplied reference images inspired the requested visual direction; the project does not depend on externally hosted art at runtime.

## Web roadmap evidence (2026-11-14)

These sources support feature motivation, not operational validation or software
compliance. The earlier sections describe the original synthetic desktop scope;
the web migration also includes research CSVs whose source registry needs completion.

- [Private mood/stress issue #11](https://github.com/ItayBlank/space-health-monitor/issues/11):
  [OCHMO-STD-100.1A §6.6.2, supplied copy](https://ntrs.nasa.gov/api/citations/20240006194/downloads/OCHMO%20STD%20100%201A%2005142024.pdf)
  describes private psychological conferences addressing mood and performance.
  This copy contains placeholder approval dates; it is not evidence that this
  prototype meets a verified current operational standard.
  [Inspiration4, Extended Data Figure 10](https://www.nature.com/articles/s41586-024-07648-x)
  is the field-selection evidence supplied for mood/stress self-ratings.
  The three-check-in rule and baseline algorithm are prototype choices.
- [Pre-task PVT issue #12](https://github.com/ItayBlank/space-health-monitor/issues/12):
  [Jones et al. (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8919197/)
  links short sleep and poorer vigilant attention in 24 ISS astronauts.
  [Piechowski et al. (2024)](https://doi.org/10.1038/s41526-024-00361-z)
  relates sleep-loss vulnerability on PVT to simulated docking performance; its
  PVT was ten minutes. Neither establishes our browser timing or two-hour gate.
  [OpenNeuro ds004902 v1.0.8](https://openneuro.org/datasets/ds004902/versions/1.0.8)
  supplies research reference records, not a personal astronaut baseline.
  See [the reproducible summary calculation](DATA_PROVENANCE.md#published-pvt-summary-pair-calculation)
  for +41.2 ms across 30 summary pairs versus 29 raw-file pairs.
