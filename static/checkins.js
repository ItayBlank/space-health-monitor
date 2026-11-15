(() => {
  const $ = (id) => document.getElementById(id);
  const lock = $("checkins-lock");
  const panel = $("checkins-private");
  if (!lock || !panel) return;
  let privateData = null;
  let sessionGeneration = 0;
  let previewIds = null;
  const escapeText = (value) => String(value ?? "");

  async function api(path, options = {}) {
    const response = await fetch(`/api/private/${path}`, {
      credentials: "same-origin",
      cache: "no-store",
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && path !== "login") lockState();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  }

  function lockState() {
    sessionGeneration += 1;
    privateData = null;
    previewIds = null;
    panel.classList.add("hidden");
    lock.classList.remove("hidden");
    $("checkins-owner").textContent = "";
    $("checkins-history").replaceChildren();
    $("checkins-baseline").replaceChildren();
    $("checkins-followup").replaceChildren();
    $("checkins-followup").classList.add("hidden");
    $("checkins-demo-results").replaceChildren();
    $("checkins-share-preview").replaceChildren();
    $("checkins-share").classList.add("hidden");
    $("checkins-entry-form").reset();
    $("checkin-note").value = "";
    $("mood-value").value = "3";
    $("stress-value").value = "3";
    $("checkins-save-status").textContent = "";
    $("checkins-share-status").textContent = "";
    $("checkins-login-error").textContent = "";
    $("checkins-consent").checked = false;
    $("checkins-share-submit").disabled = true;
    $("checkins-share-open").disabled = true;
    $("checkins-login").reset();
    $("checkins-password").value = "";
    document.dispatchEvent(new Event("astra-private-locked"));
  }

  function enterState(crewId) {
    sessionGeneration += 1;
    lock.classList.add("hidden");
    panel.classList.remove("hidden");
    $("checkins-owner").textContent = crewId;
    document.dispatchEvent(new Event("astra-private-entered"));
  }

  function make(tag, text, className = "") {
    const node = document.createElement(tag);
    node.textContent = escapeText(text);
    if (className) node.className = className;
    return node;
  }

  function selectedIds() {
    return [...document.querySelectorAll(".checkins-select:checked")].map((item) => item.value);
  }

  function render(data) {
    privateData = data;
    if (!$("checkins-share").classList.contains("hidden")) {
      $("checkins-share").classList.add("hidden");
      $("checkins-share-preview").replaceChildren();
      $("checkins-consent").checked = false;
      previewIds = null;
    }
    const trend = data.trend;
    const baseline = $("checkins-baseline");
    baseline.replaceChildren();
    if (!trend.baseline_ready) {
      baseline.append(make("p", `Establishing your personal baseline: ${trend.baseline_count} of ${trend.baseline_required} measured check-ins. Your entries remain visible below.`));
    } else {
      baseline.append(make("p", `Usual mood range: ${trend.usual_mood[0]}–${trend.usual_mood[1]} / 5 (higher is better).`));
      baseline.append(make("p", `Usual perceived stress range: ${trend.usual_stress[0]}–${trend.usual_stress[1]} / 5 (higher is more stress).`));
      baseline.append(make("small", "Illustrative range = average of your first 5 measured check-ins ±1 point. Baseline stays fixed so the three entries being evaluated cannot absorb their own change."));
    }

    const history = $("checkins-history");
    history.replaceChildren();
    if (!data.entries.length) history.append(make("p", "No private check-ins recorded yet."));
    [...data.entries].reverse().forEach((entry) => {
      const row = document.createElement("article");
      row.className = "checkin-row";
      const check = document.createElement("input");
      check.type = "checkbox";
      check.className = "checkins-select";
      check.value = entry.id;
      check.setAttribute("aria-label", `Select check-in ${entry.created_at}`);
      check.addEventListener("change", updateShareAvailability);
      const copy = document.createElement("div");
      copy.append(make("strong", `Mood ${entry.mood}/5 · Stress ${entry.stress}/5`));
      if (entry.note) copy.append(make("p", entry.note));
      const when = document.createElement("time");
      when.dateTime = entry.created_at;
      when.textContent = new Date(entry.created_at).toLocaleString();
      row.append(check, copy, when);
      history.append(row);
    });

    const followup = $("checkins-followup");
    followup.replaceChildren();
    followup.classList.toggle("hidden", !trend.prompt);
    if (trend.prompt) {
      followup.append(make("h2", "Would private support be useful?"));
      followup.append(make("p", "Three consecutive measured check-ins are outside your illustrative personal usual range. This is a private supportive follow-up, not a diagnosis."));
      const shareButton = make("button", "Choose entries to include", "btn-glass-pri");
      shareButton.type = "button";
      shareButton.addEventListener("click", openShare);
      const dismissButton = make("button", "Dismiss this follow-up", "btn-glass-sec");
      dismissButton.type = "button";
      dismissButton.addEventListener("click", dismissPrompt);
      followup.append(familyMessageButton("Watch a message from home"), shareButton, dismissButton);
    }
    renderDemos(data.demo_cases || []);
  }

  function familyMessageButton(label) {
    const button = make("button", label, "btn-glass-sec");
    button.type = "button";
    button.addEventListener("click", () => document.dispatchEvent(new Event("astra-open-family-message")));
    return button;
  }

  function renderDemos(cases) {
    const area = $("checkins-demo-results");
    area.replaceChildren();
    cases.forEach((item) => {
      const card = document.createElement("div");
      card.className = "checkins-demo-case";
      card.append(make("strong", `${item.case === "isolated" ? "Isolated dip" : "Sustained change"}: ${item.trend.prompt ? "follow-up offered" : "no follow-up"}`));
      card.append(make("p", "Synthetic examples only. They do not alter your baseline, personal history, or consult requests."));
      if (item.trend.prompt) card.append(familyMessageButton("Open sample message"));
      area.append(card);
    });
  }

  function updateShareAvailability() {
    $("checkins-share-open").disabled = selectedIds().length === 0;
    if (previewIds && JSON.stringify([...selectedIds()].sort()) !== JSON.stringify([...previewIds].sort())) {
      previewIds = null;
      $("checkins-consent").checked = false;
      $("checkins-share-submit").disabled = true;
      $("checkins-share-status").textContent = "Selection changed. Review the updated entries before continuing.";
      $("checkins-share-preview").replaceChildren();
    }
    const consent = $("checkins-consent");
    if (consent) $("checkins-share-submit").disabled = !previewIds || !consent.checked || selectedIds().length === 0;
  }

  function openShare() {
    const ids = selectedIds();
    if (!ids.length) {
      $("checkins-share-status").textContent = "Select entries in your history first.";
      return;
    }
    const entries = privateData.entries.filter((item) => ids.includes(item.id));
    previewIds = [...ids];
    const preview = $("checkins-share-preview");
    preview.replaceChildren();
    entries.forEach((entry) => {
      const line = make("p", `${new Date(entry.created_at).toLocaleString()} · Mood ${entry.mood}/5 · Stress ${entry.stress}/5${entry.note ? ` · ${entry.note}` : ""}`);
      preview.append(line);
    });
    $("checkins-consent").checked = false;
    $("checkins-share-submit").disabled = true;
    $("checkins-share-status").textContent = "";
    $("checkins-share").classList.remove("hidden");
  }

  async function dismissPrompt() {
    const generation = sessionGeneration;
    try {
      await api("dismiss", { method: "POST", body: JSON.stringify({ triplet_key: privateData.trend.triplet_key }) });
      if (generation !== sessionGeneration || panel.classList.contains("hidden")) return;
      await refresh();
    } catch (error) { if (generation === sessionGeneration && !panel.classList.contains("hidden")) $("checkins-save-status").textContent = error.message; }
  }

  async function refresh() {
    const generation = sessionGeneration;
    const data = await api("checkins");
    if (generation !== sessionGeneration || panel.classList.contains("hidden")) return;
    render(data);
  }

  document.addEventListener("astra-private-expired", lockState);
  window.addEventListener("pagehide", lockState);

  document.addEventListener("astra-level-change", (event) => {
    if (event.detail?.level !== "checkins" && !panel.classList.contains("hidden")) {
      lockState();
      // Revoke the owner session when leaving the private page; UI locks immediately.
      api("logout", { method: "POST", body: "{}" }).catch(() => {});
    }
  });
  $("checkins-login").addEventListener("submit", async (event) => {
    event.preventDefault();
    const generation = sessionGeneration;
    $("checkins-login-error").textContent = "";
    try {
      const crewId = $("checkins-crew-id").value.trim();
      await api("login", { method: "POST", body: JSON.stringify({ crew_id: crewId, password: $("checkins-password").value }) });
      if (generation !== sessionGeneration || $("view-checkins").classList.contains("hidden")) {
        api("logout", { method: "POST", body: "{}" }).catch(() => {});
        return;
      }
      enterState(crewId);
      $("checkins-password").value = "";
      await refresh();
    } catch (error) {
      $("checkins-password").value = "";
      if (generation !== sessionGeneration) return;
      $("checkins-login-error").textContent = error.message === "Crew ID or password is incorrect" ? error.message : "Sign-in failed. Check your connection and try again.";
    }
  });
  $("checkins-logout").addEventListener("click", async () => {
    let revoked = false;
    try { await api("logout", { method: "POST", body: "{}" }); revoked = true; } catch (_) { /* lock locally, then explain revocation could not be confirmed */ }
    lockState();
    if (!revoked) $("checkins-login-error").textContent = "Locked locally. Server sign-out could not be confirmed; the session remains valid until it expires.";
  });
  $("checkin-mood").addEventListener("input", (event) => $("mood-value").value = event.target.value);
  $("checkin-stress").addEventListener("input", (event) => $("stress-value").value = event.target.value);
  $("checkins-entry-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const generation = sessionGeneration;
    $("checkins-save-status").textContent = "Saving…";
    try {
      await api("checkins", { method: "POST", body: JSON.stringify({ mood: Number($("checkin-mood").value), stress: Number($("checkin-stress").value), note: $("checkin-note").value }) });
      if (generation !== sessionGeneration || panel.classList.contains("hidden")) return;
      $("checkin-note").value = "";
      $("checkins-save-status").textContent = "Saved privately.";
      await refresh();
    } catch (error) { if (generation === sessionGeneration && !panel.classList.contains("hidden")) $("checkins-save-status").textContent = error.message; }
  });
  $("checkins-demo").addEventListener("click", async () => {
    const generation = sessionGeneration;
    try { await api("demo", { method: "POST", body: "{}" }); if (generation === sessionGeneration && !panel.classList.contains("hidden")) await refresh(); }
    catch (error) { if (generation === sessionGeneration && !panel.classList.contains("hidden")) $("checkins-save-status").textContent = error.message; }
  });
  $("checkins-share-open").addEventListener("click", openShare);
  $("checkins-share-cancel").addEventListener("click", () => $("checkins-share").classList.add("hidden"));
  $("checkins-consent").addEventListener("change", updateShareAvailability);
  $("checkins-share-submit").addEventListener("click", async () => {
    const ids = selectedIds();
    if (!$("checkins-consent").checked || !ids.length) return;
    const generation = sessionGeneration;
    try {
      const ids = previewIds;
      if (!ids || JSON.stringify([...selectedIds()].sort()) !== JSON.stringify([...ids].sort())) {
        updateShareAvailability();
        throw new Error("Selection changed. Review the entries again before continuing.");
      }
      const result = await api("consult-requests", { method: "POST", body: JSON.stringify({ entry_ids: ids, recipient: "Flight surgeon (local demo)", consent: true }) });
      if (generation !== sessionGeneration || panel.classList.contains("hidden")) return;
      $("checkins-share-status").textContent = `Request ${result.status.replaceAll("_", " ")}. No delivery occurred.`;
      $("checkins-share-submit").disabled = true;
    } catch (error) { if (generation === sessionGeneration && !panel.classList.contains("hidden")) $("checkins-share-status").textContent = error.message; }
  });

  document.addEventListener("visibilitychange", async () => {
    if (document.visibilityState === "visible" && !panel.classList.contains("hidden")) {
      try { await refresh(); } catch (_) { /* 401 handler clears private state */ }
    }
  });
  const initialGeneration = sessionGeneration;
  api("session").then((status) => {
    if (initialGeneration !== sessionGeneration) return;
    if (status.authenticated) {
      // Server never returns the owner identity: require re-authentication after a page reload.
      lockState();
    }
  }).catch(() => lockState());
  window.setInterval(async () => {
    if (panel.classList.contains("hidden")) return;
    try {
      const status = await api("session");
      if (!status.authenticated) lockState();
    } catch (_) { lockState(); }
  }, 60_000);
  updateShareAvailability();
})();
