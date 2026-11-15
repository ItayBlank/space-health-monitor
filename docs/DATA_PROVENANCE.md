# Data provenance

## Registry and attribution

`data/sources.json` is the machine-readable source registry. Each source has a
stable ID, kind, import/distribution status, authors, license, version when
applicable, original file URLs/checksums, transformations, and limitations.
`THIRD_PARTY_NOTICES.md` provides readable attribution. The root `LICENSE` remains
the project's MIT license and does not relicense external data or models.
The Windows ZIP includes the registry and notices beside the executable.

Register sources before importing them. Pin a released version/DOI, preserve
upstream citation/acknowledgement and license information, and hash original bytes
before parsing or normalizing line endings. An assessed candidate must remain
`assessed_not_imported` until an importer and explicit application use exist.
Keep large raw downloads outside Git. List the exact selected files, exclusions,
processing script and code revision for every derived asset. Regenerate hashes
when intentionally changing shipped assets; never silently update a source version.

## Record provenance contract

Future PVT importers and reports should embed a `provenance` object conforming to
`data/record-provenance.schema.json`. This is a contract for upcoming features;
existing reports have not been migrated by this documentation change.

- `kind`: `measured`, `dataset_replay`, `synthetic`, or `derived`.
- `source_id`: registry ID for external/generated records; measured records identify
  the application protocol instead. `protocol_id` and `protocol_version` describe
  live measurement independently of the source dataset's protocol.
- `upstream_subject_id`, `upstream_session_id`, and `source_file` identify a replay
  record. These IDs must not be presented as astronaut identities.
- `units`, `transformations`, and `created_at_utc` record how values are represented
  and produced. Derived records reference their `parent_record_ids`.

Use provenance per component: a measured result beside a synthetic baseline has
two origins. A research-cohort comparison is not a personal preflight baseline.
Live reaction times need the app's monotonic timing method and device/input context;
UTC timestamps describe records, not the reaction-time clock. Recorded cohort data
cannot validate our display/input timing or establish fitness for duty.

## ds004902 assessment

Inspected on 2026-11-14: OpenNeuro **ds004902 version 1.0.8**,
[DOI](https://doi.org/10.18112/openneuro.ds004902.v1.0.8).
The complete Git file tree was inspected, and all 67 small PVT TSVs plus README,
CHANGES, dataset description, and participant metadata were downloaded for audit.
No EEG was downloaded. Original-byte SHA-256 hashes and per-file headers/counts
are in `data/provenance/ds004902-1.0.8-audit.json`; raw records remain outside Git.

**Suitable for example PVT histories and exploratory cohort comparisons, subject
to explicit normalization. Not sufficient to define or validate our live test.**

Confirmed from actual versioned files:

- 71 rows in `participants.tsv`, but trial-level PVT files cover only **38 people**:
  **30 normal-sleep sessions**, **37 sleep-deprivation sessions**, and **29 paired people**.
- `ses-1` means normal sleep and `ses-2` sleep deprivation; these labels are not
  chronological order. Use `SessionOrder` to determine order.
- 67 behavioral TSV files contain trial indices and response values, with **45–95
  trials per file**. Most contain 45–51; sub-70 and sub-71 contain 90–95.
- Headers vary: 63 files use `trial,response_time`; exceptions use `response`
  (sub-01/ses-2), `trail` (sub-03/ses-2), `respones_time` (sub-12/ses-1), and
  `resoonse_time` (sub-19/ses-1). An importer needs explicit aliases and must reject
  unknown schemas. Preserve original names in provenance.
- Participant metadata has PVT lapse count, median RT, and RT standard deviation
  for 31 normal-sleep and 37 sleep-deprivation sessions. Summary coverage and trial
  file coverage differ; do not silently substitute one for the other.
- Sleep diaries, sleepiness scales, and a sleep-condition label are available.
  Time in bed is not measured sleep duration; PSQI component scores are not hours.
  There is no mission-event schedule.

The [publication](https://doi.org/10.1038/s41597-024-03268-2) describes RT in
milliseconds and defines lapses as **RT > 500 ms**. The TSVs themselves have no
unit sidecars; record this publication-based interpretation explicitly when
importing. Do not silently change the boundary to >=500 ms. Exact test duration,
stimulus timing, treatment of false starts/nonresponses, and equivalence to a
three-minute PVT-B have not been established from the inspected files. No stimulus
onset/interval columns are provided, so these files support response-series
examples, not exact stimulus-timeline replay.

Recommended next step: a separate importer that validates headers/values, preserves
missingness and condition labels, and compares derived summaries with published
summary columns before selecting a small reproducible subset. Do not convert this
cohort into astronaut norms or derive an operational sleep threshold from it.

## Published PVT summary-pair calculation

On 2026-11-14, `participants.tsv` from the pinned 1.0.8 release was rechecked.
Select rows where both `PVT_item2_NS` and `PVT_item2_SD` are numeric; compute each
row's `SD - NS`, then the arithmetic mean of those differences. This gives **30
pairs, +41.2166666667 ms** (rounded +41 ms). The median paired difference is 44 ms.
This is a difference between published session medians, not a pooled-trial mean,
not the median of all differences, and not a clinical effect threshold.
The original-byte hash of `participants.tsv` is in the audit manifest.

The raw-file audit remains correct at **29 complete trial-file pairs**. Published
summary coverage differs from raw-file coverage; preserve that distinction when
constructing the research replay for #12. No participant measurements were imported
into the app by this calculation.
