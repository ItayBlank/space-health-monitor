"""Pure-NumPy signal processing helpers (replaces scipy.signal/interpolate for serverless size)."""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np


def bandpass_np(x: np.ndarray, lo: float, hi: float, fs: float, order: int = 3) -> np.ndarray:
    """Zero-phase Butterworth-magnitude bandpass filter via FFT."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    if n < 4 or fs <= 0:
        return arr - np.mean(arr) if n else arr
    centered = arr - np.mean(arr)
    pad = min(n - 1, max(12, int(round(fs * 2.0))))
    padded = np.pad(centered, pad, mode="reflect") if pad > 0 else centered
    m = len(padded)
    nyq = 0.5 * fs
    lo_c = max(1e-6, min(lo, nyq * 0.98))
    hi_c = max(lo_c + 1e-6, min(hi, nyq * 0.99))
    freqs = np.fft.rfftfreq(m, d=1.0 / fs)
    p = max(2, order * 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        hp = np.where(freqs > 0, (1.0 / (1.0 + (lo_c / freqs) ** p)) ** 2, 0.0)
        lp = (1.0 / (1.0 + (freqs / hi_c) ** p)) ** 2
    spec = np.fft.rfft(padded) * hp * lp
    out = np.fft.irfft(spec, n=m)
    return out[pad : pad + n] if pad > 0 else out


def notch_np(x: np.ndarray, f0: float, q: float, fs: float) -> np.ndarray:
    """Zero-phase IIR-style notch filter via FFT."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    if n < 4 or fs <= 0 or f0 <= 0 or f0 >= 0.5 * fs:
        return arr
    bw = max(f0 / max(q, 1.0), 1e-4)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    gain = 1.0 - np.exp(-0.5 * ((freqs - f0) / (0.5 * bw)) ** 2)
    return np.fft.irfft(np.fft.rfft(arr) * gain, n=n)


def hilbert_abs_np(x: np.ndarray) -> np.ndarray:
    """Magnitude of the analytic signal via FFT (equivalent to np.abs(scipy.signal.hilbert(x)))."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    if n == 0:
        return arr
    xf = np.fft.fft(arr)
    h = np.zeros(n, dtype=float)
    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1 : n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (n + 1) // 2] = 2.0
    return np.abs(np.fft.ifft(xf * h))


def find_peaks_np(
    x: np.ndarray,
    height: Optional[float] = None,
    distance: int = 1,
    prominence: Optional[float] = None,
) -> Tuple[np.ndarray, dict]:
    """Find local maxima with height, prominence, and minimum distance constraints."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    if n < 3:
        return np.array([], dtype=int), {}

    # Strict local maxima
    mid = arr[1:-1]
    idx = np.where((mid > arr[:-2]) & (mid >= arr[2:]))[0] + 1
    if len(idx) == 0:
        return np.array([], dtype=int), {}

    if height is not None:
        idx = idx[arr[idx] >= height]
    if len(idx) == 0:
        return np.array([], dtype=int), {}

    if prominence is not None and prominence > 0:
        keep = []
        win = max(int(distance) * 3, 10)
        for p in idx:
            lo = max(0, p - win)
            hi = min(n, p + win + 1)
            left_min = float(np.min(arr[lo:p])) if p > lo else float(arr[p])
            right_min = float(np.min(arr[p + 1 : hi])) if p + 1 < hi else float(arr[p])
            prom = float(arr[p]) - max(left_min, right_min)
            if prom >= prominence:
                keep.append(p)
        idx = np.array(keep, dtype=int)
        if len(idx) == 0:
            return np.array([], dtype=int), {}

    dist = max(1, int(distance))
    if dist > 1 and len(idx) > 1:
        order = np.argsort(arr[idx])[::-1]
        selected = []
        taken = np.zeros(n, dtype=bool)
        for o in order:
            p = int(idx[o])
            if not taken[p]:
                selected.append(p)
                taken[max(0, p - dist + 1) : min(n, p + dist)] = True
        idx = np.sort(np.array(selected, dtype=int))

    return idx, {}


def cubic_interp_np(x_new: np.ndarray, x_old: np.ndarray, y_old: np.ndarray) -> np.ndarray:
    """Natural cubic spline interpolation in pure NumPy (falls back to linear if <4 points)."""
    x = np.asarray(x_old, dtype=float)
    y = np.asarray(y_old, dtype=float)
    xq = np.asarray(x_new, dtype=float)
    n = len(x)
    if n < 4:
        return np.interp(xq, x, y)

    h = np.diff(x)
    if np.any(h <= 0):
        return np.interp(xq, x, y)

    # Tridiagonal system for second derivatives M
    a = np.zeros((n, n), dtype=float)
    b = np.zeros(n, dtype=float)
    a[0, 0] = 1.0
    a[-1, -1] = 1.0
    for i in range(1, n - 1):
        a[i, i - 1] = h[i - 1]
        a[i, i] = 2.0 * (h[i - 1] + h[i])
        a[i, i + 1] = h[i]
        b[i] = 6.0 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    m = np.linalg.solve(a, b)

    idx = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, n - 2)
    dx = xq - x[idx]
    hi = h[idx]
    ai = y[idx]
    bi = (y[idx + 1] - y[idx]) / hi - hi * (2.0 * m[idx] + m[idx + 1]) / 6.0
    ci = 0.5 * m[idx]
    di = (m[idx + 1] - m[idx]) / (6.0 * hi)
    return ai + dx * (bi + dx * (ci + dx * di))


def welch_np(x: np.ndarray, fs: float = 1.0, nperseg: int = 256) -> Tuple[np.ndarray, np.ndarray]:
    """Welch PSD estimate with Hann window and 50% overlap in pure NumPy."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    seg = min(int(nperseg), n)
    if seg < 4:
        return np.array([0.0]), np.array([0.0])
    step = max(1, seg // 2)
    win = np.hanning(seg)
    scale = fs * float(np.sum(win ** 2))
    freqs = np.fft.rfftfreq(seg, d=1.0 / fs)
    acc = np.zeros(len(freqs), dtype=float)
    count = 0
    for start in range(0, n - seg + 1, step):
        chunk = arr[start : start + seg] - np.mean(arr[start : start + seg])
        spec = np.fft.rfft(chunk * win)
        psd = (np.abs(spec) ** 2) / scale
        if seg % 2 == 0:
            psd[1:-1] *= 2.0
        else:
            psd[1:] *= 2.0
        acc += psd
        count += 1
    if count == 0:
        return freqs, acc
    return freqs, acc / count


def rolling_median_np(x: np.ndarray, window: int = 11, center: bool = True) -> np.ndarray:
    """Rolling median ignoring NaNs, forward/backward filled."""
    arr = np.asarray(x, dtype=float)
    n = len(arr)
    out = np.empty(n, dtype=float)
    half = window // 2 if center else window - 1
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1) if center else i + 1
        sl = arr[lo:hi]
        valid = sl[~np.isnan(sl)]
        out[i] = float(np.median(valid)) if len(valid) else np.nan
    # bfill then ffill any remaining NaNs
    for i in range(n - 2, -1, -1):
        if np.isnan(out[i]):
            out[i] = out[i + 1]
    for i in range(1, n):
        if np.isnan(out[i]):
            out[i] = out[i - 1]
    return out
