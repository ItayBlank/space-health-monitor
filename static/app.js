/* ASTRA-Core VisionOS Cabin Tablet UI (3-Level Progressive Disclosure) */
/* Grounded in NASA-STD-3001 / HIDH, Endsley SA Model, Cowan 4-Chunk Rule & EEMUA 191 */

const TIER_RANK = { critical: 3, warning: 2, nominal: 1 };
const TIER_META = {
  nominal: {
    pillShort: "✓ ALL GOOD",
    pillLong: "GREEN · ALL GOOD",
    heroTitle: "GREEN — ALL GOOD",
    stageClass: "state-nominal",
    popupClass: "popup-nominal",
    floatClass: "float-nominal",
    pillClass: "pill-nominal",
    cardClass: "card-nominal",
    glanceClass: "gc-nominal",
    notifClass: "nb-nominal",
    dotClass: "dot-nominal",
  },
  warning: {
    pillShort: "! INTERVENTION",
    pillLong: "ORANGE · INTERVENTION NEEDED",
    heroTitle: "ORANGE — INTERVENTION NEEDED",
    stageClass: "state-warning",
    popupClass: "popup-warning",
    floatClass: "float-warning",
    pillClass: "pill-warning",
    cardClass: "card-warning",
    glanceClass: "gc-warning",
    notifClass: "nb-warning",
    dotClass: "dot-warning",
  },
  critical: {
    pillShort: "⚠ IMMEDIATE",
    pillLong: "RED · IMMEDIATE INTERVENTION",
    heroTitle: "RED — IMMEDIATE INTERVENTION NEEDED",
    stageClass: "state-critical",
    popupClass: "popup-critical",
    floatClass: "float-critical",
    pillClass: "pill-critical",
    cardClass: "card-critical",
    glanceClass: "gc-critical",
    notifClass: "nb-critical",
    dotClass: "dot-critical",
  },
};

const CABIN_NAMES = {
  uslab: "Destiny US Lab",
  node3: "Node 3 (Tranquility)",
  columbus: "Columbus Lab",
  jpm: "Kibo (JPM)",
  node1: "Node 1 (Unity)",
  cupola: "Cupola Dome",
};

const ZONE_META = {
  head: { kicker: "01 · HEAD / SLEEP & COGNITION", label: "Head · Sleep" },
  lungs: { kicker: "02 · LUNGS / CABIN AIR & CO2", label: "Lungs · Air" },
  heart: { kicker: "03 · HEART / ECG & HRV VITALS", label: "Heart · Vitals" },
  torso: { kicker: "04 · TORSO / RADIATION SHIELD", label: "Torso · Radiation" },
  limbs: { kicker: "05 · LIMBS / STRENGTH & NUTRITION", label: "Limbs · Strength" },
};

