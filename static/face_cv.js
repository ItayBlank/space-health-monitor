/**
 * Passive Facial rPPG (POS), PERCLOS Drowsiness (EAR < 0.21) & Cephalad Fluid-Shift Morphometry.
 * Real webcam MediaPipe FaceLandmarker (GPU with CPU fallback) + Secondary Demo Replay.
 */
(function () {
  "use strict";

  const MP_ESM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";
  const MP_WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
  const FACE_MODEL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

  function computePosRppgHr(rgbBuffer, fps = 30) {
    const n = rgbBuffer.length;
    if (n < Math.max(20, fps * 3)) return null;
    const meanR = rgbBuffer.reduce((s, c) => s + c[0], 0) / n || 1;
    const meanG = rgbBuffer.reduce((s, c) => s + c[1], 0) / n || 1;
    const meanB = rgbBuffer.reduce((s, c) => s + c[2], 0) / n || 1;

    const s1 = new Float64Array(n);
    const s2 = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const rn = rgbBuffer[i][0] / meanR - 1;
      const gn = rgbBuffer[i][1] / meanG - 1;
      const bn = rgbBuffer[i][2] / meanB - 1;
      s1[i] = gn - bn;
      s2[i] = gn + bn - 2 * rn;
    }
    const std1 = Math.sqrt(s1.reduce((s, v) => s + v * v, 0) / n) || 1;
    const std2 = Math.sqrt(s2.reduce((s, v) => s + v * v, 0) / n) || 1;
    const alpha = std1 / std2;
    const h = new Float64Array(n);
    for (let i = 0; i < n; i++) h[i] = s1[i] + alpha * s2[i];

    // Bandpass 0.7 - 3.0 Hz (42 - 180 BPM) via DFT peak search
    let bestHr = 68, bestPow = -1;
    for (let bpm = 42; bpm <= 180; bpm += 2) {
      const freq = bpm / 60;
      let re = 0, im = 0;
      for (let i = 0; i < n; i++) {
        const ang = (2 * Math.PI * freq * i) / fps;
        re += h[i] * Math.cos(ang);
        im -= h[i] * Math.sin(ang);
      }
      const pwr = re * re + im * im;
      if (pwr > bestPow) { bestPow = pwr; bestHr = bpm; }
    }
    return { hrBpm: bestHr, pulseSample: h[n - 1] };
  }

  function dist(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  function computeEar(lm, idx) {
    const p1 = lm[idx[0]], p2 = lm[idx[1]], p3 = lm[idx[2]], p4 = lm[idx[3]], p5 = lm[idx[4]], p6 = lm[idx[5]];
    const v1 = dist(p2, p6), v2 = dist(p3, p5), h = Math.max(dist(p1, p4), 1e-5);
    return (v1 + v2) / (2.0 * h);
  }

  class FaceCVSession {
    constructor(canvas, onUpdate, onComplete, onStatus) {
      this.canvas = canvas;
      this.ctx = canvas ? canvas.getContext("2d") : null;
      this.onUpdate = onUpdate;
      this.onComplete = onComplete;
      this.onStatus = onStatus || (() => {});
      this.running = false;
      this._timer = null;
      this._rafId = null;
      this.stream = null;
      this.video = null;
      this.landmarker = null;
      this.offscreen = document.createElement("canvas");
      this.offCtx = this.offscreen.getContext("2d", { willReadFrequently: true });
      this.trace = [];
    }

    async ensureLandmarker() {
      if (this.landmarker) return this.landmarker;
      this.onStatus("Loading FaceLandmarker...");
      const vision = await import(MP_ESM);
      const fileset = await vision.FilesetResolver.forVisionTasks(MP_WASM);
      try {
        this.landmarker = await vision.FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: FACE_MODEL, delegate: "GPU" },
          runningMode: "VIDEO",
          numFaces: 1,
        });
      } catch {
        this.landmarker = await vision.FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: FACE_MODEL, delegate: "CPU" },
          runningMode: "VIDEO",
          numFaces: 1,
        });
      }
      return this.landmarker;
    }

    sampleRoiRgb(videoEl, lm) {
      const vw = videoEl.videoWidth || 320, vh = videoEl.videoHeight || 240;
      this.offscreen.width = vw;
      this.offscreen.height = vh;
      this.offCtx.drawImage(videoEl, 0, 0, vw, vh);
      // Forehead (10, 151) + Cheeks (50, 280)
      const pts = [10, 151, 50, 280];
      let rSum = 0, gSum = 0, bSum = 0, count = 0;
      for (const idx of pts) {
        const p = lm[idx];
        if (!p) continue;
        const x = Math.max(4, Math.min(vw - 5, Math.round(p.x * vw)));
        const y = Math.max(4, Math.min(vh - 5, Math.round(p.y * vh)));
        const data = this.offCtx.getImageData(x - 4, y - 4, 8, 8).data;
        for (let i = 0; i < data.length; i += 4) {
          rSum += data[i]; gSum += data[i + 1]; bSum += data[i + 2]; count++;
        }
      }
      return count ? [rSum / count, gSum / count, bSum / count] : [128, 128, 128];
    }

    async startCamera(videoEl) {
      this.stop();
      this.video = videoEl;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.onStatus("Camera API unavailable in this browser");
        return;
      }
      try {
        this.onStatus("Requesting camera permission...");
        this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
        videoEl.srcObject = this.stream;
        await videoEl.play();
      } catch {
        this.onStatus("Camera permission denied or unavailable");
        return;
      }
      try {
        await this.ensureLandmarker();
      } catch {
        this.onStatus("Failed to load FaceLandmarker model");
        this.stop();
        return;
      }

      this.running = true;
      this.trace = [];
      const rgbBuffer = [];
      const earHistory = [];
      let blinks = 0, wasClosed = false;
      const startMs = performance.now();
      this.onStatus("Live Tracking");

      const loop = () => {
        if (!this.running) return;
        const nowMs = performance.now();
        if (this.video.readyState >= 2) {
          const res = this.landmarker.detectForVideo(this.video, nowMs);
          if (res.faceLandmarks && res.faceLandmarks.length > 0) {
            this.onStatus("Live Tracking");
            const lm = res.faceLandmarks[0];
            const rgb = this.sampleRoiRgb(this.video, lm);
            rgbBuffer.push(rgb);
            const elapsedSec = Math.max(1, (nowMs - startMs) / 1000);
            const fps = Math.min(60, Math.max(10, rgbBuffer.length / elapsedSec));
            if (rgbBuffer.length > fps * 10) rgbBuffer.shift();

            const lEar = computeEar(lm, [33, 160, 158, 133, 153, 144]);
            const rEar = computeEar(lm, [362, 385, 387, 263, 373, 380]);
            const ear = (lEar + rEar) / 2;
            const isClosed = ear < 0.21;
            if (isClosed && !wasClosed) blinks++;
            wasClosed = isClosed;

            earHistory.push({ t: nowMs, closed: isClosed });
            while (earHistory.length && nowMs - earHistory[0].t > 60000) earHistory.shift();
            const perclosPct = Number(((earHistory.filter((e) => e.closed).length / earHistory.length) * 100).toFixed(1));

            const interCanthal = Math.max(dist(lm[133], lm[362]), 1e-5);
            const aperture = (dist(lm[159], lm[145]) + dist(lm[386], lm[374])) / 2;
            const palpebralRatio = Number((aperture / interCanthal).toFixed(3));

            const pos = computePosRppgHr(rgbBuffer, fps);
            const hrBpm = pos ? pos.hrBpm : 68;
            this.drawLiveMesh(lm, pos ? pos.pulseSample : 0, hrBpm, ear, perclosPct, blinks);

            if (this.onUpdate) {
              this.onUpdate({
                hrBpm,
                ear: Number(ear.toFixed(2)),
                perclosPct,
                palpebralRatio,
                blinks,
                progressPct: Math.min(100, Math.round((rgbBuffer.length / (fps * 10)) * 100)),
              });
            }
          } else {
            if (this.ctx && this.canvas) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.onStatus("No face detected");
          }
        }
        this._rafId = requestAnimationFrame(loop);
      };
      this._rafId = requestAnimationFrame(loop);
    }

    drawLiveMesh(lm, pulseSample, hrBpm, ear, perclosPct, blinks) {
      if (!this.ctx || !this.canvas) return;
      const ctx = this.ctx, w = this.canvas.width, h = this.canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#64d2ff";
      for (let i = 0; i < lm.length; i += 4) {
        const p = lm[i];
        ctx.fillRect((1 - p.x) * w - 1, p.y * h - 1, 2, 2);
      }
      this.trace.push(pulseSample);
      if (this.trace.length > 90) this.trace.shift();
      ctx.strokeStyle = "#30d158";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < this.trace.length; i++) {
        const x = (i / 90) * w;
        const y = h - 22 - Math.max(-18, Math.min(18, this.trace[i] * 800));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.font = "11px monospace";
      ctx.fillText(`POS ${hrBpm} BPM | EAR ${ear.toFixed(2)} | PERCLOS ${perclosPct}% | Blinks ${blinks}`, 8, 16);
    }

    drawFrame(ear, pulseVal, hrBpm, perclosPct) {
      if (!this.ctx || !this.canvas) return;
      const ctx = this.ctx, w = this.canvas.width, h = this.canvas.height;
      ctx.clearRect(0, 0, w, h);
      const cx = 62, cy = h / 2;
      ctx.strokeStyle = "#64d2ff"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(cx, cy, 34, 44, 0, 0, Math.PI * 2); ctx.stroke();
      const eyeH = Math.max(1.5, (ear / 0.30) * 6);
      ctx.fillStyle = ear < 0.21 ? "#ff9f0a" : "#30d158";
      ctx.beginPath();
      ctx.ellipse(cx - 13, cy - 8, 7, eyeH, 0, 0, Math.PI * 2);
      ctx.ellipse(cx + 13, cy - 8, 7, eyeH, 0, 0, Math.PI * 2);
      ctx.fill();
      this.trace.push(pulseVal);
      if (this.trace.length > 90) this.trace.shift();
      ctx.strokeStyle = "#30d158"; ctx.lineWidth = 2; ctx.beginPath();
      const x0 = 115, tw = w - x0 - 10;
      for (let i = 0; i < this.trace.length; i++) {
        const x = x0 + (i / 90) * tw, y = cy - this.trace[i] * 18;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.fillStyle = "rgba(255,255,255,0.75)"; ctx.font = "11px monospace";
      ctx.fillText(`POS ${hrBpm} BPM | EAR ${ear.toFixed(2)} | PERCLOS ${perclosPct}%`, x0, 18);
    }

    startReplay() {
      this.stop();
      this.running = true;
      this.trace = [];
      this.onStatus("Demo Replay");
      const fps = 15, totalSec = 30, totalSteps = totalSec * fps;
      const rgbBuffer = [];
      let closedFrames = 0, step = 0;
      const tick = () => {
        if (!this.running) return;
        const t = step / fps;
        const pulse = Math.sin(2 * Math.PI * (68 / 60) * t) * 1.4;
        rgbBuffer.push([150 + pulse * 0.4, 128 + pulse * 1.2, 112 + pulse * 0.3]);
        if (rgbBuffer.length > fps * 10) rgbBuffer.shift();
        const isDrowsy = (t >= 12 && t <= 14.2) || (t >= 22 && t <= 24.5);
        const ear = isDrowsy ? 0.18 : 0.29 + 0.02 * Math.sin(t * 2);
        if (ear < 0.21) closedFrames++;
        const perclosPct = Number(((closedFrames / (step + 1)) * 100).toFixed(1));
        const palpebralRatio = Number((0.31 - 0.015 * Math.min(1, t / 20)).toFixed(3));
        const pos = computePosRppgHr(rgbBuffer, fps);
        const hrBpm = pos ? pos.hrBpm : 68;
        this.drawFrame(ear, pulse, hrBpm, perclosPct);
        if (this.onUpdate) {
          this.onUpdate({ hrBpm, ear: Number(ear.toFixed(2)), perclosPct, palpebralRatio, progressPct: Math.round(((step + 1) / totalSteps) * 100) });
        }
        step++;
        if (step >= totalSteps) {
          this.running = false;
          if (this.onComplete) this.onComplete({ hrBpm, perclosPct, palpebralRatio, fluidShiftFlag: palpebralRatio < 0.30 });
          return;
        }
        this._timer = setTimeout(tick, 35);
      };
      tick();
    }

    stop() {
      this.running = false;
      if (this._timer) clearTimeout(this._timer);
      if (this._rafId) cancelAnimationFrame(this._rafId);
      if (this.stream) {
        this.stream.getTracks().forEach((t) => t.stop());
        this.stream = null;
      }
      if (this.video) this.video.srcObject = null;
    }
  }

  window.FaceCV = { FaceCVSession, computePosRppgHr };
})();
