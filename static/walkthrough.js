/* ==================== ASTRA-CORE JUDGE DEMO & WALKME TOUR ==================== */
(function initJudgeWalkthrough() {
  const STEPS = [
    {
      kicker: "STEP 1 OF 7 · CREW GLANCE",
      title: "Single Crew Member Spotlight",
      body: "Instead of overwhelming clinicians with raw telemetry, each astronaut tile distills live heart rate, SpO₂, readiness score, and triage tier at a glance.",
      navId: "rail-glance",
      getTarget: () =>
        document.querySelector("#crew-glance-grid .glance-card.glance-critical") ||
        document.querySelector("#crew-glance-grid .glance-card.glance-warning") ||
        document.querySelector("#crew-glance-grid .glance-card"),
      padding: 8,
    },
    {
      kicker: "STEP 2 OF 7 · STATION READINESS",
      title: "Executive Station Readiness",
      body: "Aggregates all 6 crew members alongside cabin CO₂, orbital radiation dose rate, and 42-channel wearable network health in one executive card.",
      navId: "rail-glance",
      getTarget: () => document.querySelector("#view-glance .overview-board"),
      padding: 8,
    },
    {
      kicker: "STEP 3 OF 7 · CREW ACTIONS HUD",
      title: "Focused Astronaut Summary",
      body: "Clicking any crew member opens their focused Action HUD—translating vitals, sleep, and radiation into plain-language status for 20-min Earth-delay autonomy.",
      navId: "rail-body",
      getTarget: () => document.getElementById("csa-hero-card"),
      padding: 8,
    },
    {
      kicker: "STEP 4 OF 7 · COUNTERMEASURES",
      title: "Prioritized Action Items",
      body: "Every detected anomaly turns into concrete, prioritized protocol steps so crew or flight surgeons can verify and resolve countermeasures in one tap.",
      navId: "rail-body",
      getTarget: () => document.querySelector("#crew-simple-pane .simple-checklist-card"),
      padding: 8,
    },
    {
      kicker: "STEP 5 OF 7 · BIO-SENSE LAB",
      title: "Contactless Radar & Camera CV",
      body: "Captures physiological signals without extra wearables: ESP32 Wi-Fi CSI / Sleep Radar apnea detection, ARED exercise CV, and webcam rPPG + PERCLOS fatigue.",
      navId: "rail-biosense",
      getTarget: () => document.querySelector("#view-biosense .cv-sleep-grid"),
      padding: 8,
    },
    {
      kicker: "STEP 6 OF 7 · ISS UNIFIED MEDHUB",
      title: "6-Silo Pre-Symptomatic Fusion",
      body: "Connects NASA's 6 isolated medical silos—blood, imaging, vitals, respiration, cognition, and NASA OSDR/DONKI benchmarks—to flag coupled risk before symptoms appear.",
      navId: "rail-medhub",
      getTarget: () => document.getElementById("medhub-hero-card") || document.getElementById("view-medhub"),
      padding: 8,
    },
    {
      kicker: "STEP 7 OF 7 · HAL2030 COMPANION",
      title: "Offline Deep-Space AI Companion",
      body: "100% local CPU voice & text companion (Kokoro TTS + Faster-Whisper STT) designed for 22-minute Mars communication delays with zero cloud dependency.",
      navId: "rail-companion",
      getTarget: () => document.querySelector("#view-companion .comp-layout") || document.getElementById("view-companion"),
      padding: 8,
    },
  ];

  let active = false;
  let stepIndex = 0;
  let currentTarget = null;
  let rafId = null;

  const toggleBtn = () => document.getElementById("btn-judge-demo");
  const welcomeModal = () => document.getElementById("judge-welcome-modal");
  const wtLayer = () => document.getElementById("wt-layer");
  const paneTop = () => document.getElementById("wt-blur-top");
  const paneRight = () => document.getElementById("wt-blur-right");
  const paneBottom = () => document.getElementById("wt-blur-bottom");
  const paneLeft = () => document.getElementById("wt-blur-left");
  const ring = () => document.getElementById("wt-spotlight-ring");
  const popover = () => document.getElementById("wt-popover");

  function setToggleState(isOn) {
    const btn = toggleBtn();
    if (!btn) return;
    btn.classList.toggle("active", isOn);
    btn.textContent = isOn ? "🎯 Judge Tour: ON" : "🎯 Judge Tour";
    btn.setAttribute("aria-pressed", isOn ? "true" : "false");
  }

  function hideWelcome() {
    const modal = welcomeModal();
    if (modal) modal.classList.add("hidden");
  }

  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
  }

  function positionSpotlight() {
    if (!active || !currentTarget) return;
    const rect = currentTarget.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    const step = STEPS[stepIndex];
    const pad = step.padding || 8;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const top = clamp(rect.top - pad, 4, vh - 20);
    const left = clamp(rect.left - pad, 4, vw - 20);
    const right = clamp(rect.right + pad, left + 20, vw - 4);
    const bottom = clamp(rect.bottom + pad, top + 20, vh - 4);
    const width = right - left;
    const height = bottom - top;

    // 4 blur panes surrounding the spotlight cutout
    const tEl = paneTop();
    const bEl = paneBottom();
    const lEl = paneLeft();
    const rEl = paneRight();
    const ringEl = ring();

    if (tEl) {
      tEl.style.top = "0px";
      tEl.style.left = "0px";
      tEl.style.width = `${vw}px`;
      tEl.style.height = `${top}px`;
    }
    if (bEl) {
      bEl.style.top = `${bottom}px`;
      bEl.style.left = "0px";
      bEl.style.width = `${vw}px`;
      bEl.style.height = `${Math.max(0, vh - bottom)}px`;
    }
    if (lEl) {
      lEl.style.top = `${top}px`;
      lEl.style.left = "0px";
      lEl.style.width = `${left}px`;
      lEl.style.height = `${height}px`;
    }
    if (rEl) {
      rEl.style.top = `${top}px`;
      rEl.style.left = `${right}px`;
      rEl.style.width = `${Math.max(0, vw - right)}px`;
      rEl.style.height = `${height}px`;
    }
    if (ringEl) {
      ringEl.style.top = `${top}px`;
      ringEl.style.left = `${left}px`;
      ringEl.style.width = `${width}px`;
      ringEl.style.height = `${height}px`;
    }

    // Position floating popover smartly without covering target
    const pop = popover();
    if (pop) {
      const popRect = pop.getBoundingClientRect();
      const popW = popRect.width || 360;
      const popH = popRect.height || 210;
      const gap = 16;

      let popLeft;
      let popTop;

      if (vw - right >= popW + gap + 12) {
        popLeft = right + gap;
        popTop = clamp(top, 16, vh - popH - 16);
      } else if (left >= popW + gap + 12) {
        popLeft = left - popW - gap;
        popTop = clamp(top, 16, vh - popH - 16);
      } else if (vh - bottom >= popH + gap + 12) {
        popLeft = clamp(left, 16, vw - popW - 16);
        popTop = bottom + gap;
      } else if (top >= popH + gap + 12) {
        popLeft = clamp(left, 16, vw - popW - 16);
        popTop = top - popH - gap;
      } else {
        popLeft = clamp(vw - popW - 20, 16, vw - popW - 16);
        popTop = clamp(vh - popH - 20, 16, vh - popH - 16);
      }

      pop.style.left = `${popLeft}px`;
      pop.style.top = `${popTop}px`;
    }
  }

  function renderDots() {
    const dotsEl = document.getElementById("wt-dots");
    if (!dotsEl) return;
    dotsEl.innerHTML = STEPS.map(
      (_, i) => `<span class="wt-dot${i === stepIndex ? " active" : ""}"></span>`
    ).join("");
  }

  function showStep(idx) {
    stepIndex = clamp(idx, 0, STEPS.length - 1);
    const step = STEPS[stepIndex];

    const navBtn = document.getElementById(step.navId);
    if (navBtn) navBtn.click();

    document.getElementById("wt-step-kicker").textContent = step.kicker;
    document.getElementById("wt-pop-title").textContent = step.title;
    document.getElementById("wt-pop-body").textContent = step.body;
    document.getElementById("wt-prev-btn").disabled = stepIndex === 0;
    document.getElementById("wt-next-btn").textContent =
      stepIndex === STEPS.length - 1 ? "Finish Tour ✓" : "Next →";
    renderDots();

    // Wait two frames for view transition / render, then scroll & measure
    requestAnimationFrame(() => {
      setTimeout(() => {
        if (!active) return;
        const target = step.getTarget();
        if (target) {
          currentTarget = target;
          target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
          setTimeout(positionSpotlight, 220);
        }
      }, 90);
    });
  }

  function startTour() {
    hideWelcome();
    active = true;
    setToggleState(true);
    const layer = wtLayer();
    if (layer) layer.classList.remove("hidden");
    showStep(0);
  }

  function stopTour() {
    active = false;
    currentTarget = null;
    setToggleState(false);
    const layer = wtLayer();
    if (layer) layer.classList.add("hidden");
    if (rafId) cancelAnimationFrame(rafId);
  }

  function bindEvents() {
    const btnStartTour = document.getElementById("judge-btn-walkthrough");
    const btnFreeDemo = document.getElementById("judge-btn-freedemo");
    const btnToggle = toggleBtn();
    const btnPrev = document.getElementById("wt-prev-btn");
    const btnNext = document.getElementById("wt-next-btn");
    const btnClose = document.getElementById("wt-close-btn");

    if (btnStartTour) btnStartTour.addEventListener("click", startTour);
    if (btnFreeDemo) btnFreeDemo.addEventListener("click", hideWelcome);

    if (btnToggle) {
      btnToggle.addEventListener("click", () => {
        if (active) stopTour();
        else startTour();
      });
    }

    if (btnPrev) {
      btnPrev.addEventListener("click", () => {
        if (stepIndex > 0) showStep(stepIndex - 1);
      });
    }

    if (btnNext) {
      btnNext.addEventListener("click", () => {
        if (stepIndex < STEPS.length - 1) showStep(stepIndex + 1);
        else stopTour();
      });
    }

    if (btnClose) btnClose.addEventListener("click", stopTour);

    window.addEventListener("resize", () => {
      if (active) positionSpotlight();
    });
    window.addEventListener("scroll", () => {
      if (active) positionSpotlight();
    }, true);

    document.addEventListener("keydown", (e) => {
      if (!active) return;
      if (e.key === "Escape") stopTour();
      else if (e.key === "ArrowRight") {
        if (stepIndex < STEPS.length - 1) showStep(stepIndex + 1);
        else stopTour();
      } else if (e.key === "ArrowLeft" && stepIndex > 0) {
        showStep(stepIndex - 1);
      }
    });

    // Optional URL param ?notour=1 skips startup splash for automated tests
    if (new URLSearchParams(window.location.search).get("notour") === "1") {
      hideWelcome();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindEvents);
  } else {
    bindEvents();
  }

  window.ASTRAWalkthrough = { start: startTour, stop: stopTour, goTo: showStep };
})();