const INITIAL_CREW_PROFILES = {
  anton: {
    id: "anton",
    name: "Anton",
    role: "Mission Commander",
    cabin: "Cupola Dome",
    avatar: "/static/assets/portraits/anton.png",
    recordId: "bidmc_12",
    atmoProfile: "iss_nominal",
    ppCo2: 2.2,
    priorCareerMsv: 165,
    cabinHours: { uslab: 4, node3: 6, columbus: 2, jpm: 2, node1: 3, cupola: 7 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
  },
  idan: {
    id: "idan",
    name: "Idan",
    role: "Systems & Avionics",
    cabin: "Columbus Lab",
    avatar: "/static/assets/portraits/idan.png",
    recordId: "ptt_s3_sit",
    atmoProfile: "iss_nominal",
    ppCo2: 1.9,
    priorCareerMsv: 118,
    cabinHours: { uslab: 5, node3: 7, columbus: 8, jpm: 2, node1: 2, cupola: 0 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
  },
  itay: {
    id: "itay",
    name: "Itay",
    role: "Flight Medical Officer",
    cabin: "Destiny US Lab",
    avatar: "/static/assets/portraits/itay.png",
    recordId: "ptt_s3_sit",
    atmoProfile: "iss_nominal",
    ppCo2: 1.9,
    priorCareerMsv: 96,
    cabinHours: { uslab: 11, node3: 8, columbus: 2, jpm: 2, node1: 1, cupola: 0 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
  },
  emily: {
    id: "emily",
    name: "Emily Carter",
    role: "EV & Robotics",
    cabin: "Node 3 (Tranquility)",
    avatar: "/static/assets/portraits/emily.png",
    recordId: "ptt_s3_sit",
    atmoProfile: "iss_nominal",
    ppCo2: 2.0,
    priorCareerMsv: 142,
    cabinHours: { uslab: 6, node3: 10, columbus: 3, jpm: 3, node1: 2, cupola: 0 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
  },
  sofia: {
    id: "sofia",
    name: "Sofia Almeida",
    role: "ECLSS Specialist",
    cabin: "Kibo (JPM)",
    avatar: "/static/assets/portraits/sofia.png",
    recordId: "ptt_s3_sit",
    atmoProfile: "iss_nominal",
    ppCo2: 2.1,
    priorCareerMsv: 110,
    cabinHours: { uslab: 4, node3: 8, columbus: 2, jpm: 8, node1: 2, cupola: 0 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
    sleepAlert: true,
  },
  camila: {
    id: "camila",
    name: "Camila Santos",
    role: "Payload & Neuro",
    cabin: "Node 1 (Unity)",
    avatar: "/static/assets/portraits/camila.png",
    recordId: "bidmc_19",
    atmoProfile: "iss_nominal",
    ppCo2: 2.0,
    priorCareerMsv: 130,
    cabinHours: { uslab: 4, node3: 7, columbus: 3, jpm: 2, node1: 7, cupola: 1 },
    resolved: { head: false, lungs: false, heart: false, torso: false, limbs: false },
  },
};

const state = {
  level: "glance", // "glance" | "body" | "cardio" | "engineer" | "sensors" | "downlink" | "companion"
  theme: "day", // "day" | "night"
  bodyMode: "simple", // "simple" | "map"
  cardioMode: "simple", // "simple" | "eng"
  radMode: "simple", // "simple" | "eng"
  sensorsMode: "quick", // "quick" | "depth"
  downlinkMode: "quick", // "quick" | "depth"
  activeCrewId: "anton",
  activeZone: "heart",
  stormOn: false,
  stormSheltered: false,
  cabinAirAlert: false,
  dosimeterOnline: true,
  missionDays: 30,
  previewActive: false,
  standards: null,
  remSummary: null,
  crewProfiles: structuredClone(INITIAL_CREW_PROFILES),
  crewSimCache: {}, // { [crewId]: { rad, vitals, readiness, zones, worstZone, overallTier, overallScore } }
  vitalsMemo: {},
  checkedSteps: {},
  // HAL2030 Integrated Telemetry Replay, Sensors, Downlink & Companion state
  halT: 40,
  halPlaying: false,
  halSpeed: 1,
  halTimerId: null,
  halFrame: null,
  halResolvedKeys: {},
  sensorFilter: { crew: "all", state: "all" },
  downlink: null,
  downlinkTimerId: null,
  selectedPacketId: null,
  pvt: {
    phase: "idle", // "idle" | "wait" | "go" | "done"
    trials: [],
    startTs: 0,
    timeoutId: null,
    lastMeanMs: null,
  },
  sans: {
    stage: "setup", // "setup" | "test" | "summary"
    phase: "practice", // "practice" | "eye"
    eye: "right", // "right" | "left"
    pxPerMmX: 4.0,
    pxPerMmY: 4.0,
    distanceMm: 400,
    levels: [],
    levelIdx: 0,
    confirming: false,
    batch: [],
    trials: [],
    practiceIdx: 0,
    practiceLog: [],
    direction: "right",
    pendingCmd: null,
    eyes: {},
    attempts: [],
    lastReport: null,
    calibration: null,
    narration: true,
  },
  voice: {
    status: "off", // "off" | "loading" | "listening" | "speaking"
    detail: "Checking Voice Engine…",
    ttsEngine: "browser-fallback",
    sttEngine: "browser-fallback",
    ttsReady: false,
    sttReady: false,
    recommendedVoice: "af_heart",
    lastSpeakSource: null, // "kokoro" | "browser"
    recorder: null,
    chunks: [],
    activeContext: "global", // "vision" | "companion" | "global"
    speakToken: 0,
    speakAbort: null,
    currentAudioUrl: null,
    audioUnlocked: false,
    pendingPlayText: null,
  },
  audioAlert: {
    enabled: true,
    speechEnabled: true, // "voice" (Chime+Red Speech) | false with enabled ("chime") | both false ("muted")
    ctx: null,
    prevTiers: {},
    prevAirFlag: false,
    prevCo2: null,
    seeded: false,
    lastPlayedAt: {},
    lastSpeechAt: 0,
    lastCrewSpokenAt: {},
    speechTimerId: null,
    speakingAlert: false,
  },
  comp: {
    crewId: "anton",
    familyMode: false,
    voiceTimerId: null,
    voiceStep: 0,
    histories: {
      anton: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Anton. Private cabin session active — excluded from downlink packets. Ask to review readings, unwind, or test Family Archive simulation." }],
      idan: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Idan. Private cabin session ready. Nothing here is shared with Mission Control." }],
      itay: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Itay. Private cabin session ready." }],
      emily: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Emily. Private cabin session ready." }],
      sofia: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Sofia. Private cabin session ready." }],
      camila: [{ speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Hello Camila. Private cabin session ready." }],
    },
  },
  sim: {
    open: false,
    playing: false,
    minutes: 0, // 0..1440 (24h orbital/transit day)
    stage: 0, // 0: 00:00 Calm, 1: 06:30 Air+Exercise, 2: 12:30 Heart+Air Alert, 3: 19:00 Recovered
    timerId: null,
    stepAntonPaused: false,
    busy: false,
  },
  charts: {
    heartMini: null,
    cardioWave: null,
    cardioTrend: null,
    halWave: null,
    co2Hatch: null,
    cumulative: null,
    remHistory: null,
  },
};

const $ = (id) => document.getElementById(id);

function chartThemeColors() {
  const night = state.theme === "night";
  return {
    tick: night ? "rgba(226, 232, 240, 0.72)" : "rgba(30, 41, 59, 0.74)",
    grid: night ? "rgba(255, 255, 255, 0.08)" : "rgba(15, 23, 42, 0.08)",
    legend: night ? "#e2e8f0" : "#1e293b",
  };
}

function tierFromStatus(statusStr) {
  const s = String(statusStr || "").toUpperCase();
  if (s === "CRITICAL" || s === "RED") return "critical";
  if (s === "WARNING" || s === "WATCH" || s === "ORANGE" || s === "YELLOW") return "warning";
  return "nominal";
}

function normalizePillarOverrides(profile) {
  const ov = {};
  if (profile.sleepAlert && !profile.resolved.head) {
    ov.sleep_vigilance = {
      status: "WARNING",
      score: 54,
      value: "5.2h · Slow focus",
      summary: "Sleep deficit affecting reaction speed in crew quarters.",
      crew_action: "Sleep 90m in shielded bay & dim cabin lights.",
      action: "Schedule 90-min recovery nap and dim displays.",
    };
  }
  if (state.cabinAirAlert) {
    ov.air_quality = {
      status: "WARNING",
      score: 52,
      value: "CO2 High · Scrubber Dip",
      summary: "Cabin air scrubber flow dropped across the habitat.",
      crew_action: "Check rack airflow & switch CDRA scrubber to HIGH.",
      action: "All 4 crew check airflow and switch CDRA scrubber to HIGH.",
    };
    if (!ov.sleep_vigilance) {
      ov.sleep_vigilance = {
        status: "WARNING",
        score: 62,
        value: "CO2 Fatigue",
        summary: "Stale cabin air causing mild head fatigue across all 4 crew.",
        crew_action: "Crew-wide O2/CO2 check & boost airflow.",
        action: "Clear cabin CO2 pocket and hydrate after airflow stabilizes.",
      };
    }
  } else if (profile.airAlert && !profile.resolved.lungs) {
    ov.air_quality = {
      status: "WARNING",
      score: 62,
      value: `ppCO2 ${profile.ppCo2.toFixed(1)} mmHg`,
      summary: "Elevated cabin CO2 pocket near Columbus rack bay.",
      crew_action: "Verify portable fan airflow + switch station scrubbers to HIGH.",
      action: "Run auxiliary fan purge in Columbus Bay 2.",
    };
  }
  if (profile.limbsAlert && !profile.resolved.limbs) {
    ov.exercise_nutrition = {
      status: "WARNING",
      score: 66,
      value: "ARED skipped · 1.2L water",
      summary: "Hydration & bone-load countermeasure overdue today.",
      crew_action: "Drink 500 mL electrolytes + complete 20m ARED squats.",
      action: "Replenish electrolytes and log shortened ARED session.",
    };
  }
  return ov;
}

function buildCrewZoneModels(profile, rad, vitals, readiness) {
  const ew = vitals.early_warning || {};
  const m = vitals.summary_metrics || {};
  const simpleRad = rad.simple_summary || {};
  const recMove = simpleRad.recommended_action || {};
  const pillars = readiness.pillars || {};

  // 1. HEAD (Sleep & Cognition)
  const sleepP = pillars.sleep_vigilance || {};
  const headTier = tierFromStatus(sleepP.status);
  const head = {
    tier: headTier,
    shortTag: sleepP.value || "7.4h",
    floatBadge: headTier === "nominal" ? "HEAD · ALL GOOD" : "HEAD · FATIGUE",
    floatText: sleepP.value || "Rested",
    headline:
      headTier === "nominal"
        ? "Alert & well rested"
        : state.cabinAirAlert && !(profile.sleepAlert && !profile.resolved.head)
        ? "CO2-linked head fatigue"
        : "Sleep deficit detected",
    summary: sleepP.summary || "Circadian alertness and reaction times are nominal.",
    actionTitle:
      headTier === "nominal"
        ? "Maintain 21:30 UTC sleep block"
        : sleepP.crew_action || "Take a 90-minute recovery nap now",
    actionDetail:
      headTier === "nominal"
        ? "Keep cabin dim before rest to protect REM recovery."
        : "Reduces micro-error risk on console & robotics tasks (no Earth wait needed).",
    glanceAction:
      headTier === "nominal"
        ? "Rested"
        : state.cabinAirAlert && !(profile.sleepAlert && !profile.resolved.head)
        ? "Crew-wide O2/CO2 check"
        : "Sleep 90m",
    applyLabel: headTier === "nominal" ? "Sleep Logged ✓" : "Start 90m Recovery Nap",
    canApply: headTier !== "nominal" && !(state.cabinAirAlert && !(profile.sleepAlert && !profile.resolved.head)),
    previewText:
      headTier !== "nominal" && !(state.cabinAirAlert && !(profile.sleepAlert && !profile.resolved.head))
        ? "Logging 90m nap restores Head Readiness to 88/100."
        : "",
  };

  // 2. LUNGS (Air & CO2)
  const airP = pillars.air_quality || {};
  const lungsTier = tierFromStatus(airP.status);
  const co2Val = state.cabinAirAlert
    ? Math.max(profile.ppCo2, 3.6)
    : profile.resolved.lungs
    ? 1.8
    : profile.ppCo2;
  const lungs = {
    tier: lungsTier,
    shortTag: `${co2Val.toFixed(1)} mmHg`,
    floatBadge: lungsTier === "nominal" ? "LUNGS · CLEAN AIR" : "LUNGS · CO2 HIGH",
    floatText: `CO2 ${co2Val.toFixed(1)} mmHg`,
    headline:
      lungsTier === "nominal"
        ? "Cabin air clean & oxygen nominal"
        : state.cabinAirAlert
        ? "Crew-wide cabin O2/CO2 scrubber alert"
        : "Cabin CO2 buildup nearby",
    summary: airP.summary || "O2 21.1% and CO2 scrubber flow within safe habitat limits.",
    actionTitle:
      lungsTier === "nominal"
        ? "Airflow balanced"
        : airP.crew_action || "Turn on rack ventilation fan + check scrubber",
    actionDetail:
      lungsTier === "nominal"
        ? "No scrubber adjustment required."
        : "Rapidly clears stagnant CO2 across habitat in 12 minutes.",
    glanceAction:
      lungsTier === "nominal"
        ? "Air clean"
        : state.cabinAirAlert
        ? "Crew-wide O2/CO2 check"
        : "Check cabin airflow",
    applyLabel: lungsTier === "nominal" ? "Ventilation OK ✓" : "Boost Scrubber & Fan",
    canApply: lungsTier !== "nominal",
    previewText: lungsTier !== "nominal" ? "Drops cabin ppCO2 to 1.8 mmHg within 12 minutes." : "",
  };

  // 3. HEART (PhysioNet ECG+PPG Vitals)
  const cardioTier = tierFromStatus(ew.status);
  const sigs = ew.signals || [];
  const topSig = sigs[0];
  const meanHr = Math.round(m.mean_hr_bpm || 68);
  const rmssd = Math.round(m.rmssd_ms || 38);
  const spo2 = (m.spo2_min_pct || 97).toFixed(0);
  const heart = {
    tier: cardioTier,
    shortTag: `${meanHr} bpm`,
    floatBadge:
      cardioTier === "critical"
        ? "HEART · URGENT"
        : cardioTier === "warning"
        ? "HEART · WATCH"
        : "HEART · STEADY",
    floatText: `${meanHr} bpm · SpO2 ${spo2}%`,
    headline:
      cardioTier === "critical"
        ? "Immediate cardiac strain alert"
        : cardioTier === "warning"
        ? "Low recovery — pace physical load"
        : "Heart rhythm & oxygen steady",
    summary: topSig
      ? `${topSig.metric}: ${topSig.value} (${topSig.mechanism})`
      : `Pulse ${meanHr} bpm, Blood Oxygen ${spo2}% — all within safe limits.`,
    actionTitle:
      cardioTier === "nominal"
        ? "Continue nominal physical activity"
        : cardioTier === "critical"
        ? "Stop heavy work, drink 500 mL electrolytes & rest 30m"
        : "Switch to light duty, hydrate & pace workload",
    actionDetail:
      cardioTier === "nominal"
        ? "Continuous pulse & oxygen telemetry stays clear."
        : "Pause EVA/heavy work, rest seated in Destiny core, and drink 500 mL electrolytes (no Earth wait needed).",
    glanceAction:
      cardioTier === "nominal" ? "Heart steady" : "Rest & hydrate",
    applyLabel:
      cardioTier === "nominal"
        ? "Cardio Cleared ✓"
        : cardioTier === "critical"
        ? "Stop Work & Rest Now"
        : "Log Light Duty & Fluids",
    canApply: cardioTier !== "nominal",
    previewText:
      cardioTier !== "nominal"
        ? "Seated rest + 500 mL electrolytes stabilizes pulse toward ~68 bpm."
        : "",
  };

  // 4. TORSO (Radiation & Module Shielding)
  const radTier = tierFromStatus(rad.status);
  const doseStr = `${rad.daily_cabin_msv.toFixed(2)} mSv/d`;
  const torso = {
    tier: radTier,
    shortTag: doseStr,
    floatBadge:
      radTier === "critical"
        ? "TORSO · SHELTER NOW"
        : radTier === "warning"
        ? "TORSO · HIGH FLUX"
        : "TORSO · SAFE SHIELD",
    floatText: doseStr,
    headline: simpleRad.verdict_headline || "Orbital radiation status",
    summary: simpleRad.culprit_text || simpleRad.verdict_detail || "Daily radiation rate tracked.",
    actionTitle: recMove.action_title || "Stay in Destiny / Node 3 core",
    actionDetail: recMove.action_detail || "Current shielding minimizes daily exposure.",
    glanceAction:
      radTier === "critical"
        ? "Move to core shelter"
        : radTier === "warning"
        ? "Shift to shielded core"
        : recMove.can_improve
        ? "Move to Destiny Core"
        : "Well shielded",
    applyLabel: recMove.can_improve ? "Move & Log Shelter Now" : "Optimal Shelter ✓",
    canApply: Boolean(recMove.can_improve),
    canPreview: Boolean(recMove.can_improve),
    previewText: recMove.can_improve
      ? `Moves ${recMove.hours_to_move}h to Destiny Lab -> drops daily dose to ${recMove.preview_daily_msv.toFixed(3)} mSv/d (−${recMove.dose_reduction_pct}%).`
      : "",
  };

  // 5. LIMBS (Strength & Hydration)
  const exP = pillars.exercise_nutrition || {};
  const limbsTier = tierFromStatus(exP.status);
  const limbs = {
    tier: limbsTier,
    shortTag: limbsTier === "nominal" ? "ARED ✓" : "HYDRATE",
    floatBadge: limbsTier === "nominal" ? "LIMBS · STRONG" : "LIMBS · DUE",
    floatText: exP.value || "Nominal",
    headline: limbsTier === "nominal" ? "Muscle & hydration on track" : "Workout & hydration overdue",
    summary: exP.summary || "Bone loading & fluid balance meet daily protocol.",
    actionTitle:
      limbsTier === "nominal"
        ? "Maintain evening meal + fluids"
        : exP.crew_action || "Drink 500 mL electrolytes + 20m ARED squats",
    actionDetail:
      limbsTier === "nominal"
        ? "Prevents fluid shift & muscle loss."
        : "Restores hydration & strength before next shift.",
    glanceAction: limbsTier === "nominal" ? "Strength OK" : "Exercise more",
    applyLabel: limbsTier === "nominal" ? "Logged ✓" : "Log Fluids & ARED",
    canApply: limbsTier !== "nominal",
    previewText: limbsTier !== "nominal" ? "Clears dehydration risk within 20 minutes." : "",
  };

  const zones = { head, lungs, heart, torso, limbs };

  // Overlay HAL2030 replay scenario signals (activity awareness, no_signal honesty, skin temp / SpO2 alerts)
  const halSample = state.halFrame?.samples?.[profile.id] || null;
  const halAlerts = (state.halFrame?.alerts || []).filter(
    (a) => a.crew_id === profile.id && !state.halResolvedKeys[a.key]
  );
  let missingChannels = 0;

  if (halSample && !state.sim.open) {
    const sStat = halSample.sensor_status || {};
    const hVals = halSample.values || {};
    missingChannels = Object.values(sStat).filter((v) => v === "no_signal").length;

    // Reset HAL alert resolved tracking when seeking to a different timestamp
    if (state._lastHalResolveT !== Math.floor(state.halT)) {
      if (Math.abs((state._lastHalResolveT ?? state.halT) - state.halT) > 15) {
        state.halResolvedKeys = {};
      }
      state._lastHalResolveT = Math.floor(state.halT);
    }

    // Missing oximeter -> honest unknown SpO2 on Heart & Lungs (never fake nominal!)
    if (sStat.oximeter === "no_signal") {
      const oxiAlert = halAlerts.find((a) => a.sensor_id === "oximeter");
      heart.tier = TIER_RANK[heart.tier] < 2 ? "warning" : heart.tier;
      heart.shortTag = "NO SIGNAL";
      heart.floatBadge = "OXIMETER · NO SIGNAL";
      heart.floatText = "SpO2 — (Signal Lost)";
      heart.headline = oxiAlert?.title || "Pulse oximeter signal lost";
      heart.summary = oxiAlert?.recommendation || "Check finger/forehead strap. Missing data is never filled with a normal guess.";
      heart.actionTitle = oxiAlert?.steps?.[0] || "Check sensor contact & cable seat";
      heart.actionDetail = (oxiAlert?.steps || []).slice(1).join(" · ") || "Confirm with alternate device.";
      heart.glanceAction = "Check oximeter (No signal)";
    }

    // Missing EEG -> honest unknown focus on Head
    if (sStat.eeg === "no_signal") {
      const eegAlert = halAlerts.find((a) => a.sensor_id === "eeg");
      head.tier = TIER_RANK[head.tier] < 2 ? "warning" : head.tier;
      head.shortTag = "NO SIGNAL";
      head.floatBadge = "HEAD · EEG LOST";
      head.floatText = "EEG — (Signal Lost)";
      head.headline = eegAlert?.title || "EEG headband signal lost";
      head.summary = eegAlert?.recommendation || "EEG channel reports no signal. Check headband dry-electrode contact.";
      head.actionTitle = eegAlert?.steps?.[0] || "Reposition headband & check fit";
      head.actionDetail = (eegAlert?.steps || []).slice(1).join(" · ") || "Resume monitoring once streaming.";
      head.glanceAction = "EEG signal lost";
    }

    // HAL physiological alerts (Anton low SpO2, Idan elevated resting HR/Resp, Sofia elevated skin temp)
    for (const ha of halAlerts) {
      if (ha.metric === "spo2" || ha.metric === "heart_rate" || ha.metric === "resp_rate") {
        const zTarget = ha.metric === "spo2" || ha.metric === "resp_rate" ? lungs : heart;
        if (TIER_RANK[ha.severity] >= TIER_RANK[zTarget.tier]) {
          zTarget.tier = ha.severity;
          zTarget.headline = ha.title;
          zTarget.summary = ha.recommendation;
          zTarget.actionTitle = ha.steps?.[0] || zTarget.actionTitle;
          zTarget.actionDetail = (ha.steps || []).slice(1).join(" · ") || zTarget.actionDetail;
          zTarget.glanceAction = ha.title;
          if (ha.metric === "spo2" && hVals.spo2 != null) {
            zTarget.floatBadge = ha.severity === "critical" ? "LUNGS · O2 LOW" : "LUNGS · O2 WATCH";
            zTarget.floatText = `SpO2 ${Number(hVals.spo2).toFixed(0)}% · Resp ${Number(hVals.resp_rate || 0).toFixed(0)}`;
          }
        }
      } else if (ha.metric === "skin_temp") {
        if (TIER_RANK[ha.severity] >= TIER_RANK[limbs.tier]) {
          limbs.tier = ha.severity;
          limbs.floatBadge = "TEMP · ELEVATED";
          limbs.floatText = `${Number(hVals.skin_temp || 37.3).toFixed(1)} °C`;
          limbs.headline = ha.title;
          limbs.summary = ha.recommendation;
          limbs.actionTitle = ha.steps?.[0] || "Measure core oral/tympanic temperature";
          limbs.actionDetail = (ha.steps || []).slice(1).join(" · ") || "Check activity/clothing before treating.";
          limbs.glanceAction = "Confirm skin temp";
          limbs.canApply = true;
          limbs.applyLabel = "Log Core Temp Check";
        }
      }
    }

    // Starter-guide PVT check result impact on Head zone
    if (profile.id === state.activeCrewId && state.pvt.lastMeanMs && state.pvt.lastMeanMs >= 330) {
      head.tier = "warning";
      head.floatBadge = "HEAD · PVT SLOW";
      head.floatText = `PVT ${Math.round(state.pvt.lastMeanMs)} ms`;
      head.headline = `Reaction check slowed (${Math.round(state.pvt.lastMeanMs)} ms)`;
      head.actionTitle = "Schedule 90m rest before critical ops";
      head.glanceAction = "Slow PVT reaction";
      head.canApply = true;
    }
  }

  // Compute worst zone & overall astronaut tier strictly from the 5 live zones
  let worstZone = "torso";
  let overallTier = "nominal";
  for (const zk of ["heart", "torso", "lungs", "head", "limbs"]) {
    if (TIER_RANK[zones[zk].tier] > TIER_RANK[overallTier]) {
      overallTier = zones[zk].tier;
      worstZone = zk;
    } else if (
      overallTier === "nominal" &&
      zk === "torso" &&
      rad.simple_summary?.recommended_action?.can_improve
    ) {
      worstZone = "torso";
    }
  }

  // Synthesize intuitive 0-100 crew score anchored by backend readiness & cardio
  const backendScore = readiness.overall_score || 85;
  const cardioScore = Math.round(ew.cardio_score ?? 90);
  let overallScore = Math.round(backendScore * 0.55 + cardioScore * 0.45);
  if (overallTier === "critical") overallScore = Math.min(overallScore, 44);
  else if (overallTier === "warning") overallScore = Math.min(Math.max(overallScore, 55), 76);

  // Pick concise 1-line action-first notification for Level 1 Glance Card (Cowan <= 4 chunk rule!)
  const worstObj = zones[worstZone];
  const glanceNote =
    overallTier === "nominal"
      ? halSample?.activity === "Exercise"
        ? "Exercising · Expected load"
        : "All systems green"
      : worstObj.glanceAction || worstObj.actionTitle;

  const halVals = halSample?.values || {};
  const halSStat = halSample?.sensor_status || {};
  const displayHr =
    halSample && !state.sim.open
      ? halSStat.ecg === "no_signal" || halVals.heart_rate == null
        ? null
        : Math.round(halVals.heart_rate)
      : meanHr;
  const displaySpo2 =
    halSample && !state.sim.open
      ? halSStat.oximeter === "no_signal" || halVals.spo2 == null
        ? null
        : Number(halVals.spo2)
      : Number(spo2);

  return {
    zones,
    worstZone,
    overallTier,
    overallScore,
    glanceNote,
    meanHr: displayHr,
    spo2Val: displaySpo2,
    activity: halSample?.activity || "Working",
    missingChannels,
    dailyMsv: rad.daily_cabin_msv,
    halAlerts,
  };
}

async function simulateCrewMember(crewId) {
  const profile = state.crewProfiles[crewId];
  const pillarOverrides = normalizePillarOverrides(profile);
  const effectivePpCo2 = state.cabinAirAlert
    ? Math.max(Number(profile.ppCo2 || 1.9), 3.6)
    : Number(profile.ppCo2 || 1.9);
  const vitKey = `${profile.recordId}|${profile.atmoProfile}|${effectivePpCo2.toFixed(1)}`;

  const radPromise = fetch("/api/radiation/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cabin_hours: profile.cabinHours,
      mission_days: state.missionDays,
      prior_career_msv: profile.priorCareerMsv,
      solar_storm_active: state.stormOn,
      personal_dosimeter_online: state.dosimeterOnline,
      pillar_overrides: pillarOverrides,
    }),
  }).then((r) => r.json());

  const vitPromise = state.vitalsMemo[vitKey]
    ? Promise.resolve({ vitals: state.vitalsMemo[vitKey] })
    : fetch("/api/vitals/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          record_id: profile.recordId,
          atmosphere_profile: profile.atmoProfile,
          cabin_ppco2_mmhg: effectivePpCo2,
        }),
      })
        .then((r) => r.json())
        .then((d) => {
          state.vitalsMemo[vitKey] = d.vitals;
          return d;
        });

  const [radResp, vitResp] = await Promise.all([radPromise, vitPromise]);

  const rad = radResp.radiation;
  const readiness = radResp.readiness;
  const vitals = vitResp.vitals;
  const model = buildCrewZoneModels(profile, rad, vitals, readiness);

  state.crewSimCache[crewId] = {
    profile,
    rad,
    vitals,
    readiness,
    ...model,
  };
  return state.crewSimCache[crewId];
}

async function refreshAllCrew() {
  await Promise.all(
    Object.keys(state.crewProfiles).map((id) => simulateCrewMember(id))
  );
  renderAll();
}

function getSortedCrewList() {
  return Object.values(state.crewSimCache).sort((a, b) => {
    const diff = TIER_RANK[b.overallTier] - TIER_RANK[a.overallTier];
    if (diff !== 0) return diff;
    return a.overallScore - b.overallScore;
  });
}

/* ==================== RENDER: SHELL & NAVIGATION ==================== */
function setBodyMode(mode) {
  state.bodyMode = mode === "map" ? "map" : "simple";
  state.previewActive = false;
  $("body-mode-simple")?.classList.toggle("active", state.bodyMode === "simple");
  $("body-mode-map")?.classList.toggle("active", state.bodyMode === "map");
  $("crew-simple-pane")?.classList.toggle("hidden", state.bodyMode !== "simple");
  $("body-split-grid")?.classList.toggle("hidden", state.bodyMode !== "map");
  if (state.level === "body") {
    const active = state.crewSimCache[state.activeCrewId];
    const crewLabel = active ? active.profile.name : "Crew";
    $("win-main-title").textContent =
      state.bodyMode === "simple"
        ? `${crewLabel} · Crew Action Checklist`
        : `${crewLabel} · Body Action HUD`;
    $("win-main-sub").textContent =
      state.bodyMode === "simple"
        ? `${active?.profile.cabin || "Habitat"} · Everything this crew member needs to do right now (no Earth wait)`
        : `${active?.profile.cabin || "Habitat"} · Tap any body marker to inspect & act`;
    renderLevel2Body();
  }
}

function _flipSpring(el, before, easing = "cubic-bezier(0.32, 1.36, 0.56, 1)", duration = 520) {
  if (!el || !before || typeof el.animate !== "function") return;
  const after = el.getBoundingClientRect();
  const dx = before.left - after.left;
  const dy = before.top - after.top;
  if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return;
  el.getAnimations().forEach((a) => {
    if (a.id === "astra-flip") a.cancel();
  });
  const anim = el.animate(
    [
      { transform: `translate3d(${dx}px, ${dy}px, 0)` },
      { transform: "translate3d(0, 0, 0)" },
    ],
    { duration, easing, fill: "none" }
  );
  anim.id = "astra-flip";
}

function setLevel(newLevel) {
  const prevLevel = state.level;
  const switching = prevLevel !== newLevel;
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;

  const railEl = document.querySelector(".vision-rail");
  const winEl = $("glass-window");
  const ctrlEl = document.querySelector(".win-right-controls");
  const titleEl = $("win-title-group") || document.querySelector(".win-title-group");

  const railBefore = switching && !reduceMotion ? railEl?.getBoundingClientRect() : null;
  const winBefore = switching && !reduceMotion ? winEl?.getBoundingClientRect() : null;
  const ctrlBefore = switching && !reduceMotion ? ctrlEl?.getBoundingClientRect() : null;
  const titleBefore = switching && !reduceMotion ? titleEl?.getBoundingClientRect() : null;

  state.level = newLevel;
  state.previewActive = false;

  const viewMap = {
    glance: "view-glance",
    checkins: "view-checkins",
    body: "view-simple",
    cardio: "view-cardio",
    engineer: "view-engineer",
    sensors: "view-sensors",
    biosense: "view-biosense",
    medhub: "view-medhub",
    downlink: "view-downlink",
    companion: "view-companion",
  };
  const railMap = {
    glance: "rail-glance",
    checkins: "rail-checkins",
    body: "rail-body",
    cardio: "rail-cardio",
    engineer: "rail-engineer",
    sensors: "rail-sensors",
    biosense: "rail-biosense",
    medhub: "rail-medhub",
    downlink: "rail-downlink",
    companion: "rail-companion",
  };

  Object.entries(viewMap).forEach(([k, id]) => $(id)?.classList.toggle("hidden", newLevel !== k));
  Object.entries(railMap).forEach(([k, id]) => $(id)?.classList.toggle("active", newLevel === k));

  document.body.classList.toggle("glance-active", newLevel === "glance");
  winEl?.classList.toggle("glance-layout-active", newLevel === "glance");
  document.dispatchEvent(new CustomEvent("astra-level-change", { detail: { level: newLevel } }));
  $("btn-back-glance").classList.toggle("hidden", newLevel === "glance");

  if (switching && !reduceMotion) {
    _flipSpring(railEl, railBefore, "cubic-bezier(0.32, 1.38, 0.56, 1)", 520);
    _flipSpring(winEl, winBefore, "cubic-bezier(0.32, 1.36, 0.56, 1)", 540);
    _flipSpring(titleEl, titleBefore, "cubic-bezier(0.32, 1.32, 0.56, 1)", 480);
    _flipSpring(ctrlEl, ctrlBefore, "cubic-bezier(0.30, 1.40, 0.54, 1)", 560);

    const entering = $(viewMap[newLevel]);
    if (entering && typeof entering.animate === "function") {
      entering.animate(
        [
          { opacity: 0.25, transform: "translate3d(0, 12px, 0) scale(0.986)" },
          { opacity: 1, transform: "translate3d(0, 0, 0) scale(1)" },
        ],
        { duration: 420, easing: "cubic-bezier(0.28, 1.32, 0.48, 1)" }
      );
    }
  }

  const active = state.crewSimCache[state.activeCrewId];
  const crewLabel = active ? active.profile.name : "Crew";

  if (newLevel === "checkins") {
    $("win-main-title").textContent = "My Private Check-ins";
    $("win-main-sub").textContent = "Owner-only mood and perceived stress history";
  } else if (newLevel === "glance") {
    $("win-main-title").textContent = "ASTRA · HAL2030 Crew Glance";
    $("win-main-sub").textContent = `Mars-Transit Tablet · Day ${String(state.missionDays).padStart(3, "0")} · 6-Crew Local Autonomous Telemetry`;
  } else if (newLevel === "body") {
    $("win-main-title").textContent =
      state.bodyMode === "simple"
        ? `${crewLabel} · Crew Action Checklist`
        : `${crewLabel} · Body Action HUD`;
    $("win-main-sub").textContent =
      state.bodyMode === "simple"
        ? `${active?.profile.cabin || "Habitat"} · Everything this crew member needs to do right now (no Earth wait)`
        : `${active?.profile.cabin || "Habitat"} · Tap any body marker to inspect & act`;
  } else if (newLevel === "cardio") {
    $("win-main-title").textContent = `${crewLabel} · Heart & Multi-Channel Waveforms`;
    $("win-main-sub").textContent =
      state.cardioMode === "simple"
        ? "Crew Action guidance · Clear everyday steps (no Earth wait needed)"
        : "PhysioNet 250 Hz DSP + HAL2030 ECG/Resp/EEG traces (missing signals left blank)";
  } else if (newLevel === "engineer") {
    $("win-main-title").textContent = `${crewLabel} · Radiation & Shielding`;
    $("win-main-sub").textContent =
      state.radMode === "simple"
        ? "Crew Action shielding plan · Safest modules & immediate moves"
        : "ISS RadLab 24h module simulator & NASA-STD-3001 career limits";
  } else if (newLevel === "sensors") {
    $("win-main-title").textContent = "Wearable Sensor Network & Field Checks";
    $("win-main-sub").textContent = "42 crew wearable channels · 3-Min PVT Check · Near-Vision SANS · CO2 Hatch Trace";
  } else if (newLevel === "biosense") {
    $("win-main-title").textContent = "Bio-Sense Lab · Contactless Sleep, ARED & Facial CV";
    $("win-main-sub").textContent = "Quadrature Sleep Radar / ESP32 CSI · ARED Pose Biomechanics · Passive Facial rPPG";
  } else if (newLevel === "medhub") {
    $("win-main-title").textContent = "ISS Unified MedHub · Pre-Symptomatic Intelligence";
    $("win-main-sub").textContent = "6 Medical Silos Fused · NASA OSDR (OSD-569/575) & CCMC DONKI Grounded";
  } else if (newLevel === "downlink") {
    $("win-main-title").textContent = "Mission Control Earth-Mars Downlink";
    $("win-main-sub").textContent = "Store-and-forward local JSON queue · Null preserved on missing signals · Chats excluded";
  } else if (newLevel === "companion") {
    $("win-main-title").textContent = "HAL2030 Private Cabin Companion";
    $("win-main-sub").textContent = "Scripted onboard support & clearly marked Family Archive simulation (local only)";
  }

  renderCurrentLevel();
}

function setTheme(newTheme) {
  state.theme = newTheme;
  document.body.classList.toggle("theme-day", newTheme === "day");
  document.body.classList.toggle("theme-night", newTheme === "night");
  $("theme-day").classList.toggle("active", newTheme === "day");
  $("theme-night").classList.toggle("active", newTheme === "night");
  $("rail-theme-lbl").textContent = newTheme === "day" ? "Day" : "Night";
  renderCurrentLevel();
}

function renderCrewWideBanner() {
  const banner = $("crew-wide-banner");
  const badge = $("cwb-badge");
  const title = $("cwb-title");
  const detail = $("cwb-detail");
  const actionBtn = $("cwb-action-btn");
  if (!banner) return;

  const showStorm = state.stormOn && !state.stormSheltered;
  const showAir = state.cabinAirAlert;

  if (!showStorm && !showAir) {
    banner.classList.add("hidden");
    banner.classList.remove("cwb-critical");
    return;
  }

  banner.classList.remove("hidden");
  if (showStorm && showAir) {
    banner.classList.add("cwb-critical");
    badge.className = "triage-pill pill-critical";
    badge.textContent = "CREW-WIDE CRITICAL ALERT";
    title.textContent = "Solar Storm + Cabin O2/CO2 Scrubber Alert · 20-min Earth delay";
    detail.textContent = "Radiation spiking & cabin air stale — All 6 crew move to Destiny Core shelter, check airflow & switch CDRA to HIGH.";
    actionBtn.textContent = "Shelter All + Boost Scrubber";
  } else if (showStorm) {
    banner.classList.add("cwb-critical");
    badge.className = "triage-pill pill-critical";
    badge.textContent = "CREW-WIDE STORM SHELTER";
    title.textContent = "Solar Radiation Spike · 20-min Earth delay: All 6 crew move to Shielded Core";
    detail.textContent = "Outside radiation is surging. Leave outer/windowed bays (Cupola, Columbus, Node 1) now and shelter inside Destiny Core or water-wall racks.";
    actionBtn.textContent = "Move All Crew to Core Shelter";
  } else {
    banner.classList.remove("cwb-critical");
    badge.className = "triage-pill pill-warning";
    badge.textContent = "CREW-WIDE HABITAT ALERT";
    title.textContent = "CREW-WIDE HABITAT ALERT · 20-min Earth delay: Cabin O2/CO2 scrubber alert";
    detail.textContent = "All 6 crew check airflow & switch CDRA to HIGH (no Earth wait needed).";
    actionBtn.textContent = "Switch Scrubber to HIGH (All Crew)";
  }
}

async function resolveCabinAirAlertAllCrew() {
  state.cabinAirAlert = false;
  Object.values(state.crewProfiles).forEach((profile) => {
    profile.airAlert = false;
    profile.resolved.lungs = true;
    profile.ppCo2 = 1.8;
  });
  await refreshAllCrew();
}

async function resolveStormShelterAllCrew() {
  const coreHours = { uslab: 16, node3: 8, columbus: 0, jpm: 0, node1: 0, cupola: 0 };
  Object.values(state.crewProfiles).forEach((profile) => {
    profile.cabinHours = { ...coreHours };
    profile.cabin = CABIN_NAMES.uslab;
  });
  state.stormSheltered = true;
  await refreshAllCrew();
}

async function resolveCrewWideAlert() {
  const resolveAir = state.cabinAirAlert;
  const resolveStorm = state.stormOn && !state.stormSheltered;
  if (resolveAir) {
    state.cabinAirAlert = false;
    Object.values(state.crewProfiles).forEach((profile) => {
      profile.airAlert = false;
      profile.resolved.lungs = true;
      profile.ppCo2 = 1.8;
    });
  }
  if (resolveStorm) {
    const coreHours = { uslab: 16, node3: 8, columbus: 0, jpm: 0, node1: 0, cupola: 0 };
    Object.values(state.crewProfiles).forEach((profile) => {
      profile.cabinHours = { ...coreHours };
      profile.cabin = CABIN_NAMES.uslab;
    });
    state.stormSheltered = true;
  }
  await refreshAllCrew();
}

function renderShellHeader() {
  const active = state.crewSimCache[state.activeCrewId];
  if (active) {
    $("header-avatar-img").src = active.profile.avatar;
    $("header-avatar-dot").className = `avatar-dot ${TIER_META[active.overallTier].dotClass}`;
  }

  const all = Object.values(state.crewSimCache);
  const urgentCount = all.filter((c) => c.overallTier !== "nominal").length;
  $("notif-count-badge").textContent = String(urgentCount);

  const atmoChip = $("top-btn-atmo");
  if (atmoChip) {
    atmoChip.textContent = state.cabinAirAlert ? "⚠ Cabin Air: HIGH CO2" : "Cabin Air: OK";
    atmoChip.classList.toggle("atmo-alert", state.cabinAirAlert);
  }

  const stormChip = $("top-btn-storm");
  stormChip.textContent = state.stormOn ? "Storm: ACTIVE" : "Storm: OFF";
  stormChip.classList.toggle("storm-on", state.stormOn);
  $("rail-storm").classList.toggle("active", state.stormOn);

  const dosChip = $("top-btn-dosimeter");
  dosChip.textContent = state.dosimeterOnline ? "Dosimeter: ON" : "Dosimeter: OFF";
  dosChip.classList.toggle("dos-offline", !state.dosimeterOnline);

  // Reflect worst station state gently in body class
  const anyCrit = all.some((c) => c.overallTier === "critical");
  const anyWarn = all.some((c) => c.overallTier === "warning");
  document.body.classList.remove("state-nominal", "state-warning", "state-critical");
  document.body.classList.add(anyCrit ? "state-critical" : anyWarn ? "state-warning" : "state-nominal");

  renderCrewWideBanner();
}

function renderHalReplayBar() {
  const sec = Math.floor(state.halT);
  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  if ($("hal-clock")) $("hal-clock").textContent = `T+${mm}:${ss} / 09:59`;
  if ($("hal-scrubber")) {
    const scrub = $("hal-scrubber");
    scrub.value = String(sec);
    syncRangeTrack(scrub);
  }
  if ($("hal-play-btn")) $("hal-play-btn").textContent = state.halPlaying ? "⏸ Pause" : "▶ Replay";
  if ($("hal-speed-btn")) $("hal-speed-btn").textContent = `${state.halSpeed}×`;

  const sample = state.halFrame?.samples?.[state.activeCrewId];
  const co2Ppm = sample?.cabin_co2;
  const co2Pill = $("hal-co2-pill");
  if (co2Pill) {
    const val = co2Ppm != null ? `${Math.round(co2Ppm)} ppm` : "-- ppm";
    co2Pill.textContent = state.cabinAirAlert ? `CO2: HIGH (${val})` : `CO2: ${val}`;
    co2Pill.classList.toggle("co2-warn", Boolean(state.cabinAirAlert || (co2Ppm != null && co2Ppm > 1200)));
  }

  const dlBtn = $("hal-quick-downlink");
  if (dlBtn && state.downlink) {
    const pending = (state.downlink.queued_count || 0) + (state.downlink.in_transit_count || 0);
    dlBtn.textContent = pending ? `📡 Downlink (${pending})` : "📡 Send Packet";
  }
}

/* ==================== RENDER: LEVEL 1 GLANCE ==================== */
function renderLevel1Glance() {
  renderHalReplayBar();
  const sorted = getSortedCrewList();
  if (!sorted.length) return;

  // 1. Render 6 Team Crew Cards (Cowan <= 4 visual chunks per card, real portraits & activity)
  const grid = $("crew-glance-grid");
  grid.innerHTML = sorted
    .map((c) => {
      const tm = TIER_META[c.overallTier];
      const hrTxt = c.meanHr == null ? "—" : `${c.meanHr} bpm`;
      const o2Txt = c.spo2Val == null ? "NO SIGNAL" : `${c.spo2Val.toFixed(0)}%`;
      const isEx = c.activity === "Exercise";
      return `
        <button class="glance-card ${tm.glanceClass}" data-crew="${c.profile.id}" type="button">
          <div class="gc-top">
            <div class="gc-avatar-wrap">
              <img src="${c.profile.avatar}" alt="${c.profile.name}" />
              <span class="avatar-dot ${tm.dotClass}"></span>
            </div>
            <div class="gc-score-pill">${c.overallScore}<small>/100</small></div>
          </div>
          <div class="gc-name-row">
            <div>
              <div class="gc-name">${c.profile.name}</div>
              <div class="gc-cabin">${c.profile.cabin}</div>
            </div>
            <span class="gc-activity-pill ${isEx ? "act-exercise" : ""}">${c.activity}</span>
          </div>
          <span class="gc-status-pill ${tm.pillClass}">${tm.pillShort}</span>
          <div class="gc-note">${c.glanceNote}</div>
          <div class="gc-mini-metrics">
            <span>♥ ${hrTxt}</span>
            <span class="${c.spo2Val == null ? "gc-missing-badge" : ""}">O2 ${o2Txt}</span>
            <span>☢ ${c.dailyMsv.toFixed(2)} mSv</span>
          </div>
        </button>
      `;
    })
    .join("");

  grid.querySelectorAll(".glance-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cid = btn.dataset.crew;
      const crew = state.crewSimCache[cid];
      state.activeCrewId = cid;
      state.activeZone = crew ? crew.worstZone : "torso";
      state.bodyMode = "simple";
      setLevel("body");
    });
  });

  // 2. Render Priority-Ordered Notification Feed (EEMUA 191 deduplication for habitat-wide alerts)
  const notifList = $("notif-list");
  const showStormBanner = state.stormOn && !state.stormSheltered;
  const habitatRows = [];

  if (showStormBanner && state.cabinAirAlert) {
    habitatRows.push(`
      <button class="notif-row" data-habitat-action="both" type="button">
        <span class="notif-row-dot dot-critical"></span>
        <span class="notif-row-text"><strong>ALL 6 CREW · Habitat</strong>: Solar storm + CO2 scrubber alert — Move to core &amp; CDRA HIGH</span>
        <span class="notif-badge-pill nb-critical">⚠ IMMEDIATE</span>
      </button>
    `);
  } else if (showStormBanner) {
    habitatRows.push(`
      <button class="notif-row" data-habitat-action="storm" type="button">
        <span class="notif-row-dot dot-critical"></span>
        <span class="notif-row-text"><strong>ALL 6 CREW · Solar Storm</strong>: Move all 6 crew to Destiny Core shelter</span>
        <span class="notif-badge-pill nb-critical">⚠ IMMEDIATE</span>
      </button>
    `);
  } else if (state.cabinAirAlert) {
    habitatRows.push(`
      <button class="notif-row" data-habitat-action="air" type="button">
        <span class="notif-row-dot dot-warning"></span>
        <span class="notif-row-text"><strong>ALL 6 CREW · Cabin Air</strong>: Crew-wide O2/CO2 check — Switch CDRA to HIGH</span>
        <span class="notif-badge-pill nb-warning">! INTERVENTION</span>
      </button>
    `);
  }

  const crewRows = sorted
    .filter((c) => {
      if (!state.cabinAirAlert && !showStormBanner) return true;
      // Avoid 4 duplicate habitat rows; keep crew who have a separate personal issue (e.g. heart/head/limbs)
      const isOnlySharedAir =
        state.cabinAirAlert &&
        (c.worstZone === "lungs" || (c.worstZone === "head" && !(c.profile.sleepAlert && !c.profile.resolved.head)));
      const isOnlySharedStorm = showStormBanner && c.worstZone === "torso";
      return !isOnlySharedAir && !isOnlySharedStorm;
    })
    .map((c) => {
      const tm = TIER_META[c.overallTier];
      const zLabel = ZONE_META[c.worstZone].label;
      return `
        <button class="notif-row" data-crew="${c.profile.id}" data-zone="${c.worstZone}" type="button">
          <span class="notif-row-dot ${tm.dotClass}"></span>
          <span class="notif-row-text"><strong>${c.profile.name}</strong> · ${zLabel}: ${c.glanceNote}</span>
          <span class="notif-badge-pill ${tm.notifClass}">${tm.pillShort}</span>
        </button>
      `;
    });

  notifList.innerHTML = [...habitatRows, ...crewRows].join("");

  notifList.querySelectorAll(".notif-row").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.habitatAction) {
        const targetZone = btn.dataset.habitatAction === "air" ? "lungs" : "torso";
        state.activeZone = targetZone;
        if (targetZone === "torso") {
          setLevel("engineer");
        } else {
          state.bodyMode = "simple";
          setLevel("body");
        }
        return;
      }
      state.activeCrewId = btn.dataset.crew;
      state.activeZone = btn.dataset.zone;
      state.bodyMode = "simple";
      setLevel("body");
    });
  });

  const nonNom = sorted.filter((c) => c.overallTier !== "nominal").length;
  $("notif-summary-tag").textContent = nonNom ? `${nonNom} active · Tap to intervene` : "All quiet · Nominal";

  // 3. Render Station Readiness Donut
  const avg = Math.round(sorted.reduce((acc, c) => acc + c.overallScore, 0) / sorted.length);
  const circum = 251.2;
  const arc = $("station-donut-arc");
  arc.style.strokeDashoffset = String(circum * (1 - avg / 100));
  arc.style.stroke = avg >= 80 ? "#10b981" : avg >= 60 ? "#f97316" : "#ef4444";
  $("station-avg-score").textContent = `${avg}%`;

  const nomCount = sorted.filter((c) => c.overallTier === "nominal").length;
  const warnCount = sorted.filter((c) => c.overallTier === "warning").length;
  const critCount = sorted.filter((c) => c.overallTier === "critical").length;
  $("ov-nom-count").textContent = `${nomCount} All Good`;
  $("ov-warn-count").textContent = `${warnCount} Attention`;
  $("ov-crit-count").textContent = `${critCount} Urgent`;

  // Expanded Station Readiness sub-telemetry
  const stPill = $("ov-station-pill");
  if (stPill) {
    if (critCount > 0 || state.cabinAirAlert || state.stormOn) {
      stPill.className = "triage-pill pill-critical";
      stPill.textContent = "CREW PRIORITY";
    } else if (warnCount > 0) {
      stPill.className = "triage-pill pill-warning";
      stPill.textContent = "ELEVATED WATCH";
    } else {
      stPill.className = "triage-pill pill-nominal";
      stPill.textContent = "NOMINAL · SYNCED";
    }
  }

  const co2Ppm = state.halFrame?.cabin?.co2_ppm;
  const cabinTemp = state.halFrame?.cabin?.temp_c;
  if ($("ov-cabin-val")) {
    const co2Str = state.cabinAirAlert
      ? "CO2 Spike"
      : co2Ppm != null
      ? `${Math.round(co2Ppm)} ppm`
      : "Nominal";
    const tempStr = cabinTemp != null ? `${Number(cabinTemp).toFixed(1)} °C` : "22.0 °C";
    $("ov-cabin-val").textContent = `${co2Str} · ${tempStr}`;
  }

  const avgDose =
    sorted.reduce((acc, c) => acc + (c.rad?.daily_cabin_msv ?? 0.44), 0) / Math.max(1, sorted.length);
  if ($("ov-rad-val")) {
    $("ov-rad-val").textContent = `${avgDose.toFixed(2)} mSv · ${state.stormOn ? "STORM" : "Calm"}`;
  }

  const sRows = state.halFrame?.sensor_matrix || [];
  const onlineCnt = sRows.length ? sRows.filter((r) => r.link_state === "online").length : 42;
  if ($("ov-sensors-val")) {
    $("ov-sensors-val").textContent = `${onlineCnt} / 42 Online`;
  }

  const lowest = [...sorted].sort((a, b) => a.overallScore - b.overallScore)[0];
  state._lowestCrewId = lowest?.profile?.id || sorted[0]?.profile?.id || "anton";
  state._lowestZone = lowest?.worstZone || "heart";
  if ($("ov-priority-note") && lowest) {
    const label = lowest.profile.name;
    if (lowest.overallTier === "nominal") {
      $("ov-priority-note").textContent = "All 6 crew nominal · Station life-support & sensors steady.";
    } else {
      const zMeta = lowest.zones?.[lowest.worstZone];
      $("ov-priority-note").textContent = `Lowest readiness: ${label} (${Math.round(lowest.overallScore)}/100) · ${zMeta?.headline || "Review priority action"}.`;
    }
  }
}

const escText = (s) =>
  String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

function halMatchesZone(zk, alertObj) {
  if (!alertObj) return false;
  if (zk === "lungs") return alertObj.metric === "spo2" || alertObj.metric === "resp_rate";
  if (zk === "heart") return alertObj.metric === "heart_rate" || alertObj.sensor_id === "oximeter";
  if (zk === "head") return alertObj.sensor_id === "eeg";
  if (zk === "limbs") return alertObj.metric === "skin_temp";
  return false;
}

function buildZoneActionSteps(zk, zone, matchingHal) {
  const fromHal = [];
  for (const ha of matchingHal) {
    for (const s of ha.steps || []) {
      if (s && !fromHal.includes(s)) fromHal.push(s);
    }
  }
  if (fromHal.length >= 2) return fromHal.slice(0, 4);

  if (zk === "heart") {
    return zone.tier === "critical"
      ? [
          "Stop heavy work or EVA tasks right now",
          "Drink 500 mL electrolytes & water",
          "Take 30 min seated rest in core (no Earth wait needed)",
        ]
      : [
          zone.actionTitle || "Switch to light duty & pace workload",
          "Drink 500 mL electrolytes & water",
          "Recheck resting pulse after 20 min",
        ];
  }
  if (zk === "lungs") {
    return [
      zone.actionTitle || "Turn on rack ventilation fan + check scrubber",
      zone.actionDetail || "Verify unobstructed airflow near sleeping/work rack",
      "Confirm SpO2 & breathing rate return to nominal",
    ];
  }
  if (zk === "torso") {
    return [
      zone.actionTitle || "Shift work hours from Cupola into Destiny Core",
      zone.previewText || zone.actionDetail || "Keep sleep rack inside water-wall core",
      "Confirm updated 24h module hours in log",
    ];
  }
  if (zk === "head") {
    return [
      zone.actionTitle || "Take a 90-minute recovery nap now",
      "Dim cabin lights & pause critical console tasks until rested",
      "Run 3-Min PVT reaction check after rest if needed",
    ];
  }
  return [
    zone.actionTitle || "Drink 500 mL electrolytes + 20m ARED squats",
    zone.actionDetail || "Complete bone-loading & hydration before next shift",
    "Log fluid intake & workout completion",
  ];
}

