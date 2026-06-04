"""
Generates simulated accelerometer gait data for training and evaluation.

Gait model: 3-axis accelerometer at 50 Hz.
  acc_x = forward/backward
  acc_y = lateral (mediolateral)
  acc_z = vertical (dominant oscillation during walking)

Features extracted per 128-sample window (2.56 s):
  For each axis: mean, std, min, max, rms, zero_crossing_rate  =>  18 features total
"""

import numpy as np
import os

FS = 50           # Hz
WINDOW_SIZE = 128  # samples (~2.56 s)
STRIDE = 64        # 50% overlap


# ---------------------------------------------------------------------------
# Gait signal simulators
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
    """Asymmetric amplitude on alternating steps."""
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    # modulator oscillates between ~0.5 and ~1.5 at half the step frequency
    limp_mod = 1.0 + 0.5 * np.sign(np.sin(np.pi * step_freq * t))
    acc_z = (1.0
             + limp_mod * 0.4 * np.sin(2 * np.pi * step_freq * t)
             + 0.05 * np.random.randn(len(t)))
    acc_x = (limp_mod * 0.2 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.03 * np.random.randn(len(t)))
    acc_y = (0.3 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.03 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_shuffling_gait(duration_s=60, fs=FS, step_freq=1.4, seed=None):
    """Reduced vertical oscillation, slower cadence."""
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    acc_z = (1.0
             + 0.15 * np.sin(2 * np.pi * step_freq * t)
             + 0.05 * np.random.randn(len(t)))
    acc_x = (0.04 * np.sin(2 * np.pi * step_freq * t + np.pi / 4)
             + 0.03 * np.random.randn(len(t)))
    acc_y = (0.06 * np.sin(2 * np.pi * step_freq * t + np.pi / 2)
             + 0.03 * np.random.randn(len(t)))
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


def simulate_running_gait(duration_s=60, fs=FS, step_freq=2.8, seed=None):
    """Higher cadence and much larger amplitude."""
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
    """Irregular timing and variable amplitude."""
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(duration_s * fs)) / fs
    # Jitter the phase
    phase_noise = np.cumsum(0.3 * np.random.randn(len(t))) / fs
    phase = 2 * np.pi * 1.8 * t + phase_noise
    amp_noise = 1.0 + 0.5 * np.random.randn(len(t))
    amp_noise = np.clip(amp_noise, 0.2, 2.0)
    acc_z = amp_noise * (0.6 * np.sin(phase) + 0.2 * np.sin(2 * phase)) + 1.0
    acc_x = 0.15 * np.sin(phase + np.pi / 4) * amp_noise
    acc_y = 0.2 * np.sin(phase + np.pi / 2) * amp_noise
    return np.column_stack([acc_x, acc_y, acc_z]).astype(np.float32)


# ---------------------------------------------------------------------------
# Feature extraction  (must stay identical to GaitFeatureExtractor.kt)
# ---------------------------------------------------------------------------

def extract_features(signal, window_size=WINDOW_SIZE, stride=STRIDE):
    """
    signal : ndarray shape (N, 3) — acc_x, acc_y, acc_z in g
    returns : ndarray shape (W, 18) — one row of 18 features per window
    """
    windows = []
    for start in range(0, len(signal) - window_size + 1, stride):
        w = signal[start:start + window_size]
        feats = []
        for axis in range(3):
            col = w[:, axis]
            mean = col.mean()
            std = col.std()
            feats.append(mean)
            feats.append(std)
            feats.append(col.min())
            feats.append(col.max())
            feats.append(float(np.sqrt(np.mean(col ** 2))))
            # zero-crossing rate relative to axis mean
            centered = col - mean
            zcr = float(np.sum(np.diff(np.sign(centered)) != 0)) / window_size
            feats.append(zcr)
        windows.append(feats)
    return np.array(windows, dtype=np.float32)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)

    print("Generating training data — 100 synthetic subjects (normal gait only) ...")
    rng = np.random.default_rng(0)
    train_windows = []
    for i in range(100):
        freq = float(rng.uniform(1.7, 2.1))
        signal = simulate_normal_gait(duration_s=60, step_freq=freq, seed=i)
        train_windows.append(extract_features(signal))
    train_data = np.vstack(train_windows)
    np.save('data/train_normal.npy', train_data)
    print(f"  Saved data/train_normal.npy  shape={train_data.shape}")

    print("\nGenerating test data ...")
    test_sets = {
        'normal':   simulate_normal_gait(60, seed=999),
        'limp':     simulate_limping_gait(60, seed=999),
        'shuffle':  simulate_shuffling_gait(60, seed=999),
        'run':      simulate_running_gait(60, seed=999),
        'ataxic':   simulate_ataxic_gait(60, seed=999),
    }
    for name, sig in test_sets.items():
        feats = extract_features(sig)
        np.save(f'data/test_{name}.npy', feats)
        print(f"  Saved data/test_{name}.npy  shape={feats.shape}")

    print("\nDone.")
