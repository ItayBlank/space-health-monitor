"""
24/7 Wearable Vitals & Pre-Event Cardiovascular Early-Warning Engine.

Simulates CSA Bio-Monitor / Astroskin continuous physiological streams using
real open-access PhysioNet recordings:
1. PhysioNet Pulse Transit Time PPG (`ptt_s3_sit`): healthy 25-yr-old adult
   with 500 Hz ECG, PPG, 3-axis IMU, skin temperature, and reference cuff BP/SpO2.
2. PhysioNet BIDMC (`bidmc_12`, `bidmc_16`, `bidmc_17`, `bidmc_19`): 125 Hz
   synchronous ECG + PPG + Impedance Respiration + 1 Hz HR/PULSE/RESP/SpO2.

Implements peer-reviewed signal processing and pre-event early-warning markers
aligned with NASA-STD-3001 Vol 1/2, NASA HRP Cardiac Rhythm Risk, and NASA's
Exploration Atmosphere (8.2 psia / 34% O2) standards:
- Autonomic withdrawal: SDNN (<50 ms), RMSSD, pNN50, LF/HF, PRSA Deceleration
  Capacity (Bauer et al., Lancet 2006), and short-term DFA alpha-1.
- Electrical / repolarization instability: Fridericia QTcF & Bazett QTcB
  (D'Aunno et al. 2003), premature/ectopic beat burden, ECG-vs-PPG mechanical
  pulse deficit, T-wave alternans (TWA), and normalized ST deviation.
- Hemodynamic / vascular strain: Systolic-bounded Pulse Arrival Time (PAT =
  t_PPG_foot - t_R), baseline-anchored relative SBP trend, Shock Index
  (HR / SBP_est), and NASA orthostatic HR rise (>= +30 bpm).
- Respiratory & hypoxic stress: Impedance respiration (or ECG-derived
  respiration when no belt channel exists), apnea pauses (>= 10 s), SpO2
  thresholds (ISS 14.7 psi vs Exploration 8.2 psi), and ODI3.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.signal import butter, find_peaks, sosfiltfilt, welch

from hal2030.paths import resource_root

from .standards import NASA_CARDIO_VITALS_STANDARDS

DATA_ROOT = resource_root() / "data"
BIDMC_DIR = DATA_ROOT / "physionet_bidmc"
PTT_DIR = DATA_ROOT / "physionet_ptt"


@dataclass(frozen=True)
class PhysioNetRecordMeta:
    """Metadata for a bundled real PhysioNet recording."""

    record_id: str
    dataset: str
    title: str
    clinical_profile: str
    spaceflight_scenario: str


PHYSIONET_RECORDS: Dict[str, PhysioNetRecordMeta] = {
    "ptt_s3_sit": PhysioNetRecordMeta(
        record_id="ptt_s3_sit",
        dataset="pulse-transit-time-ppg",
        title="Healthy Baseline (PhysioNet PTT s3_sit @ 500 Hz)",
        clinical_profile="Healthy 25-yr-old resting adult: HR ~73 bpm, SDNN ~62 ms, RMSSD ~38 ms, BP 120/74 -> 111/72, SpO2 97%, Skin Temp 35.8 C.",
        spaceflight_scenario="Nominal Astronaut Astroskin Baseline (Healthy Orbit / Pre-EVA)",
    ),
    "bidmc_19": PhysioNetRecordMeta(
        record_id="bidmc_19",
        dataset="bidmc",
        title="BIDMC #19 — Low-HRV & Borderline QTcF Watch",
        clinical_profile="Normal HR (~73.5 bpm) & 100% SpO2, but suppressed HRV (SDNN ~20 ms) and borderline QTcF (~479 ms).",
        spaceflight_scenario="Long-Duration Autonomic Unloading & Repolarization Watch",
    ),
    "bidmc_12": PhysioNetRecordMeta(
        record_id="bidmc_12",
        dataset="bidmc",
        title="BIDMC #12 — Transient Hypoxemia & Vagal Collapse",
        clinical_profile="Elevated HR (89-99 bpm), severely suppressed RMSSD (~7 ms) & DC (<2 ms), with real SpO2 dips to 92%.",
        spaceflight_scenario="Cabin O2 / CO2 Scrubber Stress & Pre-Event Autonomic Drift",
    ),
    "bidmc_17": PhysioNetRecordMeta(
        record_id="bidmc_17",
        dataset="bidmc",
        title="BIDMC #17 — High Ectopy Burden & Desaturation",
        clinical_profile="Frequent premature beats (>20% ectopy), ECG-vs-PPG rate gap, DFA breakdown, and SpO2 92-96%.",
        spaceflight_scenario="NASA HRP Cardiac Rhythm Instability / Electrolyte Check",
    ),
    "bidmc_16": PhysioNetRecordMeta(
        record_id="bidmc_16",
        dataset="bidmc",
        title="BIDMC #16 — Sustained Tachycardia & Sympathetic Strain",
        clinical_profile="Persistent tachycardia (102-113 bpm), SDNN ~16 ms, DC <1 ms, and fractal breakdown (DFA1 ~0.23).",
        spaceflight_scenario="Post-EVA / Hypercapnic or Orthostatic Cardiovascular Strain",
    ),
}


@lru_cache(maxsize=8)
def load_physionet_record(record_id: str) -> Dict[str, Any]:
    """Load a bundled real PhysioNet record (BIDMC or Pulse Transit Time PPG)."""
    if record_id not in PHYSIONET_RECORDS:
        raise ValueError(f"Unknown PhysioNet record_id '{record_id}'. Available: {list(PHYSIONET_RECORDS)}")

    meta = PHYSIONET_RECORDS[record_id]
    if meta.dataset == "bidmc":
        sig_path = BIDMC_DIR / f"{record_id}_Signals.csv"
        num_path = BIDMC_DIR / f"{record_id}_Numerics.csv"
        if not sig_path.exists() or not num_path.exists():
            raise FileNotFoundError(f"Missing PhysioNet BIDMC files for '{record_id}' in {BIDMC_DIR}")
        sig = pd.read_csv(sig_path)
        num = pd.read_csv(num_path)
        sig.columns = [c.strip() for c in sig.columns]
        num.columns = [c.strip() for c in num.columns]
        t = sig["Time [s]"].to_numpy(dtype=float)
        fs_hz = round(float((len(t) - 1) / max(t[-1] - t[0], 1e-6)), 3)
        return {
            "sig_df": sig,
            "num_df": num,
            "fs_hz": fs_hz,
            "cuff_sbp_baseline": 120.0,
            "skin_temp_c": None,
            "accel_rms_g": None,
        }

    # Pulse Transit Time PPG dataset (e.g., ptt_s3_sit -> s3_sit.csv)
    csv_name = record_id.removeprefix("ptt_")
    csv_path = PTT_DIR / f"{csv_name}.csv"
    info_path = PTT_DIR / "subjects_info.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing PhysioNet PTT file '{csv_path}'")

    raw = pd.read_csv(csv_path)
    t_dt = pd.to_datetime(raw["time"])
    t_sec = (t_dt - t_dt.iloc[0]).dt.total_seconds().to_numpy(dtype=float)
    fs_hz = round(float((len(t_sec) - 1) / max(t_sec[-1], 1e-6)), 2)

    # Normalize into unified stream dataframe (downsample 500 Hz -> 250 Hz Astroskin rate)
    step = 2 if fs_hz >= 450.0 else 1
    out_fs = round(fs_hz / step, 2)
    sliced = raw.iloc[::step].reset_index(drop=True)
    t_out = t_sec[::step]

    # Normalize 16-bit ADC counts to mV-like float units; invert reflectance PPG so systole points upward
    ecg_norm = (sliced["ecg"].to_numpy(dtype=float) - np.median(sliced["ecg"])) / 1000.0
    pleth_norm = -(sliced["pleth_1"].to_numpy(dtype=float) - np.median(sliced["pleth_1"])) / 1000.0
    sig = pd.DataFrame({"Time [s]": t_out, "II": ecg_norm, "PLETH": pleth_norm})

    skin_temp = round(float(sliced["temp_1"].mean()), 2) if "temp_1" in sliced.columns else None
    accel_rms = None
    if {"a_x", "a_y", "a_z"}.issubset(sliced.columns):
        ax = sliced["a_x"].to_numpy(dtype=float)
        ay = sliced["a_y"].to_numpy(dtype=float)
        az = sliced["a_z"].to_numpy(dtype=float)
        mag = np.sqrt(ax ** 2 + ay ** 2 + az ** 2) / 9.80665
        accel_rms = round(float(np.std(mag)), 3)

    cuff_sbp = 115.5
    num_df: Optional[pd.DataFrame] = None
    if info_path.exists():
        info = pd.read_csv(info_path)
        row = info[info["record"] == csv_name]
        if not row.empty:
            r0 = row.iloc[0]
            cuff_sbp = float(0.5 * (r0["bp_sys_start"] + r0["bp_sys_end"]))
            t_1hz = np.arange(0.0, t_out[-1] + 1.0, 1.0)
            spo2_interp = np.linspace(float(r0["spo2_start"]), float(r0["spo2_end"]), len(t_1hz))
            hr_interp = np.linspace(float(r0["hr_1_start"]), float(r0["hr_1_end"]), len(t_1hz))
            num_df = pd.DataFrame({"Time [s]": t_1hz, "HR": hr_interp, "SpO2": np.round(spo2_interp, 1)})

    return {
        "sig_df": sig,
        "num_df": num_df,
        "fs_hz": out_fs,
        "cuff_sbp_baseline": round(cuff_sbp, 1),
        "skin_temp_c": skin_temp,
        "accel_rms_g": accel_rms,
    }


def _bandpass(signal: np.ndarray, low_hz: float, high_hz: float, fs_hz: float, order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth bandpass filter with DC offset removal."""
    centered = np.nan_to_num(signal - np.nanmedian(signal), nan=0.0)
    nyq = 0.5 * fs_hz
    hi = min(high_hz, nyq * 0.92)
    lo = max(low_hz, 0.01)
    if lo >= hi or len(centered) < 24:
        return centered
    sos = butter(order, [lo, hi], btype="bandpass", fs=fs_hz, output="sos")
    return sosfiltfilt(sos, centered)


