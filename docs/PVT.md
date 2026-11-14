# Pre-task PVT prototype

## Rule and scope

For a crew member, show a recommendation only when all of these are true:

1. The next assigned critical event is still in the future and starts in
   `(now_utc, now_utc + 2 hours]`; equivalently,
   `event_utc - 2 hours <= now < event_utc`.
2. A complete, user-entered sleep snapshot was recorded in the preceding
   24 hours and its sleep intervals total less than 360 minutes in the rolling
   24-hour window.
3. No valid, completed measured session with protocol
   `pvt-b-180s-v1` is recorded in that event's current two-hour window.

The six-hour boundary reflects an observational association reported for ISS
astronauts; it is an issue-level prototype rule, not a medical or operational
readiness threshold. Missing, incomplete, or stale sleep logs produce
**Sleep unknown** and do not recommend a PVT.

Sleep data are interval logs entered by the user. A `complete` flag is an
assertion by the recorder that the sleep log is complete; the app does not
measure sleep or independently verify continuous coverage. The service saves
UTC intervals, unions overlaps, clips them to `now - 24 hours .. now`, and
retains the snapshot's UTC as-of time. A snapshot older than 24 hours is
unknown. The UI calls these logged intervals and shows their as-of time.

Event times are assigned per crew in UTC. The UI can assign or reschedule an
event; status is recalculated after each update. A completed PVT suppresses
another same-protocol prompt for any event whose two-hour window contains that
completion. The schedule is reevaluated after event rescheduling.

## PVT-B prototype protocol v1

- Duration: 180 seconds, measured by the browser monotonic clock
  (`performance.now()`) and checked by server UTC elapsed time.
- Stimulus: visual signal; randomized stimulus intervals are 2,000–5,000 ms.
  The final signal is scheduled no later than 178 seconds, leaving at least a
  two-second tail before completion.
- Response: touch/mouse button, Space, or Enter; no speech latency.
- An anticipatory response under 100 ms, an input outside an active stimulus,
  backgrounding the tab/window, leaving the Sensors pane, or explicit cancel
  invalidates the session.
- Unanswered signals are retained as null responses. The browser advances
  them after 1.9 seconds; the server counts each null as a lapse.
- The illustrative lapse rule is RT >= 500 ms. This is an explicitly chosen
  prototype boundary; the cited ds004902 paper describes a different
  `RT > 500 ms` convention. Neither definition is validated for this UI.
- The server accepts only a known session, its exact response count, bounded
  integer RT values (100–2,000 ms) or null, at least 180 seconds elapsed, and
  completion within a 30-second delivery grace period. Median RT and lapse
  count are calculated from raw responses on the server. Incomplete,
  interrupted, expired, or five-trial runs cannot qualify or suppress a
  recommendation.

This timing and visual protocol is a software demonstration. It has not been
validated against a certified PVT-B, flight hardware, or any operational
readiness decision. The browser reports response times; a modified client can
forge them. The server checks session identity, elapsed duration, trial count,
and value bounds, but does not authenticate physical input or prove that a human
performed the task. Do not use the output to clear or restrict anyone for duty.

## Baselines, records, and provenance

Sleep logs, assigned events, session starts, aborts, and completed records are
stored per stable crew ID in UTC JSON. By default, the file is
`runtime/pvt_records.json` (ignored by Git). The store uses an in-process lock
and atomic replacement, and supports a single server process only; it is not
safe for multiple worker processes. These records are shared by crew ID, are
not private or authenticated, and are intended only for a loopback or trusted
demo environment. Set `ASTRA_PVT_STORE` to an isolated path for tests or
disposable browser review.

Completed measured runs and synthetic demonstration scenarios are separate:
the three read-only scenarios (**Short sleep**, **Already tested**, **Missing
sleep log**) return `provenance: synthetic` and never write the store. They
cannot suppress a real prompt or contribute to a personal baseline. Only valid
same-protocol measured sessions can appear in the real record list.

A personal baseline is shown after at least three earlier valid measured runs
of this protocol. It contains median RT and median lapse count; the most recent
result is excluded from its own comparison. Research-cohort values are not
personal baselines.

OpenNeuro ds004902 v1.0.8 was assessed for exploratory example histories but
was not imported into the app. Its paired trial coverage is incomplete, file
headers vary, and its files lack stimulus onset/interval timing. See
[the ds004902 assessment](DATA_PROVENANCE.md#ds004902-assessment) and the
[record provenance contract](DATA_PROVENANCE.md#record-provenance-contract).
No research replay or synthetic demo can create measured records.

## Evidence and limits

- Jones et al., *Sleep deficiency in spaceflight is associated with degraded
  neurobehavioral functions and elevated stress in astronauts on six-month
  missions aboard the International Space Station* (2022), reported the
  observational sleep-duration association and assessed vigilant attention
  using PVT-B. [Publication](https://doi.org/10.1093/sleep/zsac006).
- Piechowski et al., *Effects of total sleep deprivation on performance in a
  manual spacecraft docking task* (2024), compared PVT and a docking simulation
  after sleep deprivation. This is relevant context, not validation of this
  prototype prompt or threshold. [Publication](https://doi.org/10.1038/s41526-024-00361-z).
- Xiang et al., *A Resting-state EEG Dataset for Sleep Deprivation*, OpenNeuro
  ds004902 v1.0.8. The assessed dataset supports only carefully labeled
  exploratory examples; it is not imported and does not define this protocol.
  [Version DOI](https://doi.org/10.18112/openneuro.ds004902.v1.0.8).

The studies are observational or research protocols and do not establish this
app's event window, sleep snapshot freshness, visual timing, lapse boundary,
or three-minute session as an astronaut fitness-for-duty tool.

## Manual review

1. Set `ASTRA_PVT_STORE` to a new disposable JSON path and launch the server.
2. In Sensors, select each of the three synthetic scenarios. Verify the banner
   and record provenance; these scenarios should not alter the real status.
3. In live records, choose a crew member, enter a complete sleep snapshot with
   one or more intervals, and assign a critical event in UTC/local time.
4. Verify no recommendation before the event window, a recommendation for
   short sleep inside it, **Sleep unknown** for missing/incomplete/stale logs,
   and suppression after a completed same-protocol run.
5. Run the measured task for its full 180 seconds. Try a false start, tab or
   window backgrounding, and navigating away; each run should be invalidated.
6. Reschedule the event and refresh. Eligibility should follow the new time.
7. Review the record list and personal baseline; no synthetic record should be
   present in measured history.