function buildCrewSimpleTasks(crew) {
  const cid = crew.profile.id;
  const halAlerts = crew.halAlerts || [];
  const halSample = state.halFrame?.samples?.[cid] || null;
  const sStat = (!state.sim.open && halSample?.sensor_status) || {};
  const tasks = [];
  const usedHalKeys = new Set();

  // 1. Shared habitat-wide alerts (affect every crew member simultaneously)
  if (state.stormOn && !state.stormSheltered) {
    tasks.push({
      id: "habitat-storm",
      scopeKey: `crew:${cid}:habitat-storm`,
      zone: "torso",
      actionMode: "storm",
      area: "HABITAT · SOLAR STORM",
      tier: "critical",
      title: "Move into shielded water-wall core now",
      reason: "Solar storm flux active across Mars-transit habitat. Skip Cupola and exposed airlocks (no Earth wait needed).",
      steps: [
        "Move all tasks out of Cupola Dome & exposed hatches",
        "Stage inside Destiny / Node 3 water-wall core",
        "Confirm shelter status across all 6 crew members",
      ],
      canApply: true,
      applyLabel: "Shelter Crew Now",
      showBodyMap: true,
      showRadLab: true,
    });
  }

  if (state.cabinAirAlert) {
    tasks.push({
      id: "habitat-air",
      scopeKey: `crew:${cid}:habitat-air`,
      zone: "lungs",
      actionMode: "air",
      area: "HABITAT · AIR & CO2",
      tier: "critical",
      title: "Switch CO2 scrubber (CDRA) to HIGH & check airflow",
      reason: "Elevated habitat ppCO2 affects breathing, focus, and pulse across all 6 crew simultaneously.",
      steps: [
        "Switch CDRA / CO2 scrubber fan to HIGH",
        "Check return ducts & hatch seals for obstruction",
        "Verify cabin ppCO2 drops back toward 1.8 mmHg",
      ],
      canApply: true,
      applyLabel: "Clear Habitat Air Alert",
      showBodyMap: true,
    });
  }

  // 2. Gather every non-nominal or actionable zone task across all 5 body zones
  const zoneOrder = ["heart", "lungs", "torso", "head", "limbs"];
  const zoneLabels = {
    heart: "HEART & PULSE",
    lungs: "LUNGS & O2",
    torso: "RADIATION & SHELTER",
    head: "SLEEP & FOCUS",
    limbs: "STRENGTH & HYDRATION",
  };
  const seenHeadlines = new Set();

  for (const zk of zoneOrder) {
    const z = crew.zones[zk];
    if (!z) continue;
    if (zk === "lungs" && state.cabinAirAlert) continue;
    if (zk === "torso" && state.stormOn && !state.stormSheltered) continue;
    if (
      zk === "head" &&
      state.cabinAirAlert &&
      !(crew.profile.sleepAlert && !crew.profile.resolved.head) &&
      !halAlerts.some((a) => a.sensor_id === "eeg")
    ) {
      continue;
    }

    const matchingHal = halAlerts.filter((a) => halMatchesZone(zk, a));
    matchingHal.forEach((a) => usedHalKeys.add(a.key));

    if (seenHeadlines.has(z.headline)) {
      continue;
    }

    if (z.tier !== "nominal" || z.canApply) {
      seenHeadlines.add(z.headline);
      const isNoSig = z.shortTag === "NO SIGNAL";
      tasks.push({
        id: `zone-${zk}`,
        scopeKey: `crew:${cid}:${zk}`,
        zone: zk,
        actionMode: "zone",
        area: zoneLabels[zk] || ZONE_META[zk].label.toUpperCase(),
        tier: z.tier,
        title: z.headline,
        reason: z.summary,
        steps: buildZoneActionSteps(zk, z, matchingHal),
        canApply: Boolean(z.canApply || matchingHal.length),
        applyLabel: z.applyLabel && z.canApply ? z.applyLabel : "Mark Done",
        showBodyMap: true,
        showHeartLab: zk === "heart",
        showRadLab: zk === "torso",
        showSensors: zk === "head" || isNoSig,
      });
    }
  }

  // 3. Any remaining HAL2030 alerts or offline wearable channels not already covered
  for (const ha of halAlerts) {
    if (usedHalKeys.has(ha.key)) continue;
    tasks.push({
      id: `hal-${ha.key}`,
      scopeKey: `crew:${cid}:hal:${ha.key}`,
      zone: ha.metric === "skin_temp" ? "limbs" : ha.metric === "spo2" || ha.metric === "resp_rate" ? "lungs" : "heart",
      actionMode: "hal",
      halKey: ha.key,
      area: `SENSOR · ${(ha.sensor_id || "HAL").toUpperCase()}`,
      tier: ha.severity || "warning",
      title: ha.title,
      reason: ha.recommendation || "Wearable channel flagged an anomaly.",
      steps: ha.steps?.length ? ha.steps : ["Inspect wearable sensor contact", "Verify streaming in Sensors tab"],
      canApply: true,
      applyLabel: "Confirm Checked",
      showSensors: true,
    });
  }

  for (const [ch, status] of Object.entries(sStat)) {
    if (status !== "no_signal") continue;
    if (ch === "oximeter" || ch === "eeg") continue;
    tasks.push({
      id: `nosig-${ch}`,
      scopeKey: `crew:${cid}:nosig:${ch}`,
      zone: ch === "resp" ? "lungs" : ch === "temp" ? "limbs" : "heart",
      actionMode: "none",
      area: "WEARABLE · NO SIGNAL",
      tier: "warning",
      title: `Reconnect ${ch.toUpperCase()} wearable channel`,
      reason: "Channel reports no signal. Missing telemetry stays blank and is never filled with guesses.",
      steps: [
        `Inspect ${ch.toUpperCase()} electrode/strap contact & cable seat`,
        "Verify live packet stream in Sensors Network tab",
      ],
      canApply: false,
      showSensors: true,
      showBodyMap: true,
    });
  }

  if (!state.dosimeterOnline) {
    tasks.push({
      id: "dosimeter-offline",
      scopeKey: `crew:${cid}:dosimeter`,
      zone: "torso",
      actionMode: "none",
      area: "RADIATION · DOSIMETER",
      tier: "warning",
      title: "Reconnect personal radiation dosimeter",
      reason: "Live dose badge is offline — cabin totals use module estimates until badge reconnects.",
      steps: [
        "Check clip-on dosimeter battery & sync dock",
        "Tap Dosimeter pill in top bar once streaming",
      ],
      canApply: false,
      showRadLab: true,
      showBodyMap: true,
    });
  }

  // Sort strictly: critical -> warning -> nominal
  tasks.sort((a, b) => TIER_RANK[b.tier] - TIER_RANK[a.tier]);

  // 4. Calm routine plan when zero urgent or warning tasks exist
  if (tasks.length === 0) {
    tasks.push({
      id: "routine-clear",
      scopeKey: `crew:${cid}:routine`,
      zone: "torso",
      actionMode: "none",
      area: "ALL SYSTEMS · CLEAR",
      tier: "nominal",
      title: "All clear · Routine daily plan",
      reason: "No urgent health, air, sensor, or radiation tasks right now. Cleared for scheduled EVA or maintenance.",
      steps: [
        "Stay hydrated — 500 mL water across this shift",
        "Complete scheduled 2h ARED / cycle exercise",
        "Keep sleep & work hours inside Destiny / Node 3 core",
      ],
      canApply: false,
      showSensors: true,
      showBodyMap: true,
    });
  }

  return tasks;
}

function renderCrewSimplePane(crew) {
  const cid = crew.profile.id;
  const tm = TIER_META[crew.overallTier];
  const tasks = buildCrewSimpleTasks(crew);
  const urgentCount = tasks.filter((t) => t.tier !== "nominal").length;
  const topTask = tasks[0];

  $("body-mode-crew").textContent = `${crew.profile.name} · ${crew.profile.role}`;
  $("csa-hero-card").className = `sub-glass hero-summary-card ${tm.cardClass}`;
  $("csa-avatar").src = crew.profile.avatar;
  $("csa-avatar").alt = crew.profile.name;
  $("csa-name").textContent = crew.profile.name;
  $("csa-meta").textContent = `${crew.profile.role} · ${crew.profile.cabin}`;
  $("csa-activity").textContent =
    crew.missingChannels > 0
      ? `${crew.activity || "Working"} · ${crew.missingChannels} sensor offline`
      : crew.activity || "Working";
  $("csa-score-pill").textContent = `Readiness ${crew.overallScore}/100`;
  $("csa-status-pill").className = `triage-pill ${tm.pillClass}`;
  $("csa-status-pill").textContent = tm.pillLong;

  if (urgentCount === 0) {
    $("csa-headline").textContent = "All clear — ready for scheduled EVA & maintenance";
    $("csa-plain-summary").textContent =
      "Pulse, blood oxygen, cabin air, sleep, and radiation are all inside safe Mars-transit limits.";
  } else if (urgentCount === 1) {
    $("csa-headline").textContent = `1 Action Item: ${topTask.title}`;
    $("csa-plain-summary").textContent = `${topTask.reason} Complete the checklist below — no Earth wait needed.`;
  } else {
    $("csa-headline").textContent = `${urgentCount} Action Items for ${crew.profile.name.split(" ")[0]}`;
    $("csa-plain-summary").textContent = `Top priority: ${topTask.title}. Work top-to-bottom below — no Earth wait needed.`;
  }

  const hrStr = crew.meanHr != null ? `${crew.meanHr} bpm` : "-- (No Signal)";
  const o2Str = crew.spo2Val != null ? `${crew.spo2Val.toFixed(0)}%` : "--";
  $("csa-kpi-cardio").textContent = `Pulse ${hrStr} · O2 ${o2Str}`;
  $("csa-kpi-env").textContent = `CO2 ${crew.zones.lungs.shortTag} · Sleep ${crew.zones.head.shortTag}`;
  $("csa-kpi-rad").textContent = `${crew.dailyMsv.toFixed(2)} mSv/d · ${crew.zones.torso.tier === "nominal" ? "Core Shield OK" : "Move to Core"}`;

  $("csa-task-count").textContent =
    urgentCount === 0 ? "0 urgent tasks · Routine plan" : `${urgentCount} urgent · ${tasks.length} total`;

  const listEl = $("crew-all-tasks-list");
  listEl.innerHTML = tasks
    .map((t) => {
      const tMeta = TIER_META[t.tier];
      const saved = state.checkedSteps[t.scopeKey] || {};
      const stepsHtml = t.steps
        .map((step, idx) => {
          const isChecked = Boolean(saved[idx]);
          return `
            <label class="action-check-item ${isChecked ? "checked" : ""}">
              <input type="checkbox" data-scope-key="${escText(t.scopeKey)}" data-step-idx="${idx}" ${isChecked ? "checked" : ""} />
              <span class="action-step-num">${idx + 1}</span>
              <span class="action-step-text">${escText(step)}</span>
            </label>
          `;
        })
        .join("");

      const actionsHtml = [
        t.canApply
          ? `<button class="btn-glass-pri" type="button" data-task-apply="${escText(t.id)}">${escText(t.applyLabel || "Apply Fix")}</button>`
          : "",
        t.showSensors
          ? `<button class="btn-glass-sec" type="button" data-task-sensors="1">⏱ 3-Min PVT / SANS</button>`
          : "",
        t.showHeartLab
          ? `<button class="mini-link-btn" type="button" data-task-heart="1">Heart Details →</button>`
          : "",
        t.showRadLab
          ? `<button class="mini-link-btn" type="button" data-task-rad="1">Radiation Plan →</button>`
          : "",
        t.showBodyMap
          ? `<button class="mini-link-btn" type="button" data-task-map="${escText(t.zone)}">Body Map</button>`
          : "",
      ]
        .filter(Boolean)
        .join("");

      return `
        <article class="crew-task-card task-${escText(t.tier)}">
          <div class="crew-task-head">
            <div class="crew-task-head-left">
              <span class="crew-task-area">${escText(t.area)}</span>
            </div>
            <span class="triage-pill ${tMeta.pillClass}">${tMeta.pillLong}</span>
          </div>
          <h4 class="crew-task-title">${escText(t.title)}</h4>
          <p class="crew-task-reason">${escText(t.reason)}</p>
          <div class="crew-task-steps">${stepsHtml}</div>
          <div class="crew-task-actions">${actionsHtml}</div>
        </article>
      `;
    })
    .join("");

  const taskById = Object.fromEntries(tasks.map((t) => [t.id, t]));
  listEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", (e) => {
      const sk = e.target.dataset.scopeKey;
      const idx = Number(e.target.dataset.stepIdx);
      state.checkedSteps[sk] = { ...(state.checkedSteps[sk] || {}), [idx]: e.target.checked };
      e.target.closest(".action-check-item")?.classList.toggle("checked", e.target.checked);
    });
  });

  listEl.querySelectorAll("[data-task-apply]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const t = taskById[btn.dataset.taskApply];
      if (!t) return;
      await executeSimpleTaskAction(cid, t);
    });
  });

  listEl.querySelectorAll("[data-task-sensors]").forEach((btn) => {
    btn.addEventListener("click", () => setLevel("sensors"));
  });
  listEl.querySelectorAll("[data-task-heart]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.cardioMode = "simple";
      setLevel("cardio");
    });
  });
  listEl.querySelectorAll("[data-task-rad]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.radMode = "simple";
      setLevel("engineer");
    });
  });
  listEl.querySelectorAll("[data-task-map]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.activeZone = btn.dataset.taskMap || crew.worstZone;
      setBodyMode("map");
    });
  });

  const topActionable = tasks.find((t) => t.canApply) || null;
  state._topSimpleTask = topActionable;
  const doAllBtn = $("csa-do-all-btn");
  if (doAllBtn) {
    doAllBtn.disabled = !topActionable;
    doAllBtn.textContent = topActionable ? topActionable.applyLabel || "Apply Top Priority Action" : "All Clear ✓";
  }
}

async function executeSimpleTaskAction(cid, task) {
  if (!task || !task.canApply) return;
  delete state.checkedSteps[task.scopeKey];
  if (task.actionMode === "storm") {
    state.previewActive = false;
    await resolveStormShelterAllCrew();
    return;
  }
  if (task.actionMode === "air") {
    state.previewActive = false;
    await resolveCabinAirAlertAllCrew();
    return;
  }
  if (task.actionMode === "hal" && task.halKey) {
    state.halResolvedKeys[task.halKey] = true;
    await simulateCrewMember(cid);
    renderAll();
    return;
  }
  await applyZoneIntervention(cid, task.zone);
}

/* ==================== RENDER: LEVEL 2 BODY HUD ==================== */
function renderLevel2Body() {
  const crew = state.crewSimCache[state.activeCrewId];
  if (!crew) return;

  $("body-mode-simple")?.classList.toggle("active", state.bodyMode === "simple");
  $("body-mode-map")?.classList.toggle("active", state.bodyMode === "map");
  $("crew-simple-pane")?.classList.toggle("hidden", state.bodyMode !== "simple");
  $("body-split-grid")?.classList.toggle("hidden", state.bodyMode !== "map");

  // Update mini crew chips
  $("level2-crew-bar").querySelectorAll(".crew-chip").forEach((btn) => {
    const cid = btn.dataset.crew;
    btn.classList.toggle("active", cid === state.activeCrewId);
    const cData = state.crewSimCache[cid];
    if (cData) {
      $(`l2-dot-${cid}`).className = `dot-sm ${TIER_META[cData.overallTier].dotClass}`;
    }
  });

  renderCrewSimplePane(crew);

  const tm = TIER_META[crew.overallTier];
  const stage = $("avatar-stage");
  stage.classList.remove("state-nominal", "state-warning", "state-critical");
  stage.classList.add(tm.stageClass);

  $("hero-popup").className = `hero-popup ${tm.popupClass}`;
  $("hero-crew-avatar").src = crew.profile.avatar;
  $("hero-popup-title").textContent = `${crew.profile.name} · ${tm.heroTitle}`;
  $("hero-popup-sub").textContent =
    crew.overallTier === "nominal"
      ? `All 5 systems nominal · Readiness ${crew.overallScore}/100`
      : `Priority zone: ${ZONE_META[crew.worstZone].label} · Readiness ${crew.overallScore}/100`;
  $("stage-score-val").textContent = String(crew.overallScore);

  const jumpBtn = $("hero-jump-btn");
  jumpBtn.classList.toggle("hidden", crew.overallTier === "nominal" || state.activeZone === crew.worstZone);

  $("dosimeter-popup").classList.toggle("hidden", state.dosimeterOnline);

  // Hotspots on full body
  document.querySelectorAll(".body-hotspot").forEach((hs) => {
    const zk = hs.dataset.zone;
    const zData = crew.zones[zk];
    hs.classList.toggle("active-zone", zk === state.activeZone);
    hs.classList.remove("hs-nominal", "hs-warning", "hs-critical");
    if (zData) hs.classList.add(`hs-${zData.tier}`);
  });

  // Active zone details
  const zKey = state.activeZone;
  const z = crew.zones[zKey];
  const zTm = TIER_META[z.tier];
  const zTopPositions = { head: "9%", lungs: "26%", heart: "31%", torso: "44%", limbs: "60%" };

  const floatPopup = $("zone-float-popup");
  floatPopup.className = `zone-float-popup ${zTm.floatClass}`;
  floatPopup.style.top = zTopPositions[zKey] || "36%";
  $("float-badge").textContent = z.floatBadge;
  $("float-label").textContent = z.floatText;

  $("mobile-float-bar").className = `mobile-float-bar ${zTm.floatClass}`;
  $("mfloat-badge").textContent = z.floatBadge;
  $("mfloat-label").textContent = z.floatText;

  const actionCard = $("action-glass-card");
  actionCard.className = `sub-glass action-panel ${zTm.cardClass}`;
  $("zone-kicker").textContent = ZONE_META[zKey].kicker;
  $("zone-status-pill").className = `triage-pill ${zTm.pillClass}`;
  $("zone-status-pill").textContent = zTm.pillLong;
  $("zone-headline").textContent = z.headline;
  $("zone-summary").textContent = z.summary;
  $("zone-action-title").textContent = z.actionTitle;
  $("zone-action-detail").textContent = z.actionDetail;

  const prevBanner = $("zone-preview-banner");
  if (state.previewActive && z.previewText) {
    prevBanner.textContent = z.previewText;
    prevBanner.classList.remove("hidden");
  } else {
    prevBanner.classList.add("hidden");
  }

  const btnPrev = $("btn-zone-preview");
  btnPrev.textContent = zKey === "torso" ? "Preview Move" : "Preview Impact";
  btnPrev.classList.toggle("hidden", !z.previewText);
  const btnApply = $("btn-zone-apply");
  btnApply.textContent = z.applyLabel;
  btnApply.disabled = !z.canApply;

  // Quick tools for Head (PVT & SANS checks) and Lungs (Sensors / CO2 trace)
  const qt = $("zone-quick-tools");
  if (qt) {
    qt.classList.toggle("hidden", zKey !== "head" && zKey !== "lungs" && crew.missingChannels === 0);
  }

  // Contextual bottom panel: Torso shows Shielding bars; Heart shows live Astroskin ECG sparkline!
  const showHeart = zKey === "heart";
  $("shelter-mini-card").classList.toggle("hidden", showHeart);
  $("heart-mini-card").classList.toggle("hidden", !showHeart);

  if (showHeart) {
    renderHeartMiniCard(crew.vitals);
  } else {
    renderShelterMiniBars(crew.rad);
  }

  // Compact 5-zone dock strip inside Action Card
  $("body-dock-list").innerHTML = Object.keys(ZONE_META)
    .map((zk) => {
      const zd = crew.zones[zk];
      const dot = TIER_META[zd.tier].dotClass;
      return `
        <button class="dock-item ${zk === zKey ? "active" : ""}" data-zone="${zk}" type="button">
          <span class="dock-dot ${dot}"></span>
          <span>${ZONE_META[zk].label}</span>
        </button>
      `;
    })
    .join("");

  $("body-dock-list").querySelectorAll(".dock-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.activeZone = btn.dataset.zone;
      state.previewActive = false;
      renderLevel2Body();
    });
  });
}

function renderShelterMiniBars(rad) {
  const rates = rad.simple_summary?.effective_rates_ugy_h || {};
  const ratings = rad.simple_summary?.shielding_ratings || {};
  const ordered = ["uslab", "node3", "columbus", "node1", "cupola"];
  const maxRate = Math.max(...ordered.map((c) => rates[c] || 20), 40);

  $("shelter-mini-bars").innerHTML = ordered
    .map((cid) => {
      const r = rates[cid] || 25;
      const pct = Math.min(100, Math.round((r / maxRate) * 100));
      const cls = r > 120 ? "crit" : r > 30 ? "high" : "";
      const tag = ratings[cid] || `${r.toFixed(0)} uGy/h`;
      return `
        <div class="sbar-row">
          <span>${CABIN_NAMES[cid]}</span>
          <div class="sbar-track"><div class="sbar-fill ${cls}" style="width:${pct}%"></div></div>
          <span class="sbar-tag">${tag}</span>
        </div>
      `;
    })
    .join("");
}

function renderHeartMiniCard(vitals) {
  const m = vitals.summary_metrics || {};
  const wp = vitals.waveform_preview || {};
  $("hm-hr").textContent = `${Math.round(m.mean_hr_bpm || 0)} bpm`;
  $("hm-rmssd").textContent = `${Math.round(m.rmssd_ms || 0)} ms`;
  $("hm-qtcf").textContent = `${Math.round(m.qtcf_ms || 0)} ms`;
  $("hm-spo2").textContent = `${(m.spo2_min_pct || 0).toFixed(0)}%`;

  const t = wp.time_s || [];
  const ecg = wp.ecg_clean || [];
  const step = Math.max(1, Math.floor(t.length / 180));
  const labels = t.filter((_, i) => i % step === 0).map((v) => v.toFixed(1));
  const vals = ecg.filter((_, i) => i % step === 0);

  const canvas = $("heartMiniChart");
  if (!canvas || typeof Chart === "undefined") return;
  if (state.charts.heartMini) state.charts.heartMini.destroy();
  state.charts.heartMini = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          data: vals,
          borderColor: vitals.early_warning?.status === "CRITICAL" ? "#ef4444" : "#007aff",
          borderWidth: 1.75,
          pointRadius: 0,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false } },
    },
  });
}

async function applyZoneIntervention(cid, zk) {
  const profile = state.crewProfiles[cid];
  if (!profile) return;

  if (zk === "lungs" && state.cabinAirAlert) {
    state.previewActive = false;
    await resolveCabinAirAlertAllCrew();
    return;
  }

  if (zk === "torso" && state.stormOn && !state.stormSheltered) {
    state.previewActive = false;
    await resolveStormShelterAllCrew();
    return;
  }

  // Mark matching HAL2030 alert keys resolved for this crew member & zone
  const halAlerts = state.halFrame?.alerts || [];
  halAlerts
    .filter((a) => a.crew_id === cid)
    .forEach((a) => {
      if (
        (zk === "lungs" && (a.metric === "spo2" || a.metric === "resp_rate")) ||
        (zk === "heart" && (a.metric === "heart_rate" || a.metric === "spo2" || a.sensor_id === "oximeter")) ||
        (zk === "limbs" && a.metric === "skin_temp") ||
        (zk === "head" && a.sensor_id === "eeg")
      ) {
        state.halResolvedKeys[a.key] = true;
      }
    });

  if (zk === "torso") {
    const crew = state.crewSimCache[cid];
    const rec = crew?.rad?.simple_summary?.recommended_action;
    if (rec && rec.preview_cabin_hours) {
      profile.cabinHours = { ...rec.preview_cabin_hours };
      profile.cabin = CABIN_NAMES.uslab;
    }
    delete state.checkedSteps[`rad:${cid}`];
  } else if (zk === "heart" || zk === "lungs") {
    profile.recordId = "ptt_s3_sit";
    profile.resolved.heart = true;
    profile.resolved.lungs = true;
    profile.ppCo2 = 1.8;
    delete state.checkedSteps[`cardio:${cid}`];
  } else if (zk === "head") {
    profile.resolved.head = true;
  } else if (zk === "limbs") {
    profile.resolved.limbs = true;
  }

  delete state.checkedSteps[`crew:${cid}:${zk}`];
  state.previewActive = false;
  await simulateCrewMember(cid);
  renderAll();
}

async function applyCurrentZoneIntervention() {
  await applyZoneIntervention(state.activeCrewId, state.activeZone);
}

const fmt = (v, d = 1) => (v == null || Number.isNaN(Number(v)) ? "--" : Number(v).toFixed(d));

function renderActionChecklist(containerId, scopeKey, steps) {
  const el = $(containerId);
  if (!el) return;
  const saved = state.checkedSteps[scopeKey] || {};
  el.innerHTML = steps
    .map((step, idx) => {
      const isChecked = Boolean(saved[idx]);
      return `
        <label class="action-check-item ${isChecked ? "checked" : ""}">
          <input type="checkbox" data-step-idx="${idx}" ${isChecked ? "checked" : ""} />
          <span class="action-step-num">${idx + 1}</span>
          <span class="action-step-text">${step}</span>
        </label>
      `;
    })
    .join("");

  el.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", (e) => {
      const idx = Number(e.target.dataset.stepIdx);
      const next = { ...(state.checkedSteps[scopeKey] || {}), [idx]: e.target.checked };
      state.checkedSteps[scopeKey] = next;
      const item = e.target.closest(".action-check-item");
      if (item) item.classList.toggle("checked", e.target.checked);
    });
  });
}