def _select_best_ecg_lead(sig_df: pd.DataFrame, fs_hz: float) -> Tuple[str, np.ndarray]:
    """Select the cleanest available ECG lead (preferring Lead II when SNR is solid)."""
    candidates = [col for col in ("II", "V", "AVR") if col in sig_df.columns]
    if not candidates:
        raise ValueError("No ECG lead columns (II, V, AVR) found in waveform file.")
    if len(candidates) == 1:
        return candidates[0], sig_df[candidates[0]].to_numpy(dtype=float)

    best_lead = candidates[0]
    best_score = -1.0
    for col in candidates:
        raw = sig_df[col].to_numpy(dtype=float)
        qrs = _bandpass(raw, 5.0, 18.0, fs_hz)
        p99 = float(np.percentile(np.abs(qrs), 99))
        p50 = float(np.percentile(np.abs(qrs), 50)) + 1e-6
        snr_proxy = p99 / p50
        weighted = snr_proxy * (1.15 if col == "II" else 1.0)
        if weighted > best_score:
            best_score = weighted
            best_lead = col
    return best_lead, sig_df[best_lead].to_numpy(dtype=float)


def detect_ecg_r_peaks(ecg: np.ndarray, fs_hz: float) -> np.ndarray:
    """Detect ECG R-peaks via Pan-Tompkins bandpass, MWI, and local extremum refinement."""
    qrs = _bandpass(ecg, 5.0, 18.0, fs_hz)
    deriv = np.gradient(qrs)
    squared = deriv ** 2
    win_len = max(3, int(round(0.120 * fs_hz)))
    mwi = np.convolve(squared, np.ones(win_len) / win_len, mode="same")

    thr = max(float(np.percentile(mwi, 96)) * 0.25, 1e-9)
    min_dist = max(1, int(round(0.28 * fs_hz)))
    coarse_peaks, _ = find_peaks(mwi, height=thr, distance=min_dist)

    clean = _bandpass(ecg, 0.5, 35.0, fs_hz)
    if abs(np.percentile(clean, 0.5)) > abs(np.percentile(clean, 99.5)):
        clean = -clean

    half_search = int(round(0.065 * fs_hz))
    refined: List[int] = []
    n = len(clean)
    for pk in coarse_peaks:
        lo = max(0, pk - half_search)
        hi = min(n, pk + half_search + 1)
        exact = lo + int(np.argmax(clean[lo:hi]))
        if not refined or (exact - refined[-1]) >= int(round(0.25 * fs_hz)):
            refined.append(exact)
        elif clean[exact] > clean[refined[-1]]:
            refined[-1] = exact

    return np.asarray(refined, dtype=int)


def classify_rr_and_ectopy(r_peaks: np.ndarray, fs_hz: float) -> Dict[str, Any]:
    """Convert R-peaks to RR intervals, flag premature/ectopic beats, and isolate clean NN."""
    if len(r_peaks) < 4:
        return {
            "rr_ms": np.array([], dtype=float),
            "nn_ms": np.array([], dtype=float),
            "nn_times_s": np.array([], dtype=float),
            "ectopic_count": 0,
            "ectopy_burden_pct": 0.0,
            "total_beats": int(len(r_peaks)),
        }

    r_times_s = r_peaks / fs_hz
    rr_ms = np.diff(r_times_s) * 1000.0
    valid_phys = (rr_ms >= 300.0) & (rr_ms <= 2000.0)

    rr_series = pd.Series(np.where(valid_phys, rr_ms, np.nan))
    local_med = rr_series.rolling(window=11, center=True, min_periods=1).median().bfill().ffill().to_numpy()

    ectopic_mask = np.zeros(len(rr_ms), dtype=bool)
    for i in range(len(rr_ms)):
        if not valid_phys[i]:
            continue
        med_i = local_med[i]
        if rr_ms[i] < 0.80 * med_i:
            has_pause = (i + 1 < len(rr_ms)) and (rr_ms[i + 1] > 1.15 * med_i)
            if has_pause or rr_ms[i] < 0.76 * med_i:
                ectopic_mask[i] = True

    sinus_mask = valid_phys & (~ectopic_mask) & (np.abs(rr_ms - local_med) <= 0.25 * local_med)
    for i in range(len(ectopic_mask) - 1):
        if ectopic_mask[i] and rr_ms[i + 1] > 1.15 * local_med[i + 1]:
            sinus_mask[i + 1] = False

    nn_ms = rr_ms[sinus_mask]
    nn_times_s = r_times_s[1:][sinus_mask]
    ectopic_count = int(np.sum(ectopic_mask))
    total_beats = int(len(r_peaks))
    burden_pct = 100.0 * ectopic_count / max(total_beats, 1)

    return {
        "rr_ms": rr_ms,
        "nn_ms": nn_ms,
        "nn_times_s": nn_times_s,
        "ectopic_count": ectopic_count,
        "ectopy_burden_pct": round(burden_pct, 2),
        "total_beats": total_beats,
    }


