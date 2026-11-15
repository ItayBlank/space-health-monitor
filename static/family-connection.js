(() => {
  const $ = (id) => document.getElementById(id);
  const ownerPanel = $("family-connection");
  const recipientPanel = $("family-recipient-portal");
  if (!ownerPanel && !recipientPanel) return;

  function element(tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    return node;
  }

  async function request(path, body, headers = {}) {
    const options = { credentials: headers.Authorization ? "omit" : "same-origin", cache: "no-store", headers };
    if (body !== undefined) {
      options.method = "POST";
      options.headers = { ...headers, "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(typeof data.detail === "string" ? data.detail : "Family Connection request failed.");
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function values(content) {
    const lines = [];
    if (Object.hasOwn(content, "mood")) {
      lines.push(content.mood === null ? "Mood unavailable" : `Latest mood ${content.mood}/5`);
    }
    if (Object.hasOwn(content, "sleep_minutes")) {
      const duration = content.sleep_minutes;
      lines.push(duration === null ? "Sleep unknown" :
        `Logged sleep ${Math.floor(duration / 60)} h ${duration % 60} min in the past 24 hours`);
    }
    return lines;
  }

  function record(item, lines, showStatus = true) {
    const row = document.createElement("li");
    if (showStatus) {
      const status = item.status[0].toUpperCase() + item.status.slice(1);
      row.append(element("strong", status));
    }
    for (const line of lines) row.append(element("div", line));
    const time = element("time", new Date(item.created_at).toLocaleString());
    time.dateTime = item.created_at;
    row.append(time);
    return row;
  }

  function fill(container, rows, emptyMessage) {
    container.replaceChildren(...(rows.length ? rows : [element("li", emptyMessage)]));
  }

  function ownerFlow() {
    const base = "/api/private/family";
    let signedIn = false;
    let generation = 0;
    let busy = false;
    let state = null;
    let previewId = null;
    let formGeneration = 0;
    const feedback = $("family-status");
    const previewForm = $("family-preview-form");

    function clearPreview() {
      formGeneration += 1;
      previewId = null;
      $("family-preview-values").replaceChildren();
      $("family-preview").classList.add("hidden");
    }

    function closeVideo() {
      const video = $("family-video");
      video.pause();
      video.removeAttribute("src");
      video.load();
      $("family-playback").classList.add("hidden");
    }

    function clearPairingCode() {
      $("family-pairing-code").value = "";
      $("family-code-panel").classList.add("hidden");
    }

    function reset() {
      generation += 1;
      signedIn = false;
      busy = false;
      state = null;
      ownerPanel.open = false;
      ownerPanel.removeAttribute("aria-busy");
      $("family-enable-form").reset();
      previewForm.reset();
      $("family-sharing").classList.add("hidden");
      $("family-enable-form").classList.add("hidden");
      $("family-approved-recipient").textContent = "";
      $("family-link-status").textContent = "";
      $("family-advance").disabled = true;
      $("family-reports").replaceChildren();
      $("family-inbox").replaceChildren();
      feedback.textContent = "";
      clearPreview();
      clearPairingCode();
      closeVideo();
    }

    function render(data) {
      state = data;
      $("family-enable-form").classList.toggle("hidden", data.enabled);
      $("family-sharing").classList.toggle("hidden", !data.enabled);
      $("family-approved-recipient").textContent = data.recipient || "";
      if (!data.enabled) {
        clearPairingCode();
        clearPreview();
      }
      $("family-link-status").textContent = data.link.connected ?
        `Available · ${data.link.latency_s} s simulated one-way delay` :
        "Unavailable. Queued reports and replies wait for Ground link available in Downlink.";
      $("family-advance").disabled = !data.link.connected;
      fill($("family-reports"), data.reports.map((item) => {
        const row = record(item, values(item.content));
        if (item.status === "queued") {
          const cancel = element("button", "Cancel queued update");
          cancel.type = "button";
          cancel.className = "btn-glass-sec";
          cancel.addEventListener("click", () => run(async (current) => {
            await request(`${base}/reports/${encodeURIComponent(item.id)}/cancel`, {});
            await refresh(current);
            return "Update canceled.";
          }));
          row.append(cancel);
        }
        return row;
      }), "No updates yet.");
      fill($("family-inbox"), data.inbox.map((item) => record(item, [item.text], false)), "No replies delivered.");
    }

    async function refresh(current) {
      const data = await request(base);
      if (current === generation) render(data);
    }

    async function run(action) {
      if (!signedIn || busy) return;
      const current = generation;
      busy = true;
      ownerPanel.setAttribute("aria-busy", "true");
      feedback.textContent = "";
      try {
        const message = await action(current);
        if (current === generation) feedback.textContent = message || "";
      } catch (error) {
        if (current !== generation) return;
        if (error.status === 401) document.dispatchEvent(new Event("astra-private-expired"));
        else feedback.textContent = error.message;
      } finally {
        if (current === generation) {
          busy = false;
          ownerPanel.removeAttribute("aria-busy");
        }
      }
    }

    async function openVideo(current) {
      ownerPanel.open = true;
      const data = await request(base);
      if (current !== generation || !ownerPanel.open) return;
      render(data);
      if (!data.video_url) throw new Error("The preloaded message is unavailable.");
      const url = new URL(data.video_url, window.location.href);
      if (url.origin !== window.location.origin) throw new Error("The preloaded message is unavailable.");
      $("family-video").src = url.href;
      $("family-playback").classList.remove("hidden");
      $("family-video").focus();
    }

    document.addEventListener("astra-private-locked", reset);
    document.addEventListener("astra-private-entered", () => { reset(); signedIn = true; });
    document.addEventListener("astra-open-family-message", () => run(openVideo));
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && ownerPanel.open) run(refresh);
    });
    ownerPanel.addEventListener("toggle", () => {
      if (ownerPanel.open) run(refresh);
      else { closeVideo(); clearPairingCode(); clearPreview(); }
    });
    $("family-watch").addEventListener("click", () => run(openVideo));
    $("family-video-close").addEventListener("click", () => { closeVideo(); $("family-watch").focus(); });
    $("family-enable-form").addEventListener("submit", (event) => {
      event.preventDefault();
      run(async (current) => {
        const result = await request(`${base}/enable`, { recipient: $("family-recipient-name").value.trim() });
        if (current !== generation) return;
        $("family-pairing-code").value = result.pairing_code;
        if (ownerPanel.open) $("family-code-panel").classList.remove("hidden");
        else clearPairingCode();
        await refresh(current);
        return "Family sharing enabled. Give the pairing code to the approved recipient.";
      });
    });
    $("family-revoke").addEventListener("click", () => run(async (current) => {
      await request(`${base}/revoke`, {});
      await refresh(current);
      return "Sharing stopped. Queued updates were canceled.";
    }));
    previewForm.addEventListener("change", clearPreview);
    previewForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const fields = new FormData(previewForm).getAll("field");
      clearPreview();
      const fieldVersion = formGeneration;
      if (!fields.length) {
        feedback.textContent = "Choose at least one field.";
        return;
      }
      run(async (current) => {
        const preview = await request(`${base}/preview`, { fields });
        if (current !== generation || fieldVersion !== formGeneration || !ownerPanel.open) return;
        previewId = preview.preview_id;
        $("family-preview-values").replaceChildren(...values(preview.content).map(line => element("li", line)));
        $("family-preview").classList.remove("hidden");
        $("family-approve").focus();
      });
    });
    $("family-discard").addEventListener("click", clearPreview);
    $("family-approve").addEventListener("click", () => {
      if (previewId === null) return;
      run(async (current) => {
        await request(`${base}/reports`, { preview_id: previewId });
        if (current === generation) clearPreview();
        await refresh(current);
        return "Approved update queued.";
      });
    });
    $("family-refresh").addEventListener("click", () => run(refresh));
    $("family-advance").addEventListener("click", () => {
      if (!state?.link.connected) return;
      run(async (current) => {
        const result = await request(`${base}/advance`, { seconds: Math.min(86400, Math.max(1, state.link.latency_s)) });
        await refresh(current);
        return result.delivered === 1 ? "One message delivered." : `${result.delivered} messages delivered.`;
      });
    });
    reset();
  }

  function recipientFlow() {
    const base = "/api/family";
    let code = "";
    let generation = 0;
    let pending = false;
    const gate = $("family-portal-gate");
    const home = $("family-portal-home");
    const status = $("family-portal-status");

    function lock() {
      generation += 1;
      pending = false;
      code = "";
      gate.reset();
      $("family-reply-form").reset();
      $("family-portal-name").textContent = "";
      $("family-portal-link").textContent = "";
      $("family-portal-reports").replaceChildren();
      $("family-portal-replies").replaceChildren();
      status.textContent = "";
      home.hidden = true;
      gate.hidden = false;
    }

    async function load(current) {
      const data = await request(base, undefined, { Authorization: `Bearer ${code}` });
      if (current !== generation) return;
      $("family-portal-name").textContent = data.recipient;
      $("family-portal-link").textContent = data.link.connected ? "Mission link available." :
        "Mission link unavailable. Replies will wait for the uplink.";
      fill($("family-portal-reports"), data.reports.map(item => record(item, values(item.content))), "No delivered updates.");
      fill($("family-portal-replies"), data.replies.map(item => record(item, [item.text])), "No replies yet.");
      gate.hidden = true;
      home.hidden = false;
    }

    async function run(action) {
      if (pending) return;
      const current = generation;
      pending = true;
      status.textContent = "";
      try {
        const message = await action(current);
        if (current === generation) status.textContent = message || "";
      } catch (error) {
        if (current !== generation) return;
        if (error.status === 401 || error.status === 403) lock();
        status.textContent = error.message;
      } finally {
        if (current === generation) pending = false;
      }
    }

    gate.addEventListener("submit", (event) => {
      event.preventDefault();
      if (pending) return;
      code = $("family-portal-code").value.trim();
      gate.reset();
      run(load);
    });
    $("family-portal-lock").addEventListener("click", lock);
    $("family-portal-refresh").addEventListener("click", () => run(load));
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && code && !home.hidden) run(load);
    });
    $("family-reply-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const text = $("family-reply-text").value.trim();
      if (!text) { status.textContent = "Enter a message first."; return; }
      run(async (current) => {
        await request(`${base}/replies`, { text }, { Authorization: `Bearer ${code}` });
        if (current === generation) $("family-reply-form").reset();
        await load(current);
        return "Reply queued for the simulated uplink.";
      });
    });
    window.addEventListener("pagehide", lock);
  }

  if (ownerPanel) ownerFlow();
  else recipientFlow();
})();
