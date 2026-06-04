"""
Generates plots illustrating the three-stage FFT preprocessing pipeline:
  Stage 1 — raw window + Z-score normalisation (scale invariance)
  Stage 2 — FFT magnitude spectrum (phase invariance)
  Stage 3 — tuned spectrum with aligned fundamental (frequency invariance)

Also generates a side-by-side comparison of tuned spectra for all gait types,
showing that the fundamental always lands at K_REF regardless of cadence.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from generate_gait_data import (
    simulate_normal_gait, simulate_limping_gait,
    simulate_shuffling_gait, simulate_running_gait, simulate_ataxic_gait,
    FS, WINDOW_SIZE, FUND_LO, FUND_HI, K_REF, N_OUT_BINS, process_axis
)

os.makedirs("plots", exist_ok=True)

FREQ_BINS = np.arange(WINDOW_SIZE // 2 + 1) * FS / WINDOW_SIZE   # Hz per bin


def get_window(sim_fn, seed=0):
    sig = sim_fn(duration_s=4, seed=seed)
    return sig[:WINDOW_SIZE, :]


def fft_pipeline(col):
    """Return all intermediate stages for one axis column."""
    col = col.astype(np.float64)
    # Stage 1: Z-score
    mean, std = col.mean(), max(col.std(), 1e-8)
    normed = (col - mean) / std
    # Stage 2: FFT magnitude
    mag = np.abs(np.fft.rfft(normed))
    # Stage 3: find fundamental + tune
    k_fund = int(np.argmax(mag[FUND_LO:FUND_HI + 1])) + FUND_LO
    scale  = K_REF / k_fund
    tuned  = np.zeros(N_OUT_BINS)
    for k in range(N_OUT_BINS):
        src  = k / scale
        lo   = int(src); hi = lo + 1; frac = src - lo
        lo_v = float(mag[lo]) if lo < len(mag) else 0.0
        hi_v = float(mag[hi]) if hi < len(mag) else 0.0
        tuned[k] = lo_v * (1 - frac) + hi_v * frac
    return col, normed, mag, tuned, k_fund, scale


# ── Figure 1: Full pipeline for normal walking (vertical axis) ────────────────
t = np.arange(WINDOW_SIZE) / FS
w = get_window(simulate_normal_gait)
raw, normed, mag, tuned, k_fund, scale = fft_pipeline(w[:, 2])

fig = plt.figure(figsize=(13, 9))
fig.suptitle("FFT Preprocessing Pipeline  —  Normal Walking (acc_z)",
             fontsize=13, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

# (a) Raw window
ax = fig.add_subplot(gs[0, 0])
ax.plot(t, raw, color="#90CAF9", linewidth=1.2)
ax.set_title("(a)  Raw window", fontweight="bold")
ax.set_xlabel("Time (s)"); ax.set_ylabel("Acceleration (g)")
ax.grid(alpha=0.3)

# (b) Z-score normalised
ax = fig.add_subplot(gs[0, 1])
ax.plot(t, normed, color="#1565C0", linewidth=1.2)
ax.axhline(0,  color="red",  linewidth=0.8, linestyle="--", label="mean = 0")
ax.axhline(1,  color="grey", linewidth=0.6, linestyle=":", label="±1σ")
ax.axhline(-1, color="grey", linewidth=0.6, linestyle=":")
ax.set_title("(b)  Z-score normalised  (scale invariance)", fontweight="bold")
ax.set_xlabel("Time (s)"); ax.set_ylabel("Normalised amplitude")
ax.legend(fontsize=8); ax.grid(alpha=0.3)

# (c) FFT magnitude (positive freqs up to 15 Hz)
ax = fig.add_subplot(gs[1, 0])
show = FREQ_BINS <= 15
ax.plot(FREQ_BINS[show], mag[show], color="#2E7D32", linewidth=1.4)
ax.axvline(FREQ_BINS[k_fund], color="red", linewidth=1.2, linestyle="--",
           label=f"fundamental  k={k_fund}  ({FREQ_BINS[k_fund]:.2f} Hz)")
ax.set_title("(c)  FFT magnitude  (phase invariance)", fontweight="bold")
ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("|FFT|")
ax.legend(fontsize=8); ax.grid(alpha=0.3)

# (d) Tuned spectrum
ax = fig.add_subplot(gs[1, 1])
bin_idx = np.arange(N_OUT_BINS)
ax.bar(bin_idx, tuned, color="#F57F17", alpha=0.8, width=0.7)
ax.axvline(K_REF, color="red", linewidth=1.5, linestyle="--",
           label=f"K_REF = {K_REF}  (fundamental aligned here)")
for h in range(2, 7):
    ax.axvline(K_REF * h, color="red", linewidth=0.6, linestyle=":", alpha=0.5)
ax.set_title(f"(d)  Tuned spectrum  (frequency invariance)\nscale = {scale:.3f}", fontweight="bold")
ax.set_xlabel("Output bin index"); ax.set_ylabel("|FFT| (resampled)")
ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")

plt.savefig("plots/preprocessing_pipeline.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved plots/preprocessing_pipeline.png")


# ── Figure 2: Tuned spectra for all gait types — fundamental always at K_REF ──
GAIT_TYPES = [
    ("Normal",   simulate_normal_gait,    "#1565C0"),
    ("Limping",  simulate_limping_gait,   "#E53935"),
    ("Shuffling",simulate_shuffling_gait, "#FB8C00"),
    ("Running",  simulate_running_gait,   "#6A1B9A"),
    ("Ataxic",   simulate_ataxic_gait,    "#00897B"),
]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Effect of Frequency Tuning  —  Vertical Axis (acc_z)",
             fontsize=12, fontweight="bold")

for name, sim_fn, color in GAIT_TYPES:
    w   = get_window(sim_fn)
    col = w[:, 2]
    col = col.astype(np.float64)
    col = (col - col.mean()) / max(col.std(), 1e-8)
    mag = np.abs(np.fft.rfft(col))
    k_f = int(np.argmax(mag[FUND_LO:FUND_HI + 1])) + FUND_LO

    # Before tuning (raw FFT)
    show = FREQ_BINS <= 12
    axes[0].plot(FREQ_BINS[show], mag[show], color=color, linewidth=1.4,
                 label=f"{name}  (f={FREQ_BINS[k_f]:.2f} Hz)")

    # After tuning
    scale = K_REF / k_f
    tuned = np.zeros(N_OUT_BINS)
    for k in range(N_OUT_BINS):
        src  = k / scale
        lo   = int(src); hi = lo + 1; frac = src - lo
        lo_v = float(mag[lo]) if lo < len(mag) else 0.0
        hi_v = float(mag[hi]) if hi < len(mag) else 0.0
        tuned[k] = lo_v * (1 - frac) + hi_v * frac
    axes[1].plot(np.arange(N_OUT_BINS), tuned, color=color, linewidth=1.4, label=name)

axes[0].set_title("Before tuning\n(fundamentals at different frequencies)", fontweight="bold")
axes[0].set_xlabel("Frequency (Hz)"); axes[0].set_ylabel("|FFT|")
axes[0].legend(fontsize=8); axes[0].grid(alpha=0.3)

axes[1].axvline(K_REF, color="red", linewidth=1.5, linestyle="--",
                label=f"K_REF = {K_REF}  (aligned fundamental)")
for h in range(2, 7):
    axes[1].axvline(K_REF * h, color="red", linewidth=0.5, linestyle=":", alpha=0.4)
axes[1].set_title("After tuning\n(all fundamentals aligned to K_REF = 5)", fontweight="bold")
axes[1].set_xlabel("Output bin index"); axes[1].set_ylabel("|FFT| (resampled)")
axes[1].legend(fontsize=8); axes[1].grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("plots/frequency_tuning_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved plots/frequency_tuning_comparison.png")


# ── Figure 3: Updated autoencoder architecture (encoder-only export) ──────────
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.set_xlim(0, 12); ax.set_ylim(0, 6)
ax.axis("off"); fig.patch.set_facecolor("#FAFAFA")

layers = [
    (1.0,  "Input\n96 features",    96, "#BBDEFB", "#1565C0"),
    (3.0,  "Encoder\n48 neurons",   48, "#C8E6C9", "#2E7D32"),
    (5.0,  "Encoder\n24 neurons",   24, "#C8E6C9", "#2E7D32"),
    (7.0,  "Bottleneck\n12 neurons",12, "#FFE082", "#F57F17"),
    (9.0,  "Decoder\n24 neurons",   24, "#E0E0E0", "#888888"),
    (11.0, "Decoder\n48 → 96",      48, "#E0E0E0", "#888888"),
]

neuron_radius = 0.17
max_show = 7

def draw_layer(ax, x, label, n, bg, fg, greyed=False):
    shown   = min(n, max_show)
    spacing = 4.0 / (shown + 1)
    y_start = 1.0
    ys = [y_start + (i + 1) * spacing for i in range(shown)]
    for y in ys:
        alpha = 0.3 if greyed else 1.0
        circle = plt.Circle((x, y), neuron_radius, color=bg, ec=fg,
                             linewidth=1.5, zorder=3, alpha=alpha)
        ax.add_patch(circle)
    if n > max_show:
        ax.text(x, ys[len(ys) // 2] + 0.15, "⋮", ha="center", va="center",
                fontsize=13, color=fg, zorder=4, alpha=0.3 if greyed else 1.0)
    col = "#BBBBBB" if greyed else fg
    ax.text(x, 0.3, label, ha="center", va="center", fontsize=8,
            color=col, fontweight="bold", multialignment="center")
    return ys

all_pos = []
for i, (x, label, n, bg, fg) in enumerate(layers):
    greyed = (i >= 4)
    ys = draw_layer(ax, x, label, n, bg, fg, greyed=greyed)
    all_pos.append((x, ys, greyed))

for li in range(len(all_pos) - 1):
    x1, p1, g1 = all_pos[li]
    x2, p2, g2 = all_pos[li + 1]
    alpha = 0.15 if (g1 or g2) else 0.5
    for y1 in p1[::2]:
        for y2 in p2[::2]:
            ax.plot([x1 + neuron_radius, x2 - neuron_radius], [y1, y2],
                    color="#CCCCCC", linewidth=0.4, zorder=1, alpha=alpha)

# Bracket: encoder exported
ax.annotate("", xy=(7.5, 5.6), xytext=(0.4, 5.6),
            arrowprops=dict(arrowstyle="-", color="#1565C0", lw=2))
ax.text(3.9, 5.8, "exported as  gait_encoder.tflite",
        ha="center", fontsize=9, color="#1565C0", fontweight="bold")

# Bracket: decoder (training only)
ax.annotate("", xy=(11.5, 5.6), xytext=(8.5, 5.6),
            arrowprops=dict(arrowstyle="-", color="#AAAAAA", lw=2))
ax.text(10.0, 5.8, "training only  (not shipped)",
        ha="center", fontsize=9, color="#AAAAAA")

ax.set_title("Gait Autoencoder  —  96 → 48 → 24 → 12 → 24 → 48 → 96",
             fontsize=11, pad=14, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/autoencoder_architecture.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved plots/autoencoder_architecture.png  (updated)")

print("\nAll preprocessing plots saved.")