/* ==================== RENDER: LEVEL 3A HEART & ECG LAB ==================== */
function renderCardioSimplePane(crew) {
  const profile = crew.profile;
  const v = crew.vitals;
  const m = v.summary_metrics || {};
  const ew = v.early_warning || {};

  const cardioTier = tierFromStatus(ew.status);
  const meanHr = Math.round(m.mean_hr_bpm || 68);
  const spo2 = Math.round(m.spo2_min_pct || 97);
  const limbsDue = Boolean(profile.limbsAlert && !profile.resolved.limbs);

  $("cardio-mode-crew").textContent = `Showing: ${profile.name} · ${profile.cabin}`;

  const hrLabel =
    meanHr >= 100
      ? `${meanHr} bpm · Racing`
      : meanHr >= 88
      ? `${meanHr} bpm · Elevated`
      : `${meanHr} bpm · Resting / Normal`;
  const recLabel =
    cardioTier === "critical"
      ? "Strained — Stop & Rest"
      : cardioTier === "warning"
      ? "Low Recovery — Pace Load"
      : "Well Recovered";
  const o2Label =
    spo2 < 93
      ? `${spo2}% · Low (Check Air)`
      : spo2 < 95
      ? `${spo2}% · Slightly Low`
      : `${spo2}% · Strong`;

  $("cs-hr-plain").textContent = hrLabel;
  $("cs-recovery-plain").textContent = recLabel;
  $("cs-o2-plain").textContent = o2Label;

  let cardClass = "card-nominal";
  let pillClass = "pill-nominal";
  let pillText = "GREEN · CLEAR FOR DUTY";
  let headline = "Heart & oxygen steady";
  let summary = "Resting pulse, recovery, and blood oxygen are all in a healthy range.";
  let steps = [
    "All steady — clear for scheduled EVA/maintenance.",
    "Keep drinking water regularly across your shift.",
  ];
  let primaryBtnText = "Cleared for Duty ✓";
  let primaryDisabled = true;
  let primaryMode = "none";

  if (cardioTier === "critical") {
    cardClass = "card-critical";
    pillClass = "pill-critical";
    primaryDisabled = false;
    primaryMode = "resolve-heart";
    if (spo2 < 93 || profile.recordId === "bidmc_12") {
      pillText = "RED · STOP & CHECK AIR";
      headline = "Blood oxygen dipping — pause tasks & check air";
      summary = "Blood oxygen dropped below comfort level. Stop exertion and check cabin airflow (no Earth wait needed).";
      steps = [
        "Stop heavy work right now and sit upright.",
        "Check rack airflow fan & cabin air scrubber status.",
        "Drink 500 mL electrolytes & take 30 min calm seated rest.",
      ];
      primaryBtnText = "Log Rest & Air Check Now";
    } else {
      pillText = "RED · STOP & REST NOW";
      headline = "Heart working too hard — pause tasks now";
      summary = "Your pulse and rhythm show strain right now. Handle this onboard — do not wait for Earth.";
      steps = [
        "Stop heavy work right now — heart is strained.",
        "Drink 500 mL electrolytes & water.",
        "Take 30 min seated rest (no Earth wait needed).",
      ];
      primaryBtnText = "Log Rest & Electrolytes Now";
    }
  } else if (cardioTier === "warning") {
    cardClass = "card-warning";
    pillClass = "pill-warning";
    pillText = "ORANGE · PACE YOURSELF";
    headline = "Low recovery — skip heavy strain today";
    summary = "Your heart is not bouncing back fully between shifts. Lighten today's physical load.";
    steps = [
      "Switch heavy equipment moves to light console or inspection work.",
      "Drink 500 mL electrolytes & water and skip caffeine for 6 hours.",
      "Take a 20-min seated stretch or recovery break (no Earth wait needed).",
    ];
    primaryBtnText = "Switch to Light Duty & Hydrate";
    primaryDisabled = false;
    primaryMode = "resolve-heart";
  } else if (limbsDue) {
    cardClass = "card-warning";
    pillClass = "pill-warning";
    pillText = "ORANGE · WORKOUT DUE";
    headline = "Heart steady, but daily workout skipped";
    summary = "Pulse and oxygen are steady, but today's strength & hydration session is overdue.";
    steps = [
      "You missed workout today — schedule 20m ARED resistance.",
      "Drink 500 mL electrolytes & water right after your session.",
    ];
    primaryBtnText = "Log 20m Workout & Fluids";
    primaryDisabled = false;
    primaryMode = "resolve-limbs";
  } else if (state.cabinAirAlert) {
    cardClass = "card-warning";
    pillClass = "pill-warning";
    pillText = "ORANGE · CHECK CABIN AIR";
    headline = "Heart steady — cabin air needs boost";
    summary = "Pulse is steady, but habitat air scrubber flow is low across all 6 crew.";
    steps = [
      "Check rack vents are unblocked and switch CDRA scrubber to HIGH.",
      "Drink 500 mL water and keep exertion light until air clears.",
    ];
    primaryBtnText = "Switch Scrubber to HIGH (All Crew)";
    primaryDisabled = false;
    primaryMode = "resolve-air";
  }

  $("cs-hero-card").className = `sub-glass simple-hero-card ${cardClass}`;
  $("cs-status-pill").className = `triage-pill ${pillClass}`;
  $("cs-status-pill").textContent = pillText;
  $("cs-headline").textContent = headline;
  $("cs-plain-summary").textContent = summary;

  renderActionChecklist("cs-actions-list", `cardio:${profile.id}`, steps);

  const applyBtn = $("cs-apply-primary-btn");
  applyBtn.textContent = primaryBtnText;
  applyBtn.disabled = primaryDisabled;
  applyBtn.dataset.actionMode = primaryMode;
}

