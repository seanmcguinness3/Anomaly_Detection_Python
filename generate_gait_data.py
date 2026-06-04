"""
Generates simulated accelerometer gait data and extracts FFT-based features.

Preprocessing pipeline (must stay identical to GaitFeatureExtractor.kt):
  1. Z-score normalise each axis window         → scale invariance
  2. FFT magnitude spectrum                     → phase invariance
  3. Resample spectrum to align fundamental     → frequency invariance

Feature vector: 3 axes × N_OUT_BINS = 96 floats per window.
"""

import numpy as np
import os

# ── Sampling / windowing ──────────────────────────────────────────────────────
FS          = 50    # Hz
WINDOW_SIZE = 128   # samples  (~2.56 s)
STRIDE      = 64    # 50 % overlap

# ── FFT tuning constants (must match GaitFeatureExtractor.kt) ─────────────────
FUND_LO    = 2      # lowest  bin to search for fundamental
FUND_HI    = 20     # highest bin to search for fundamental
K_REF      = 5      # reference fundamental bin  (~1.95 Hz at 50 Hz / 128)
N_OUT_BINS = 32     # tuned spectrum bins per axis  (includes DC at index 0)
NUM_FEATURES = 3 * N_OUT_BINS   # 96


# ---------------------------------------------------------------------------
# Gait signal simulators  (unchanged)
# ---------------------------------------------------------------------------

def simulate_normal_gait(duration_s=60, fs=FS, step_freq=1.9, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    acc_z = (1.0
             + 0.7 * np.sin(2 * np.pi * step_freq * t)
             + 0.3 * np.sin(4 * np.pi * step_freq * t)
             + 0.05 * np.random.randn(len(t)))
    acc_x = (0.1 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.03 * np.random.randn(len(t)))
    acc_y = (0.15 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.03 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_limping_gait(duration_s=60, fs=FS, step_freq=1.7, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    limp_mod = 1.0 + 0.5 * np.sign(np.sin(np.pi * step_freq * t))
    acc_z = (1.0 + limp_mod * 0.4 * np.sin(2 * np.pi * step_freq * t)
             + 0.05 * np.random.randn(len(t)))
    acc_x = (limp_mod * 0.2 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.03 * np.random.randn(len(t)))
    acc_y = (0.3 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.03 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_shuffling_gait(duration_s=60, fs=FS, step_freq=1.4, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    acc_z = (1.0 + 0.15 * np.sin(2 * np.pi * step_freq * t)
             + 0.05 * np.random.randn(len(t)))
    acc_x = (0.04 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.03 * np.random.randn(len(t)))
    acc_y = (0.06 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.03 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_running_gait(duration_s=60, fs=FS, step_freq=2.8, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    acc_z = (2.0
             + 1.5 * np.sin(2 * np.pi * step_freq * t)
             + 0.5 * np.sin(4 * np.pi * step_freq * t)
             + 0.10 * np.random.randn(len(t)))
    acc_x = (0.30 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.05 * np.random.randn(len(t)))
    acc_y = (0.25 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.05 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_ataxic_gait(duration_s=60, fs=FS, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    phase_noise = np.cumsum(0.3 * np.random.randn(len(t))) / fs
    phase = 2 * np.pi * 1.8 * t + phase_noise
    amp = np.clip(1.0 + 0.5 * np.random.randn(len(t)), 0.2, 2.0)
    acc_z = amp * (0.6 * np.sin(phase) + 0.2 * np.sin(2 * phase)) + 1.0
    acc_x = 0.15 * np.sin(phase + np.pi / 4) * amp
    acc_y = 0.20 * np.sin(phase + np.pi / 2) * amp
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


# ---------------------------------------------------------------------------
# Core preprocessing  (must stay identical to GaitFeatureExtractor.kt)
# ---------------------------------------------------------------------------

def process_axis(col: np.ndarray) -> np.ndarray:
    """
    Process a single-axis window of length WINDOW_SIZE.

    Steps:
      1. Z-score normalise  → scale invariance
      2. rfft magnitude     → phase invariance
      3. Resample to align fundamental to K_REF  → frequency invariance

    Returns N_OUT_BINS floats.
    """
    col = col.astype(np.float64)

    # 1. Z-score normalise
    mean = col.mean()
    std  = max(col.std(), 1e-8)
    col  = (col - mean) / std

    # 2. FFT magnitude  (bins 0 .. WINDOW_SIZE/2 = 0 .. 64)
    mag = np.abs(np.fft.rfft(col))          # length 65

    # 3. Find fundamental: peak bin in [FUND_LO, FUND_HI]
    search = mag[FUND_LO:FUND_HI + 1]
    k_fund = int(np.argmax(search)) + FUND_LO

    # 4. Resample: output bin k  ←  input position k / scale
    #    scale = K_REF / k_fund  ensures  k_fund → K_REF
    scale = K_REF / k_fund
    out   = np.zeros(N_OUT_BINS, dtype=np.float32)
    for k in range(N_OUT_BINS):
        src  = k / scale
        lo   = int(src)
        hi   = lo + 1
        frac = src - lo
        lo_v = float(mag[lo]) if lo < len(mag) else 0.0
        hi_v = float(mag[hi]) if hi < len(mag) else 0.0
        out[k] = lo_v * (1.0 - frac) + hi_v * frac

    return out


def process_window(window: np.ndarray) -> np.ndarray:
    """
    window : ndarray shape (WINDOW_SIZE, 3)
    returns: ndarray shape (NUM_FEATURES,) = 96 floats
    """
    return np.concatenate([process_axis(window[:, axis]) for axis in range(3)])


def extract_features(signal: np.ndarray,
                     window_size: int = WINDOW_SIZE,
                     stride: int = STRIDE) -> np.ndarray:
    """
    Slide a window over signal (N, 3) and return feature matrix (W, NUM_FEATURES).
    """
    windows = []
    for start in range(0, len(signal) - window_size + 1, stride):
        windows.append(process_window(signal[start:start + window_size]))
    return np.array(windows, dtype=np.float32)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)

    print(f"Feature vector size: {NUM_FEATURES}  "
          f"(3 axes × {N_OUT_BINS} tuned FFT bins)")
    print(f"K_REF = {K_REF}  "
          f"(≈ {K_REF * FS / WINDOW_SIZE:.2f} Hz reference fundamental)\n")

    print("Generating training data — 100 synthetic subjects (normal gait) …")
    rng = np.random.default_rng(0)
    train_windows = []
    for i in range(100):
        freq   = float(rng.uniform(1.7, 2.1))
        signal = simulate_normal_gait(duration_s=60, step_freq=freq, seed=i)
        train_windows.append(extract_features(signal))
    train_data = np.vstack(train_windows)
    np.save('data/train_normal.npy', train_data)
    print(f"  Saved data/train_normal.npy  shape={train_data.shape}")

    print("\nGenerating test data …")
    test_sets = {
        'normal':  simulate_normal_gait(60, seed=999),
        'limp':    simulate_limping_gait(60, seed=999),
        'shuffle': simulate_shuffling_gait(60, seed=999),
        'run':     simulate_running_gait(60, seed=999),
        'ataxic':  simulate_ataxic_gait(60, seed=999),
    }
    for name, sig in test_sets.items():
        feats = extract_features(sig)
        np.save(f'data/test_{name}.npy', feats)
        print(f"  Saved data/test_{name}.npy  shape={feats.shape}")

    print("\nDone.")
