"""
Generates waveform plots for each simulated gait type.
Saves individual PNGs used by the Word document.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
from generate_gait_data import (
    simulate_normal_gait, simulate_limping_gait,
    simulate_shuffling_gait, simulate_running_gait, simulate_ataxic_gait, FS
)

os.makedirs("plots", exist_ok=True)

DURATION = 4.0   # seconds to show per plot
N = int(DURATION * FS)
t = np.arange(N) / FS

GAIT_TYPES = [
    ("Normal Walking",   simulate_normal_gait,    "#1565C0", 42),
    ("Limping",          simulate_limping_gait,   "#E53935", 42),
    ("Shuffling",        simulate_shuffling_gait, "#FB8C00", 42),
    ("Running",          simulate_running_gait,   "#6A1B9A", 42),
    ("Ataxic",           simulate_ataxic_gait,    "#00897B", 42),
]

AXIS_LABELS = ["acc_x (forward)", "acc_y (lateral)", "acc_z (vertical)"]
AXIS_COLORS = ["#90CAF9", "#A5D6A7", "#1565C0"]

# ── Individual waveform plots (3-axis, 4 s) ──────────────────────────────────
for name, sim_fn, color, seed in GAIT_TYPES:
    if name == "Ataxic":
        signal = sim_fn(duration_s=DURATION + 1, seed=seed)[:N]
    else:
        signal = sim_fn(duration_s=DURATION + 1, seed=seed)[:N]

    fig, axes = plt.subplots(3, 1, figsize=(9, 5), sharex=True)
    fig.suptitle(name, fontsize=14, fontweight="bold", color=color, y=1.01)

    for ax_idx, (ax, label, col) in enumerate(zip(axes, AXIS_LABELS, AXIS_COLORS)):
        ax.plot(t, signal[:, ax_idx], color=col, linewidth=1.2)
        ax.set_ylabel(label, fontsize=8)
        ax.set_ylim(-2.5, 4.0)
        ax.axhline(0, color="#CCCCCC", linewidth=0.6, linestyle="--")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)

    axes[-1].set_xlabel("Time (s)", fontsize=9)
    plt.tight_layout()
    fname = name.lower().replace(" ", "_") + "_waveform.png"
    plt.savefig(f"plots/{fname}", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved plots/{fname}")

# ── Comparison overview: vertical axis only, all types on one figure ─────────
fig, axes = plt.subplots(len(GAIT_TYPES), 1, figsize=(10, 9), sharex=True)
fig.suptitle("Vertical Acceleration Comparison (acc_z)", fontsize=13, fontweight="bold")

for i, (name, sim_fn, color, seed) in enumerate(GAIT_TYPES):
    signal = sim_fn(duration_s=DURATION + 1, seed=seed)[:N]
    axes[i].plot(t, signal[:, 2], color=color, linewidth=1.4)
    axes[i].set_ylabel(name, fontsize=9, color=color, fontweight="bold")
    axes[i].set_ylim(-1.0, 4.5)
    axes[i].axhline(0, color="#DDDDDD", linewidth=0.6)
    axes[i].grid(True, alpha=0.25)
    axes[i].tick_params(labelsize=8)

axes[-1].set_xlabel("Time (s)", fontsize=10)
plt.tight_layout()
plt.savefig("plots/comparison_vertical.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved plots/comparison_vertical.png")

# ── Autoencoder architecture diagram ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")
fig.patch.set_facecolor("#FAFAFA")

layers = [
    (1.0,  "Input\n18 features",  18, "#BBDEFB", "#1565C0"),
    (3.0,  "Encoder\n12 neurons", 12, "#C8E6C9", "#2E7D32"),
    (5.0,  "Bottleneck\n6 neurons",6, "#FFE082", "#F57F17"),
    (7.0,  "Decoder\n12 neurons", 12, "#C8E6C9", "#2E7D32"),
    (9.0,  "Output\n18 features", 18, "#BBDEFB", "#1565C0"),
]

neuron_radius = 0.18
max_neurons_shown = 7

def draw_layer(ax, x, label, n, bg, fg):
    shown = min(n, max_neurons_shown)
    spacing = 4.0 / (shown + 1)
    y_start = 1.0
    positions = [y_start + (i + 1) * spacing for i in range(shown)]
    for y in positions:
        circle = plt.Circle((x, y), neuron_radius, color=bg, ec=fg, linewidth=1.5, zorder=3)
        ax.add_patch(circle)
    if n > max_neurons_shown:
        ax.text(x, y_start + (shown // 2 + 0.5) * spacing + 0.15, "⋮",
                ha="center", va="center", fontsize=14, color=fg, zorder=4)
    ax.text(x, 0.3, label, ha="center", va="center", fontsize=8.5,
            color=fg, fontweight="bold", multialignment="center")
    return positions

all_positions = []
for (x, label, n, bg, fg) in layers:
    pos = draw_layer(ax, x, label, n, bg, fg)
    all_positions.append((x, pos))

# Draw connections (sampled)
for li in range(len(all_positions) - 1):
    x1, p1 = all_positions[li]
    x2, p2 = all_positions[li + 1]
    for y1 in p1[::2]:
        for y2 in p2[::2]:
            ax.plot([x1 + neuron_radius, x2 - neuron_radius], [y1, y2],
                    color="#CCCCCC", linewidth=0.4, zorder=1, alpha=0.7)

# MSE reconstruction error label
ax.annotate("MSE reconstruction\nerror = anomaly score",
            xy=(9.0, 5.2), fontsize=9, ha="center", color="#C62828",
            bbox=dict(boxstyle="round,pad=0.3", fc="#FFEBEE", ec="#C62828"))
ax.annotate("", xy=(9.0, 4.8), xytext=(9.0, 5.0),
            arrowprops=dict(arrowstyle="->", color="#C62828"))

ax.set_title("Gait Autoencoder Architecture  (18 → 12 → 6 → 12 → 18)",
             fontsize=11, pad=12, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/autoencoder_architecture.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved plots/autoencoder_architecture.png")

print("\nAll plots saved to python/plots/")