function renderLevel3Cardio() {
  const crew = state.crewSimCache[state.activeCrewId];
  if (!crew) return;
  const profile = crew.profile;
  const v = crew.vitals;
  const m = v.summary_metrics || {};
  const ew = v.early_warning || {};
  const rec = v.record || {};

  const isSimple = state.cardioMode === "simple";
  $("cardio-simple-pane").classList.toggle("hidden", !isSimple);
  $("cardio-eng-pane").classList.toggle("hidden", isSimple);
  $("cardio-mode-simple").classList.toggle("active", isSimple);
  $("cardio-mode-eng").classList.toggle("active", !isSimple);

  renderCardioSimplePane(crew);

  if (isSimple) return;

  // Sync toolbar state
  $("cardio-record-btns").querySelectorAll(".eng-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.record === profile.recordId);
  });
  $("cardio-atmo-select").value = profile.atmoProfile;
  $("cardio-ppco2").value = String(profile.ppCo2);

  // KPIs
  $("ckpi-hr").textContent = `${fmt(m.mean_hr_bpm, 1)} bpm`;
  $("ckpi-hr-sub").textContent = `PPG Pulse ${fmt(m.ppg_pulse_bpm, 1)} · Deficit ${fmt(m.effective_pulse_deficit_bpm ?? m.pulse_deficit_bpm, 1)}`;
  $("ckpi-hrv").textContent = `${fmt(m.rmssd_ms, 0)} / ${fmt(m.sdnn_ms, 0)} ms`;
  $("ckpi-hrv-sub").textContent = `PRSA DC ${fmt(m.deceleration_capacity_ms, 1)} ms · α1 ${fmt(m.dfa_alpha1, 2)}`;
  $("ckpi-qtcf").textContent = `${fmt(m.qtcf_ms, 0)} ms`;
  $("ckpi-qtcf-sub").textContent = `Ectopy ${fmt(m.ectopy_burden_pct, 1)}% · PAT ${fmt(m.pat_ms, 0)} ms`;
  $("ckpi-score").textContent = `${ew.cardio_score ?? "--"} / 100`;
  $("ckpi-score-sub").textContent = `Pre-event risk ${ew.pre_event_risk_score ?? "--"}%`;

  const tm = TIER_META[tierFromStatus(ew.status)];
  $("cardio-record-title").textContent = rec.title || profile.recordId;
  $("cardio-status-badge").className = `triage-pill ${tm.pillClass}`;
  $("cardio-status-badge").textContent = ew.status || "NOMINAL";
  $("cardio-lead-tag").textContent = `${rec.lead_used || "ECG"} · ${rec.sampling_rate_hz || 250} HZ`;
  $("cardio-scenario-note").textContent = `${rec.clinical_profile || ""} — ${ew.primary_action || ""}`;
  $("cardio-scenario-note").className = `alara-note ${ew.status || ""}`;

  // Waveform Chart (ECG + PPG)
  const wp = v.waveform_preview || {};
  const t = wp.time_s || [];
  const ecg = wp.ecg_clean || [];
  const ppg = wp.pleth || [];
  const step = Math.max(1, Math.floor(t.length / 260));
  const labels = t.filter((_, i) => i % step === 0).map((s) => `${s.toFixed(1)}s`);
  const ecgPts = ecg.filter((_, i) => i % step === 0);
  const ppgPts = ppg.filter((_, i) => i % step === 0);

  const tc = chartThemeColors();
  if (state.charts.cardioWave) state.charts.cardioWave.destroy();
  state.charts.cardioWave = new Chart($("cardioWaveChart").getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "ECG (norm)", data: ecgPts, borderColor: "#ef4444", borderWidth: 1.8, pointRadius: 0, tension: 0.2 },
        { label: "PPG Pulse", data: ppgPts, borderColor: "#007aff", borderWidth: 1.6, pointRadius: 0, tension: 0.3 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { labels: { color: tc.legend, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: tc.tick, maxTicksLimit: 8 }, grid: { color: tc.grid } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    },
  });

  // Trend Chart (Window Pre-Event Risk & RMSSD)
  const traj = v.window_trajectory || [];
  if (state.charts.cardioTrend) state.charts.cardioTrend.destroy();
  state.charts.cardioTrend = new Chart($("cardioTrendChart").getContext("2d"), {
    type: "line",
    data: {
      labels: traj.map((w) => `${Math.round(w.t_end_s)}s`),
      datasets: [
        {
          label: "Pre-Event Risk %",
          data: traj.map((w) => w.pre_event_risk_score),
          borderColor: "#f97316",
          backgroundColor: "rgba(249,115,22,0.14)",
          fill: true,
          tension: 0.3,
        },
        {
          label: "RMSSD (ms)",
          data: traj.map((w) => w.rmssd_ms),
          borderColor: "#10b981",
          borderWidth: 2,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { labels: { color: tc.legend, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    },
  });

  // 4-Axis Table
  const ax = ew.axis_risk || {};
  const rows = [
    ["Autonomic (RMSSD / PRSA DC)", `${fmt(m.rmssd_ms, 1)} ms / ${fmt(m.deceleration_capacity_ms, 1)} ms`, "RMSSD >= 25 ms", ax.autonomic ?? 0],
    ["Electrical (QTcF / Ectopy)", `${fmt(m.qtcf_ms, 0)} ms / ${fmt(m.ectopy_burden_pct, 1)}%`, "QTcF < 450 ms", ax.electrical ?? 0],
    ["Vascular (PAT / Est SBP)", `${fmt(m.pat_ms, 0)} ms / ${fmt(m.sbp_est_mmhg, 0)} mmHg`, "PAT 150-300 ms", ax.hemodynamic ?? 0],
    ["Hypoxic (SpO2 / Resp / ODI3)", `${fmt(m.spo2_min_pct, 1)}% / ${fmt(m.resp_rate_bpm, 1)} brpm`, "SpO2 >= 93%", ax.respiratory ?? 0],
  ];
  $("cardio-metrics-tbody").innerHTML = rows
    .map(
      ([name, val, bound, risk]) => `
      <tr>
        <td><strong>${name}</strong></td>
        <td class="mono-num">${val}</td>
        <td class="mono-num">${bound}</td>
        <td class="mono-num"><strong>${risk}%</strong></td>
      </tr>`
    )
    .join("");

  // Signals & Actions
  const sigs = ew.signals || [];
  $("cardio-alerts-panel").innerHTML = sigs.length
    ? sigs
        .map(
          (s) => `
          <div class="sig-alert-item sig-${s.severity}">
            <div class="sig-alert-head"><span>${s.axis} · ${s.metric}</span><span>${s.value} (Limit ${s.threshold})</span></div>
            <div class="sig-alert-body">${s.mechanism}. <strong>Action:</strong> ${s.action}</div>
          </div>`
        )
        .join("")
    : `<div class="sig-alert-item"><div class="sig-alert-head"><span>ALL 4 AXES NOMINAL</span><span>CLEAR</span></div><div class="sig-alert-body">No autonomic, electrical, vascular, or hypoxic pre-event anomalies detected.</div></div>`;

  // HAL2030 Multi-Channel Waveforms (ECG, Respiration, EEG with honest null gaps on disconnect)
  renderHalWaveChart(crew);
}

async function renderHalWaveChart(crew) {
  const cid = crew.profile.id;
  if ($("hal-wave-crew-lbl")) $("hal-wave-crew-lbl").textContent = crew.profile.name;
  let frameData = state.halFrame;
  try {
    const resp = await fetch(`/api/hal/frame?t=${Math.floor(state.halT)}&crew_id=${encodeURIComponent(cid)}`);
    if (resp.ok) frameData = await resp.json();
  } catch {
    // Keep last frame
  }
  const wf = frameData?.waveforms;
  const sample = frameData?.samples?.[cid];
  const metaPill = $("hal-wave-meta-pill");
  if (metaPill && sample) {
    const disconnected = Object.entries(sample.sensor_status || {})
      .filter(([, st]) => st === "no_signal")
      .map(([k]) => k.toUpperCase());
    metaPill.className = `triage-pill ${disconnected.length ? "pill-warning" : "pill-nominal"}`;
    metaPill.textContent = disconnected.length
      ? `NO SIGNAL: ${disconnected.join(", ")}`
      : `${sample.activity.toUpperCase()} · ALL CHANNELS STREAMING`;
  }
  if (!wf || !$("halWaveChart") || typeof Chart === "undefined") return;

  const tc = chartThemeColors();
  const labels = (wf.ecg?.t || []).map((v) => (v == null ? "" : `${v.toFixed(1)}s`));
  if (state.charts.halWave) state.charts.halWave.destroy();
  state.charts.halWave = new Chart($("halWaveChart").getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "HAL ECG (sim)",
          data: wf.ecg?.values || [],
          borderColor: "#10b981",
          borderWidth: 1.6,
          pointRadius: 0,
          spanGaps: false,
          tension: 0.2,
        },
        {
          label: "HAL Resp (offset)",
          data: (wf.respiration?.values || []).map((v) => (v == null ? null : v - 2.2)),
          borderColor: "#2563eb",
          borderWidth: 1.5,
          pointRadius: 0,
          spanGaps: false,
          tension: 0.25,
        },
        {
          label: "HAL EEG (offset)",
          data: (wf.eeg?.values || []).map((v) => (v == null ? null : v - 4.4)),
          borderColor: "#f59e0b",
          borderWidth: 1.4,
          pointRadius: 0,
          spanGaps: false,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { labels: { color: tc.legend, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: tc.tick, maxTicksLimit: 8 }, grid: { color: tc.grid } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    },
  });
}

/* ==================== RENDER: LEVEL 3B RADIATION LAB ==================== */
function renderRadSimplePane(crew) {
  const profile = crew.profile;
  const rad = crew.rad;
  const simpleRad = rad.simple_summary || {};
  const recMove = simpleRad.recommended_action || {};
  const radTier = tierFromStatus(rad.status);
  const rTm = TIER_META[radTier];

  $("rad-mode-crew").textContent = `Showing: ${profile.name} · Shielding Plan`;
  $("rs-hero-card").className = `sub-glass simple-hero-card ${rTm.cardClass}`;
  $("rs-status-pill").className = `triage-pill ${rTm.pillClass}`;

  let pillText = "GREEN · WELL SHIELDED";
  let headline = "Daily shielding is safe";
  let summary = "Most of your shift is inside well-shielded central modules (Destiny Core & Node 3).";

  if (radTier === "critical") {
    pillText = "RED · SHELTER NOW";
    headline = "High radiation exposure — move to core";
    summary = "Solar storm or outer-window hours are raising exposure. Move tasks into Destiny Core immediately (no Earth wait needed).";
  } else if (radTier === "warning") {
    pillText = "ORANGE · REDUCE OUTER TIME";
    headline = "Move long tasks out of outer bays";
    summary = "Shifting work hours into central water-lined racks cuts today's exposure significantly.";
  } else if (recMove.can_improve) {
    headline = "Daily shielding is safe (can optimize)";
    summary = "Within safe limits, and moving outer-bay hours to Destiny Core cuts exposure even further.";
  }

  $("rs-status-pill").textContent = pillText;
  $("rs-headline").textContent = headline;
  $("rs-plain-summary").textContent = summary;

  const sourceId = recMove.source_cabin_id || simpleRad.culprit_cabin_id || "cupola";
  const sourceName = CABIN_NAMES[sourceId] || "outer bays";
  const moveHrs = recMove.hours_to_move || 8;
  const steps = recMove.can_improve
    ? [
        `Move ${moveHrs}h tasks out of ${sourceName} to Destiny Core.`,
        "Sleep inside water-wall racks tonight (Node 3 / Destiny).",
        "Keep non-essential outer window checks under 30 min.",
      ]
    : [
        "Continue work inside Destiny Core / Node 3 water-wall shelter.",
        "No shelter change needed unless a solar alert fires.",
      ];
  renderActionChecklist("rs-actions-list", `rad:${profile.id}`, steps);

  const shelterRows = [
    { id: "uslab", label: "Destiny Core", pct: 95, barCls: "", tag: "Safest", tagCls: "tag-safe" },
    { id: "node3", label: "Node 3 (Sleep)", pct: 86, barCls: "", tag: "Safest", tagCls: "tag-safe" },
    { id: "columbus", label: "Columbus Lab", pct: 54, barCls: "high", tag: "Limit Time", tagCls: "tag-limit" },
    { id: "jpm", label: "Kibo (JPM)", pct: 54, barCls: "high", tag: "Limit Time", tagCls: "tag-limit" },
    { id: "node1", label: "Node 1 (Unity)", pct: 42, barCls: "high", tag: "Limit Time", tagCls: "tag-limit" },
    { id: "cupola", label: "Cupola Dome", pct: state.stormOn ? 14 : 22, barCls: "crit", tag: "Avoid in Storm", tagCls: "tag-avoid" },
  ];

  $("rs-shelter-guide").innerHTML = shelterRows
    .map(
      (row) => `
      <div class="sbar-row">
        <span>${row.label}</span>
        <div class="sbar-track"><div class="sbar-fill ${row.barCls}" style="width:${row.pct}%"></div></div>
        <span class="sbar-tag ${row.tagCls}">${row.tag}</span>
      </div>
    `
    )
    .join("");

  const moveBtn = $("rs-apply-move-btn");
  moveBtn.disabled = !recMove.can_improve;
  moveBtn.textContent = recMove.can_improve ? "Move to Shielded Core Now" : "Optimal Shelter Active ✓";
}

function renderLevel3Engineer() {
  const crew = state.crewSimCache[state.activeCrewId];
  if (!crew) return;
  const profile = crew.profile;
  const rad = crew.rad;

  const isSimple = state.radMode === "simple";
  $("rad-simple-pane").classList.toggle("hidden", !isSimple);
  $("rad-eng-pane").classList.toggle("hidden", isSimple);
  $("rad-mode-simple").classList.toggle("active", isSimple);
  $("rad-mode-eng").classList.toggle("active", !isSimple);

  renderRadSimplePane(crew);

  if (isSimple) return;

  $("eng-crew-owner").textContent = profile.name;
  $("input-days").value = String(state.missionDays);
  $("input-career").value = String(profile.priorCareerMsv);

  $("kpi-cabin-daily").textContent = `${rad.daily_cabin_msv.toFixed(3)} mSv/d`;
  $("kpi-vessel-daily").textContent = `${rad.daily_vessel_avg_msv.toFixed(3)} mSv/d`;
  const deltaSign = rad.delta_vs_vessel_pct >= 0 ? "+" : "";
  $("kpi-delta").textContent = `${deltaSign}${rad.delta_vs_vessel_pct.toFixed(1)}%`;
  $("kpi-career").textContent = `${rad.career_pct_used.toFixed(1)}%`;
  $("kpi-career-sub").textContent = `${rad.career_total_msv.toFixed(1)} / ${rad.career_limit_msv} mSv`;

  const totalH = Object.values(profile.cabinHours).reduce((a, b) => a + Number(b || 0), 0);
  const needsNorm = Math.abs(totalH - 24) > 0.1;
  $("eng-hours-total").textContent = `TOTAL: ${totalH.toFixed(0)}/24H`;
  $("eng-hours-total").className = `triage-pill ${needsNorm ? "pill-warning" : "pill-nominal"}`;
  $("btn-normalize-24h").classList.toggle("hidden", !needsNorm);
  $("eng-hours-warn").classList.toggle("hidden", !needsNorm);

  // Render 6 ISS cabin hour sliders
  const rates = rad.simple_summary?.effective_rates_ugy_h || {};
  const sc = $("sliders-container");
  sc.innerHTML = Object.keys(CABIN_NAMES)
    .map((cid) => {
      const hrs = Number(profile.cabinHours[cid] || 0);
      const rate = rates[cid] || 25;
      return `
        <div class="slider-row">
          <span>${CABIN_NAMES[cid]}</span>
          <input type="range" min="0" max="24" step="1" value="${Math.round(hrs)}" data-cabin="${cid}" />
          <strong class="mono-num">${Math.round(hrs)}h</strong>
          <span class="mono-num">${rate.toFixed(1)} uGy/h</span>
        </div>
      `;
    })
    .join("");

  sc.querySelectorAll('input[type="range"]').forEach((inp) => {
    syncRangeTrack(inp);
    inp.addEventListener("change", async (e) => {
      profile.cabinHours[e.target.dataset.cabin] = Number(e.target.value);
      await simulateCrewMember(state.activeCrewId);
      renderAll();
    });
  });

  $("alara-guidance").textContent = rad.alara_guidance;
  $("alara-guidance").className = `alara-note ${rad.status || ""}`;
  $("eng-dosimeter-tag").textContent = state.dosimeterOnline ? "MEASURED" : "ESTIMATED";
  const rTm = TIER_META[tierFromStatus(rad.status)];
  $("rad-status-badge").className = `triage-pill ${rTm.pillClass}`;
  $("rad-status-badge").textContent = rad.status;

  // 24h Cumulative Curve
  const tc = chartThemeColors();
  const trace = rad.hourly_trace || [];
  if (state.charts.cumulative) state.charts.cumulative.destroy();
  state.charts.cumulative = new Chart($("cumulativeChart").getContext("2d"), {
    type: "line",
    data: {
      labels: trace.map((p) => p.label),
      datasets: [
        {
          label: "Cabin-Tracked (uSv)",
          data: trace.map((p) => p.cum_cabin_usv),
          borderColor: "#007aff",
          backgroundColor: "rgba(0, 122, 255, 0.14)",
          fill: true,
          tension: 0.25,
        },
        {
          label: "Naive Vessel Avg (uSv)",
          data: trace.map((p) => p.cum_vessel_avg_usv),
          borderColor: "#f97316",
          borderDash: [5, 4],
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { labels: { color: tc.legend, boxWidth: 12 } } },
      scales: {
        x: { ticks: { color: tc.tick, maxTicksLimit: 8 }, grid: { color: tc.grid } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    },
  });

  // NASA-STD-3001 Table
  const organs = state.standards?.radiation?.organs || {};
  const bfo = rad.bfo_30d_mgy_eq;
  const rows = [
    ["Effective Career Dose", "—", `${rad.career_limit_msv} mSv`, `${rad.career_total_msv.toFixed(1)} mSv (${rad.career_pct_used.toFixed(1)}%)`],
    ["BFO (Blood Forming Organs)", `${organs.bfo?.limit_30d || 250} mGy-Eq`, `${organs.bfo?.limit_career || 1500} mGy-Eq`, `${bfo.toFixed(1)} mGy-Eq / 30d`],
    ["Eye Lens", `${organs.lens?.limit_30d || 1000} mGy-Eq`, `${organs.lens?.limit_career || 4000} mGy-Eq`, `${(bfo * 1.05).toFixed(1)} mGy-Eq`],
    ["Skin", `${organs.skin?.limit_30d || 1500} mGy-Eq`, `${organs.skin?.limit_career || 6000} mGy-Eq`, `${(bfo * 1.15).toFixed(1)} mGy-Eq`],
  ];
  $("standards-tbody").innerHTML = rows
    .map((r) => `<tr><td><strong>${r[0]}</strong></td><td class="mono-num">${r[1]}</td><td class="mono-num">${r[2]}</td><td class="mono-num">${r[3]}</td></tr>`)
    .join("");

  // RadLab 23-day module bar chart
  const rem = state.remSummary?.cabins || {};
  const remKeys = Object.keys(CABIN_NAMES).filter((k) => rem[k]);
  if (state.charts.remHistory) state.charts.remHistory.destroy();
  state.charts.remHistory = new Chart($("remHistoryChart").getContext("2d"), {
    type: "bar",
    data: {
      labels: remKeys.map((k) => CABIN_NAMES[k]),
      datasets: [
        {
          label: "Mean Dose Rate (uGy/h)",
          data: remKeys.map((k) => rem[k].rem_mean_ugy_h),
          backgroundColor: remKeys.map((k) => (k === "cupola" ? "#ef4444" : k === "uslab" ? "#10b981" : "#007aff")),
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: tc.tick }, grid: { display: false } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    },
  });
}

/* ==================== 24H INTERACTIVE COMPANION SIMULATION ==================== */
function formatSimClock(totalMinutes) {
  const clamped = Math.max(0, Math.min(1440, Math.round(totalMinutes)));
  const hh = Math.floor(clamped / 60) % 24;
  const mm = clamped % 60;
  const day = clamped >= 1440 ? state.missionDays + 1 : state.missionDays;
  return `DAY ${String(day).padStart(3, "0")} · ${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")} UTC`;
}

function stopSimTimer() {
  if (state.sim.timerId) {
    clearInterval(state.sim.timerId);
    state.sim.timerId = null;
  }
  state.sim.playing = false;
}

function startSimTimer() {
  stopSimTimer();
  if (!state.sim.open) return;
  state.sim.playing = true;
  state.sim.timerId = setInterval(async () => {
    if (!state.sim.open || !state.sim.playing || state.sim.busy) return;

    // Hold calmly at Stage 2 (12:30 Heart + Air Alert) until crew fixes it or steps forward
    if (state.sim.stage === 2) {
      const anton = state.crewProfiles.anton;
      const stage2Resolved = !state.cabinAirAlert && anton.resolved.heart && anton.recordId === "ptt_s3_sit";
      if (!stage2Resolved) {
        stopSimTimer();
        renderSimCompanionBar();
        return;
      }
    }

    const nextMin = Math.min(1440, state.sim.minutes + 30);
    state.sim.minutes = nextMin;

    if (nextMin >= 1140 && state.sim.stage < 3) {
      await applySimStage(3, { keepPlaying: false });
      return;
    }
    if (nextMin >= 750 && state.sim.stage < 2) {
      await applySimStage(2, { keepPlaying: false });
      return;
    }
    if (nextMin >= 390 && state.sim.stage < 1) {
      await applySimStage(1, { keepPlaying: true });
      return;
    }
    if (nextMin >= 1440) {
      stopSimTimer();
    }
    renderSimCompanionBar();
  }, 650);
}

async function applySimStage(stageIdx, opts = {}) {
  if (state.sim.busy) return;
  state.sim.busy = true;
  try {
    state.sim.stage = stageIdx;
    const coreHours = { uslab: 14, node3: 8, columbus: 2, jpm: 0, node1: 0, cupola: 0 };

    if (stageIdx === 0) {
      state.sim.minutes = 0;
      state.sim.stepAntonPaused = false;
      state.stormOn = false;
      state.stormSheltered = false;
      state.cabinAirAlert = false;
      Object.values(state.crewProfiles).forEach((p) => {
        p.recordId = "ptt_s3_sit";
        p.ppCo2 = 1.8;
        p.sleepAlert = false;
        p.airAlert = false;
        p.limbsAlert = false;
        p.cabin = CABIN_NAMES.uslab;
        p.cabinHours = { ...coreHours };
        p.resolved = { head: true, lungs: true, heart: true, torso: true, limbs: true };
      });
      state.activeCrewId = "idan";
      state.activeZone = "torso";
    } else if (stageIdx === 1) {
      state.sim.minutes = 390; // 06:30
      state.sim.stepAntonPaused = false;
      state.stormOn = false;
      state.stormSheltered = false;
      state.cabinAirAlert = true;
      Object.values(state.crewProfiles).forEach((p) => {
        p.recordId = "ptt_s3_sit";
        p.sleepAlert = p.id === "sofia";
        p.airAlert = false;
        p.limbsAlert = p.id === "emily";
        p.cabinHours = { ...coreHours };
        p.resolved = {
          head: p.id !== "sofia",
          lungs: false,
          heart: true,
          torso: true,
          limbs: p.id !== "emily",
        };
      });
      state.activeCrewId = "emily";
      state.activeZone = "lungs";
    } else if (stageIdx === 2) {
      state.sim.minutes = 750; // 12:30
      state.sim.stepAntonPaused = false;
      state.stormOn = false;
      state.stormSheltered = false;
      state.cabinAirAlert = true;
      Object.values(state.crewProfiles).forEach((p) => {
        p.sleepAlert = false;
        p.airAlert = false;
        p.limbsAlert = false;
        p.resolved = { head: true, lungs: false, heart: p.id !== "anton", torso: true, limbs: true };
        p.recordId = p.id === "anton" ? "bidmc_12" : "ptt_s3_sit";
      });
      state.crewProfiles.anton.cabin = CABIN_NAMES.cupola;
      state.crewProfiles.anton.cabinHours = { uslab: 8, node3: 8, columbus: 2, jpm: 0, node1: 2, cupola: 4 };
      state.activeCrewId = "anton";
      state.activeZone = "heart";
      delete state.checkedSteps["cardio:anton"];
    } else {
      state.sim.minutes = 1140; // 19:00
      state.sim.stepAntonPaused = true;
      state.stormOn = false;
      state.stormSheltered = false;
      state.cabinAirAlert = false;
      Object.values(state.crewProfiles).forEach((p) => {
        p.recordId = "ptt_s3_sit";
        p.ppCo2 = 1.8;
        p.sleepAlert = false;
        p.airAlert = false;
        p.limbsAlert = false;
        p.cabin = CABIN_NAMES.uslab;
        p.cabinHours = { ...coreHours };
        p.resolved = { head: true, lungs: true, heart: true, torso: true, limbs: true };
      });
      state.activeCrewId = "anton";
      state.activeZone = "heart";
    }

    if (opts.keepPlaying === false) {
      stopSimTimer();
    } else if (opts.keepPlaying === true) {
      startSimTimer();
    }

    await refreshAllCrew();
  } finally {
    state.sim.busy = false;
  }
}

async function openSimDemo() {
  state.sim.open = true;
  await applySimStage(0, { keepPlaying: true });
}

function closeSimDemo() {
  stopSimTimer();
  state.sim.open = false;
  renderAll();
}

function renderSimCompanionBar() {
  const bar = $("sim-companion-bar");
  const topBtn = $("btn-demo-sim");
  const railBtn = $("rail-sim");
  if (topBtn) topBtn.classList.toggle("sim-running", state.sim.open);
  if (railBtn) railBtn.classList.toggle("sim-running", state.sim.open);
  if (!bar) return;

  bar.classList.toggle("hidden", !state.sim.open);
  if (!state.sim.open) return;

  const st = state.sim.stage;
  const anton = state.crewProfiles.anton;
  const emily = state.crewProfiles.emily;

  const airFixed = !state.cabinAirAlert;
  const emilyFixed = !(emily.limbsAlert && !emily.resolved.limbs);
  const pausedFixed = state.sim.stepAntonPaused || (anton.resolved.heart && anton.recordId === "ptt_s3_sit");
  const heartFixed = anton.resolved.heart && anton.recordId === "ptt_s3_sit";

  const clockEl = $("sim-clock");
  clockEl.textContent = formatSimClock(state.sim.minutes);
  const clockTier =
    st === 2 && !heartFixed
      ? "pill-critical"
      : (st === 1 && !(airFixed && emilyFixed)) || (st === 2 && !airFixed)
      ? "pill-warning"
      : "pill-nominal";
  clockEl.className = `triage-pill ${clockTier}`;

  const pct = Math.max(4, Math.min(100, Math.round((state.sim.minutes / 1440) * 100)));
  $("sim-progress-fill").style.width = `${pct}%`;

  bar.querySelectorAll(".sim-stage-btn").forEach((btn) => {
    const idx = Number(btn.dataset.stage);
    btn.classList.toggle("active", idx === st);
    btn.classList.toggle("done", idx < st || (idx === 3 && st === 3));
  });

  $("sim-play-btn").textContent = state.sim.playing ? "⏸ Pause" : "▶ Play";

  const coachBox = $("sim-coach-box");
  const badge = $("sim-coach-badge");
  const title = $("sim-coach-title");
  const msg = $("sim-coach-msg");
  const stepsEl = $("sim-coach-steps");
  const guideBtn = $("sim-guide-btn");
  const autoBtn = $("sim-autofix-btn");

  let boxCls = "sim-nominal";
  let badgeCls = "pill-nominal";
  let badgeText = "ONBOARD COMPANION · CALM WATCH";
  let titleText = "Morning Check: All 6 Crew Steady";
  let msgText =
    "Your onboard companion watches pulse, recovery, radiation & cabin air continuously — zero Earth wait needed.";
  let stepItems = [
    { text: "Sleep & oxygen steady", done: true },
    { text: "Cabin air clean", done: true },
    { text: "Next event at 06:30", done: false },
  ];
  let guideText = "Jump to 06:30 Event →";
  let autoText = "All Systems Green ✓";
  let autoDisabled = true;

  if (st === 1) {
    const allDone = airFixed && emilyFixed;
    boxCls = allDone ? "sim-nominal" : "sim-warning";
    badgeCls = allDone ? "pill-nominal" : "pill-warning";
    badgeText = allDone ? "COMPANION · MORNING CLEAR" : "COMPANION · HEADS-UP";
    titleText = allDone
      ? "06:30 Alerts Resolved — Crew Ready for Midday"
      : "Cabin Air Stale & Missed Workout Detected (20m Earth Delay)";
    msgText = allDone
      ? "Cabin air scrubber boosted for all 6 crew and Emily's 20m ARED + fluids logged. Advancing toward afternoon."
      : "Cabin CO2 climbed across all 6 modules and Emily skipped her morning workout. Fix both onboard right now:";
    stepItems = [
      { text: "1. Switch CDRA air scrubber to HIGH (All 6 Crew)", done: airFixed },
      { text: "2. Log 20m ARED + 500 mL fluids for Emily", done: emilyFixed },
    ];
    guideText = allDone ? "Next: 12:30 Watch →" : "Inspect Air / Body HUD →";
    autoDisabled = false;
    autoText = allDone ? "Advance to 12:30 →" : !airFixed ? "Step 1: Boost Cabin Air" : "Step 2: Log Emily Workout";
  } else if (st === 2) {
    const allDone = airFixed && pausedFixed && heartFixed;
    boxCls = allDone ? "sim-nominal" : heartFixed ? "sim-warning" : "sim-critical";
    badgeCls = allDone ? "pill-nominal" : heartFixed ? "pill-warning" : "pill-critical";
    badgeText = allDone
      ? "COMPANION · RECOVERED GREEN"
      : heartFixed
      ? "COMPANION · AIR CHECK LEFT"
      : "COMPANION · HEART + AIR ALERT";
    titleText = allDone
      ? "Anton Recovered — RED → GREEN!"
      : "Anton O2/Heart Strain + Cabin Air Alert (No Earth Wait)";
    msgText = allDone
      ? "Cabin air is clean and Anton's vitals returned to steady GREEN after seated rest & electrolytes. Ready to close out the day."
      : "Anton's vitals show strain while cabin CO2 is elevated. No need to wait 40 min for Earth — walk through these 3 calm steps:";
    stepItems = [
      { text: "1. Boost CDRA cabin scrubber to HIGH", done: airFixed },
      { text: "2. Pause Anton's work & drink 500 mL electrolytes", done: pausedFixed },
      { text: "3. Complete 30m seated rest → Heart GREEN", done: heartFixed },
    ];
    guideText = allDone ? "Advance to 19:00 Green →" : "Open Anton's Heart Card →";
    autoDisabled = false;
    autoText = allDone
      ? "Finish Day (19:00 GREEN) →"
      : !airFixed
      ? "Step 1: Fix Cabin Air"
      : !pausedFixed
      ? "Step 2: Pause & Hydrate Anton"
      : "Step 3: Finish Rest → GREEN";
  } else if (st === 3) {
    boxCls = "sim-nominal";
    badgeCls = "pill-nominal";
    badgeText = "COMPANION · ALL GREEN";
    titleText = "19:00 — Anton & All 6 Crew Back to GREEN";
    msgText =
      "Cabin air restored, Anton returned from RED to GREEN via onboard rest & electrolytes, and evening summary is queued to Earth.";
    stepItems = [
      { text: "Cabin air clean (all 6 crew)", done: true },
      { text: "Anton vitals steady (RED → GREEN)", done: true },
      { text: "All 6 crew GREEN for evening sleep", done: true },
    ];
    guideText = "View Crew Glance →";
    autoText = "↺ Replay 24h Demo";
    autoDisabled = false;
  }

  coachBox.className = `sim-coach-box ${boxCls}`;
  badge.className = `triage-pill ${badgeCls}`;
  badge.textContent = badgeText;
  title.textContent = titleText;
  msg.textContent = msgText;
  stepsEl.innerHTML = stepItems
    .map(
      (s) =>
        `<span class="sim-step-pill ${s.done ? "done" : ""}">${s.done ? "✓" : "○"} ${s.text}</span>`
    )
    .join("");
  guideBtn.textContent = guideText;
  autoBtn.textContent = autoText;
  autoBtn.disabled = autoDisabled;
}

async function handleSimGuideClick() {
  const st = state.sim.stage;
  if (st === 0) {
    await applySimStage(1, { keepPlaying: false });
  } else if (st === 1) {
    const airFixed = !state.cabinAirAlert;
    const emilyFixed = !(state.crewProfiles.emily.limbsAlert && !state.crewProfiles.emily.resolved.limbs);
    if (airFixed && emilyFixed) {
      await applySimStage(2, { keepPlaying: false });
    } else {
      stopSimTimer();
      state.activeCrewId = "emily";
      state.activeZone = !airFixed ? "lungs" : "limbs";
      state.bodyMode = "simple";
      setLevel("body");
      renderSimCompanionBar();
    }
  } else if (st === 2) {
    const anton = state.crewProfiles.anton;
    const allDone = !state.cabinAirAlert && anton.resolved.heart && anton.recordId === "ptt_s3_sit";
    if (allDone) {
      await applySimStage(3, { keepPlaying: false });
    } else {
      stopSimTimer();
      state.activeCrewId = "anton";
      state.cardioMode = "simple";
      setLevel("cardio");
      renderSimCompanionBar();
    }
  } else {
    setLevel("glance");
  }
}

async function handleSimAutofixClick() {
  const st = state.sim.stage;
  if (st === 1) {
    if (state.cabinAirAlert) {
      await resolveCabinAirAlertAllCrew();
      return;
    }
    const emily = state.crewProfiles.emily;
    if (emily.limbsAlert && !emily.resolved.limbs) {
      emily.resolved.limbs = true;
      await simulateCrewMember("emily");
      renderAll();
      return;
    }
    await applySimStage(2, { keepPlaying: false });
  } else if (st === 2) {
    if (state.cabinAirAlert) {
      await resolveCabinAirAlertAllCrew();
      return;
    }
    const anton = state.crewProfiles.anton;
    if (!state.sim.stepAntonPaused && !(anton.resolved.heart && anton.recordId === "ptt_s3_sit")) {
      state.sim.stepAntonPaused = true;
      state.activeCrewId = "anton";
      state.cardioMode = "simple";
      setLevel("cardio");
      renderSimCompanionBar();
      return;
    }
    if (!(anton.resolved.heart && anton.recordId === "ptt_s3_sit")) {
      anton.recordId = "ptt_s3_sit";
      anton.resolved.heart = true;
      anton.cabin = CABIN_NAMES.uslab;
      anton.cabinHours = { uslab: 14, node3: 8, columbus: 2, jpm: 0, node1: 0, cupola: 0 };
      delete state.checkedSteps["cardio:anton"];
      await simulateCrewMember("anton");
      renderAll();
      return;
    }
    await applySimStage(3, { keepPlaying: false });
  } else if (st === 3) {
    await applySimStage(0, { keepPlaying: true });
  }
}

/* ==================== INTEGRATED HAL2030: REPLAY, SENSORS, DOWNLINK, COMPANION ==================== */
async function fetchHalFrame(tSec, syncCrew = true) {
  const sec = Math.max(0, Math.min(599, Number(tSec || 0)));
  state.halT = sec;
  const resp = await fetch(`/api/hal/frame?t=${Math.floor(sec)}&crew_id=${encodeURIComponent(state.activeCrewId)}`);
  if (!resp.ok) return;
  state.halFrame = await resp.json();

  // Align active PhysioNet scenario to HAL timeline on critical crew events so In-Depth DSP tracks reality
  const s = state.halFrame.samples || {};
  if (state.crewProfiles.anton && !state.sim.open) {
    state.crewProfiles.anton.recordId = (s.anton?.values?.spo2 ?? 98) < 92 ? "bidmc_12" : "ptt_s3_sit";
    state.crewProfiles.idan.recordId = (s.idan?.values?.heart_rate ?? 72) > 110 ? "bidmc_16" : "ptt_s3_sit";
  }

  if (syncCrew) {
    await refreshAllCrew();
  } else {
    renderAll();
  }
}

function toggleHalReplay() {
  if (state.halPlaying) {
    if (state.halTimerId) clearInterval(state.halTimerId);
    state.halTimerId = null;
    state.halPlaying = false;
    renderHalReplayBar();
    return;
  }
  state.halPlaying = true;
  renderHalReplayBar();
  state.halTimerId = setInterval(async () => {
    const next = state.halT + state.halSpeed;
    if (next >= 599) {
      await fetchHalFrame(599, true);
      toggleHalReplay();
      return;
    }
    await fetchHalFrame(next, true);
  }, 1000);
}

function renderSensorsView() {
  const frame = state.halFrame;
  if (!frame) return;
  const rows = frame.sensor_matrix || [];
  const online = rows.filter((r) => r.link_state === "online").length;
  const missing = rows.filter((r) => r.link_state !== "online").length;
  const critical = rows.filter((r) => r.state === "critical").length;

  $("sensor-online-pill").textContent = `${online} / 42 ONLINE`;
  $("sensor-missing-pill").textContent = `${missing} NO SIGNAL`;
  $("sensor-critical-pill").textContent = `${critical} CRITICAL`;

  const cf = state.sensorFilter.crew;
  const sf = state.sensorFilter.state;
  const filtered = rows.filter(
    (r) => (cf === "all" || r.crew_id === cf) && (sf === "all" || r.state === sf)
  );

  $("sensor-matrix-tbody").innerHTML = filtered
    .map((r) => {
      const badgeCls = r.state === "critical" ? "pill-critical" : r.state === "warning" ? "pill-warning" : "pill-nominal";
      const badgeTxt = r.link_state !== "online" ? "NO SIGNAL" : r.state === "critical" ? "CRITICAL" : r.state === "warning" ? "ATTENTION" : "ONLINE";
      return `
        <tr class="sensor-row-click" data-crew="${r.crew_id}">
          <td><strong>${r.crew_name}</strong></td>
          <td>${r.sensor_name}</td>
          <td>${r.placement}</td>
          <td class="mono-num">${r.reading_display}</td>
          <td><span class="triage-pill ${badgeCls}">${badgeTxt}</span></td>
          <td class="mono-num">${r.quality_pct != null ? `${r.quality_pct}%` : "—"}</td>
          <td class="mono-num">${r.battery_pct != null ? `${Math.round(r.battery_pct)}%` : "—"}</td>
        </tr>`;
    })
    .join("");

  $("sensor-matrix-tbody").querySelectorAll(".sensor-row-click").forEach((tr) => {
    tr.addEventListener("click", () => {
      state.activeCrewId = tr.dataset.crew;
      const c = state.crewSimCache[state.activeCrewId];
      state.activeZone = c ? c.worstZone : "torso";
      setLevel("body");
    });
  });

  // Update Cabin CO2 & Hatch Trace Chart + live readouts
  const activeSample = frame.samples?.[state.activeCrewId];
  $("sensor-co2-now").textContent = activeSample?.cabin_co2 != null ? `${Math.round(activeSample.cabin_co2)} ppm` : "-- ppm";
  $("sensor-temp-now").textContent = activeSample?.cabin_temp != null ? `${activeSample.cabin_temp.toFixed(1)} °C` : "-- °C";

  const hist = frame.cabin_co2_history || { t: [], values: [] };
  const boosted = hist.values.map((v, idx) =>
    state.cabinAirAlert && idx >= hist.values.length - 12
      ? Math.round((v || 950) + (idx - (hist.values.length - 12)) * 95)
      : v
  );
  if ($("co2HatchChart") && typeof Chart !== "undefined") {
    const tc = chartThemeColors();
    if (state.charts.co2Hatch) state.charts.co2Hatch.destroy();
    state.charts.co2Hatch = new Chart($("co2HatchChart").getContext("2d"), {
      type: "line",
      data: {
        labels: hist.t.map((s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`),
        datasets: [
          {
            label: "Cabin CO2 (ppm)",
            data: boosted,
            borderColor: state.cabinAirAlert ? "#ef4444" : "#10b981",
            backgroundColor: state.cabinAirAlert ? "rgba(239,68,68,0.16)" : "rgba(16,185,129,0.14)",
            fill: true,
            pointRadius: 0,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: tc.tick, maxTicksLimit: 6 }, grid: { display: false } },
          y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
        },
      },
    });
  }

  drawCalibratedVisionSetup();
}

function handlePvtClick() {
  const btn = $("pvt-stim-btn");
  const lbl = $("pvt-stim-label");
  const sub = $("pvt-stim-sub");
  const pill = $("pvt-status-pill");

  if (state.pvt.phase === "idle" || state.pvt.phase === "done") {
    state.pvt.trials = [];
    state.pvt.phase = "wait";
    btn.className = "pvt-stim-btn pvt-wait";
    lbl.textContent = "WAIT FOR EMERALD FLASH...";
    sub.textContent = "Trial 1 of 5";
    pill.className = "triage-pill pill-warning";
    pill.textContent = "RUNNING";
    state.pvt.timeoutId = setTimeout(() => {
      state.pvt.phase = "go";
      state.pvt.startTs = performance.now();
      btn.className = "pvt-stim-btn pvt-go";
      lbl.textContent = "TAP NOW!";
      sub.textContent = `Trial ${state.pvt.trials.length + 1} of 5`;
    }, 1100 + Math.random() * 1100);
  } else if (state.pvt.phase === "wait") {
    sub.textContent = "Too early — wait for emerald flash!";
  } else if (state.pvt.phase === "go") {
    const rt = Math.round(performance.now() - state.pvt.startTs);
    state.pvt.trials.push(rt);
    const mean = Math.round(state.pvt.trials.reduce((a, b) => a + b, 0) / state.pvt.trials.length);
    $("pvt-mean-ms").textContent = `${mean} ms`;
    $("pvt-trial-count").textContent = `${state.pvt.trials.length} / 5`;

    if (state.pvt.trials.length >= 5) {
      state.pvt.phase = "done";
      state.pvt.lastMeanMs = mean;
      btn.className = "pvt-stim-btn pvt-idle";
      lbl.textContent = `COMPLETE · ${mean} MS (TAP TO RE-RUN)`;
      sub.textContent = mean >= 330 ? "Reaction slowed — rest advised" : "Nominal cognitive readiness";
      pill.className = `triage-pill ${mean >= 330 ? "pill-warning" : "pill-nominal"}`;
      pill.textContent = mean >= 330 ? "SLOWED" : "NOMINAL";
      simulateCrewMember(state.activeCrewId).then(() => renderAll());
    } else {
      state.pvt.phase = "wait";
      btn.className = "pvt-stim-btn pvt-wait";
      lbl.textContent = `LAST: ${rt} MS · WAIT...`;
      sub.textContent = `Trial ${state.pvt.trials.length + 1} of 5`;
      state.pvt.timeoutId = setTimeout(() => {
        state.pvt.phase = "go";
        state.pvt.startTs = performance.now();
        btn.className = "pvt-stim-btn pvt-go";
        lbl.textContent = "TAP NOW!";
      }, 1000 + Math.random() * 1000);
    }
  }
}

async function fetchDownlinkState() {
  const resp = await fetch("/api/hal/downlink");
  if (!resp.ok) return;
  state.downlink = await resp.json();
  renderDownlinkView();
  renderHalReplayBar();
}

async function enqueueDownlinkSnapshot() {
  const resp = await fetch("/api/hal/downlink/enqueue", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ t: state.halT }),
  });
  if (!resp.ok) return;
  const data = await resp.json();
  state.downlink = data.state;
  state.selectedPacketId = data.packet.id;
  await inspectDownlinkPacket(data.packet.id);
  renderDownlinkView();
  renderHalReplayBar();
}

async function inspectDownlinkPacket(pktId) {
  state.selectedPacketId = pktId;
  const resp = await fetch(`/api/hal/downlink/packet/${encodeURIComponent(pktId)}`);
  if (!resp.ok) return;
  const payload = await resp.json();
  $("dl-inspect-id").textContent = pktId;
  $("dl-packet-json").textContent = JSON.stringify(payload, null, 2);
}

function renderDownlinkView() {
  const dl = state.downlink;
  if (!dl) return;
  $("dl-status-pill").textContent = dl.status_text;
  $("dl-status-pill").className = `triage-pill ${dl.connected ? "pill-nominal" : "pill-warning"}`;
  $("dl-conn-btn").textContent = dl.connected ? "Ground Link: ONLINE" : "Ground Link: OFFLINE";
  $("dl-conn-btn").classList.toggle("active", dl.connected);
  $("dl-latency-select").value = String(dl.latency_s);
  $("dl-export-link").href = `/api/hal/downlink/export?t=${Math.floor(state.halT)}`;

  $("dl-total-val").textContent = String(dl.total_packets);
  $("dl-queued-val").textContent = String(dl.queued_count);
  $("dl-transit-val").textContent = String(dl.in_transit_count);
  $("dl-delivered-val").textContent = String(dl.delivered_count);

  $("dl-queue-tbody").innerHTML = dl.queue.length
    ? dl.queue
        .map((p) => {
          const stCls = p.status === "delivered" ? "pill-nominal" : "pill-warning";
          const etaTxt = p.status === "delivered" ? "0s (Delivered)" : `${Math.ceil(p.eta_s)}s`;
          return `
            <tr>
              <td class="mono-num"><strong>${p.id}</strong></td>
              <td class="mono-num">T+${String(Math.floor(p.mission_time / 60)).padStart(2, "0")}:${String(Math.floor(p.mission_time % 60)).padStart(2, "0")}</td>
              <td><span class="triage-pill ${stCls}">${p.status.toUpperCase()}</span></td>
              <td class="mono-num">${etaTxt}</td>
              <td><button class="eng-btn dl-inspect-btn" data-pkt="${p.id}" type="button">Inspect JSON</button></td>
            </tr>`;
        })
        .join("")
    : `<tr><td colspan="5">Outbox empty. Click "Queue Telemetry Snapshot" to queue local health packet.</td></tr>`;

  $("dl-queue-tbody").querySelectorAll(".dl-inspect-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setDownlinkMode("depth");
      inspectDownlinkPacket(btn.dataset.pkt);
    });
  });
}

function setSensorsMode(mode) {
  state.sensorsMode = mode === "depth" ? "depth" : "quick";
  const depth = state.sensorsMode === "depth";
  $("sensors-mode-quick")?.classList.toggle("active", !depth);
  $("sensors-mode-depth")?.classList.toggle("active", depth);
  $("sensors-toolbar-row")?.classList.toggle("hidden", !depth);
  $("sensor-matrix-card")?.classList.toggle("hidden", !depth);
}

function setDownlinkMode(mode) {
  state.downlinkMode = mode === "depth" ? "depth" : "quick";
  const depth = state.downlinkMode === "depth";
  $("downlink-mode-quick")?.classList.toggle("active", !depth);
  $("downlink-mode-depth")?.classList.toggle("active", depth);
  $("dl-disclaimer-card")?.classList.toggle("hidden", !depth);
  $("dl-json-inspector-card")?.classList.toggle("hidden", !depth);
  $("dl-split-grid")?.classList.toggle("dl-compact", !depth);
}

function renderCompanionView() {
  const cid = state.comp.crewId;
  const profile = state.crewProfiles[cid] || Object.values(state.crewProfiles)[0];
  $("comp-crew-bar").querySelectorAll(".crew-chip").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.crew === cid);
  });
  $("comp-mode-hal").classList.toggle("active", !state.comp.familyMode);
  $("comp-mode-family").classList.toggle("active", state.comp.familyMode);
  $("comp-person-name").textContent = profile.name;
  $("comp-mode-note").textContent = state.comp.familyMode
    ? "FAMILY SIMULATION · Fictional sample replies. Not real contact with family."
    : "SCRIPTED COMPANION · Prepared local responses only. No LLM connected.";
  $("comp-mode-note").classList.toggle("mode-family", state.comp.familyMode);

  const hist = state.comp.histories[cid] || [];
  $("comp-transcript").innerHTML = hist
    .map(
      (m) => `
      <div class="comp-msg msg-${m.kind}">
        <div class="comp-msg-speaker">${m.speaker}</div>
        <div class="comp-msg-text">${m.text}</div>
      </div>`
    )
    .join("");
  $("comp-transcript").scrollTop = $("comp-transcript").scrollHeight;
}

async function sendCompanionText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) return;
  const cid = state.comp.crewId;
  const profile = state.crewProfiles[cid];
  state.comp.histories[cid].push({ speaker: profile.name, kind: "user", text });
  renderCompanionView();

  const resp = await fetch("/api/hal/companion/reply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ crew_id: cid, text, family_mode: state.comp.familyMode, t: state.halT }),
  });
  if (resp.ok) {
    const data = await resp.json();
    state.comp.histories[cid].push({ speaker: data.speaker, kind: data.kind, text: data.reply });
    renderCompanionView();
    if (state.sans.narration && data.reply) {
      speakTextNatural(data.reply);
    }
  }
}

function toggleCompanionVoiceDemo() {
  toggleVoiceRecording("companion");
}

function renderCurrentLevel() {
  if (state.level === "glance") renderLevel1Glance();
  else if (state.level === "body") renderLevel2Body();
  else if (state.level === "cardio") renderLevel3Cardio();
  else if (state.level === "engineer") renderLevel3Engineer();
  else if (state.level === "sensors") renderSensorsView();
  else if (state.level === "downlink") renderDownlinkView();
  else if (state.level === "companion") renderCompanionView();
}

function renderAll() {
  renderShellHeader();
  renderSimCompanionBar();
  renderCurrentLevel();
  checkGentleAudioAlerts();
}

/* ==================== EVENT WIRING ==================== */
function bindEvents() {
  // VisionOS Rail & Header Navigation
  $("rail-glance").addEventListener("click", () => setLevel("glance"));
  $("rail-checkins")?.addEventListener("click", () => setLevel("checkins"));
  $("rail-body").addEventListener("click", () => setLevel("body"));
  $("rail-cardio").addEventListener("click", () => setLevel("cardio"));
  $("rail-engineer").addEventListener("click", () => setLevel("engineer"));
  $("rail-sensors").addEventListener("click", () => setLevel("sensors"));
  $("rail-biosense").addEventListener("click", () => setLevel("biosense"));
  $("rail-medhub")?.addEventListener("click", () => {
    setLevel("medhub");
    if (typeof loadClinicalHub === "function") loadClinicalHub();
  });
  $("rail-downlink").addEventListener("click", () => setLevel("downlink"));
  $("rail-companion").addEventListener("click", () => {
    state.comp.crewId = state.activeCrewId;
    setLevel("companion");
  });
  $("btn-back-glance").addEventListener("click", () => setLevel("glance"));
  $("btn-glance-radlab").addEventListener("click", () => setLevel("engineer"));
  $("btn-ov-top-priority")?.addEventListener("click", () => {
    state.activeCrewId = state._lowestCrewId || "anton";
    state.activeZone = state._lowestZone || "heart";
    state.bodyMode = "simple";
    setLevel("body");
  });
  $("btn-open-rad-from-l2").addEventListener("click", () => setLevel("engineer"));
  $("btn-open-cardio-lab").addEventListener("click", () => setLevel("cardio"));
  $("header-active-avatar").addEventListener("click", () => {
    state.bodyMode = "simple";
    setLevel("body");
  });
  $("btn-l2-pvt")?.addEventListener("click", () => setLevel("sensors"));
  $("btn-l2-sans")?.addEventListener("click", () => setLevel("sensors"));
  $("btn-l2-sensors")?.addEventListener("click", () => setLevel("sensors"));

  // HAL2030 10-Min Live Replay Controls
  $("hal-play-btn")?.addEventListener("click", toggleHalReplay);
  $("hal-speed-btn")?.addEventListener("click", () => {
    state.halSpeed = state.halSpeed === 1 ? 5 : state.halSpeed === 5 ? 10 : 1;
    renderHalReplayBar();
  });
  $("hal-scrubber")?.addEventListener("change", (e) => fetchHalFrame(Number(e.target.value), true));
  $("hal-scenario-select")?.addEventListener("change", (e) => fetchHalFrame(Number(e.target.value), true));
  $("hal-quick-downlink")?.addEventListener("click", async () => {
    await enqueueDownlinkSnapshot();
    setLevel("downlink");
  });

  // Sensors, PVT, SANS & CO2 Hatch Controls
  $("sensors-mode-quick")?.addEventListener("click", () => setSensorsMode("quick"));
  $("sensors-mode-depth")?.addEventListener("click", () => setSensorsMode("depth"));
  $("downlink-mode-quick")?.addEventListener("click", () => setDownlinkMode("quick"));
  $("downlink-mode-depth")?.addEventListener("click", () => setDownlinkMode("depth"));
  $("sensor-crew-filter")?.addEventListener("change", (e) => {
    state.sensorFilter.crew = e.target.value;
    renderSensorsView();
  });
  $("sensor-state-filter")?.addEventListener("change", (e) => {
    state.sensorFilter.state = e.target.value;
    renderSensorsView();
  });
  $("pvt-stim-btn")?.addEventListener("click", handlePvtClick);
  $("pvt-reset-btn")?.addEventListener("click", () => {
    if (state.pvt.timeoutId) clearTimeout(state.pvt.timeoutId);
    state.pvt = { phase: "idle", trials: [], startTs: 0, timeoutId: null, lastMeanMs: null };
    $("pvt-stim-btn").className = "pvt-stim-btn pvt-idle";
    $("pvt-stim-label").textContent = "TAP TO START 5-TRIAL CHECK";
    $("pvt-stim-sub").textContent = "Nominal baseline < 280 ms · Auto-logs to crew fatigue";
    $("pvt-mean-ms").textContent = "-- ms";
    $("pvt-trial-count").textContent = "0 / 5";
    $("pvt-status-pill").className = "triage-pill pill-nominal";
    $("pvt-status-pill").textContent = "READY";
    simulateCrewMember(state.activeCrewId).then(() => renderAll());
  });
  $("sans-cal-x")?.addEventListener("input", (e) => {
    state.sans.pxPerMmX = Number(e.target.value || 4.0);
    $("sans-cal-x-val").textContent = state.sans.pxPerMmX.toFixed(1);
    drawCalibratedVisionSetup();
  });
  $("sans-cal-y")?.addEventListener("input", (e) => {
    state.sans.pxPerMmY = Number(e.target.value || 4.0);
    $("sans-cal-y-val").textContent = state.sans.pxPerMmY.toFixed(1);
    drawCalibratedVisionSetup();
  });
  $("sans-start-btn")?.addEventListener("click", startCalibratedVisionExam);
  $("sans-btn-up")?.addEventListener("click", () => handleVisionResponse("up"));
  $("sans-btn-down")?.addEventListener("click", () => handleVisionResponse("down"));
  $("sans-btn-left")?.addEventListener("click", () => handleVisionResponse("left"));
  $("sans-btn-right")?.addEventListener("click", () => handleVisionResponse("right"));
  $("sans-btn-unable")?.addEventListener("click", () => handleVisionResponse("unable"));
  $("sans-btn-confirm")?.addEventListener("click", () => confirmPendingVisionResponse());
  $("sans-btn-repeat")?.addEventListener("click", () => {
    const msg = $("sans-guidance-text")?.textContent;
    if (msg) speakTextNatural(msg);
  });
  $("sans-btn-back")?.addEventListener("click", () => {
    if (state.sans.pendingCmd) {
      state.sans.pendingCmd = null;
      $("sans-pending-bar")?.classList.add("hidden");
    } else {
      startVisionEyePhase(state.sans.eye);
    }
  });
  $("sans-btn-abort")?.addEventListener("click", () => resetCalibratedVisionToSetup());
  $("sans-retest-btn")?.addEventListener("click", () => resetCalibratedVisionToSetup());
  $("sans-queue-report-btn")?.addEventListener("click", queueCalibratedVisionReport);
  $("sans-voice-mic-btn")?.addEventListener("click", () => toggleVoiceRecording("vision"));
  $("sans-voice-mute-btn")?.addEventListener("click", () => {
    state.sans.narration = !state.sans.narration;
    $("sans-voice-mute-btn").textContent = state.sans.narration ? "🔊 Voice: ON" : "🔇 Voice: Muted";
    $("sans-voice-mute-btn").classList.toggle("active", state.sans.narration);
  });
  $("top-voice-btn")?.addEventListener("click", () => toggleVoiceRecording("global"));
  $("top-chime-btn")?.addEventListener("click", () => {
    const aa = state.audioAlert;
    // NASA-STD-3001 manual silence: first tap while speaking stops voice immediately without disabling alerts
    if (aa.speakingAlert) {
      cancelAlertSpeech();
      updateAlertAudioChip();
      return;
    }
    if (aa.enabled && aa.speechEnabled) {
      aa.speechEnabled = false;
    } else if (aa.enabled && !aa.speechEnabled) {
      aa.enabled = false;
    } else {
      aa.enabled = true;
      aa.speechEnabled = true;
    }
    updateAlertAudioChip();
    if (aa.enabled) playGentleChime("preview", true);
  });
  updateAlertAudioChip();

  document.querySelectorAll('input[type="range"]').forEach((el) => syncRangeTrack(el));
  document.addEventListener("input", (e) => {
    if (e.target && e.target.matches && e.target.matches('input[type="range"]')) {
      syncRangeTrack(e.target);
    }
  });

  // Unlock Web Audio cleanly on first user interaction so later alerts can chime gently
  const _unlockAudio = () => {
    ensureAudioCtx(true);
    window.removeEventListener("pointerdown", _unlockAudio);
    window.removeEventListener("keydown", _unlockAudio);
  };
  window.addEventListener("pointerdown", _unlockAudio, { passive: true });
  window.addEventListener("keydown", _unlockAudio, { passive: true });

  document.addEventListener("keydown", (e) => {
    if (state.level !== "sensors" || state.sans.stage !== "test") return;
    if (e.key === "ArrowUp") { e.preventDefault(); handleVisionResponse("up"); }
    else if (e.key === "ArrowDown") { e.preventDefault(); handleVisionResponse("down"); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); handleVisionResponse("left"); }
    else if (e.key === "ArrowRight") { e.preventDefault(); handleVisionResponse("right"); }
    else if (e.key === " " && state.sans.pendingCmd) { e.preventDefault(); confirmPendingVisionResponse(); }
  });
  $("co2-hatch-toggle-btn")?.addEventListener("click", async () => {
    state.cabinAirAlert = !state.cabinAirAlert;
    $("co2-hatch-toggle-btn").textContent = state.cabinAirAlert ? "Clear Hatch Spike" : "Simulate Hatch Spike";
    await refreshAllCrew();
  });

  // Downlink Store-and-Forward Queue Controls
  $("dl-conn-btn")?.addEventListener("click", async () => {
    const next = !(state.downlink?.connected ?? true);
    const resp = await fetch("/api/hal/downlink/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ connected: next }),
    });
    if (resp.ok) {
      state.downlink = await resp.json();
      renderDownlinkView();
      renderHalReplayBar();
    }
  });
  $("dl-latency-select")?.addEventListener("change", async (e) => {
    const resp = await fetch("/api/hal/downlink/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latency_s: Number(e.target.value) }),
    });
    if (resp.ok) {
      state.downlink = await resp.json();
      renderDownlinkView();
    }
  });
  $("dl-send-btn")?.addEventListener("click", enqueueDownlinkSnapshot);

  // HAL2030 Private Cabin Companion Controls
  $("comp-crew-bar")?.querySelectorAll(".crew-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.comp.crewId = btn.dataset.crew;
      renderCompanionView();
    });
  });
  $("comp-mode-hal")?.addEventListener("click", () => {
    state.comp.familyMode = false;
    renderCompanionView();
  });
  $("comp-mode-family")?.addEventListener("click", () => {
    state.comp.familyMode = true;
    renderCompanionView();
  });
  $("comp-voice-btn")?.addEventListener("click", toggleCompanionVoiceDemo);
  $("comp-clear-btn")?.addEventListener("click", () => {
    const cid = state.comp.crewId;
    state.comp.histories[cid] = [
      { speaker: "HAL2030 · scripted preview", kind: "assistant", text: "Session cleared. Ready whenever you want to talk." },
    ];
    renderCompanionView();
  });
  document.querySelectorAll(".comp-prompt-btn").forEach((btn) => {
    btn.addEventListener("click", () => sendCompanionText(btn.dataset.prompt));
  });
  $("comp-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const inp = $("comp-input");
    const val = inp.value;
    inp.value = "";
    await sendCompanionText(val);
  });

  // 24h Companion Simulation Demo controls
  const toggleSimDemo = async () => {
    if (state.sim.open) {
      closeSimDemo();
    } else {
      await openSimDemo();
    }
  };
  $("btn-demo-sim").addEventListener("click", toggleSimDemo);
  $("rail-sim").addEventListener("click", toggleSimDemo);
  $("sim-play-btn").addEventListener("click", () => {
    if (state.sim.playing) {
      stopSimTimer();
    } else {
      startSimTimer();
    }
    renderSimCompanionBar();
  });
  $("sim-next-btn").addEventListener("click", async () => {
    const nextStage = Math.min(3, state.sim.stage + 1);
    await applySimStage(nextStage, { keepPlaying: false });
  });
  $("sim-reset-btn").addEventListener("click", async () => {
    await applySimStage(0, { keepPlaying: true });
  });
  $("sim-close-btn").addEventListener("click", closeSimDemo);
  $("sim-companion-bar").querySelectorAll(".sim-stage-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const stageIdx = Number(btn.dataset.stage || 0);
      await applySimStage(stageIdx, { keepPlaying: false });
    });
  });
  $("sim-guide-btn").addEventListener("click", handleSimGuideClick);
  $("sim-autofix-btn").addEventListener("click", handleSimAutofixClick);

  // Theme toggles
  $("theme-day").addEventListener("click", () => setTheme("day"));
  $("theme-night").addEventListener("click", () => setTheme("night"));
  $("rail-theme").addEventListener("click", () => setTheme(state.theme === "day" ? "night" : "day"));

  // Cabin Air Alert, Crew-Wide Banner, Solar Storm & Dosimeter toggles
  $("top-btn-atmo").addEventListener("click", async () => {
    state.cabinAirAlert = !state.cabinAirAlert;
    await refreshAllCrew();
  });
  $("cwb-action-btn").addEventListener("click", resolveCrewWideAlert);

  const toggleStorm = async () => {
    state.stormOn = !state.stormOn;
    if (state.stormOn) state.stormSheltered = false;
    await refreshAllCrew();
  };
  $("top-btn-storm").addEventListener("click", toggleStorm);
  $("rail-storm").addEventListener("click", toggleStorm);
  $("top-btn-dosimeter").addEventListener("click", async () => {
    state.dosimeterOnline = !state.dosimeterOnline;
    await refreshAllCrew();
  });

  // Top notification bell jumps to highest priority astronaut checklist
  $("notif-bell-btn").addEventListener("click", () => {
    const sorted = getSortedCrewList();
    if (sorted.length) {
      state.activeCrewId = sorted[0].profile.id;
      state.activeZone = sorted[0].worstZone;
      state.bodyMode = "simple";
      setLevel("body");
    }
  });

  // Level 2 Crew Action (Simple) vs Body Map mode & shortcuts
  $("body-mode-simple")?.addEventListener("click", () => setBodyMode("simple"));
  $("body-mode-map")?.addEventListener("click", () => setBodyMode("map"));
  $("csa-open-map-btn")?.addEventListener("click", () => setBodyMode("map"));
  $("csa-open-heart-btn")?.addEventListener("click", () => {
    state.cardioMode = "simple";
    setLevel("cardio");
  });
  $("csa-open-rad-btn")?.addEventListener("click", () => {
    state.radMode = "simple";
    setLevel("engineer");
  });
  $("csa-do-all-btn")?.addEventListener("click", async () => {
    if (state._topSimpleTask) {
      await executeSimpleTaskAction(state.activeCrewId, state._topSimpleTask);
    }
  });

  // Level 2 Crew switcher bar
  $("level2-crew-bar").querySelectorAll(".crew-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cid = btn.dataset.crew;
      const crew = state.crewSimCache[cid];
      state.activeCrewId = cid;
      state.activeZone = crew ? crew.worstZone : "torso";
      state.cardioMode = "simple";
      state.radMode = "simple";
      state.previewActive = false;
      renderAll();
    });
  });

  // Body Hotspots
  document.querySelectorAll(".body-hotspot").forEach((hs) => {
    hs.addEventListener("click", () => {
      state.activeZone = hs.dataset.zone;
      state.previewActive = false;
      renderLevel2Body();
    });
  });

  $("hero-jump-btn").addEventListener("click", () => {
    const crew = state.crewSimCache[state.activeCrewId];
    if (crew) {
      state.activeZone = crew.worstZone;
      state.previewActive = false;
      setBodyMode("map");
    }
  });

  $("zone-float-mobile-cta").addEventListener("click", () => {
    $("action-glass-card").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  $("btn-zone-preview").addEventListener("click", () => {
    state.previewActive = !state.previewActive;
    renderLevel2Body();
  });

  $("btn-zone-apply").addEventListener("click", applyCurrentZoneIntervention);

  // Level 3A Heart Simple / Engineer mode toggle & primary resolution
  const setCardioMode = (mode) => {
    state.cardioMode = mode;
    setLevel("cardio");
  };
  $("cardio-mode-simple").addEventListener("click", () => setCardioMode("simple"));
  $("cardio-mode-eng").addEventListener("click", () => setCardioMode("eng"));
  $("cs-open-deep-btn").addEventListener("click", () => setCardioMode("eng"));
  $("cs-apply-primary-btn").addEventListener("click", async (e) => {
    const mode = e.currentTarget.dataset.actionMode;
    const cid = state.activeCrewId;
    const profile = state.crewProfiles[cid];
    if (!profile || mode === "none") return;

    if (mode === "resolve-air") {
      await resolveCabinAirAlertAllCrew();
      return;
    }
    if (mode === "resolve-limbs") {
      profile.resolved.limbs = true;
    } else if (mode === "resolve-heart") {
      profile.recordId = "ptt_s3_sit";
      profile.resolved.heart = true;
    }
    delete state.checkedSteps[`cardio:${cid}`];
    await simulateCrewMember(cid);
    renderAll();
  });

  // Level 3A Cardio Engineer controls
  $("cardio-record-btns").querySelectorAll(".eng-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const profile = state.crewProfiles[state.activeCrewId];
      profile.recordId = btn.dataset.record;
      profile.resolved.heart = profile.recordId === "ptt_s3_sit";
      delete state.checkedSteps[`cardio:${state.activeCrewId}`];
      await simulateCrewMember(state.activeCrewId);
      renderAll();
    });
  });

  $("cardio-atmo-select").addEventListener("change", async (e) => {
    state.crewProfiles[state.activeCrewId].atmoProfile = e.target.value;
    await simulateCrewMember(state.activeCrewId);
    renderAll();
  });

  $("cardio-ppco2").addEventListener("change", async (e) => {
    state.crewProfiles[state.activeCrewId].ppCo2 = Number(e.target.value || 1.9);
    await simulateCrewMember(state.activeCrewId);
    renderAll();
  });

  // Level 3B Radiation Simple / Engineer mode toggle & shelter move
  const setRadMode = (mode) => {
    state.radMode = mode;
    setLevel("engineer");
  };
  $("rad-mode-simple").addEventListener("click", () => setRadMode("simple"));
  $("rad-mode-eng").addEventListener("click", () => setRadMode("eng"));
  $("rs-open-deep-btn").addEventListener("click", () => setRadMode("eng"));
  $("rs-apply-move-btn").addEventListener("click", async () => {
    const cid = state.activeCrewId;
    const profile = state.crewProfiles[cid];
    const crew = state.crewSimCache[cid];
    const rec = crew?.rad?.simple_summary?.recommended_action;
    if (!profile || !rec || !rec.preview_cabin_hours) return;
    profile.cabinHours = { ...rec.preview_cabin_hours };
    profile.cabin = CABIN_NAMES.uslab;
    delete state.checkedSteps[`rad:${cid}`];
    await simulateCrewMember(cid);
    renderAll();
  });

  // Level 3B Radiation Lab presets & inputs
  const presets = {
    "btn-preset-nominal": { uslab: 11, node3: 8, columbus: 2, jpm: 2, node1: 1, cupola: 0 },
    "btn-preset-high": { uslab: 3, node3: 6, columbus: 2, jpm: 1, node1: 4, cupola: 8 },
    "btn-preset-alara": { uslab: 16, node3: 8, columbus: 0, jpm: 0, node1: 0, cupola: 0 },
  };
  Object.entries(presets).forEach(([id, hours]) => {
    $(id).addEventListener("click", async () => {
      Object.keys(presets).forEach((bid) => $(bid).classList.toggle("active", bid === id));
      state.crewProfiles[state.activeCrewId].cabinHours = { ...hours };
      await simulateCrewMember(state.activeCrewId);
      renderAll();
    });
  });

  $("btn-normalize-24h").addEventListener("click", async () => {
    const ch = state.crewProfiles[state.activeCrewId].cabinHours;
    const tot = Object.values(ch).reduce((a, b) => a + Number(b || 0), 0) || 1;
    Object.keys(ch).forEach((k) => {
      ch[k] = Math.round((ch[k] / tot) * 24);
    });
    await simulateCrewMember(state.activeCrewId);
    renderAll();
  });

  $("input-days").addEventListener("change", async (e) => {
    state.missionDays = Math.max(1, Math.min(365, Number(e.target.value || 30)));
    await refreshAllCrew();
  });

  $("input-career").addEventListener("change", async (e) => {
    state.crewProfiles[state.activeCrewId].priorCareerMsv = Math.max(0, Math.min(590, Number(e.target.value || 120)));
    await simulateCrewMember(state.activeCrewId);
    renderAll();
  });
}

async function init() {
  bindEvents();
  const [stdRes, baseRes, halRes, dlRes, voiceRes] = await Promise.all([
    fetch("/api/standards").then((r) => r.json()),
    fetch("/api/radiation/baseline").then((r) => r.json()),
    fetch(`/api/hal/frame?t=${state.halT}`).then((r) => r.json()),
    fetch("/api/hal/downlink").then((r) => r.json()),
    fetch("/api/hal/voice/status").then((r) => (r.ok ? r.json() : null)).catch(() => null),
  ]);
  state.standards = stdRes;
  state.remSummary = baseRes.rem_summary;
  state.halFrame = halRes;
  state.downlink = dlRes;
  if (voiceRes) {
    state.voice.ttsReady = Boolean(voiceRes.tts_ready);
    state.voice.sttReady = Boolean(voiceRes.stt_ready);
    state.voice.ttsEngine = voiceRes.tts_engine || "browser-fallback";
    state.voice.sttEngine = voiceRes.stt_engine || "browser-fallback";
    state.voice.recommendedVoice = voiceRes.recommended_voice || "af_heart";
    updateVoiceIndicators(
      "off",
      state.voice.ttsReady
        ? `Natural Voice Ready (${state.voice.ttsEngine})`
        : "Kokoro offline · Browser Fallback active"
    );
  } else {
    state.voice.ttsReady = false;
    state.voice.sttReady = false;
    updateVoiceIndicators("off", "Voice status unavailable · Browser Fallback");
  }
  initVoiceAudioUnlock();
  initAmbientBlurParallax();
  if (baseRes.vitals) {
    state.vitalsMemo["ptt_s3_sit|iss_nominal|1.9"] = baseRes.vitals;
  }

  // Advance any in-transit downlink packets calmly every second when link is connected
  if (!state.downlinkTimerId) {
    state.downlinkTimerId = setInterval(async () => {
      if (state.downlink && state.downlink.connected && state.downlink.in_transit_count > 0) {
        const resp = await fetch("/api/hal/downlink/tick", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ elapsed_s: 1.0 }),
        });
        if (resp.ok) {
          state.downlink = await resp.json();
          if (state.level === "downlink") renderDownlinkView();
          renderHalReplayBar();
        }
      }
    }, 1000);
  }

  await refreshAllCrew();
  // Select the most urgent crew member as initial active focus while landing on Level 1 Glance
  const sorted = getSortedCrewList();
  if (sorted.length) {
    state.activeCrewId = sorted[0].profile.id;
    state.activeZone = sorted[0].worstZone;
  }
  setLevel("glance");
}

document.addEventListener("DOMContentLoaded", init);


/* ==================== REAL-TIME GAUSSIAN BLUR PARALLAX ==================== */
function initAmbientBlurParallax() {
  let rafPending = false;
  window.addEventListener("pointermove", (e) => {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      const dx = (e.clientX / Math.max(window.innerWidth, 1) - 0.5) * -28;
      const dy = (e.clientY / Math.max(window.innerHeight, 1) - 0.5) * -22;
      document.documentElement.style.setProperty("--orb-px", `${dx.toFixed(1)}px`);
      document.documentElement.style.setProperty("--orb-py", `${dy.toFixed(1)}px`);
    });
  }, { passive: true });
}

/* ==================== LIGHTWEIGHT CPU NATURAL VOICE ENGINE ==================== */
function voiceIdleMessage() {
  return state.voice.ttsReady
    ? "Kokoro natural voice ready · Click Mic to speak"
    : "Browser fallback voice · Click Mic to speak";
}

function initVoiceAudioUnlock() {
  const unlock = () => {
    if (state.voice.audioUnlocked) return;
    state.voice.audioUnlocked = true;
    ensureAudioCtx(true);
    const pending = state.voice.pendingPlayText;
    state.voice.pendingPlayText = null;
    if (pending) {
      speakTextNatural(pending, { isAlert: true });
    }
    window.removeEventListener("pointerdown", unlock);
    window.removeEventListener("keydown", unlock);
  };
  window.addEventListener("pointerdown", unlock, { passive: true });
  window.addEventListener("keydown", unlock, { passive: true });
}

function stopCurrentVoicePlayback() {
  if (state.voice.speakAbort) {
    try {
      state.voice.speakAbort.abort();
    } catch (_) {}
    state.voice.speakAbort = null;
  }
  const player = $("voice-audio-player");
  if (player) {
    player.onended = null;
    player.onerror = null;
    try {
      player.pause();
      player.currentTime = 0;
      player.removeAttribute("src");
      player.load();
    } catch (_) {}
  }
  if (state.voice.currentAudioUrl) {
    try {
      URL.revokeObjectURL(state.voice.currentAudioUrl);
    } catch (_) {}
    state.voice.currentAudioUrl = null;
  }
  if (window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch (_) {}
  }
}

function updateVoiceIndicators(mode, message) {
  state.voice.status = mode;
  state.voice.detail = message || mode;
  const readyClass = state.voice.ttsReady ? "voice-kokoro" : "voice-fallback";
  const cls = `voice-dot voice-${mode} ${readyClass}`;
  if ($("top-voice-dot")) $("top-voice-dot").className = cls;
  if ($("top-voice-label")) {
    $("top-voice-label").textContent =
      mode === "listening"
        ? "Listening…"
        : mode === "speaking"
        ? state.voice.lastSpeakSource === "browser"
          ? "Speaking (Browser)…"
          : "Speaking…"
        : mode === "loading"
        ? "Thinking…"
        : state.voice.ttsReady
        ? "Kokoro Ready"
        : "Browser Voice";
  }
  const topBtn = $("top-voice-btn");
  if (topBtn) {
    topBtn.classList.toggle("voice-active", mode === "listening" || mode === "speaking");
    topBtn.classList.toggle("voice-kokoro", state.voice.ttsReady);
    topBtn.classList.toggle("voice-fallback", !state.voice.ttsReady);
    topBtn.title = state.voice.ttsReady
      ? `TTS: ${state.voice.ttsEngine} (Natural CPU) · STT: ${state.voice.sttEngine}`
      : `Browser Speech Fallback (Kokoro model offline) · STT: ${state.voice.sttEngine}`;
  }
  if ($("sans-voice-dot")) $("sans-voice-dot").className = cls;
  if ($("sans-voice-state")) $("sans-voice-state").textContent = message || voiceIdleMessage();
  if ($("comp-voice-status")) {
    $("comp-voice-status").textContent =
      mode === "listening"
        ? state.voice.sttReady
          ? "LISTENING · WHISPER CPU"
          : "LISTENING · BROWSER SPEECH"
        : mode === "loading"
        ? "TRANSCRIBING · WHISPER CPU…"
        : mode === "speaking"
        ? state.voice.lastSpeakSource === "browser"
          ? "SPEAKING · BROWSER FALLBACK"
          : "SPEAKING · KOKORO CPU VOICE"
        : state.voice.ttsReady
        ? "KOKORO CPU VOICE READY"
        : "BROWSER FALLBACK VOICE";
  }
  if ($("comp-voice-btn")) {
    $("comp-voice-btn").textContent = mode === "listening" ? "⏹ Stop & Send" : "🎙 Speak to HAL";
  }
  $("comp-voice-bars")?.classList.toggle("active", mode === "listening" || mode === "speaking");
  $("hal-optical-iris")?.classList.toggle("speaking", mode === "speaking" || mode === "listening");
}

function syncRangeTrack(el) {
  if (!el) return;
  const min = Number(el.min ?? 0);
  const max = Number(el.max ?? 100);
  const val = Number(el.value ?? min);
  const pct = max > min ? Math.min(100, Math.max(0, ((val - min) / (max - min)) * 100)) : 0;
  el.style.setProperty("--range-pct", `${pct.toFixed(1)}%`);
}

function updateAlertAudioChip() {
  const btn = $("top-chime-btn");
  if (!btn) return;
  const aa = state.audioAlert;
  if (aa.speakingAlert) {
    btn.textContent = "🔊 Speaking · Tap Mute";
    btn.classList.add("chime-on");
    btn.classList.remove("chime-muted");
    return;
  }
  if (!aa.enabled) {
    btn.textContent = "🔇 Alerts: Muted";
    btn.classList.remove("chime-on");
    btn.classList.add("chime-muted");
  } else if (aa.speechEnabled) {
    btn.textContent = "🔊 Alerts: Voice";
    btn.classList.add("chime-on");
    btn.classList.remove("chime-muted");
  } else {
    btn.textContent = "♪ Alerts: Chime";
    btn.classList.add("chime-on");
    btn.classList.remove("chime-muted");
  }
}

function cancelAlertSpeech() {
  const aa = state.audioAlert;
  if (aa.speechTimerId) {
    clearTimeout(aa.speechTimerId);
    aa.speechTimerId = null;
  }
  aa.speakingAlert = false;
  state.voice.speakToken = (state.voice.speakToken || 0) + 1;
  state.voice.pendingPlayText = null;
  stopCurrentVoicePlayback();
  updateVoiceIndicators("off", voiceIdleMessage());
  updateAlertAudioChip();
}

async function speakTextNatural(text, opts = {}) {
  const clean = String(text || "").trim();
  if (!clean) return false;
  const isAlert = Boolean(opts.isAlert);

  state.voice.speakToken = (state.voice.speakToken || 0) + 1;
  const token = state.voice.speakToken;
  stopCurrentVoicePlayback();

  const controller = new AbortController();
  state.voice.speakAbort = controller;

  if (isAlert) {
    state.audioAlert.speakingAlert = true;
    updateAlertAudioChip();
  }
  state.voice.lastSpeakSource = state.voice.ttsReady ? "kokoro" : "browser";
  updateVoiceIndicators("speaking", isAlert ? clean : "Preparing natural voice…");

  const finish = (customMsg) => {
    if (token !== state.voice.speakToken) return;
    if (state.voice.speakAbort === controller) state.voice.speakAbort = null;
    if (isAlert) {
      state.audioAlert.speakingAlert = false;
      updateAlertAudioChip();
    }
    updateVoiceIndicators("off", customMsg || voiceIdleMessage());
  };

  let kokoroBlockedByAutoplay = false;

  try {
    const resp = await fetch("/api/hal/voice/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: clean,
        voice: state.voice.recommendedVoice || "af_heart",
      }),
      signal: controller.signal,
    });
    if (token !== state.voice.speakToken) return false;

    if (resp.ok && resp.status === 200) {
      const ctype = (resp.headers.get("content-type") || "").toLowerCase();
      const blob = await resp.blob();
      if (token !== state.voice.speakToken) return false;

      if (blob.size > 44 && (!ctype || ctype.includes("audio") || ctype.includes("octet-stream"))) {
        state.voice.ttsReady = true;
        state.voice.lastSpeakSource = "kokoro";
        updateVoiceIndicators("speaking", isAlert ? clean : "Speaking (Kokoro natural voice)…");

        const player = $("voice-audio-player");
        if (player) {
          const url = URL.createObjectURL(blob);
          state.voice.currentAudioUrl = url;
          const cleanupUrl = () => {
            if (state.voice.currentAudioUrl === url) {
              state.voice.currentAudioUrl = null;
            }
            try {
              URL.revokeObjectURL(url);
            } catch (_) {}
          };
          player.onended = () => {
            cleanupUrl();
            finish();
          };
          player.onerror = () => {
            console.warn("[voice] Audio element decode error for Kokoro WAV");
            cleanupUrl();
            finish();
          };
          player.src = url;
          try {
            await player.play();
            state.voice.audioUnlocked = true;
            return true;
          } catch (playErr) {
            cleanupUrl();
            player.onended = null;
            player.onerror = null;
            if (playErr && playErr.name === "NotAllowedError") {
              kokoroBlockedByAutoplay = true;
              if (isAlert) state.voice.pendingPlayText = clean;
              console.warn("[voice] Autoplay blocked before user gesture; skipping robotic fallback");
              finish("Tap anywhere to enable Kokoro voice playback");
              return false;
            }
            console.warn("[voice] Kokoro audio play failed:", playErr);
          }
        }
      } else {
        console.warn("[voice] Unexpected /api/hal/voice/speak payload:", ctype, blob.size);
      }
    } else {
      const errDetail = await resp.text().catch(() => "");
      console.warn(`[voice] /api/hal/voice/speak HTTP ${resp.status}:`, errDetail);
      if (resp.status === 503) {
        state.voice.ttsReady = false;
      }
    }
  } catch (err) {
    if ((err && err.name === "AbortError") || token !== state.voice.speakToken) {
      return false;
    }
    console.warn("[voice] /api/hal/voice/speak request error:", err);
  }

  if (kokoroBlockedByAutoplay || token !== state.voice.speakToken) {
    return false;
  }

  if (window.speechSynthesis) {
    try {
      state.voice.lastSpeakSource = "browser";
      updateVoiceIndicators("speaking", isAlert ? clean : "Speaking (Browser Fallback)…");
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(clean);
      utt.lang = "en-US";
      utt.rate = 0.94;
      utt.onend = () => finish();
      utt.onerror = () => finish();
      window.speechSynthesis.speak(utt);
      return true;
    } catch (synthErr) {
      console.warn("[voice] Browser speechSynthesis failed:", synthErr);
      finish();
      return false;
    }
  }
  finish();
  return false;
}

async function applyVoiceIntentResult(res, context) {
  const txt = (res?.transcript || "").trim();
  if (!txt) {
    updateVoiceIndicators("off", "Did not catch speech — tap Mic or type");
    return;
  }
  if (context === "vision" && res.vision_command) {
    const cmd = res.vision_command;
    if (cmd === "continue") return confirmPendingVisionResponse();
    if (cmd === "repeat") return speakTextNatural($("sans-guidance-text")?.textContent || "");
    if (cmd === "back") return $("sans-btn-back")?.click();
    if (["up", "down", "left", "right", "unable"].includes(cmd)) {
      state.sans.pendingCmd = cmd;
      $("sans-pending-text").textContent = `Heard "${cmd.toUpperCase()}" — Tap or say Continue to confirm`;
      $("sans-pending-bar")?.classList.remove("hidden");
      return speakTextNatural(`Heard ${cmd}. Say continue to confirm, or choose another direction.`);
    }
  }
  if (context === "companion") {
    await sendCompanionText(txt);
    return;
  }
  if (res.crew_id && state.crewProfiles[res.crew_id]) {
    state.activeCrewId = res.crew_id;
  }
  if (res.action === "toggle_sim") {
    if (!state.sim.open) await openSimDemo();
    return speakTextNatural("Opening the twenty four hour Mars companion simulation.");
  }
  if (res.action === "open_body_map") {
    state.bodyMode = "map";
    setLevel("body");
    return speakTextNatural(`Showing body and radiation map for ${state.crewProfiles[state.activeCrewId].name}.`);
  }
  if (res.nav_level) {
    if (res.nav_level === "body") state.bodyMode = "simple";
    setLevel(res.nav_level);
    const crew = state.crewSimCache[state.activeCrewId];
    const tasks = crew ? buildCrewSimpleTasks(crew) : [];
    const topMsg = tasks[0]?.title || "All systems look steady.";
    return speakTextNatural(`${state.crewProfiles[state.activeCrewId].name}: ${topMsg}`);
  }
  const compReply = await fetch("/api/hal/companion/reply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ crew_id: state.activeCrewId, text: txt, family_mode: false, t: state.halT }),
  });
  if (compReply.ok) {
    const data = await compReply.json();
    updateVoiceIndicators("off", `“${txt}”`);
    await speakTextNatural(data.reply);
  }
}

async function toggleVoiceRecording(context = "global") {
  if (state.voice.recorder && state.voice.recorder.state === "recording") {
    state.voice.recorder.stop();
    return;
  }
  state.voice.speakToken = (state.voice.speakToken || 0) + 1;
  state.voice.pendingPlayText = null;
  stopCurrentVoicePlayback();
  state.voice.activeContext = context;
  if (navigator.mediaDevices && window.MediaRecorder) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      const rec = new MediaRecorder(stream);
      state.voice.recorder = rec;
      rec.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) chunks.push(ev.data);
      };
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        state.voice.recorder = null;
        if (!chunks.length) {
          updateVoiceIndicators("off", "Voice ready");
          return;
        }
        updateVoiceIndicators("loading", "Transcribing with Whisper (CPU)…");
        const blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
        const form = new FormData();
        form.append("file", blob, "voice.webm");
        const resp = await fetch("/api/hal/voice/transcribe", { method: "POST", body: form });
        if (resp.ok) {
          const data = await resp.json();
          updateVoiceIndicators("off", `Heard: "${data.transcript || ""}"`);
          await applyVoiceIntentResult(data, context);
        } else {
          updateVoiceIndicators("off", "Whisper unavailable — touch controls active");
        }
      };
      rec.start();
      updateVoiceIndicators("listening", "Listening… tap Mic again when done");
      return;
    } catch {
      // Fallback below if browser mic blocked
    }
  }
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    const sr = new SpeechRec();
    sr.lang = "en-US";
    updateVoiceIndicators("listening", "Listening (Browser Speech)…");
    sr.onresult = async (ev) => {
      const transcript = ev.results?.[0]?.[0]?.transcript || "";
      await applyVoiceIntentResult({ transcript }, context);
    };
    sr.onerror = () => updateVoiceIndicators("off", "Microphone blocked — use touch buttons");
    sr.start();
    return;
  }
  await speakTextNatural("Microphone hardware is offline here, so use the tap controls or quick prompts anytime.");
}

/* ==================== CALIBRATED NEAR-VISION (SANS) ENGINE ==================== */
function drawCalibratedVisionSetup() {
  const canvas = $("sans-cal-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);

  const barW = Math.round(50 * state.sans.pxPerMmX);
  const barH = Math.round(50 * state.sans.pxPerMmY * 0.42);
  ctx.strokeStyle = "#0f172a";
  ctx.fillStyle = "#0f172a";
  ctx.lineWidth = 2;

  const hx = Math.round((w - 110 - barW) / 2);
  const hy = 34;
  ctx.beginPath();
  ctx.moveTo(hx, hy);
  ctx.lineTo(hx + barW, hy);
  ctx.moveTo(hx, hy - 8);
  ctx.lineTo(hx, hy + 8);
  ctx.moveTo(hx + barW, hy - 8);
  ctx.lineTo(hx + barW, hy + 8);
  ctx.stroke();
  ctx.font = "600 12px Manrope, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`Horizontal 50 mm bar (${barW} px)`, hx + barW / 2, hy + 26);

  const vx = w - 82;
  const vy = 20;
  ctx.beginPath();
  ctx.moveTo(vx, vy);
  ctx.lineTo(vx, vy + Math.min(82, Math.max(24, barH)));
  ctx.stroke();
  ctx.font = "600 11px Manrope, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(`Y: ${state.sans.pxPerMmY.toFixed(1)}`, vx + 8, 52);
  ctx.fillText("px/mm", vx + 8, 66);
}

function drawTumblingECanvas() {
  const canvas = $("sans-e-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = "#334155";
  ctx.font = "700 11px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("TOP ↑", w / 2, 16);
  ctx.fillText("BOTTOM ↓", w / 2, h - 8);
  ctx.textAlign = "left";
  ctx.fillText("LEFT ←", 10, h / 2 + 4);
  ctx.textAlign = "right";
  ctx.fillText("RIGHT →", w - 10, h / 2 + 4);

  const isPractice = state.sans.phase === "practice";
  const level = state.sans.levels[state.sans.levelIdx] || { stroke_device_px: [14, 14] };
  const dpr = window.devicePixelRatio || 1;
  const sx = isPractice ? 16 : Math.max(2, Math.round(level.stroke_device_px[0] / dpr));
  const sy = isPractice ? 16 : Math.max(2, Math.round(level.stroke_device_px[1] / dpr));

  const cells = [];
  for (let y = 0; y < 5; y += 1) {
    for (let x = 0; x < 5; x += 1) {
      if (x === 0 || y === 0 || y === 2 || y === 4) cells.push([x, y]);
    }
  }
  const rotCount = { right: 0, down: 1, left: 2, up: 3 }[state.sans.direction] || 0;
  const rotated = cells.map(([cx, cy]) => {
    let rx = cx;
    let ry = cy;
    for (let r = 0; r < rotCount; r += 1) {
      const nx = 4 - ry;
      const ny = rx;
      rx = nx;
      ry = ny;
    }
    return [rx, ry];
  });

  const ox = Math.round((w - 5 * sx) / 2);
  const oy = Math.round((h - 5 * sy) / 2);
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = "#000000";
  rotated.forEach(([rx, ry]) => {
    ctx.fillRect(ox + rx * sx, oy + ry * sy, sx, sy);
  });
}

function setVisionStageView(stage) {
  state.sans.stage = stage;
  $("sans-stage-setup")?.classList.toggle("hidden", stage !== "setup");
  $("sans-stage-test")?.classList.toggle("hidden", stage !== "test");
  $("sans-stage-summary")?.classList.toggle("hidden", stage !== "summary");
}

function resetCalibratedVisionToSetup() {
  state.sans.pendingCmd = null;
  $("sans-pending-bar")?.classList.add("hidden");
  $("sans-status-pill").className = "triage-pill pill-nominal";
  $("sans-status-pill").textContent = "CALIBRATION";
  setVisionStageView("setup");
  drawCalibratedVisionSetup();
}

function nextRandomDirection() {
  const dirs = ["up", "down", "left", "right"];
  return dirs[Math.floor(Math.random() * dirs.length)];
}

function startVisionEyePhase(eye) {
  state.sans.eye = eye;
  state.sans.phase = "practice";
  state.sans.practiceIdx = 0;
  state.sans.levelIdx = 0;
  state.sans.confirming = false;
  state.sans.batch = [];
  state.sans.trials = [];
  state.sans.direction = ["right", "down", "left", "up"][0];
  state.sans.pendingCmd = null;
  $("sans-pending-bar")?.classList.add("hidden");
  updateVisionTestDisplay();
}

function updateVisionTestDisplay() {
  const eyeName = state.sans.eye === "right" ? "RIGHT EYE" : "LEFT EYE";
  const lvl = state.sans.levels[state.sans.levelIdx];
  const isPrac = state.sans.phase === "practice";
  $("sans-eye-pill").className = `triage-pill ${isPrac ? "pill-warning" : "pill-nominal"}`;
  $("sans-eye-pill").textContent = isPrac ? `PRACTICE · ${eyeName}` : `${eyeName} · ACTIVE`;
  $("sans-level-pill").textContent = isPrac
    ? `Practice ${state.sans.practiceIdx + 1} / 4`
    : `logMAR ${lvl.nominal_logmar.toFixed(1)} · Trial ${state.sans.batch.length + 1}/5`;
  $("sans-guidance-text").textContent = isPrac
    ? `Cover other eye and tap which edge the E legs point (${eyeName}).`
    : `Which edge do the E legs point toward? (${eyeName})`;
  drawTumblingECanvas();
}

async function startCalibratedVisionExam() {
  if (!$("sans-dist-confirm")?.checked) {
    return alert("Please confirm the 40 cm viewing distance before starting.");
  }
  const dpr = window.devicePixelRatio || 1;
  const resp = await fetch("/api/hal/vision/levels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      px_per_mm_x: state.sans.pxPerMmX,
      px_per_mm_y: state.sans.pxPerMmY,
      device_pixel_ratio: dpr,
      display_signature: `Web ${window.innerWidth}x${window.innerHeight} @${dpr}x`,
      distance_mm: 400,
    }),
  });
  if (!resp.ok) return;
  const data = await resp.json();
  state.sans.calibration = data.calibration;
  state.sans.levels = data.levels;
  state.sans.eyes = {};
  state.sans.attempts = [];
  state.sans.practiceLog = [];
  $("sans-status-pill").className = "triage-pill pill-warning";
  $("sans-status-pill").textContent = "TESTING";
  setVisionStageView("test");
  startVisionEyePhase("right");
  if (state.sans.narration) {
    speakTextNatural("Right eye practice. Which side do the E legs point toward?");
  }
}

function handleVisionResponse(cmd) {
  if (state.sans.stage !== "test") return;
  if (state.sans.phase === "practice") {
    const ok = cmd === state.sans.direction;
    state.sans.practiceLog.push({ eye: state.sans.eye, expected: state.sans.direction, response: cmd, correct: ok });
    if (!ok) {
      $("sans-guidance-text").textContent = `Not quite — that E points ${state.sans.direction.toUpperCase()}. Try again.`;
      return;
    }
    state.sans.practiceIdx += 1;
    if (state.sans.practiceIdx >= 4) {
      state.sans.phase = "eye";
      state.sans.direction = nextRandomDirection();
      if (state.sans.narration) speakTextNatural(`Begin scored trials for ${state.sans.eye} eye.`);
    } else {
      state.sans.direction = ["right", "down", "left", "up"][state.sans.practiceIdx];
    }
    updateVisionTestDisplay();
    return;
  }

  const lvl = state.sans.levels[state.sans.levelIdx];
  const correct = cmd === state.sans.direction;
  state.sans.trials.push({
    timestamp_utc: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
    level: lvl,
    expected: state.sans.direction,
    response: cmd,
    correct,
    confirmation_block: state.sans.confirming,
  });
  state.sans.batch.push(correct);

  if (state.sans.batch.length >= 5) {
    const passed = state.sans.batch.filter(Boolean).length >= 4;
    state.sans.batch = [];
    let finishedResult = null;
    if (state.sans.confirming) {
      finishedResult = { status: passed ? "confirmed" : "inconsistent", level: passed ? lvl : null };
    } else if (!passed) {
      if (state.sans.levelIdx === 0) {
        finishedResult = { status: "outside_range", level: null };
      } else {
        state.sans.levelIdx -= 1;
        state.sans.confirming = true;
      }
    } else if (state.sans.levelIdx === state.sans.levels.length - 1) {
      finishedResult = { status: "display_limit", level: lvl };
    } else {
      state.sans.levelIdx += 1;
    }

    if (finishedResult) {
      state.sans.eyes[state.sans.eye] = { result: finishedResult, trials: state.sans.trials.slice() };
      if (state.sans.eye === "right") {
        startVisionEyePhase("left");
        if (state.sans.narration) speakTextNatural("Right eye complete. Switch to left eye practice.");
        return;
      }
      finishCalibratedVisionExam();
      return;
    }
  }

  state.sans.direction = nextRandomDirection();
  updateVisionTestDisplay();
}

function confirmPendingVisionResponse() {
  const cmd = state.sans.pendingCmd;
  state.sans.pendingCmd = null;
  $("sans-pending-bar")?.classList.add("hidden");
  if (cmd) handleVisionResponse(cmd);
}

function finishCalibratedVisionExam() {
  state.sans.attempts.push({ attempt: state.sans.attempts.length + 1, eyes: { ...state.sans.eyes } });
  const rLvl = state.sans.eyes.right?.result?.level;
  const lLvl = state.sans.eyes.left?.result?.level;
  const fmtEye = (res, lvl) =>
    lvl ? `${lvl.nominal_logmar.toFixed(1)} logMAR (${res.status})` : `${res?.status || "outside_range"}`;
  $("sans-res-right").textContent = fmtEye(state.sans.eyes.right?.result, rLvl);
  $("sans-res-left").textContent = fmtEye(state.sans.eyes.left?.result, lLvl);
  $("sans-status-pill").className = "triage-pill pill-nominal";
  $("sans-status-pill").textContent = "COMPLETE · READY TO SAVE";
  setVisionStageView("summary");
  if (state.sans.narration) {
    speakTextNatural("Near vision check complete for both eyes. Review your score and save to downlink if needed.");
  }
}

async function queueCalibratedVisionReport() {
  if (!state.sans.attempts.length || !state.sans.calibration) return;
  const resp = await fetch("/api/hal/vision/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      crew_id: state.activeCrewId,
      symptom: $("sans-symptom-select")?.value || "Routine scheduled check",
      conditions: { lighting: $("sans-lighting-select")?.value || "Nominal cabin" },
      calibration: state.sans.calibration,
      attempts: state.sans.attempts,
      practice: state.sans.practiceLog,
      mission_time: state.halT,
    }),
  });
  if (resp.ok) {
    const data = await resp.json();
    state.downlink = data.state;
    state.selectedPacketId = data.packet.id;
    await inspectDownlinkPacket(data.packet.id);
    setLevel("downlink");
  }
}

/* ==================== GENTLE PSYCHOACOUSTIC MARIMBA WARNING SYSTEM ==================== */
/* Grounded in IEC 60601-1-8 AMD2 (warm marimba mallet timbre) & NASA non-startling onset envelopes */
function ensureAudioCtx(allowCreate = false) {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;
  if (!state.audioAlert.ctx && allowCreate) {
    try {
      state.audioAlert.ctx = new AudioCtx();
    } catch (_) {
      return null;
    }
  }
  const ctx = state.audioAlert.ctx;
  if (ctx && ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }
  return ctx;
}

function _playMarimbaNote(ctx, bus, freqHz, startOffsetS, durationS = 0.62, gainPeak = 0.11) {
  const t0 = ctx.currentTime + startOffsetS;
  const voiceGain = ctx.createGain();
  voiceGain.gain.setValueAtTime(0.0001, t0);
  // 28 ms soft ramp eliminates startle-inducing acoustic click
  voiceGain.gain.exponentialRampToValueAtTime(Math.max(0.01, gainPeak), t0 + 0.028);
  voiceGain.gain.exponentialRampToValueAtTime(0.0001, t0 + durationS);

  // Warm fundamental (1x) + gentle 2nd harmonic (2x) + subtle woody mallet attack transient (3.98x)
  const osc1 = ctx.createOscillator();
  osc1.type = "sine";
  osc1.frequency.setValueAtTime(freqHz, t0);

  const osc2 = ctx.createOscillator();
  const g2 = ctx.createGain();
  osc2.type = "sine";
  osc2.frequency.setValueAtTime(freqHz * 2.0, t0);
  g2.gain.setValueAtTime(0.18, t0);
  g2.gain.exponentialRampToValueAtTime(0.02, t0 + durationS * 0.65);

  const osc4 = ctx.createOscillator();
  const g4 = ctx.createGain();
  osc4.type = "triangle";
  osc4.frequency.setValueAtTime(freqHz * 3.98, t0);
  g4.gain.setValueAtTime(0.045, t0);
  g4.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.09);

  osc1.connect(voiceGain);
  osc2.connect(g2);
  g2.connect(voiceGain);
  osc4.connect(g4);
  g4.connect(voiceGain);
  voiceGain.connect(bus);

  osc1.start(t0);
  osc2.start(t0);
  osc4.start(t0);
  const stopAt = t0 + durationS + 0.04;
  osc1.stop(stopAt);
  osc2.stop(stopAt);
  osc4.stop(stopAt);
}

function playGentleChime(kind = "crew-red", force = false) {
  if (!state.audioAlert.enabled && !force) return false;
  const now = Date.now();
  const prevAt = state.audioAlert.lastPlayedAt[kind] || 0;
  if (!force && now - prevAt < 6500) return false;

  const ctx = ensureAudioCtx(true);
  if (!ctx) return false;

  const lpf = ctx.createBiquadFilter();
  lpf.type = "lowpass";
  lpf.frequency.setValueAtTime(1850, ctx.currentTime);
  lpf.connect(ctx.destination);

  if (kind === "cabin-air") {
    // Rhythmic ventilation / pressure cadence: D4 -> G4 -> D4 (soft breath-like pair)
    _playMarimbaNote(ctx, lpf, 293.66, 0.02, 0.56, 0.105);
    _playMarimbaNote(ctx, lpf, 392.0, 0.24, 0.58, 0.115);
    _playMarimbaNote(ctx, lpf, 293.66, 0.52, 0.68, 0.095);
  } else if (kind === "preview") {
    _playMarimbaNote(ctx, lpf, 523.25, 0.02, 0.48, 0.09);
    _playMarimbaNote(ctx, lpf, 392.0, 0.19, 0.56, 0.085);
  } else {
    // Crew RED triad: F4 -> A4 -> E4 warm mallet interval (attentive, non-startling)
    _playMarimbaNote(ctx, lpf, 349.23, 0.02, 0.54, 0.11);
    _playMarimbaNote(ctx, lpf, 440.0, 0.21, 0.54, 0.12);
    _playMarimbaNote(ctx, lpf, 329.63, 0.42, 0.72, 0.105);
  }
  state.audioAlert.lastPlayedAt[kind] = now;
  return true;
}

function buildCriticalSpeechSummary(kind, redCrewList = []) {
  if (kind === "cabin-air") {
    const co2 = state.halFrame?.cabin?.co2_ppm;
    return co2 && co2 >= 1000
      ? `Cabin carbon dioxide rising to ${Math.round(co2)}. Switch scrubber to high.`
      : "Cabin air quality dropping rapidly. Check scrubber now.";
  }
  if (!redCrewList.length) return "";
  if (redCrewList.length >= 2) {
    const names = redCrewList.slice(0, 2).map((c) => c.profile.name).join(" and ");
    return `Attention: ${names} require urgent intervention.`;
  }
  const c = redCrewList[0];
  const name = c.profile.name;
  if (c.worstZone === "heart") {
    const rawHr = c.meanHr ?? c.cardio?.metrics?.mean_hr_bpm ?? null;
    const rawSpo2 = c.spo2Val ?? c.cardio?.metrics?.spo2_min_pct ?? null;
    const hr = rawHr != null ? Math.round(rawHr) : null;
    const spo2 = rawSpo2 != null ? Math.round(rawSpo2) : null;
    if (hr && spo2 && spo2 < 93) {
      return `Attention: ${name} heart strain, pulse ${hr}, oxygen ${spo2} percent. Intervention needed.`;
    }
    if (hr) {
      return `Attention: ${name} heart rate ${hr} critical. Intervention needed.`;
    }
    return `Attention: ${name} cardiac strain critical. Intervention needed.`;
  }
  if (c.worstZone === "torso") {
    return `Attention: ${name} high radiation alert. Move to Destiny core shelter.`;
  }
  if (c.worstZone === "lungs") {
    return `Attention: ${name} cabin air distress. Check oxygen and scrubber.`;
  }
  return `Attention: ${name} vital alert critical. Intervention needed.`;
}

function scheduleAntiOverloadAlertSpeech(kind, phrase, dedupeKeys = []) {
  const aa = state.audioAlert;
  if (!aa.enabled || !aa.speechEnabled || !phrase) return false;
  if (state.voice?.recorder?.state === "recording") return false;
  const now = Date.now();
  // NASA-STD-3001 / ICU anti-overload: 45s global cooldown & 90s per-crew/event deduplication
  if (now - aa.lastSpeechAt < 45000) return false;
  const allOnCooldown = dedupeKeys.length > 0 && dedupeKeys.every((k) => now - (aa.lastCrewSpokenAt[k] || 0) < 90000);
  if (allOnCooldown) return false;

  if (aa.speechTimerId) clearTimeout(aa.speechTimerId);
  aa.lastSpeechAt = now;
  dedupeKeys.forEach((k) => {
    aa.lastCrewSpokenAt[k] = now;
  });
  // Two-stage earcon-then-callout (~680ms after marimba onset so tone never masks speech)
  aa.speechTimerId = setTimeout(() => {
    aa.speechTimerId = null;
    if (!aa.enabled || !aa.speechEnabled) return;
    speakTextNatural(phrase, { isAlert: true });
  }, 680);
  return true;
}

function checkGentleAudioAlerts() {
  const aa = state.audioAlert;
  const co2 = state.halFrame?.cabin?.co2_ppm ?? null;
  const cache = state.crewSimCache || {};
  const crewIds = Object.keys(cache);
  if (!crewIds.length) return;

  if (!aa.seeded) {
    crewIds.forEach((cid) => {
      aa.prevTiers[cid] = cache[cid]?.overallTier || "nominal";
    });
    aa.prevAirFlag = Boolean(state.cabinAirAlert);
    aa.prevCo2 = co2;
    aa.seeded = true;
    return;
  }

  const newlyRedCrew = [];
  crewIds.forEach((cid) => {
    const tier = cache[cid]?.overallTier || "nominal";
    if (tier === "critical" && aa.prevTiers[cid] !== "critical") {
      newlyRedCrew.push(cache[cid]);
    }
    aa.prevTiers[cid] = tier;
  });

  const airFlagNow = Boolean(state.cabinAirAlert);
  const co2Spiked =
    co2 !== null &&
    aa.prevCo2 !== null &&
    ((co2 - aa.prevCo2 >= 45) || (co2 >= 1000 && aa.prevCo2 < 1000));
  const airDeteriorated = (airFlagNow && !aa.prevAirFlag) || co2Spiked;
  aa.prevAirFlag = airFlagNow;
  if (co2 !== null) aa.prevCo2 = co2;

  if (airDeteriorated) {
    playGentleChime("cabin-air");
    const msg = buildCriticalSpeechSummary("cabin-air");
    scheduleAntiOverloadAlertSpeech("cabin-air", msg, ["cabin-air"]);
  } else if (newlyRedCrew.length > 0) {
    playGentleChime("crew-red");
    const msg = buildCriticalSpeechSummary("crew-red", newlyRedCrew);
    scheduleAntiOverloadAlertSpeech(
      "crew-red",
      msg,
      newlyRedCrew.map((c) => c.profile.id)
    );
  }
}


// === Deep-Tech Sleep Radar/CSI, ARED Gym CV & Passive Facial CV Wiring ===
(function () {
  function renderHypnogram(stages) {
    const box = document.getElementById("sleep-hypnogram");
    if (!box || !Array.isArray(stages)) return;
    const heights = { W: "95%", REM: "72%", "N1-N2": "48%", N3: "25%" };
    const colors = { W: "#ff9f0a", REM: "#64d2ff", "N1-N2": "#5e5ce6", N3: "#30d158" };
    box.innerHTML = stages
      .slice(0, 60)
      .map((s) => `<div class="hypno-bar" title="${s}" style="height:${heights[s] || "40%"};background:${colors[s] || "#5e5ce6"}"></div>`)
      .join("");
  }

  let sleepWaveTimer = null;
  let esp32Port = null;
  let esp32Reader = null;
  let esp32Running = false;

  function drawSleepVarianceTrace(vals) {
    const canvas = document.getElementById("sleep-wave-canvas");
    if (!canvas || !vals.length) return;
    const ctx = canvas.getContext("2d"), w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const min = Math.min(...vals), max = Math.max(...vals), span = Math.max(max - min, 1e-3);
    ctx.strokeStyle = "#30d158";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < vals.length; i++) {
      const x = (i / Math.max(vals.length - 1, 1)) * w;
      const y = h - 10 - ((vals[i] - min) / span) * (h - 20);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  function startSleepWaveAnim(bpm = 14.5) {
    if (sleepWaveTimer) clearInterval(sleepWaveTimer);
    const canvas = document.getElementById("sleep-wave-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let phase = 0;
    sleepWaveTimer = setInterval(() => {
      const w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = "#64d2ff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const y = h / 2 + Math.sin((x / w) * Math.PI * 4 + phase) * (h * 0.3);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      phase += (bpm / 60) * 0.35;
    }, 40);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const btnEsp32 = document.getElementById("btn-esp32-connect");
    const btnSleep = document.getElementById("btn-sleep-analyze");
    const btnSleepStop = document.getElementById("btn-sleep-stop");

    if (btnSleepStop) {
      btnSleepStop.addEventListener("click", async () => {
        if (sleepWaveTimer) clearInterval(sleepWaveTimer);
        esp32Running = false;
        try { if (esp32Reader) await esp32Reader.cancel(); } catch {}
        try { if (esp32Port) await esp32Port.close(); } catch {}
        esp32Reader = null; esp32Port = null;
        const badge = document.getElementById("sleep-csi-badge");
        if (badge) badge.textContent = "STOPPED";
      });
    }

    if (btnEsp32) {
      btnEsp32.addEventListener("click", async () => {
        const badge = document.getElementById("sleep-csi-badge");
        if (!("serial" in navigator)) {
          if (badge) badge.textContent = "Web Serial unsupported — use Chrome/Edge";
          return;
        }
        try {
          if (badge) badge.textContent = "SELECT ESP32 PORT...";
          esp32Port = await navigator.serial.requestPort();
          await esp32Port.open({ baudRate: 115200 });
          if (badge) badge.textContent = "ESP32 SERIAL LIVE";
          esp32Running = true;
          const decoder = new TextDecoderStream();
          esp32Port.readable.pipeTo(decoder.writable).catch(() => {});
          esp32Reader = decoder.readable.getReader();
          let buf = "";
          const csiBatch = [];
          const varTrace = [];
          while (esp32Running) {
            const { value, done } = await esp32Reader.read();
            if (done) break;
            buf += value;
            const lines = buf.split(/\r?\n/);
            buf = lines.pop() || "";
            for (const line of lines) {
              if (!line.trim().startsWith("{")) continue;
              try {
                const pkt = JSON.parse(line);
                if (Array.isArray(pkt.amplitudes) && pkt.amplitudes.length) {
                  const mean = pkt.amplitudes.reduce((s, v) => s + v, 0) / pkt.amplitudes.length;
                  const variance = pkt.amplitudes.reduce((s, v) => s + (v - mean) ** 2, 0) / pkt.amplitudes.length;
                  varTrace.push(variance);
                  if (varTrace.length > 100) varTrace.shift();
                  drawSleepVarianceTrace(varTrace);
                  csiBatch.push(pkt);
                  if (csiBatch.length >= 40) {
                    const batch = csiBatch.splice(0, csiBatch.length);
                    fetch("/api/sleep/csi", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ csi_frames: batch, fs_hz: 20 }) })
                      .then((r) => r.json())
                      .then((d) => {
                        document.getElementById("sleep-resp-val").textContent = d.respiration_bpm ?? "—";
                        document.getElementById("sleep-apnea-val").textContent = d.apnea_events ?? "0";
                        document.getElementById("sleep-eff-val").textContent = d.motion_arousals != null ? `${d.motion_arousals} arousals` : "Live";
                      }).catch(() => {});
                  }
                }
              } catch {}
            }
          }
        } catch (err) {
          if (badge) badge.textContent = "ESP32 DISCONNECTED";
        }
      });
    }

    if (btnSleep) {
      btnSleep.addEventListener("click", async () => {
        const badge = document.getElementById("sleep-csi-badge");
        if (badge) badge.textContent = "DEMO ANALYZING...";
        startSleepWaveAnim(14.2);
        try {
          const r = await fetch("/api/sleep/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
          const d = await r.json();
          document.getElementById("sleep-resp-val").textContent = d.respiration_bpm ?? "14.2";
          document.getElementById("sleep-apnea-val").textContent = d.apnea_events ?? "0";
          document.getElementById("sleep-eff-val").textContent = d.sleep_efficiency_pct ? `${d.sleep_efficiency_pct}%` : "88%";
          renderHypnogram(d.stages || ["W", "N1-N2", "N3", "N3", "N1-N2", "REM", "N1-N2", "N3", "REM", "W"]);
          if (badge) badge.textContent = "DEMO RADAR";
        } catch {
          document.getElementById("sleep-resp-val").textContent = "14.2";
          document.getElementById("sleep-apnea-val").textContent = "1";
          document.getElementById("sleep-eff-val").textContent = "88%";
          renderHypnogram(["W", "N1-N2", "N3", "N3", "N1-N2", "REM", "N1-N2", "N3", "REM", "W"]);
          if (badge) badge.textContent = "OFFLINE DEMO";
        }
      });
    }

    // ARED Gym CV
    const canvas = document.getElementById("ared-cv-canvas");
    const aredVideo = document.getElementById("ared-cv-video");
    if (canvas && window.AredCV) {
      const session = new window.AredCV.AredCVSession(
        canvas,
        (u) => {
          document.getElementById("ared-reps-val").textContent = u.reps.length;
          if (u.latest) {
            document.getElementById("ared-velloss-val").textContent = `${u.latest.velocity_loss_pct}%`;
            document.getElementById("ared-qual-val").textContent = `${u.latest.quality_score}/100`;
            document.getElementById("ared-flags-val").textContent = u.latest.flags.length ? u.latest.flags.join(", ") : "Nominal";
          }
        },
        async (summary) => {
          const badge = document.getElementById("ared-cv-badge");
          if (badge) badge.textContent = summary.velocity_loss_pct >= 20 ? "FATIGUE DETECTED" : "SET COMPLETE";
          try {
            await fetch("/api/exercise/set", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(summary) });
          } catch {}
        },
        (status) => {
          const badge = document.getElementById("ared-cv-badge");
          if (badge) badge.textContent = status;
        }
      );
      document.getElementById("btn-ared-camera")?.addEventListener("click", () => {
        const ex = document.getElementById("ared-exercise-select")?.value || "squat";
        session.startCamera(aredVideo, ex);
      });
      document.getElementById("btn-ared-replay")?.addEventListener("click", () => {
        const ex = document.getElementById("ared-exercise-select")?.value || "squat";
        session.startReplay(ex);
      });
      document.getElementById("btn-ared-stop")?.addEventListener("click", () => {
        session.stop(true);
        document.getElementById("ared-cv-badge").textContent = "STOPPED";
      });
    }

    // Passive Facial CV
    if (window.FaceCV) {
      const faceCanvas = document.getElementById("face-cv-canvas");
      const faceVideo = document.getElementById("face-cv-video");
      const faceSession = new window.FaceCV.FaceCVSession(
        faceCanvas,
        (u) => {
          document.getElementById("face-hr-val").textContent = u.hrBpm;
          document.getElementById("face-perclos-val").textContent = `${u.perclosPct}%`;
          document.getElementById("face-palp-val").textContent = u.palpebralRatio;
          document.getElementById("face-prog-val").textContent = `${u.progressPct}%`;
        },
        (done) => {
          const badge = document.getElementById("face-cv-badge");
          if (badge) badge.textContent = done.fluidShiftFlag ? "FLUID SHIFT FLAG" : "COMPLETE";
        },
        (status) => {
          const badge = document.getElementById("face-cv-badge");
          if (badge) badge.textContent = status;
        }
      );
      document.getElementById("btn-face-camera")?.addEventListener("click", () => {
        faceSession.startCamera(faceVideo);
      });
      document.getElementById("btn-face-replay")?.addEventListener("click", () => {
        faceSession.startReplay();
      });
      document.getElementById("btn-face-stop")?.addEventListener("click", () => {
        faceSession.stop();
        document.getElementById("face-cv-badge").textContent = "STOPPED";
      });
    }

    initClinicalMedHub();
  });

  const medhubState = {
    mode: "simple",
    data: null,
    selectedPathwayId: null,
    checkedActions: new Set(),
  };

  function _escHtml(val) {
    return String(val ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Map MedHub risk tiers & silo statuses to ASTRA-Core native VisionOS classes. */
  function _medhubTierStyle(raw) {
    const t = String(raw || "LOW").toUpperCase();
    if (t === "CRITICAL") {
      return { pill: "pill-critical", card: "card-critical", bar: "crit" };
    }
    if (t === "ELEVATED" || t === "WATCH") {
      return { pill: "pill-warning", card: "card-warning", bar: "high" };
    }
    return { pill: "pill-nominal", card: "card-nominal", bar: "" };
  }

  function setMedHubMode(mode) {
    const next = mode === "depth" ? "depth" : "simple";
    medhubState.mode = next;
    document.getElementById("medhub-mode-simple")?.classList.toggle("active", next === "simple");
    document.getElementById("medhub-mode-depth")?.classList.toggle("active", next === "depth");
    document.getElementById("medhub-simple-pane")?.classList.toggle("hidden", next !== "simple");
    document.getElementById("medhub-depth-pane")?.classList.toggle("hidden", next !== "depth");
  }

  function syncMedHubScenarioUI(scenarioId) {
    const sid = scenarioId || "nominal_iss";
    const sel = document.getElementById("medhub-scenario-select");
    if (sel && sel.value !== sid) {
      const hasOpt = Array.from(sel.options || []).some((o) => o.value === sid);
      if (hasOpt) sel.value = sid;
    }
    document.querySelectorAll(".medhub-preset-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.scenario === sid);
    });
  }

  function renderMedHubCausalBox(pathway) {
    const box = document.getElementById("medhub-causal-box");
    if (!box) return;
    if (!pathway) {
      box.textContent = "Select a pathway above to see which silo biomarkers combine and the scientific basis.";
      return;
    }
    const linked = (pathway.silos_linked || []).join(" ↔ ");
    const signals = (pathway.converging_signals || [])
      .map((sig) => `<li>${_escHtml(sig)}</li>`)
      .join("");
    const style = _medhubTierStyle(pathway.tier);
    box.innerHTML = `
      <div class="medhub-causal-head">
        <strong>${_escHtml(pathway.title)}</strong>
        <span class="triage-pill ${style.pill}">${_escHtml(pathway.score)}/100 · ${_escHtml(pathway.tier)}</span>
      </div>
      <div class="medhub-causal-silos"><strong>Silos Linked:</strong> ${_escHtml(linked)}</div>
      <ul class="medhub-signals-list">${signals}</ul>
      <div class="medhub-causal-science"><strong>Science Basis:</strong> ${_escHtml(pathway.science_basis)}</div>
      <div class="medhub-causal-action"><strong>Pre-Symptomatic Action:</strong> ${_escHtml(pathway.pre_symptomatic_action)}</div>
    `;
  }

  function renderMedHubActions(data, pathways) {
    const listEl = document.getElementById("medhub-actions-list");
    if (!listEl) return;
    const sid = data.scenario_id || "nominal_iss";
    const elevated = pathways.filter((p) => Number(p.score) >= 25);
    const items = elevated.length
      ? elevated.map((p) => ({
          key: `${sid}:${p.id}`,
          text: `${p.title}: ${p.pre_symptomatic_action}`,
        }))
      : [
          {
            key: `${sid}:routine:hydration`,
            text: "Maintain daily hydration >= 2.2 L/day and complete scheduled ARED resistive loading.",
          },
          {
            key: `${sid}:routine:eclss`,
            text: "Keep cabin CDRA ppCO2 < 2.5 mmHg and verify acoustic hearing protection compliance.",
          },
          {
            key: `${sid}:routine:labs`,
            text: "Continue scheduled OSDR-aligned i-STAT, urinalysis & contactless sleep radar checks.",
          },
        ];

    listEl.innerHTML = items
      .map((item, idx) => {
        const isChecked = medhubState.checkedActions.has(item.key);
        return `
          <label class="action-check-item ${isChecked ? "checked" : ""}">
            <input type="checkbox" data-action-key="${_escHtml(item.key)}" ${isChecked ? "checked" : ""} />
            <span class="action-step-num">${idx + 1}</span>
            <span class="action-step-text">${_escHtml(item.text)}</span>
          </label>
        `;
      })
      .join("");

    listEl.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.addEventListener("change", (e) => {
        const key = e.target.dataset.actionKey;
        if (!key) return;
        if (e.target.checked) medhubState.checkedActions.add(key);
        else medhubState.checkedActions.delete(key);
        e.target.closest(".action-check-item")?.classList.toggle("checked", e.target.checked);
      });
    });
  }

  function renderMedHubPathwaysCompact(pathways) {
    const container = document.getElementById("medhub-pathways-compact");
    if (!container) return;

    if (!pathways.length) {
      container.innerHTML = "";
      renderMedHubCausalBox(null);
      return;
    }

    if (!pathways.some((p) => p.id === medhubState.selectedPathwayId)) {
      medhubState.selectedPathwayId = pathways[0].id;
    }

    container.innerHTML = pathways
      .map((p) => {
        const score = Math.max(0, Math.min(100, Math.round(Number(p.score) || 0)));
        const style = _medhubTierStyle(p.tier);
        const isSelected = p.id === medhubState.selectedPathwayId;
        return `
          <div class="sbar-row medhub-pathway-row ${isSelected ? "active" : ""}" role="button" tabindex="0" aria-pressed="${isSelected}" data-pathway-id="${_escHtml(p.id)}">
            <span class="medhub-sbar-title">${_escHtml(p.title)}</span>
            <div class="sbar-track"><div class="sbar-fill ${style.bar}" style="width:${score}%"></div></div>
            <span class="sbar-tag">${_escHtml(score)}/100 · ${_escHtml(p.tier)}</span>
          </div>
        `;
      })
      .join("");

    const selectPathway = (pid) => {
      const match = pathways.find((p) => p.id === pid);
      if (!match) return;
      medhubState.selectedPathwayId = pid;
      container.querySelectorAll(".sbar-row").forEach((row) => {
        const on = row.dataset.pathwayId === pid;
        row.classList.toggle("active", on);
        row.setAttribute("aria-pressed", String(on));
      });
      renderMedHubCausalBox(match);
    };

    container.querySelectorAll(".sbar-row").forEach((row) => {
      row.addEventListener("click", () => selectPathway(row.dataset.pathwayId));
      row.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectPathway(row.dataset.pathwayId);
        }
      });
    });

    const activePathway = pathways.find((p) => p.id === medhubState.selectedPathwayId) || pathways[0];
    renderMedHubCausalBox(activePathway);
  }

  function renderClinicalHub(data) {
    if (!data) return;
    medhubState.data = data;
    if (data.scenario_id) syncMedHubScenarioUI(data.scenario_id);

    const pathways = Array.isArray(data.pathways) ? data.pathways : [];
    const osdrComps = Array.isArray(data.osdr_comparisons) ? data.osdr_comparisons : [];
    const top = pathways[0] || null;
    const overallScore = Number(data.overall_coupled_risk_score ?? 0);
    const topScore = Number(top?.score ?? overallScore);
    const tier = String(data.overall_coupled_tier || "LOW").toUpperCase();
    const tierStyle = _medhubTierStyle(tier);

    const heroEl = document.getElementById("medhub-hero-card");
    if (heroEl) {
      heroEl.classList.remove("card-nominal", "card-warning", "card-critical");
      heroEl.classList.add(tierStyle.card);
    }

    const scoreEl = document.getElementById("medhub-overall-score");
    const tierEl = document.getElementById("medhub-overall-tier");
    const headlineEl = document.getElementById("medhub-headline");
    const provEl = document.getElementById("medhub-provenance");
    const kpiPrimaryEl = document.getElementById("medhub-kpi-primary");
    const kpiRcvEl = document.getElementById("medhub-kpi-rcv");
    const linksEl = document.getElementById("medhub-live-links");

    if (scoreEl) scoreEl.textContent = `${data.overall_coupled_risk_score ?? 0} / 100`;
    if (tierEl) {
      tierEl.textContent = `${tier} RISK`;
      tierEl.className = `triage-pill ${tierStyle.pill}`;
    }
    if (headlineEl) {
      headlineEl.textContent = top && topScore >= 25 ? top.title : "All 6 ISS medical silos nominal";
    }
    if (provEl) provEl.textContent = data.provenance_note || "";
    if (kpiPrimaryEl) {
      kpiPrimaryEl.textContent =
        top && topScore >= 25
          ? `${top.score}/100 · ${String(top.title || "Pathway").split(" ")[0]}`
          : topScore > 0
            ? `Nominal (${topScore}/100)`
            : "Nominal (0/100)";
    }
    if (kpiRcvEl) {
      const rcvHits = osdrComps.filter((c) => c.exceeds_rcv === true).length;
      kpiRcvEl.textContent = `${rcvHits} / ${osdrComps.length}`;
    }
    if (linksEl) {
      const links = Array.isArray(data.live_links) ? data.live_links : [];
      linksEl.innerHTML = links.length
        ? links.map((l) => `<span class="triage-pill pill-nominal">LIVE · ${_escHtml(l)}</span>`).join("")
        : `<span class="triage-pill pill-nominal">OSDR + DONKI Cached</span>`;
    }

    // Sync override inputs with returned raw_state
    const raw = data.raw_state || {};
    const poc = raw.poc_labs || {};
    const img = raw.imaging || {};
    const pex = raw.pulmonary_exercise || {};
    const env = raw.environment || {};
    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el && v !== undefined && v !== null) el.value = v;
    };
    setVal("mh-ov-ica", poc.ica_mmol_l);
    setVal("mh-ov-hb", poc.hb_g_dl);
    setVal("mh-ov-hct", poc.hct_pct);
    setVal("mh-ov-usg", poc.urine_sg);
    setVal("mh-ov-onsd", img.onsd_mm);
    setVal("mh-ov-jugular", img.jugular_flow_grade || "normal");
    setVal("mh-ov-cortisol", poc.saliva_cortisol_nmol_l);
    setVal("mh-ov-hydration", pex.hydration_l_day);
    setVal("mh-ov-co2", env.ppco2_mmhg);

    // Mode 1: Crew Action checklist + 6 coupled pathways mini-bars
    renderMedHubActions(data, pathways);
    renderMedHubPathwaysCompact(pathways);

    // Mode 2.1: Render 6 Unified Silos
    const silosGrid = document.getElementById("medhub-silos-grid");
    if (silosGrid) {
      silosGrid.innerHTML = (data.silos || [])
        .map((s) => {
          const st = String(s.status || "NOMINAL").toUpperCase();
          const stStyle = _medhubTierStyle(st);
          const metricsHtml = String(s.key_metrics || "")
            .split(" · ")
            .filter(Boolean)
            .map((part) => {
              const idx = part.indexOf(" ");
              const k = idx > 0 ? part.slice(0, idx) : part;
              const v = idx > 0 ? part.slice(idx + 1) : "";
              return `<div class="medhub-kv-item"><span class="medhub-kv-k">${_escHtml(k)}</span><span class="medhub-kv-v">${_escHtml(v)}</span></div>`;
            })
            .join("");
          return `
            <article class="sub-glass medhub-silo-card">
              <div class="medhub-silo-head">
                <h3>${_escHtml(s.name)}</h3>
                <span class="triage-pill ${stStyle.pill}">${_escHtml(st)}</span>
              </div>
              <div class="medhub-devices">${_escHtml(s.devices)}</div>
              <div class="medhub-metrics-kv">${metricsHtml}</div>
            </article>
          `;
        })
        .join("");
    }

    // Mode 2.2: Render 6 Coupled Pre-Symptomatic Pathways
    const pathwaysEl = document.getElementById("medhub-pathways-list");
    if (pathwaysEl) {
      pathwaysEl.innerHTML = pathways
        .map((p) => {
          const pStyle = _medhubTierStyle(p.tier);
          const sigs = (p.converging_signals || [])
            .map((sig) => `<li>${_escHtml(sig)}</li>`)
            .join("");
          const linked = (p.silos_linked || []).join(" ↔ ");
          return `
            <article class="sub-glass medhub-pathway-card">
              <div class="medhub-pathway-head">
                <div>
                  <div class="eyebrow">${_escHtml(linked)}</div>
                  <h3>${_escHtml(p.title)}</h3>
                </div>
                <div class="medhub-pathway-score">
                  <strong>${_escHtml(p.score)}/100</strong>
                  <span class="triage-pill ${pStyle.pill}">${_escHtml(p.tier)}</span>
                </div>
              </div>
              <ul class="medhub-signals-list">${sigs}</ul>
              <p class="medhub-science-note">Evidence: ${_escHtml(p.science_basis)}</p>
              <div class="medhub-action-box"><strong>Pre-Symptomatic Action:</strong> ${_escHtml(p.pre_symptomatic_action)}</div>
            </article>
          `;
        })
        .join("");
    }

    // Mode 2.3: Render Real NASA OSDR Benchmark Comparisons
    const osdrBody = document.getElementById("medhub-osdr-tbody");
    if (osdrBody) {
      osdrBody.innerHTML = osdrComps
        .map((row) => {
          const sign = row.delta_vs_osdr_pct > 0 ? "+" : "";
          const flagCls = row.exceeds_rcv ? "pill-warning" : "pill-nominal";
          const flagTxt = row.exceeds_rcv
            ? `EXCEEDS RCV (${row.rcv_threshold_pct}%)`
            : `WITHIN RCV (${row.rcv_threshold_pct}%)`;
          return `
            <tr>
              <td><strong>${_escHtml(row.label)}</strong> <span class="medhub-devices">(${_escHtml(row.study)})</span></td>
              <td>${_escHtml(row.device)}</td>
              <td><strong>${_escHtml(row.current)}</strong> ${_escHtml(row.unit)}</td>
              <td>${_escHtml(row.osdr_preflight_median)} ${_escHtml(row.unit)}</td>
              <td>${_escHtml(row.osdr_r1_postflight_median)} ${_escHtml(row.unit)}</td>
              <td>${sign}${_escHtml(row.delta_vs_osdr_pct)}%</td>
              <td><span class="triage-pill ${flagCls}">${_escHtml(flagTxt)}</span></td>
            </tr>
          `;
        })
        .join("");
    }

    // Mode 2.4: Render Real NASA CCMC DONKI SEP Feed
    const donkiEl = document.getElementById("medhub-donki-list");
    if (donkiEl) {
      const events = data.donki_sep_events || [];
      donkiEl.innerHTML = events.length
        ? events
            .map(
              (ev) => `
                <div class="sub-glass medhub-donki-item">
                  <div><strong>${_escHtml(ev.sep_id)}</strong> · ${_escHtml(ev.event_time)}</div>
                  <div class="medhub-devices">Instruments: ${_escHtml((ev.instruments || []).join(", ") || "GOES")} · Linked CME/Flares: ${_escHtml(ev.linked_count)}</div>
                </div>
              `
            )
            .join("")
        : `<div class="sub-glass medhub-donki-item">No cached DONKI SEP events found.</div>`;
    }
  }

  async function loadClinicalHub(scenarioOverride) {
    const sel = document.getElementById("medhub-scenario-select");
    const scenarioId =
      typeof scenarioOverride === "string" && scenarioOverride
        ? scenarioOverride
        : sel?.value || "nominal_iss";
    syncMedHubScenarioUI(scenarioId);
    try {
      const res = await fetch(`/api/clinical/hub?scenario_id=${encodeURIComponent(scenarioId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderClinicalHub(data);
    } catch (err) {
      console.error("Failed loading ISS MedHub:", err);
      const provEl = document.getElementById("medhub-provenance");
      if (provEl) provEl.textContent = `MedHub API error: ${err.message}`;
    }
  }

  async function evaluateClinicalHubFromUI() {
    const sel = document.getElementById("medhub-scenario-select");
    const scenarioId = sel ? sel.value : "nominal_iss";
    const numVal = (id) => {
      const v = parseFloat(document.getElementById(id)?.value);
      return Number.isFinite(v) ? v : undefined;
    };
    const poc_labs = {};
    const imaging = {};
    const pulmonary_exercise = {};
    const environment = {};

    const ica = numVal("mh-ov-ica");
    const hb = numVal("mh-ov-hb");
    const hct = numVal("mh-ov-hct");
    const usg = numVal("mh-ov-usg");
    const onsd = numVal("mh-ov-onsd");
    const jug = document.getElementById("mh-ov-jugular")?.value;
    const cortisol = numVal("mh-ov-cortisol");
    const hydr = numVal("mh-ov-hydration");
    const co2 = numVal("mh-ov-co2");

    if (ica !== undefined) poc_labs.ica_mmol_l = ica;
    if (hb !== undefined) poc_labs.hb_g_dl = hb;
    if (hct !== undefined) poc_labs.hct_pct = hct;
    if (usg !== undefined) poc_labs.urine_sg = usg;
    if (cortisol !== undefined) poc_labs.saliva_cortisol_nmol_l = cortisol;
    if (onsd !== undefined) imaging.onsd_mm = onsd;
    if (jug) imaging.jugular_flow_grade = jug;
    if (hydr !== undefined) pulmonary_exercise.hydration_l_day = hydr;
    if (co2 !== undefined) environment.ppco2_mmhg = co2;

    try {
      const res = await fetch("/api/clinical/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_id: scenarioId,
          overrides: { poc_labs, imaging, pulmonary_exercise, environment },
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderClinicalHub(data);
    } catch (err) {
      console.error("Failed evaluating ISS MedHub overrides:", err);
      const provEl = document.getElementById("medhub-provenance");
      if (provEl) provEl.textContent = `MedHub evaluate error: ${err.message}`;
    }
  }

  function initClinicalMedHub() {
    window.loadClinicalHub = loadClinicalHub;
    document.getElementById("medhub-mode-simple")?.addEventListener("click", () => setMedHubMode("simple"));
    document.getElementById("medhub-mode-depth")?.addEventListener("click", () => setMedHubMode("depth"));
    document.getElementById("btn-medhub-open-depth")?.addEventListener("click", () => setMedHubMode("depth"));

    document.querySelectorAll(".medhub-preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sid = btn.dataset.scenario || "nominal_iss";
        syncMedHubScenarioUI(sid);
        loadClinicalHub(sid);
      });
    });

    document.getElementById("medhub-scenario-select")?.addEventListener("change", (e) => {
      const sid = e.target.value || "nominal_iss";
      syncMedHubScenarioUI(sid);
      loadClinicalHub(sid);
    });
    document.getElementById("btn-medhub-refresh")?.addEventListener("click", () => loadClinicalHub());
    document.getElementById("btn-medhub-evaluate")?.addEventListener("click", evaluateClinicalHubFromUI);

    setMedHubMode(medhubState.mode);
    loadClinicalHub();
    initKitLocator();
  }

  const KIT_BAYS = [
    { id: "bay-01", code: "BAY 01", name: "Optics & SANS Kit", devices: "Ophthalmoscope · Amsler", location: "Columbus Deck · Rack A1" },
    { id: "bay-02", code: "BAY 02", name: "Cardiac & Airway Kit", devices: "12-Lead ECG · Pulse Ox · AED", location: "Columbus Deck · Rack A2" },
    { id: "bay-03", code: "BAY 03", name: "Trauma & Splints", devices: "Hemostatic · Immobilizer", location: "Node 2 · Locker B4" },
    { id: "bay-04", code: "BAY 04", name: "IV & Meds Pack", devices: "Saline · Beta-Blocker · Epi", location: "Destiny Core · Rack C1" },
  ];
  const kitState = { selectedId: "bay-02", beaconId: "bay-02", pulledIds: new Set() };

  function renderKitLocator() {
    const grid = document.getElementById("kit-bay-grid");
    const pill = document.getElementById("kit-locator-pill");
    const status = document.getElementById("kit-locator-status");
    if (!grid) return;

    const selected = KIT_BAYS.find((b) => b.id === kitState.selectedId) || KIT_BAYS[1];
    grid.innerHTML = KIT_BAYS.map((bay) => {
      const isSelected = bay.id === kitState.selectedId;
      const isBeacon = bay.id === kitState.beaconId;
      const isPulled = kitState.pulledIds.has(bay.id);
      const cls = [
        "kit-bay-card",
        isSelected ? "is-selected" : "",
        isBeacon ? "is-beacon" : "",
        isPulled ? "is-pulled" : "",
      ].filter(Boolean).join(" ");
      const badge = isPulled
        ? `<span class="triage-pill pill-nominal">KIT PULLED</span>`
        : isBeacon
          ? `<span class="triage-pill pill-warning"><i class="kit-led-dot"></i>ACTIVE BEACON · LED LIT · PULL KIT</span>`
          : `<span class="triage-pill pill-nominal">STANDBY</span>`;
      return `
        <button type="button" class="${cls}" data-bay-id="${bay.id}">
          <div class="kit-bay-top">
            <span class="kit-bay-code">${bay.code}</span>
            ${badge}
          </div>
          <h3 class="kit-bay-title">${bay.name}</h3>
          <div class="kit-bay-devices">${bay.devices}</div>
          <div class="kit-bay-location">📍 ${bay.location}</div>
        </button>
      `;
    }).join("");

    grid.querySelectorAll(".kit-bay-card").forEach((card) => {
      card.addEventListener("click", () => {
        kitState.selectedId = card.dataset.bayId;
        renderKitLocator();
      });
    });

    if (pill) {
      if (kitState.pulledIds.has(selected.id)) {
        pill.className = "triage-pill pill-nominal";
        pill.textContent = `${selected.code} · KIT PULLED`;
      } else if (kitState.beaconId === selected.id) {
        pill.className = "triage-pill pill-warning";
        pill.textContent = `${selected.code} · ACTIVE BEACON`;
      } else {
        pill.className = "triage-pill pill-nominal";
        pill.textContent = `${selected.code} · SELECTED`;
      }
    }
    if (status) {
      if (kitState.pulledIds.has(selected.id)) {
        status.textContent = `${selected.code} (${selected.name}) confirmed pulled from ${selected.location}.`;
      } else if (kitState.beaconId === selected.id) {
        status.textContent = `${selected.code} LED beacon pulsing at ${selected.location} — pull ${selected.name} (${selected.devices}).`;
      } else {
        status.textContent = `${selected.code} selected (${selected.location}). Click Toggle LED Beacon to illuminate rack guide.`;
      }
    }
  }

  function jumpToKitLocator(bayId = "bay-02") {
    kitState.selectedId = bayId;
    kitState.beaconId = bayId;
    setMedHubMode("simple");
    if (typeof switchLevel === "function") switchLevel("medhub");
    renderKitLocator();
    setTimeout(() => {
      document.getElementById("medhub-kit-locator")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 80);
  }

  function initKitLocator() {
    renderKitLocator();
    document.getElementById("kit-beacon-toggle-btn")?.addEventListener("click", () => {
      kitState.beaconId = kitState.beaconId === kitState.selectedId ? null : kitState.selectedId;
      renderKitLocator();
    });
    document.getElementById("kit-confirm-pulled-btn")?.addEventListener("click", () => {
      if (kitState.pulledIds.has(kitState.selectedId)) {
        kitState.pulledIds.delete(kitState.selectedId);
      } else {
        kitState.pulledIds.add(kitState.selectedId);
        if (kitState.beaconId === kitState.selectedId) kitState.beaconId = null;
      }
      renderKitLocator();
    });
    document.getElementById("csa-open-kits-btn")?.addEventListener("click", () => jumpToKitLocator("bay-02"));
    document.getElementById("cwb-locator-btn")?.addEventListener("click", () => jumpToKitLocator("bay-02"));
  }
})();
