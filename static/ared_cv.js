/**
 * ARED / SPRINT Camera Biomechanics, Posture & Fatigue CV
 * Real webcam MediaPipe PoseLandmarker (GPU with CPU fallback) + 1-Euro Filter + Secondary Demo Replay.
 */
(function () {
  "use strict";

  const MP_ESM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";
  const MP_ESM_FALLBACK = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm";
  const MP_WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
  const POSE_MODEL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

  class OneEuroFilter {
    constructor(minCutoff = 1.0, beta = 0.05, dCutoff = 1.0) {
      this.minCutoff = minCutoff; this.beta = beta; this.dCutoff = dCutoff;
      this.xPrev = null; this.dxPrev = 0; this.tPrev = null;
    }
    alpha(cutoff, dt) {
      const tau = 1.0 / (2 * Math.PI * cutoff);
      return 1.0 / (1.0 + tau / Math.max(dt, 1e-4));
    }
    filter(x, tSec) {
      if (this.tPrev === null) { this.tPrev = tSec; this.xPrev = x; return x; }
      const dt = Math.max(tSec - this.tPrev, 1e-3);
      const dx = (x - this.xPrev) / dt;
      const aD = this.alpha(this.dCutoff, dt);
      const dxHat = aD * dx + (1 - aD) * this.dxPrev;
      const cutoff = this.minCutoff + this.beta * Math.abs(dxHat);
      const a = this.alpha(cutoff, dt);
      const xHat = a * x + (1 - a) * this.xPrev;
      this.xPrev = xHat; this.dxPrev = dxHat; this.tPrev = tSec;
      return xHat;
    }
  }

  function angleDeg(a, b, c) {
    const ba = { x: a.x - b.x, y: a.y - b.y };
    const bc = { x: c.x - b.x, y: c.y - b.y };
    const dot = ba.x * bc.x + ba.y * bc.y;
    const mag = Math.hypot(ba.x, ba.y) * Math.hypot(bc.x, bc.y);
    if (mag < 1e-6) return 180;
    return (Math.acos(Math.max(-1, Math.min(1, dot / mag))) * 180) / Math.PI;
  }

  function generateDeterministicReplay(exercise = "squat") {
    const frames = [], fps = 30;
    let t = 0;
    for (let rep = 1; rep <= 10; rep++) {
      const eccSec = 1.1;
      const conSec = 0.75 * (1 + (rep > 2 ? (rep - 2) * 0.068 : 0));
      const totalFrames = Math.round((eccSec + conSec) * fps);
      const eccFrames = Math.round(eccSec * fps);
      for (let f = 0; f < totalFrames; f++) {
        const isEcc = f < eccFrames;
        const p = isEcc ? f / eccFrames : 1 - (f - eccFrames) / (totalFrames - eccFrames);
        const depth = Math.sin(p * Math.PI * 0.5);
        const hipY = 0.48 + depth * (exercise === "heel_raise" ? -0.06 : 0.22);
        const kneeY = 0.70 + depth * 0.02;
        const valgusShift = rep >= 8 ? depth * 0.035 : depth * 0.006;
        const leanShift = rep >= 9 ? depth * 0.045 : depth * 0.015;
        const lm = new Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, z: 0, visibility: 0.99 }));
        lm[11] = { x: 0.42 + leanShift * 0.3, y: hipY - 0.26 + depth * 0.03, z: 0, visibility: 0.99 };
        lm[12] = { x: 0.58 + leanShift * 0.3, y: hipY - 0.26 + depth * 0.03, z: 0, visibility: 0.99 };
        lm[23] = { x: 0.44, y: hipY, z: 0, visibility: 0.99 };
        lm[24] = { x: 0.56, y: hipY, z: 0, visibility: 0.99 };
        lm[25] = { x: 0.43 + valgusShift, y: kneeY, z: 0, visibility: 0.99 };
        lm[26] = { x: 0.57 - valgusShift, y: kneeY, z: 0, visibility: 0.99 };
        lm[27] = { x: 0.43, y: 0.90 - (exercise === "heel_raise" ? depth * 0.05 : 0), z: 0, visibility: 0.99 };
        lm[28] = { x: 0.57, y: 0.90 - (exercise === "heel_raise" ? depth * 0.05 : 0), z: 0, visibility: 0.99 };
        frames.push({ t, landmarks: lm });
        t += 1 / fps;
      }
    }
    return frames;
  }

  class AredCVSession {
    constructor(canvas, onUpdate, onComplete, onStatus) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.onUpdate = onUpdate;
      this.onComplete = onComplete;
      this.onStatus = onStatus || (() => {});
      this.running = false;
      this.mode = "camera";
      this.exercise = "squat";
      this.stream = null;
      this.video = null;
      this.landmarker = null;
      this.resetMetrics();
    }

    resetMetrics() {
      this.state = "TOP";
      this.reps = [];
      this.peakBaselineVel = 0;
      this.curMinKnee = 180;
      this.curMaxValgus = 0;
      this.curMaxLean = 0;
      this.curMaxSym = 0;
      this.concentricStartT = null;
      this.concentricStartHipY = null;
      this.filters = {};
    }

    getFilter(key) {
      if (!this.filters[key]) this.filters[key] = new OneEuroFilter(1.2, 0.06, 1.0);
      return this.filters[key];
    }

    async ensureLandmarker() {
      if (this.landmarker) return this.landmarker;
      this.onStatus("Loading PoseLandmarker...");
      let vision;
      try {
        vision = await import(MP_ESM);
      } catch {
        vision = await import(MP_ESM_FALLBACK);
      }
      const fileset = await vision.FilesetResolver.forVisionTasks(MP_WASM);
      try {
        this.landmarker = await vision.PoseLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: POSE_MODEL, delegate: "GPU" },
          runningMode: "VIDEO",
          numPoses: 1,
        });
      } catch {
        this.landmarker = await vision.PoseLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: POSE_MODEL, delegate: "CPU" },
          runningMode: "VIDEO",
          numPoses: 1,
        });
      }
      return this.landmarker;
    }

    async startCamera(videoEl, exercise = "squat") {
      this.stop(false);
      this.exercise = exercise;
      this.mode = "camera";
      this.video = videoEl;
      this.resetMetrics();

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.onStatus("Camera requires HTTPS or localhost");
        return;
      }
      try {
        this.onStatus("Requesting camera permission...");
        try {
          this.stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 360 }, facingMode: "user" },
            audio: false,
          });
        } catch {
          this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
        videoEl.muted = true;
        videoEl.playsInline = true;
        videoEl.autoplay = true;
        videoEl.srcObject = this.stream;
        await videoEl.play();
      } catch (err) {
        const name = err && err.name ? err.name : "";
        if (name === "NotAllowedError" || name === "PermissionDeniedError") {
          this.onStatus("Camera permission denied");
        } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
          this.onStatus("No camera device found");
        } else if (name === "NotReadableError" || name === "TrackStartError") {
          this.onStatus("Camera busy in another app");
        } else {
          this.onStatus("Camera unavailable");
        }
        return;
      }

      let useMediaPipe = true;
      try {
        await this.ensureLandmarker();
      } catch (err) {
        console.warn("PoseLandmarker unavailable, switching to optical motion fallback:", err);
        useMediaPipe = false;
      }

      this.running = true;
      if (useMediaPipe) {
        this.onStatus("Live Tracking");
        const loop = () => {
          if (!this.running) return;
          const nowMs = performance.now();
          if (this.video.readyState >= 2) {
            const res = this.landmarker.detectForVideo(this.video, nowMs);
            if (res.landmarks && res.landmarks.length > 0) {
              this.onStatus("Live Tracking");
              this.processLandmarks(res.landmarks[0], nowMs / 1000, true);
            } else {
              this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
              this.onStatus("No person detected");
            }
          }
          this._rafId = requestAnimationFrame(loop);
        };
        this._rafId = requestAnimationFrame(loop);
      } else {
        this.onStatus("Live Optical CV");
        this._startOpticalFallbackLoop();
      }
    }

    _startOpticalFallbackLoop() {
      const off = document.createElement("canvas");
      off.width = 80;
      off.height = 45;
      const offCtx = off.getContext("2d", { willReadFrequently: true });
      let prevGray = null;
      let smoothY = 0.5;
      let motionState = "TOP";
      let minMotionY = 0.5;
      let downT = null;

      const loop = () => {
        if (!this.running) return;
        const nowMs = performance.now();
        if (this.video && this.video.readyState >= 2) {
          offCtx.drawImage(this.video, 0, 0, off.width, off.height);
          const data = offCtx.getImageData(0, 0, off.width, off.height).data;
          const gray = new Float32Array(off.width * off.height);
          let sumDiff = 0;
          let sumY = 0;
          for (let y = 0; y < off.height; y++) {
            for (let x = 0; x < off.width; x++) {
              const i = y * off.width + x;
              const p = i * 4;
              const g = 0.299 * data[p] + 0.587 * data[p + 1] + 0.114 * data[p + 2];
              gray[i] = g;
              if (prevGray) {
                const d = Math.abs(g - prevGray[i]);
                if (d > 14) {
                  sumDiff += d;
                  sumY += d * (y / off.height);
                }
              }
            }
          }
          prevGray = gray;
          if (sumDiff > 250) {
            const rawY = sumY / sumDiff;
            smoothY = smoothY * 0.72 + rawY * 0.28;
            if (motionState === "TOP" && smoothY > 0.56) {
              motionState = "ECCENTRIC";
              minMotionY = smoothY;
              downT = nowMs / 1000;
            } else if (motionState === "ECCENTRIC") {
              minMotionY = Math.max(minMotionY, smoothY);
              if (smoothY < 0.50 && downT !== null) {
                const dur = Math.max(0.25, nowMs / 1000 - downT);
                const vel = Number((0.45 / dur).toFixed(3));
                if (!this.baselineVel) this.baselineVel = vel;
                const velLoss = Math.max(0, Math.round((1 - vel / this.baselineVel) * 100));
                this.reps.push({
                  rep: this.reps.length + 1,
                  rom_deg: Math.round(70 + (minMotionY - 0.5) * 180),
                  concentric_vel: vel,
                  velocity_loss_pct: velLoss,
                  quality_score: 90,
                  flags: velLoss >= 20 ? ["VELOCITY_FATIGUE"] : [],
                });
                if (this.onUpdate) this.onUpdate(this.buildSummary());
                motionState = "TOP";
                downT = null;
              }
            }
          }
          const W = this.canvas.width, H = this.canvas.height;
          this.ctx.clearRect(0, 0, W, H);
          const cy = smoothY * H;
          this.ctx.strokeStyle = "#38bdf8";
          this.ctx.lineWidth = 2;
          this.ctx.beginPath();
          this.ctx.moveTo(16, cy);
          this.ctx.lineTo(W - 16, cy);
          this.ctx.stroke();
          this.ctx.fillStyle = "rgba(56,189,248,0.9)";
          this.ctx.font = "bold 11px monospace";
          this.ctx.fillText(`OPTICAL CV · REPS: ${this.reps.length}`, 12, 18);
        }
        this._rafId = requestAnimationFrame(loop);
      };
      this._rafId = requestAnimationFrame(loop);
    }

    processLandmarks(rawLm, tSec, mirror = false) {
      const idx = [11, 12, 23, 24, 25, 26, 27, 28];
      const lm = {};
      for (const i of idx) {
        const p = rawLm[i] || { x: 0.5, y: 0.5 };
        const rx = mirror ? 1 - p.x : p.x;
        lm[i] = {
          x: this.getFilter(`x${i}`).filter(rx, tSec),
          y: this.getFilter(`y${i}`).filter(p.y, tSec),
        };
      }

      const lKnee = angleDeg(lm[23], lm[25], lm[27]);
      const rKnee = angleDeg(lm[24], lm[26], lm[28]);
      const kneeAngle = (lKnee + rKnee) / 2;
      const symPct = (Math.abs(lKnee - rKnee) / Math.max((lKnee + rKnee) / 2, 1)) * 100;

      const midHipY = (lm[23].y + lm[24].y) / 2;
      const midShY = (lm[11].y + lm[12].y) / 2;
      const torsoLen = Math.max(Math.abs(midHipY - midShY), 0.08);
      const trunkLean = Math.abs(Math.atan2((lm[11].x + lm[12].x) / 2 - (lm[23].x + lm[24].x) / 2, torsoLen) * (180 / Math.PI));

      const lValgus = Math.max(0, (lm[25].x - lm[27].x) * 180);
      const rValgus = Math.max(0, (lm[28].x - lm[26].x) * 180);
      const valgusDeg = Math.max(lValgus, rValgus);

      this.curMinKnee = Math.min(this.curMinKnee, kneeAngle);
      this.curMaxValgus = Math.max(this.curMaxValgus, valgusDeg);
      this.curMaxLean = Math.max(this.curMaxLean, trunkLean);
      this.curMaxSym = Math.max(this.curMaxSym, symPct);

      const bottomThresh = this.exercise === "heel_raise" ? 172 : 100;
      const topThresh = this.exercise === "heel_raise" ? 177 : 160;

      if (this.state === "TOP" && kneeAngle < topThresh - 8) {
        this.state = "ECCENTRIC";
      } else if (this.state === "ECCENTRIC" && kneeAngle <= bottomThresh) {
        this.state = "BOTTOM";
        this.concentricStartT = tSec;
        this.concentricStartHipY = midHipY;
      } else if (this.state === "BOTTOM" && kneeAngle > bottomThresh + 5) {
        this.state = "CONCENTRIC";
      } else if (this.state === "CONCENTRIC" && kneeAngle >= topThresh) {
        this.state = "TOP";
        const dt = Math.max(tSec - (this.concentricStartT || tSec - 0.5), 0.15);
        const velNorm = Math.abs((this.concentricStartHipY || midHipY) - midHipY) / torsoLen / dt;
        if (this.reps.length < 2) this.peakBaselineVel = Math.max(this.peakBaselineVel, velNorm);
        const velLossPct = this.peakBaselineVel > 0
          ? Math.max(0, ((this.peakBaselineVel - velNorm) / this.peakBaselineVel) * 100) : 0;

        const romScore = this.curMinKnee <= 105 ? 35 : Math.max(10, 35 - (this.curMinKnee - 105) * 0.6);
        const postureScore = this.curMaxValgus > 18 || this.curMaxLean > 15 ? 15 : this.curMaxValgus > 10 ? 25 : 35;
        const symScore = this.curMaxSym > 15 ? 15 : this.curMaxSym > 10 ? 22 : 30;
        const quality = Math.round(romScore + postureScore + symScore);

        const flags = [];
        if (velLossPct >= 35) flags.push("TERMINATE_SET_FATIGUE");
        else if (velLossPct >= 20) flags.push("MODERATE_FATIGUE");
        if (this.curMaxValgus > 10) flags.push("KNEE_VALGUS");
        if (this.curMaxLean > 15) flags.push("LUMBAR_LEAN");

        this.reps.push({
          rep: this.reps.length + 1,
          rom_deg: Math.round(180 - this.curMinKnee),
          velocity_loss_pct: Number(velLossPct.toFixed(1)),
          valgus_deg: Number(this.curMaxValgus.toFixed(1)),
          trunk_lean_deg: Number(this.curMaxLean.toFixed(1)),
          symmetry_pct: Number(this.curMaxSym.toFixed(1)),
          quality_score: quality,
          flags,
        });
        this.curMinKnee = 180; this.curMaxValgus = 0; this.curMaxLean = 0; this.curMaxSym = 0;
      }

      const lastVelLoss = this.reps.length ? this.reps[this.reps.length - 1].velocity_loss_pct : 0;
      this.drawSkeleton(lm, valgusDeg, lastVelLoss);
      if (this.onUpdate) {
        this.onUpdate({ state: this.state, reps: this.reps, latest: this.reps[this.reps.length - 1] || null, liveKneeDeg: Math.round(kneeAngle) });
      }
    }

    drawSkeleton(lm, valgusDeg, velLossPct) {
      const ctx = this.ctx, w = this.canvas.width, h = this.canvas.height;
      ctx.clearRect(0, 0, w, h);
      const color = velLossPct >= 35 ? "#ff453a" : valgusDeg > 10 || velLossPct >= 20 ? "#ffd60a" : "#30d158";
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      const pairs = [[11, 12], [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [24, 26], [26, 28]];
      for (const [a, b] of pairs) {
        ctx.beginPath();
        ctx.moveTo(lm[a].x * w, lm[a].y * h);
        ctx.lineTo(lm[b].x * w, lm[b].y * h);
        ctx.stroke();
      }
      ctx.fillStyle = "#ffffff";
      for (const k of Object.keys(lm)) {
        ctx.beginPath();
        ctx.arc(lm[k].x * w, lm[k].y * h, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    async startReplay(exercise = "squat") {
      this.stop(false);
      this.exercise = exercise;
      this.mode = "replay";
      this.resetMetrics();
      this.running = true;
      this.onStatus("Demo Replay");
      const frames = generateDeterministicReplay(exercise);
      let i = 0;
      const step = () => {
        if (!this.running) return;
        if (i >= frames.length) {
          this.running = false;
          if (this.onComplete) this.onComplete(this.buildSummary());
          return;
        }
        this.processLandmarks(frames[i].landmarks, frames[i].t, false);
        i++;
        this._raf = setTimeout(step, 33);
      };
      step();
    }

    stop(emitComplete = true) {
      const wasRunning = this.running;
      this.running = false;
      if (this._raf) clearTimeout(this._raf);
      if (this._rafId) cancelAnimationFrame(this._rafId);
      if (this.stream) {
        this.stream.getTracks().forEach((t) => t.stop());
        this.stream = null;
      }
      if (this.video) this.video.srcObject = null;
      if (emitComplete && wasRunning && this.reps.length > 0 && this.onComplete) {
        this.onComplete(this.buildSummary());
      }
    }

    buildSummary() {
      const n = this.reps.length || 1;
      const last = this.reps[this.reps.length - 1] || { velocity_loss_pct: 0, quality_score: 85, flags: [] };
      const meanRom = Math.round(this.reps.reduce((s, r) => s + r.rom_deg, 0) / n);
      const meanQual = Math.round(this.reps.reduce((s, r) => s + r.quality_score, 0) / n);
      return {
        exercise: this.exercise,
        camera_mode: this.mode,
        reps: this.reps,
        rep_count: this.reps.length,
        velocity_loss_pct: last.velocity_loss_pct,
        mean_rom_deg: meanRom,
        rep_quality_score: meanQual,
        posture_flags: Array.from(new Set(this.reps.flatMap((r) => r.flags))),
      };
    }
  }

  window.AredCV = { AredCVSession, OneEuroFilter, generateDeterministicReplay };
})();
