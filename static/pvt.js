(() => {
  const $ = (id) => document.getElementById(id);
  const state = { crew: "anton", scenario: "", status: null, session: null, intervals: [], timers: [], startedAt: 0, phase: "idle", activeIndex: null, sleepDraft: [] };
  const api = async (path, options = {}) => {
    const response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
    const body = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(body?.detail || `Request failed (${response.status})`);
    return body;
  };
  const date = (value) => value ? new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC" : "—";
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const showError = (error) => { $("pvt-reason").textContent = error.message; $("pvt-status-pill").textContent = "UNAVAILABLE"; $("pvt-start").disabled = true; };

  async function loadCrew() {
    const result = await api("/api/pvt/crew");
    $("pvt-crew").innerHTML = result.crew.map((c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.name)}</option>`).join("");
    $("pvt-crew").value = state.crew;
  }

  async function refresh() {
    if (state.session) return;
    try {
      state.crew = $("pvt-crew").value || state.crew;
      state.scenario = $("pvt-scenario").value;
      const suffix = state.scenario ? `?scenario=${encodeURIComponent(state.scenario)}` : "";
      const data = await api(`/api/pvt/status/${encodeURIComponent(state.crew)}${suffix}`);
      state.status = data;
      const demo = Boolean(state.scenario);
      $("pvt-demo-banner").classList.toggle("hidden", !demo);
      $("pvt-status-pill").textContent = demo ? "SYNTHETIC" : data.recommend ? "RECOMMENDED" : data.sleep.status === "unknown" ? "SLEEP UNKNOWN" : "NOT INDICATED";
      $("pvt-reason").textContent = data.reason;
      $("pvt-event").textContent = data.event ? data.event.title : "No upcoming assigned critical event";
      $("pvt-event-time").textContent = data.event ? date(data.event.event_utc) : "Two-hour window is checked against UTC";
      $("pvt-sleep").textContent = data.sleep.status === "unknown" ? "Unknown" : `${Math.floor(data.sleep.total_minutes / 60)} h ${data.sleep.total_minutes % 60} min`;
      $("pvt-sleep-detail").textContent = data.sleep.status === "unknown" ? "Missing, incomplete, or stale log" : `Logged intervals · as of ${date(data.sleep.logged_at_utc)} · clipped to 24 h`;
      const baseline = data.personal_baseline;
      $("pvt-baseline").textContent = baseline.status === "available" ? `${baseline.median_rt_ms} ms · ${baseline.median_lapses} lapses` : baseline.status === "establishing" ? "Establishing" : "Unavailable";
      $("pvt-baseline-detail").textContent = baseline.status === "available" ? `Earlier measured runs · n=${baseline.sample_count}` : "At least 3 earlier measured runs required";
      $("pvt-start").disabled = !data.recommend || demo;
      $("pvt-sleep-form").querySelectorAll("input,button").forEach((el) => { el.disabled = demo; });
      $("pvt-event-form").querySelectorAll("input,button").forEach((el) => { el.disabled = demo; });
      $("pvt-start-note").textContent = demo ? "Scenario data is isolated and cannot start or suppress a measured run." : data.recommend ? "The event is in its two-hour window and sleep is under 6 hours." : "No measured check is currently recommended.";
      renderRecords(data.records || []);
      renderCorrelation(data);
    } catch (error) { showError(error); }
  }

  function renderCorrelation(data, forceDemo = false) {
    if (!$("pvt-correlation-card")) return;
    const records = (data?.records || []).filter((r) => typeof r.median_rt_ms === "number");
    const latest = records.length ? records[records.length - 1] : null;
    const baselineReady = data?.personal_baseline?.status === "available" && typeof data.personal_baseline.median_rt_ms === "number";

    const useLive = !forceDemo && baselineReady && latest;
    const baseMs = useLive ? data.personal_baseline.median_rt_ms : 274;
    const baseRuns = useLive ? (data.personal_baseline.sample_count || 3) : 12;
    const currMs = useLive ? latest.median_rt_ms : 342;
    const lapses = useLive ? (latest.lapses ?? 0) : 4;
    const deltaMs = currMs - baseMs;
    const pct = baseMs > 0 ? ((deltaMs / baseMs) * 100) : 0;
    const pctStr = `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;

    const sleepText = (!forceDemo && data?.sleep?.status !== "unknown" && typeof data?.sleep?.total_minutes === "number")
      ? `${Math.floor(data.sleep.total_minutes / 60)}h ${String(data.sleep.total_minutes % 60).padStart(2, "0")}m`
      : "5h 09m";
    const eventTitle = (!forceDemo && data?.event?.title) ? data.event.title : "Docking Window";

    $("pvt-corr-context").textContent = `${eventTitle} · Sleep ${sleepText}`;
    $("pvt-corr-baseline-label").textContent = `Personal Baseline (${baseRuns} runs)`;
    $("pvt-corr-baseline-val").textContent = `${baseMs} ms`;
    $("pvt-corr-current-label").textContent = `Current Pre-${eventTitle.split(" ")[0]} PVT`;
    $("pvt-corr-current-val").textContent = `${currMs} ms (${deltaMs >= 0 ? "+" : ""}${deltaMs} ms, ${lapses} lapses)`;

    const degraded = pct > 10 || lapses >= 3;
    $("pvt-corr-rec-val").textContent = degraded ? "Defer Docking · 90m Recovery" : "Cleared for Task Window";
    $("pvt-corr-pill").textContent = `${pctStr} LATENCY`;
    $("pvt-corr-pill").className = `triage-pill ${degraded ? "pill-warning" : "pill-nominal"}`;
    $("pvt-corr-bar-label").textContent = `${pctStr} LATENCY vs. BASELINE`;
    const fill = $("pvt-corr-bar-fill");
    if (fill) {
      fill.style.width = `${Math.min(100, Math.max(10, Math.abs(pct) * 2.5))}%`;
      fill.classList.toggle("is-nominal", !degraded);
    }
  }

  function renderRecords(records) {
    const list = $("pvt-records-list");
    list.replaceChildren();
    $("pvt-records-empty").classList.toggle("hidden", records.length > 0);
    for (const row of records.slice().reverse()) {
      const item = document.createElement("li");
      const origin = row.provenance === "synthetic" ? "SYNTHETIC DEMO" : "MEASURED";
      item.innerHTML = `<span class="pvt-origin ${row.provenance === "synthetic" ? "synthetic" : ""}">${origin}</span><strong>${row.median_rt_ms ?? "—"} ms median</strong><span>${row.lapses ?? "—"} lapses · ${row.trial_count ?? "—"} stimuli</span><time>${date(row.completed_at_utc)}</time>`;
      list.appendChild(item);
    }
  }

  function clearTimers() { state.timers.forEach((timer) => { clearTimeout(timer); clearInterval(timer); }); state.timers = []; }
  function setControlsBusy(busy) {
    ["pvt-crew", "pvt-scenario", "pvt-refresh"].forEach((id) => { if ($(id)) $(id).disabled = busy; });
    const demo = Boolean(state.scenario);
    $("pvt-start").disabled = busy || demo || !state.status?.recommend;
    $("pvt-sleep-form").querySelectorAll("input,button").forEach((el) => { el.disabled = busy || demo; });
    $("pvt-event-form").querySelectorAll("input,button").forEach((el) => { el.disabled = busy || demo; });
    document.querySelectorAll("#pvt-sleep-draft button").forEach((el) => { el.disabled = busy || demo; });
  }
  function renderSleepDraft() {
    const list = $("pvt-sleep-draft");
    list.replaceChildren();
    state.sleepDraft.forEach((interval, index) => {
      const li = document.createElement("li");
      li.textContent = `${new Date(interval.start_utc).toLocaleString()} – ${new Date(interval.end_utc).toLocaleString()} `;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "mini-link-btn";
      remove.textContent = "Remove";
      remove.addEventListener("click", () => { state.sleepDraft.splice(index, 1); renderSleepDraft(); });
      li.appendChild(remove);
      list.appendChild(li);
    });
  }
  async function abort(reason) {
    if (!state.session) return;
    clearTimers();
    const id = state.session.session_id;
    state.session = null;
    state.phase = "idle";
    $("pvt-run").classList.add("hidden");
    setControlsBusy(false);
    $("pvt-result").classList.remove("hidden");
    $("pvt-result").textContent = `Check invalidated: ${reason}. No result was recorded.`;
    try { await api(`/api/pvt/sessions/${encodeURIComponent(id)}/abort`, { method: "POST" }); } catch (_) {}
    await refresh();
  }

  function updateClock() {
    if (!state.session) return;
    const elapsed = performance.now() - state.startedAt;
    const remain = Math.max(0, Math.ceil(180 - elapsed / 1000));
    $("pvt-run-clock").textContent = `${String(Math.floor(remain / 60)).padStart(2, "0")}:${String(remain % 60).padStart(2, "0")}`;
    if (remain === 0) finish();
  }

  function finish() {
    if (!state.session || state.phase === "finishing") return;
    state.phase = "finishing";
    clearTimers();
    state.activeIndex = null;
    $("pvt-stimulus").className = "pvt-stimulus";
    $("pvt-stimulus").textContent = "SAVING";
    $("pvt-run-message").textContent = "Three minutes complete. Saving the measured responses…";
    const { session_id } = state.session;
    const responses = state.responses;
    api(`/api/pvt/sessions/${encodeURIComponent(session_id)}/complete`, { method: "POST", body: JSON.stringify({ reaction_times_ms: responses }) })
      .then((result) => {
        state.session = null;
        state.phase = "idle";
        $("pvt-run").classList.add("hidden");
        setControlsBusy(false);
        $("pvt-result").classList.remove("hidden");
        $("pvt-result").textContent = `Measured result · median ${result.median_rt_ms} ms · ${result.lapses} lapses across ${result.trial_count} stimuli. Lapse threshold is illustrative.`;
        refresh();
      })
      .catch((error) => abort(error.message));
  }

  function scheduleStimuli() {
    let at = 0;
    state.intervals.forEach((interval, index) => {
      at += interval;
      state.timers.push(setTimeout(() => {
        if (!state.session || state.phase === "finishing") return;
        if (state.activeIndex !== null) {
          state.activeIndex = null;
          state.phase = "wait";
        }
        state.activeIndex = index;
        state.phase = "go";
        state.stimulusAt = performance.now();
        $("pvt-stimulus").className = "pvt-stimulus is-go";
        $("pvt-stimulus").textContent = "RESPOND";
        $("pvt-run-message").textContent = `Stimulus ${index + 1} of ${state.intervals.length}`;
        state.timers.push(setTimeout(() => {
          if (state.session && state.activeIndex === index && state.phase === "go") {
            state.activeIndex = null;
            state.phase = "wait";
            $("pvt-stimulus").className = "pvt-stimulus";
            $("pvt-stimulus").textContent = "WAIT";
            $("pvt-run-message").textContent = "No response recorded for that signal. Continue.";
          }
        }, 1900));
      }, at));
    });
    state.timers.push(setTimeout(finish, 180000));
    state.timers.push(setInterval(updateClock, 250));
  }

  async function start() {
    $("pvt-start").disabled = true;
    setControlsBusy(true);
    $("pvt-result").classList.add("hidden");
    try {
      const session = await api("/api/pvt/sessions/start", { method: "POST", body: JSON.stringify({ crew_id: state.crew }) });
      state.session = session;
      state.intervals = session.stimulus_intervals_ms;
      state.responses = Array(state.intervals.length).fill(null);
      state.startedAt = performance.now();
      state.phase = "wait";
      setControlsBusy(true);
      $("pvt-run").classList.remove("hidden");
      $("pvt-stimulus").className = "pvt-stimulus";
      $("pvt-stimulus").textContent = "READY";
      $("pvt-run-message").textContent = "Wait for the visual signal; respond with the button, Space, or Enter.";
      scheduleStimuli();
    } catch (error) { setControlsBusy(false); showError(error); await refresh(); }
  }

  function respond() {
    if (!state.session) return;
    if (state.phase !== "go" || state.activeIndex === null) {
      abort("false start or response outside a visual stimulus");
      return;
    }
    const reaction = Math.round(performance.now() - state.stimulusAt);
    if (reaction < 100) { abort("anticipatory response under 100 ms"); return; }
    state.responses[state.activeIndex] = Math.min(2000, reaction);
    state.activeIndex = null;
    state.phase = "wait";
    $("pvt-stimulus").className = "pvt-stimulus";
    $("pvt-stimulus").textContent = "WAIT";
    $("pvt-run-message").textContent = "Wait for the next visual signal.";
  }

  function addSleepInterval() {
    const a = $("pvt-sleep-start").value, b = $("pvt-sleep-end").value;
    if (!a || !b || new Date(a) >= new Date(b)) { showError(new Error("Enter a valid start and end for each interval.")); return; }
    state.sleepDraft.push({ start_utc: new Date(a).toISOString(), end_utc: new Date(b).toISOString() });
    $("pvt-sleep-start").value = "";
    $("pvt-sleep-end").value = "";
    $("pvt-reason").textContent = `${state.sleepDraft.length} interval(s) staged. Add any naps, then save the complete 24-hour snapshot.`;
    renderSleepDraft();
  }

  async function submitSleep(event) {
    event.preventDefault();
    try {
      const a = $("pvt-sleep-start").value, b = $("pvt-sleep-end").value;
      const intervals = [...state.sleepDraft];
      if (a || b) {
        if (!a || !b || new Date(a) >= new Date(b)) throw new Error("Enter a valid start and end for every sleep interval.");
        intervals.push({ start_utc: new Date(a).toISOString(), end_utc: new Date(b).toISOString() });
      }
      await api("/api/pvt/sleep", { method: "POST", body: JSON.stringify({ crew_id: state.crew, complete: $("pvt-sleep-complete").checked, intervals }) });
      state.sleepDraft = [];
      renderSleepDraft();
      event.target.reset();
      $("pvt-result").classList.remove("hidden");
      $("pvt-result").textContent = "Sleep snapshot saved. Refreshing eligibility.";
      await refresh();
    } catch (error) { showError(error); }
  }

  async function submitEvent(event) {
    event.preventDefault();
    try {
      const local = $("pvt-event-input").value;
      if (!local) throw new Error("Choose an event time.");
      const eventUtc = new Date(local).toISOString();
      if (state.status?.event?.id && !state.status.event.provenance?.includes("synthetic")) {
        await api(`/api/pvt/events/${encodeURIComponent(state.status.event.id)}?event_utc=${encodeURIComponent(eventUtc)}`, { method: "PUT" });
      } else {
        await api("/api/pvt/events", { method: "POST", body: JSON.stringify({ crew_id: state.crew, title: $("pvt-event-title").value, event_utc: eventUtc, critical: true }) });
      }
      $("pvt-result").classList.remove("hidden");
      $("pvt-result").textContent = "Assigned event saved. Eligibility was recalculated.";
      await refresh();
    } catch (error) { showError(error); }
  }

  function init() {
    if (!$("pvt-panel")) return;
    loadCrew().then(refresh).catch(showError);
    $("pvt-crew").addEventListener("change", () => { state.sleepDraft = []; renderSleepDraft(); refresh(); });
    $("pvt-scenario").addEventListener("change", refresh);
    $("pvt-refresh").addEventListener("click", refresh);
    $("pvt-start").addEventListener("click", start);
    $("pvt-stimulus").addEventListener("click", respond);
    $("pvt-abort").addEventListener("click", () => abort("cancelled by crew"));
    $("pvt-sleep-form").addEventListener("submit", submitSleep);
    $("pvt-sleep-add").addEventListener("click", addSleepInterval);
    $("pvt-event-form").addEventListener("submit", submitEvent);
    $("pvt-corr-demo-btn")?.addEventListener("click", () => renderCorrelation(state.status, true));
    document.addEventListener("keydown", (event) => {
      if (!state.session || state.phase === "finishing" || event.repeat || !["Space", "Enter"].includes(event.code)) return;
      event.preventDefault();
      respond();
    });
    document.addEventListener("visibilitychange", () => { if (document.hidden && state.session) abort("tab or window went to the background"); });
    window.addEventListener("blur", () => { if (state.session) abort("window lost focus"); });
    const pane = $("view-sensors");
    if (pane) new MutationObserver(() => { if (pane.classList.contains("hidden") && state.session) abort("left the Sensors pane"); }).observe(pane, { attributes: true, attributeFilter: ["class"] });
  }
  document.addEventListener("DOMContentLoaded", init);
})();