def _compute_deceleration_capacity(nn_ms: np.ndarray) -> Optional[float]:
    """Compute PRSA Deceleration Capacity (Bauer et al., Lancet 2006) in ms."""
    if len(nn_ms) < 12:
        return None
    anchors = [i for i in range(2, len(nn_ms) - 1) if 1.0 < (nn_ms[i] / max(nn_ms[i - 1], 1e-6)) <= 1.08]
    if len(anchors) < 3:
        anchors = [i for i in range(2, len(nn_ms) - 1) if nn_ms[i] > nn_ms[i - 1]]
    if not anchors:
        return None

    dc_vals = [0.25 * (nn_ms[i] + nn_ms[i + 1] - nn_ms[i - 1] - nn_ms[i - 2]) for i in anchors]
    return round(float(np.mean(dc_vals)), 2)


def _compute_dfa_alpha1(nn_ms: np.ndarray) -> Optional[float]:
    """Compute short-term Detrended Fluctuation Analysis scaling exponent (n=4..16)."""
    if len(nn_ms) < 24:
        return None
    y = np.cumsum(nn_ms - np.mean(nn_ms))
    max_box = min(16, len(y) // 4)
    if max_box < 6:
        return None
    scales = np.arange(4, max_box + 1, dtype=int)
    flucts: List[float] = []
    valid_scales: List[int] = []
    for n in scales:
        n_segs = len(y) // n
        if n_segs < 2:
            continue
        trimmed = y[: n_segs * n].reshape(n_segs, n)
        x = np.arange(n, dtype=float)
        rms_list = []
        for seg in trimmed:
            slope, intercept = np.polyfit(x, seg, 1)
            rms_list.append(np.sqrt(np.mean((seg - (slope * x + intercept)) ** 2)))
        f_n = float(np.sqrt(np.mean(np.square(rms_list))))
        if f_n > 1e-9:
            flucts.append(f_n)
            valid_scales.append(int(n))
    if len(valid_scales) < 3:
        return None
    alpha1, _ = np.polyfit(np.log10(valid_scales), np.log10(flucts), 1)
    return round(float(alpha1), 3)


def compute_hrv_metrics(nn_ms: np.ndarray, nn_times_s: np.ndarray) -> Dict[str, Optional[float]]:
    """Compute time-domain, Poincare, Welch frequency-domain, DC, and DFA alpha-1 HRV."""
    if len(nn_ms) < 8:
        return {
            "mean_hr_bpm": None,
            "mean_nn_ms": None,
            "sdnn_ms": None,
            "rmssd_ms": None,
            "pnn50_pct": None,
            "sd1_ms": None,
            "sd2_ms": None,
            "sd1_sd2_ratio": None,
            "lf_power_ms2": None,
            "hf_power_ms2": None,
            "lf_hf_ratio": None,
            "deceleration_capacity_ms": None,
            "dfa_alpha1": None,
        }

    mean_nn = float(np.mean(nn_ms))
    mean_hr = 60000.0 / max(mean_nn, 1.0)
    sdnn = float(np.std(nn_ms, ddof=1))
    diff_nn = np.diff(nn_ms)
    rmssd = float(np.sqrt(np.mean(diff_nn ** 2)))
    pnn50 = float(np.mean(np.abs(diff_nn) > 50.0) * 100.0)
    sd1 = rmssd / np.sqrt(2.0)
    sd2 = float(np.sqrt(max(0.0, 2.0 * sdnn ** 2 - 0.5 * rmssd ** 2)))
    sd_ratio = sd1 / sd2 if sd2 > 1e-6 else None

    lf_power: Optional[float] = None
    hf_power: Optional[float] = None
    lf_hf: Optional[float] = None

    if len(nn_ms) >= 20 and len(nn_times_s) == len(nn_ms) and (nn_times_s[-1] - nn_times_s[0]) >= 30.0:
        uniq_t, uniq_idx = np.unique(nn_times_s, return_index=True)
        uniq_nn = nn_ms[uniq_idx]
        if len(uniq_t) >= 16:
            fs_interp = 4.0
            grid_t = np.arange(uniq_t[0], uniq_t[-1], 1.0 / fs_interp)
            interp_nn = CubicSpline(uniq_t, uniq_nn)(grid_t) - np.mean(uniq_nn)
            freqs, psd = welch(interp_nn, fs=fs_interp, nperseg=min(256, len(interp_nn)))
            lf_mask = (freqs >= 0.04) & (freqs < 0.15)
            hf_mask = (freqs >= 0.15) & (freqs <= 0.40)
            if np.any(lf_mask) and np.any(hf_mask):
                lf_power = round(float(np.trapezoid(psd[lf_mask], freqs[lf_mask])), 1)
                hf_power = round(float(np.trapezoid(psd[hf_mask], freqs[hf_mask])), 1)
                if hf_power > 1e-6:
                    lf_hf = round(float(lf_power / hf_power), 2)

    return {
        "mean_hr_bpm": round(mean_hr, 1),
        "mean_nn_ms": round(mean_nn, 1),
        "sdnn_ms": round(sdnn, 1),
        "rmssd_ms": round(rmssd, 1),
        "pnn50_pct": round(pnn50, 1),
        "sd1_ms": round(float(sd1), 1),
        "sd2_ms": round(sd2, 1),
        "sd1_sd2_ratio": round(float(sd_ratio), 3) if sd_ratio is not None else None,
        "lf_power_ms2": lf_power,
        "hf_power_ms2": hf_power,
        "lf_hf_ratio": lf_hf,
        "deceleration_capacity_ms": _compute_deceleration_capacity(nn_ms),
        "dfa_alpha1": _compute_dfa_alpha1(nn_ms),
    }


def compute_repolarization_and_morphology(
    ecg: np.ndarray, r_peaks: np.ndarray, fs_hz: float
) -> Dict[str, Optional[float]]:
    """Delineate Q-onset, T-end (tangent method), QTcF/QTcB, T-wave alternans, and ST shift."""
    if len(r_peaks) < 8:
        return {"qt_ms": None, "qtcf_ms": None, "qtcb_ms": None, "twa_ratio": None, "st_deviation_ratio": None}

    clean = _bandpass(ecg, 0.5, 35.0, fs_hz)
    if abs(np.percentile(clean, 0.5)) > abs(np.percentile(clean, 99.5)):
        clean = -clean

    rr_sec_all = np.diff(r_peaks) / fs_hz
    valid_rr = rr_sec_all[(rr_sec_all >= 0.35) & (rr_sec_all <= 1.8)]
    if len(valid_rr) < 4:
        return {"qt_ms": None, "qtcf_ms": None, "qtcb_ms": None, "twa_ratio": None, "st_deviation_ratio": None}
    med_rr_s = float(np.median(valid_rr))

    qt_list: List[float] = []
    t_amps: List[float] = []
    st_ratios: List[float] = []

    pre_base_lo = int(round(0.10 * fs_hz))
    pre_base_hi = int(round(0.04 * fs_hz))
    q_lo = int(round(0.06 * fs_hz))
    q_hi = int(round(0.015 * fs_hz))
    t_start = int(round(0.12 * fs_hz))
    t_end_max = int(round(min(0.46, 0.72 * med_rr_s) * fs_hz))
    st_lo = int(round(0.06 * fs_hz))
    st_hi = int(round(0.10 * fs_hz))

    n = len(clean)
    for idx, pk in enumerate(r_peaks[:-1]):
        rr_s = (r_peaks[idx + 1] - pk) / fs_hz
        if not (0.35 <= rr_s <= 1.8):
            continue
        if pk - pre_base_lo < 0 or pk + t_end_max + int(0.12 * fs_hz) >= n:
            continue

        baseline = float(np.median(clean[pk - pre_base_lo : pk - pre_base_hi]))
        r_amp = float(clean[pk] - baseline)
        if r_amp <= 1e-6:
            continue

        q_seg = clean[pk - q_lo : pk - q_hi] - baseline
        q_idx = (pk - q_lo) + int(np.argmin(np.abs(q_seg)))
        st_ratios.append(float(np.mean(clean[pk + st_lo : pk + st_hi]) - baseline) / r_amp)

        t_win_hi = min(pk + t_end_max, pk + int(round(0.72 * rr_s * fs_hz)))
        if t_win_hi <= pk + t_start + 4:
            continue
        t_seg = clean[pk + t_start : t_win_hi] - baseline
        t_rel = int(np.argmax(np.abs(t_seg)))
        t_pk_idx = pk + t_start + t_rel
        t_amp = float(t_seg[t_rel])
        t_amps.append(abs(t_amp))

        tail_hi = min(n, t_pk_idx + int(round(0.16 * fs_hz)))
        if tail_hi <= t_pk_idx + 3:
            continue
        tail = clean[t_pk_idx:tail_hi] - baseline
        slopes = np.gradient(tail) * fs_hz
        steep_rel = int(np.argmin(slopes) if t_amp >= 0 else np.argmax(slopes))
        slope_val = float(slopes[steep_rel])
        val_at_steep = float(tail[steep_rel])
        if abs(slope_val) > 1e-6:
            dt_zero = float(np.clip(-val_at_steep / slope_val, 0.01, 0.14))
            t_end_idx = t_pk_idx + steep_rel + int(round(dt_zero * fs_hz))
        else:
            t_end_idx = t_pk_idx + int(round(0.08 * fs_hz))

        qt_ms = (t_end_idx - q_idx) * 1000.0 / fs_hz
        if 220.0 <= qt_ms <= 620.0:
            qt_list.append(qt_ms)

    if not qt_list:
        return {"qt_ms": None, "qtcf_ms": None, "qtcb_ms": None, "twa_ratio": None, "st_deviation_ratio": None}

    qt_med = float(np.median(qt_list))
    qtcf = qt_med / (med_rr_s ** (1.0 / 3.0))
    qtcb = qt_med / np.sqrt(med_rr_s)

    twa_ratio: Optional[float] = None
    if len(t_amps) >= 8:
        even_t = np.mean(t_amps[0::2])
        odd_t = np.mean(t_amps[1::2])
        mean_t = np.mean(t_amps)
        if mean_t > 1e-6:
            twa_ratio = round(float(abs(even_t - odd_t) / mean_t), 3)

    return {
        "qt_ms": round(qt_med, 1),
        "qtcf_ms": round(float(qtcf), 1),
        "qtcb_ms": round(float(qtcb), 1),
        "twa_ratio": twa_ratio,
        "st_deviation_ratio": round(float(np.median(st_ratios)), 3) if st_ratios else None,
    }


def compute_ppg_and_hemodynamics(
    pleth: np.ndarray,
    r_peaks: np.ndarray,
    ecg_hr_bpm: Optional[float],
    fs_hz: float,
    cuff_sbp_baseline: float = 120.0,
    baseline_pat_ms: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    """
    Extract PPG pulse rate, mechanical pulse deficit, systolic-bounded PAT (ms),
    and baseline-anchored relative SBP & Shock Index trends.
    """
    ppg_bp = _bandpass(pleth, 0.5, 8.0, fs_hz)
    ppg_std = float(np.std(ppg_bp))
    if ppg_std < 1e-6 or len(r_peaks) < 4:
        return {
            "ppg_pulse_bpm": None,
            "pulse_deficit_bpm": None,
            "pat_ms": None,
            "sbp_est_mmhg": None,
            "shock_index": None,
        }

    p_peaks, _ = find_peaks(ppg_bp, distance=int(round(0.30 * fs_hz)), prominence=0.35 * ppg_std)
    ppg_pulse_bpm: Optional[float] = None
    if len(p_peaks) >= 4:
        ppg_rr = np.diff(p_peaks) / fs_hz
        ppg_rr = ppg_rr[(ppg_rr >= 0.30) & (ppg_rr <= 2.0)]
        if len(ppg_rr) >= 3:
            ppg_pulse_bpm = round(float(60.0 / np.median(ppg_rr)), 1)

    pulse_deficit: Optional[float] = None
    if ecg_hr_bpm is not None and ppg_pulse_bpm is not None:
        pulse_deficit = round(float(max(0.0, ecg_hr_bpm - ppg_pulse_bpm)), 1)

    # Pulse Arrival Time: delay from R-peak to steepest PPG systolic upstroke (max +dPPG/dt)
    # Supports both low-latency wearable sensors (~180-300 ms) and buffered bedside monitors (~450-650 ms)
    up_lo = int(round(0.12 * fs_hz))
    up_hi = int(round(0.68 * fs_hz))
    pats: List[float] = []
    n = len(ppg_bp)
    dppg = np.gradient(ppg_bp)
    for pk in r_peaks:
        if pk + up_hi >= n:
            continue
        up_rel = int(np.argmax(dppg[pk + up_lo : pk + up_hi]))
        pat_ms = (up_lo + up_rel) * 1000.0 / fs_hz
        if 120.0 <= pat_ms <= 680.0:
            pats.append(pat_ms)

    pat_med = round(float(np.median(pats)), 1) if len(pats) >= 4 else None
    sbp_est: Optional[float] = None
    shock_idx: Optional[float] = None
    if pat_med is not None:
        # Uncalibrated PAT tracks delta-SBP relative to baseline_pat_ms (never invent raw mmHg)
        ref_pat = baseline_pat_ms if baseline_pat_ms is not None else pat_med
        sbp_est = round(float(np.clip(cuff_sbp_baseline - 0.50 * (pat_med - ref_pat), 75.0, 200.0)), 1)
        if ecg_hr_bpm is not None:
            shock_idx = round(float(ecg_hr_bpm / sbp_est), 3)

    return {
        "ppg_pulse_bpm": ppg_pulse_bpm,
        "pulse_deficit_bpm": pulse_deficit,
        "pat_ms": pat_med,
        "sbp_est_mmhg": sbp_est,
        "shock_index": shock_idx,
    }


def _estimate_edr_respiration_rate(ecg: np.ndarray, r_peaks: np.ndarray, fs_hz: float) -> Tuple[Optional[float], Optional[float]]:
    """ECG-Derived Respiration (EDR) from R-wave amplitude modulation when no RESP belt exists."""
    if len(r_peaks) < 12:
        return None, None
    clean = _bandpass(ecg, 0.5, 35.0, fs_hz)
    if abs(np.percentile(clean, 0.5)) > abs(np.percentile(clean, 99.5)):
        clean = -clean
    r_times = r_peaks / fs_hz
    if r_times[-1] - r_times[0] < 20.0:
        return None, None
    r_amps = clean[r_peaks]
    fs_edr = 4.0
    grid_t = np.arange(r_times[0], r_times[-1], 1.0 / fs_edr)
    edr_sig = CubicSpline(r_times, r_amps)(grid_t)
    edr_bp = _bandpass(edr_sig, 0.10, 0.60, fs_edr, order=3)
    edr_std = float(np.std(edr_bp))
    if edr_std < 1e-6:
        return None, None
    b_peaks, _ = find_peaks(edr_bp, distance=int(round(1.5 * fs_edr)), prominence=0.25 * edr_std)
    if len(b_peaks) < 3:
        return None, None
    gaps = np.diff(b_peaks) / fs_edr
    valid_gaps = gaps[(gaps >= 1.5) & (gaps <= 12.0)]
    rr_bpm = round(float(60.0 / np.median(valid_gaps)), 1) if len(valid_gaps) >= 2 else None
    return rr_bpm, round(float(np.max(gaps)), 1)


def compute_respiration_and_spo2(
    resp: Optional[np.ndarray],
    ecg: np.ndarray,
    r_peaks: np.ndarray,
    num_df: Optional[pd.DataFrame],
    fs_hz: float,
    atmosphere_profile: str = "iss_nominal",
) -> Dict[str, Any]:
    """Extract respiration rate (belt or EDR), apnea pauses, and SpO2 / ODI3 metrics."""
    rr_bpm: Optional[float] = None
    max_gap_s: Optional[float] = None
    resp_source = "impedance_belt"

    if resp is not None:
        resp_bp = _bandpass(resp, 0.08, 0.80, fs_hz)
        resp_std = float(np.std(resp_bp))
        if resp_std > 1e-6:
            b_peaks, _ = find_peaks(resp_bp, distance=int(round(1.2 * fs_hz)), prominence=0.30 * resp_std)
            if len(b_peaks) >= 3:
                gaps = np.diff(b_peaks) / fs_hz
                max_gap_s = round(float(np.max(gaps)), 1)
                valid_gaps = gaps[(gaps >= 1.2) & (gaps <= 12.0)]
                if len(valid_gaps) >= 2:
                    rr_bpm = round(float(60.0 / np.median(valid_gaps)), 1)
    else:
        resp_source = "ecg_derived_edr"
        rr_bpm, max_gap_s = _estimate_edr_respiration_rate(ecg, r_peaks, fs_hz)

    spo2_mean: Optional[float] = None
    spo2_min: Optional[float] = None
    spo2_cov_pct = 0.0
    odi3_per_hr: Optional[float] = None
    ref_hr_mean: Optional[float] = None
    ref_pulse_mean: Optional[float] = None
    ref_pulse_deficit: Optional[float] = None

    if num_df is not None and not num_df.empty:
        if "HR" in num_df.columns:
            hr_s = pd.to_numeric(num_df["HR"], errors="coerce").dropna()
            if not hr_s.empty:
                ref_hr_mean = round(float(hr_s.mean()), 1)
        if "PULSE" in num_df.columns:
            p_s = pd.to_numeric(num_df["PULSE"], errors="coerce").dropna()
            if not p_s.empty:
                ref_pulse_mean = round(float(p_s.mean()), 1)
        if ref_hr_mean is not None and ref_pulse_mean is not None:
            ref_pulse_deficit = round(float(max(0.0, ref_hr_mean - ref_pulse_mean)), 1)

        if "SpO2" in num_df.columns:
            spo2_raw = pd.to_numeric(num_df["SpO2"], errors="coerce")
            spo2_valid = spo2_raw.dropna()
            spo2_cov_pct = round(100.0 * len(spo2_valid) / max(len(num_df), 1), 1)
            if not spo2_valid.empty:
                spo2_mean = round(float(spo2_valid.mean()), 1)
                spo2_min = round(float(spo2_valid.min()), 1)

                base = spo2_valid.rolling(window=60, min_periods=1).median().to_numpy()
                vals = spo2_valid.to_numpy()
                dips = 0
                last_dip = -15
                for idx in range(len(vals)):
                    if (base[idx] - vals[idx]) >= 3.0 and (idx - last_dip) >= 10:
                        dips += 1
                        last_dip = idx
                hours = len(vals) / 3600.0
                odi3_per_hr = round(float(dips / max(hours, 1e-4)), 1) if hours >= (1.0 / 60.0) else 0.0

    atmo_map = NASA_CARDIO_VITALS_STANDARDS["atmosphere_spo2"]  # type: ignore[index]
    atmo = atmo_map.get(atmosphere_profile, atmo_map["iss_nominal"])  # type: ignore[union-attr]

    return {
        "resp_rate_bpm": rr_bpm,
        "resp_source": resp_source,
        "max_breath_gap_s": max_gap_s,
        "spo2_mean_pct": spo2_mean,
        "spo2_min_pct": spo2_min,
        "spo2_coverage_pct": spo2_cov_pct,
        "odi3_per_hr": odi3_per_hr,
        "ref_hr_mean_bpm": ref_hr_mean,
        "ref_pulse_mean_bpm": ref_pulse_mean,
        "ref_pulse_deficit_bpm": ref_pulse_deficit,
        "atmosphere_profile": atmosphere_profile,
        "atmosphere_label": atmo["label"],
    }


def _evaluate_early_warnings(
    summary: Dict[str, Any],
    baseline: Dict[str, Any],
    atmosphere_profile: str,
    cabin_ppco2_mmhg: Optional[float] = None,
) -> Dict[str, Any]:
    """Score autonomic, electrical, hemodynamic, and respiratory pre-event warning signs."""
    hr_std = NASA_CARDIO_VITALS_STANDARDS["heart_rate_bpm"]  # type: ignore[index]
    hrv_std = NASA_CARDIO_VITALS_STANDARDS["hrv_autonomic"]  # type: ignore[index]
    rep_std = NASA_CARDIO_VITALS_STANDARDS["repolarization_electrical"]  # type: ignore[index]
    hemo_std = NASA_CARDIO_VITALS_STANDARDS["hemodynamics"]  # type: ignore[index]
    resp_std = NASA_CARDIO_VITALS_STANDARDS["respiration"]  # type: ignore[index]
    atmo_map = NASA_CARDIO_VITALS_STANDARDS["atmosphere_spo2"]  # type: ignore[index]
    atmo = atmo_map.get(atmosphere_profile, atmo_map["iss_nominal"])  # type: ignore[union-attr]

    alerts: List[Dict[str, Any]] = []
    axis_risk = {"autonomic": 0.0, "electrical": 0.0, "hemodynamic": 0.0, "respiratory": 0.0}

    def add_alert(axis: str, severity: str, points: float, metric: str, value: Any, threshold: str, mechanism: str, action: str) -> None:
        axis_risk[axis] = min(100.0, axis_risk[axis] + points)
        alerts.append(
            {
                "axis": axis,
                "severity": severity,
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "mechanism": mechanism,
                "action": action,
            }
        )

    # 1. Autonomic Withdrawal & Nonlinear Pre-Event Markers
    # Task Force SDNN (<50 ms) applies to multi-minute streams (>=120 beats); short 60s slices use tighter cutoff
    total_beats = int(summary.get("total_beats") or 0)
    sdnn = summary.get("sdnn_ms")
    if sdnn is not None:
        sdnn_crit = hrv_std["sdnn_critical_ms"] if total_beats >= 120 else 20.0
        sdnn_watch = hrv_std["sdnn_watch_ms"] if total_beats >= 120 else 30.0
        if sdnn < sdnn_crit:
            add_alert("autonomic", "CRITICAL", 45, "SDNN", f"{sdnn} ms", f"< {sdnn_crit} ms",
                      "Severe global HRV suppression (autonomic collapse preceding arrhythmia/decompensation).",
                      "Initiate rest protocol, verify electrolytes/hydration, and alert flight surgeon.")
        elif sdnn < sdnn_watch:
            add_alert("autonomic", "WATCH", 25, "SDNN", f"{sdnn} ms", f"< {sdnn_watch} ms",
                      "Depressed overall HRV (<50 ms ESC/NASPE risk cutoff).",
                      "Repeat 5-min supine resting ECG & check sleep/stress load.")

    rmssd = summary.get("rmssd_ms")
    base_rmssd = baseline.get("rmssd_ms")
    if rmssd is not None:
        if rmssd < hrv_std["rmssd_critical_ms"]:
            add_alert("autonomic", "CRITICAL", 35, "RMSSD", f"{rmssd} ms", f"< {hrv_std['rmssd_critical_ms']} ms",
                      "Acute parasympathetic (vagal) withdrawal.",
                      "Perform paced slow breathing (6 breaths/min) & fluid-status check.")
        elif rmssd < hrv_std["rmssd_watch_ms"]:
            add_alert("autonomic", "WATCH", 20, "RMSSD", f"{rmssd} ms", f"< {hrv_std['rmssd_watch_ms']} ms",
                      "Reduced vagal tone; sympathetic predominance.",
                      "Log workload/fatigue & monitor HRV over next 30 minutes.")
        if base_rmssd and base_rmssd > 5.0:
            drop_pct = 100.0 * (rmssd - base_rmssd) / base_rmssd
            if drop_pct <= hrv_std["rmssd_drop_critical_pct"]:
                add_alert("autonomic", "WARNING", 25, "RMSSD Drift", f"{drop_pct:+.1f}%", f"<= {hrv_std['rmssd_drop_critical_pct']}%",
                          "Progressive vagal withdrawal vs. astronaut's early baseline.",
                          "Flag pre-event autonomic drift; defer strenuous EVA.")

    dc = summary.get("deceleration_capacity_ms")
    if dc is not None and dc <= hrv_std["deceleration_capacity_watch_ms"]:
        sev = "CRITICAL" if dc <= hrv_std["deceleration_capacity_critical_ms"] else "WATCH"
        pts = 30 if sev == "CRITICAL" else 18
        add_alert("autonomic", sev, pts, "Deceleration Capacity", f"{dc} ms", f"<= {hrv_std['deceleration_capacity_watch_ms']} ms",
                  "Impaired vagal heart-rate deceleration reflex (Bauer et al. pre-event marker).",
                  "Cross-check baroreflex/orthostatic tolerance before posture transitions.")

    dfa = summary.get("dfa_alpha1")
    if dfa is not None and total_beats >= 120 and (dfa < hrv_std["dfa_alpha1_min"] or dfa > hrv_std["dfa_alpha1_max"]):
        add_alert("autonomic", "WATCH", 15, "DFA alpha-1", dfa, f"[{hrv_std['dfa_alpha1_min']}, {hrv_std['dfa_alpha1_max']}]",
                  "Loss of healthy fractal RR correlation (erratic or overly rigid sympathetic lock).",
                  "Reduce acute physical/cognitive load and re-evaluate in 15 min.")

    # 2. Electrical / Repolarization Instability
    qtcf = summary.get("qtcf_ms")
    base_qtcf = baseline.get("qtcf_ms")
    if qtcf is not None:
        if qtcf >= rep_std["qtcf_critical_ms"]:
            add_alert("electrical", "CRITICAL", 55, "QTcF", f"{qtcf} ms", f">= {rep_std['qtcf_critical_ms']} ms",
                      "Critical ventricular repolarization prolongation (Torsades/VT risk; D'Aunno et al.).",
                      "NO EVA. Capture 12-lead ECG, review QT-prolonging meds & serum K+/Mg2+.")
        elif qtcf >= rep_std["qtcf_watch_ms"]:
            add_alert("electrical", "WATCH", 25, "QTcF", f"{qtcf} ms", f">= {rep_std['qtcf_watch_ms']} ms",
                      "Borderline QTcF prolongation (spaceflight cardiac unloading/electrolyte watch).",
                      "Monitor repolarization trend and verify hydration/potassium intake.")
        if base_qtcf and (qtcf - base_qtcf) >= rep_std["qtcf_delta_critical_ms"]:
            add_alert("electrical", "CRITICAL", 35, "QTcF Delta", f"+{qtcf - base_qtcf:.1f} ms", f"+{rep_std['qtcf_delta_critical_ms']} ms",
                      "Acute QTcF lengthening from personal baseline.",
                      "Immediate flight surgeon review & continuous Holter surveillance.")

    ectopy = summary.get("ectopy_burden_pct", 0.0)
    if ectopy >= rep_std["ectopy_critical_pct"]:
        add_alert("electrical", "CRITICAL", 45, "Ectopy Burden", f"{ectopy}%", f">= {rep_std['ectopy_critical_pct']}%",
                  "High premature beat (PVC/PAC) burden raising re-entrant arrhythmia risk.",
                  "Restrict exertion, check electrolytes, and inspect raw ECG strip.")
    elif ectopy >= rep_std["ectopy_watch_pct"]:
        add_alert("electrical", "WATCH", 20, "Ectopy Burden", f"{ectopy}%", f">= {rep_std['ectopy_watch_pct']}%",
                  "Elevated premature beat count vs. healthy resting rhythm.",
                  "Continue continuous Bio-Monitor ECG logging.")

    pdef = summary.get("effective_pulse_deficit_bpm")
    if pdef is not None and pdef >= rep_std["pulse_deficit_watch_bpm"]:
        sev = "CRITICAL" if pdef >= rep_std["pulse_deficit_critical_bpm"] else "WARNING"
        pts = 40 if sev == "CRITICAL" else 25
        add_alert("electrical", sev, pts, "ECG-PPG Pulse Deficit", f"{pdef} bpm", f">= {rep_std['pulse_deficit_watch_bpm']} bpm",
                  "Electrical beats outnumber perfusing PPG pulses (non-perfusing ectopy / coupling loss).",
                  "Inspect ECG for bigeminy/PVCs & confirm radial/carotid pulse.")

    twa = summary.get("twa_ratio")
    if twa is not None and twa >= rep_std["twa_watch_ratio"]:
        sev = "WARNING" if twa >= rep_std["twa_critical_ratio"] else "WATCH"
        add_alert("electrical", sev, 20 if sev == "WARNING" else 12, "T-Wave Alternans", twa, f">= {rep_std['twa_watch_ratio']}",
                  "Beat-to-beat T-wave amplitude alternation (localized repolarization lability).",
                  "Monitor for escalating electrical instability prior to VT.")

    # 3. Hemodynamic & Orthostatic Strain
    hr = summary.get("mean_hr_bpm")
    base_hr = baseline.get("mean_hr_bpm")
    if hr is not None:
        if hr >= hr_std["tachy_critical"]:
            add_alert("hemodynamic", "CRITICAL", 45, "Resting HR", f"{hr} bpm", f">= {hr_std['tachy_critical']} bpm",
                      "Marked tachycardia at rest.",
                      "Check hydration, fever, cabin CO2, and orthostatic stress.")
        elif hr >= hr_std["tachy_watch"]:
            add_alert("hemodynamic", "WATCH", 22, "Resting HR", f"{hr} bpm", f">= {hr_std['tachy_watch']} bpm",
                      "Elevated resting heart rate above NASA nominal resting envelope.",
                      "Verify recent exercise recovery vs. plasma volume / CO2 load.")
        elif hr <= hr_std["brady_critical"]:
            add_alert("hemodynamic", "CRITICAL", 45, "Resting HR", f"{hr} bpm", f"<= {hr_std['brady_critical']} bpm",
                      "Severe bradycardia.",
                      "Verify sensor contact & assess conduction/presyncope symptoms.")
        if base_hr and (hr - base_hr) >= hr_std["orthostatic_delta_bpm"]:
            add_alert("hemodynamic", "CRITICAL", 40, "Orthostatic HR Jump", f"+{hr - base_hr:.1f} bpm", f">= +{hr_std['orthostatic_delta_bpm']} bpm",
                      "Meets NASA post-spaceflight Orthostatic Intolerance / POTS threshold.",
                      "Assume seated/supine posture, execute fluid/salt loading + compression garment.")

    pat = summary.get("pat_ms")
    base_pat = baseline.get("pat_ms")
    if pat is not None and base_pat is not None:
        d_pat = pat - base_pat
        if d_pat <= hemo_std["pat_drop_watch_ms"]:
            add_alert("hemodynamic", "WATCH", 18, "PAT Shift", f"{d_pat:+.1f} ms", f"<= {hemo_std['pat_drop_watch_ms']} ms",
                      "Shortening Pulse Arrival Time indicates rising arterial stiffness / BP surge.",
                      "Take reference cuff BP check.")
        elif d_pat >= hemo_std["pat_rise_watch_ms"]:
            add_alert("hemodynamic", "WATCH", 18, "PAT Shift", f"{d_pat:+.1f} ms", f">= +{hemo_std['pat_rise_watch_ms']} ms",
                      "Lengthening PAT suggests dropping stroke volume / orthostatic preload drop.",
                      "Check hydration & orthostatic tolerance.")

    si = summary.get("shock_index")
    if si is not None and si >= hemo_std["shock_index_watch"]:
        sev = "CRITICAL" if si >= hemo_std["shock_index_critical"] else "WARNING"
        add_alert("hemodynamic", sev, 35 if sev == "CRITICAL" else 20, "Shock Index Proxy", si, f">= {hemo_std['shock_index_watch']}",
                  "Elevated HR/SBP_est ratio flagging hemodynamic compromise / hypovolemia.",
                  "Immediate cuff BP verification & oral rehydration.")

    # 4. Respiratory & Hypoxic Stress
    spo2_min = summary.get("spo2_min_pct")
    if spo2_min is not None:
        if spo2_min < atmo["critical_below"]:
            add_alert("respiratory", "CRITICAL", 55, "Min SpO2", f"{spo2_min}%", f"< {atmo['critical_below']}% ({atmosphere_profile})",
                      f"Hypoxemia below {atmo['label']} critical floor.",
                      "Verify cabin ppO2 / suit seal, administer supplemental O2, check DCS.")
        elif spo2_min < atmo["nominal_min"]:
            add_alert("respiratory", "WARNING", 30, "Min SpO2", f"{spo2_min}%", f"< {atmo['nominal_min']}%",
                      "Transient desaturation below nominal spacecraft threshold.",
                      "Inspect pulse-ox contact & monitor cabin O2 partial pressure.")

    odi3 = summary.get("odi3_per_hr")
    if odi3 is not None and odi3 >= atmo["odi3_watch_per_hr"]:
        sev = "CRITICAL" if odi3 >= atmo["odi3_critical_per_hr"] else "WARNING"
        add_alert("respiratory", sev, 35 if sev == "CRITICAL" else 22, "ODI3 Desaturations", f"{odi3}/hr", f">= {atmo['odi3_watch_per_hr']}/hr",
                  "Repeated >=3% oxygen desaturation episodes.",
                  "Evaluate sleep-disordered breathing / cabin CO2 retention.")

    rr = summary.get("resp_rate_bpm")
    if rr is not None:
        if rr >= resp_std["rr_critical_high"] or rr <= resp_std["rr_critical_low"]:
            add_alert("respiratory", "CRITICAL", 40, "Respiration Rate", f"{rr} br/min", f"[{resp_std['rr_critical_low']}, {resp_std['rr_critical_high']}]",
                      "Abnormal respiratory drive (hypercapnia, hypoxia, or distress).",
                      "Cross-check cabin ppCO2 immediately (NASA-STD-3001 limit <= 3.0 mmHg).")
        elif rr >= resp_std["rr_watch_high"]:
            add_alert("respiratory", "WATCH", 20, "Respiration Rate", f"{rr} br/min", f">= {resp_std['rr_watch_high']} br/min",
                      "Mild tachypnea above resting nominal range.",
                      "Check cabin ventilation / CO2 scrubber status.")

    gap = summary.get("max_breath_gap_s")
    if gap is not None and gap >= resp_std["apnea_pause_sec"]:
        add_alert("respiratory", "WARNING", 20, "Breath Pause", f"{gap} s", f">= {resp_std['apnea_pause_sec']} s",
                  "Prolonged respiratory pause (>=10 s).",
                  "Check for central/obstructive apnea or signal artifact.")

    if cabin_ppco2_mmhg is not None and cabin_ppco2_mmhg > 3.0 and (
        (rr is not None and rr >= 20.0) or (hr is not None and hr >= 90.0)
    ):
        add_alert("respiratory", "CRITICAL", 30, "Hypercapnic Cardiopulmonary Link",
                  f"ppCO2={cabin_ppco2_mmhg} mmHg, RR={rr}, HR={hr}", "ppCO2 <= 3.0 mmHg",
                  "Tachypnea/tachycardia co-occurring with elevated cabin CO2 (NASA-STD-3001 breach).",
                  "Trigger CDRA CO2 scrubber boost & log astronaut headache/PVT check.")

    weighted_risk = (
        0.30 * axis_risk["electrical"]
        + 0.25 * axis_risk["autonomic"]
        + 0.25 * axis_risk["respiratory"]
        + 0.20 * axis_risk["hemodynamic"]
    )
    max_axis = max(axis_risk.values())
    pre_event_risk = round(float(min(100.0, max(weighted_risk, 0.70 * max_axis))), 1)
    cardio_score = max(0, min(100, round(100.0 - pre_event_risk)))

    severities = {a["severity"] for a in alerts}
    if "CRITICAL" in severities or cardio_score < 50:
        status = "CRITICAL"
    elif "WARNING" in severities or cardio_score < 70:
        status = "WARNING"
    elif "WATCH" in severities or cardio_score < 85:
        status = "WATCH"
    else:
        status = "NOMINAL"

    return {
        "axis_risk": {k: round(v, 1) for k, v in axis_risk.items()},
        "pre_event_risk_score": pre_event_risk,
        "cardio_score": cardio_score,
        "status": status,
        "early_warning_signals": alerts,
    }


def _analyze_slice(
    sig_slice: pd.DataFrame,
    num_slice: Optional[pd.DataFrame],
    lead_name: str,
    fs_hz: float,
    atmosphere_profile: str,
    cuff_sbp_baseline: float,
    baseline_pat_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """Run full multimodal DSP feature extraction on a continuous time slice."""
    ecg = sig_slice[lead_name].to_numpy(dtype=float)
    pleth = sig_slice["PLETH"].to_numpy(dtype=float)
    resp = sig_slice["RESP"].to_numpy(dtype=float) if "RESP" in sig_slice.columns else None

    r_peaks = detect_ecg_r_peaks(ecg, fs_hz)
    rr_info = classify_rr_and_ectopy(r_peaks, fs_hz)
    hrv = compute_hrv_metrics(rr_info["nn_ms"], rr_info["nn_times_s"])
    repol = compute_repolarization_and_morphology(ecg, r_peaks, fs_hz)
    hemo = compute_ppg_and_hemodynamics(
        pleth,
        r_peaks,
        hrv["mean_hr_bpm"],
        fs_hz,
        cuff_sbp_baseline=cuff_sbp_baseline,
        baseline_pat_ms=baseline_pat_ms,
    )
    resp_spo2 = compute_respiration_and_spo2(resp, ecg, r_peaks, num_slice, fs_hz, atmosphere_profile)

    pdef_candidates = [v for v in (hemo["pulse_deficit_bpm"], resp_spo2["ref_pulse_deficit_bpm"]) if v is not None]
    eff_pdef = round(max(pdef_candidates), 1) if pdef_candidates else None

    return {
        "lead_used": lead_name,
        "total_beats": rr_info["total_beats"],
        "ectopic_count": rr_info["ectopic_count"],
        "ectopy_burden_pct": rr_info["ectopy_burden_pct"],
        **hrv,
        **repol,
        **hemo,
        "effective_pulse_deficit_bpm": eff_pdef,
        **resp_spo2,
    }


def analyze_vitals_stream(
    record_id: str = "ptt_s3_sit",
    atmosphere_profile: str = "iss_nominal",
    window_sec: float = 60.0,
    step_sec: float = 30.0,
    cabin_ppco2_mmhg: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Analyze a continuous Bio-Monitor/Astroskin proxy stream and track rolling
    pre-event warning trajectories against personal baseline & NASA standards.
    """
    loaded = load_physionet_record(record_id)
    sig_df: pd.DataFrame = loaded["sig_df"]
    num_df: Optional[pd.DataFrame] = loaded["num_df"]
    fs_hz: float = loaded["fs_hz"]
    cuff_sbp: float = loaded["cuff_sbp_baseline"]

    meta = PHYSIONET_RECORDS[record_id]
    lead_name, _ = _select_best_ecg_lead(sig_df, fs_hz)

    duration_s = float(sig_df["Time [s]"].iloc[-1] - sig_df["Time [s]"].iloc[0])
    win_samples = int(round(window_sec * fs_hz))
    step_samples = max(1, int(round(step_sec * fs_hz)))

    # First pass on window 0 to anchor personal baseline PAT
    first_end = min(len(sig_df), win_samples)
    num_win0 = (
        num_df[(num_df["Time [s]"] >= 0.0) & (num_df["Time [s]"] <= float(sig_df["Time [s]"].iloc[first_end - 1]))]
        if num_df is not None
        else None
    )
    baseline_slice = _analyze_slice(
        sig_df.iloc[:first_end], num_win0, lead_name, fs_hz, atmosphere_profile, cuff_sbp, baseline_pat_ms=None
    )
    baseline_pat = baseline_slice.get("pat_ms")

    windows_raw: List[Dict[str, Any]] = []
    n_total = len(sig_df)
    for start_idx in range(0, max(1, n_total - win_samples + 1), step_samples):
        end_idx = min(n_total, start_idx + win_samples)
        if (end_idx - start_idx) < int(30 * fs_hz):
            continue
        t_start = float(sig_df["Time [s]"].iloc[start_idx])
        t_end = float(sig_df["Time [s]"].iloc[end_idx - 1])
        sig_win = sig_df.iloc[start_idx:end_idx]
        num_win = num_df[(num_df["Time [s]"] >= t_start) & (num_df["Time [s]"] <= t_end)] if num_df is not None else None
        metrics = _analyze_slice(
            sig_win, num_win, lead_name, fs_hz, atmosphere_profile, cuff_sbp, baseline_pat_ms=baseline_pat
        )
        windows_raw.append({"t_start_s": round(t_start, 1), "t_end_s": round(t_end, 1), **metrics})

    full_metrics = _analyze_slice(
        sig_df, num_df, lead_name, fs_hz, atmosphere_profile, cuff_sbp, baseline_pat_ms=baseline_pat
    )
    full_metrics["skin_temp_c"] = loaded["skin_temp_c"]
    full_metrics["accel_rms_g"] = loaded["accel_rms_g"]

    window_trajectory: List[Dict[str, Any]] = []
    for w in windows_raw:
        ev = _evaluate_early_warnings(w, baseline_slice, atmosphere_profile, cabin_ppco2_mmhg)
        window_trajectory.append(
            {
                "t_start_s": w["t_start_s"],
                "t_end_s": w["t_end_s"],
                "mean_hr_bpm": w["mean_hr_bpm"],
                "sdnn_ms": w["sdnn_ms"],
                "rmssd_ms": w["rmssd_ms"],
                "qtcf_ms": w["qtcf_ms"],
                "pat_ms": w["pat_ms"],
                "spo2_min_pct": w["spo2_min_pct"],
                "resp_rate_bpm": w["resp_rate_bpm"],
                "pre_event_risk_score": ev["pre_event_risk_score"],
                "cardio_score": ev["cardio_score"],
                "status": ev["status"],
                "alert_count": len(ev["early_warning_signals"]),
            }
        )

    overall_eval = _evaluate_early_warnings(full_metrics, baseline_slice, atmosphere_profile, cabin_ppco2_mmhg)

    worst_window = max(window_trajectory, key=lambda x: x["pre_event_risk_score"]) if window_trajectory else None
    effective_score = overall_eval["cardio_score"]
    if worst_window and worst_window["cardio_score"] < effective_score:
        effective_score = round(0.6 * overall_eval["cardio_score"] + 0.4 * worst_window["cardio_score"])

    status = overall_eval["status"]
    if worst_window and worst_window["status"] == "CRITICAL" and status != "CRITICAL":
        status = "WARNING"

    top_alert = overall_eval["early_warning_signals"][0] if overall_eval["early_warning_signals"] else None
    primary_action = (
        top_alert["action"]
        if top_alert
        else "ECG, HRV, QTcF, PAT, respiration, and SpO2 within NASA-STD-3001 bounds."
    )
    summary_text = (
        f"HR {full_metrics['mean_hr_bpm']} bpm | SDNN {full_metrics['sdnn_ms']} ms | "
        f"RMSSD {full_metrics['rmssd_ms']} ms | QTcF {full_metrics['qtcf_ms']} ms | "
        f"SpO2 min {full_metrics['spo2_min_pct']}%"
    )

    preview_end = min(len(sig_df), int(round(15.0 * fs_hz)))
    preview_step = max(1, int(round(fs_hz / 62.5)))
    prev_df = sig_df.iloc[:preview_end:preview_step]
    ecg_prev_clean = _bandpass(sig_df[lead_name].to_numpy(dtype=float)[:preview_end], 0.5, 35.0, fs_hz)[::preview_step]
    preview_peaks = [
        round(float(pk / fs_hz), 3)
        for pk in detect_ecg_r_peaks(sig_df[lead_name].to_numpy(dtype=float)[:preview_end], fs_hz)
    ]
    resp_prev = [round(float(x), 4) for x in prev_df["RESP"].to_numpy()] if "RESP" in prev_df.columns else []

    readiness_patch = {
        "score": effective_score,
        "status": status if status != "WATCH" else "WARNING",
        "source": f"PhysioNet {record_id} ({lead_name} @ {fs_hz:.0f} Hz -> Astroskin DSP)",
        "summary": summary_text,
        "action": primary_action,
        "is_live_module": True,
    }

    return {
        "record": {
            "record_id": meta.record_id,
            "dataset": meta.dataset,
            "title": meta.title,
            "clinical_profile": meta.clinical_profile,
            "spaceflight_scenario": meta.spaceflight_scenario,
            "duration_s": round(duration_s, 1),
            "sampling_rate_hz": fs_hz,
            "target_astroskin_ecg_hz": NASA_CARDIO_VITALS_STANDARDS["hardware_reference"]["ecg_hz"],  # type: ignore[index]
            "lead_used": lead_name,
        },
        "summary_metrics": full_metrics,
        "baseline_window": {
            "sdnn_ms": baseline_slice.get("sdnn_ms"),
            "rmssd_ms": baseline_slice.get("rmssd_ms"),
            "qtcf_ms": baseline_slice.get("qtcf_ms"),
            "mean_hr_bpm": baseline_slice.get("mean_hr_bpm"),
            "pat_ms": baseline_pat,
        },
        "early_warning": {
            "cardio_score": effective_score,
            "pre_event_risk_score": round(100.0 - effective_score, 1),
            "status": status,
            "axis_risk": overall_eval["axis_risk"],
            "signals": overall_eval["early_warning_signals"],
            "worst_window": worst_window,
            "primary_action": primary_action,
        },
        "window_trajectory": window_trajectory,
        "waveform_preview": {
            "time_s": [round(float(x), 3) for x in prev_df["Time [s]"].to_numpy()],
            "ecg_clean": [round(float(x), 4) for x in ecg_prev_clean],
            "pleth": [round(float(x), 4) for x in prev_df["PLETH"].to_numpy()],
            "resp": resp_prev,
            "r_peak_times_s": preview_peaks,
        },
        "readiness_patch": readiness_patch,
    }
