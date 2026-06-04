"""
Trains a dense autoencoder on FFT-based gait features, then exports only the
encoder half as a TFLite model for on-device embedding extraction.

Enrolment / inference flow
──────────────────────────
  Enrolment : collect encoder embeddings for a user's normal windows
              template = vector mean of embeddings
  Inference : L2(encoder(window), template) > threshold  →  imposter

Run after generate_gait_data.py:
    python generate_gait_data.py
    python train_autoencoder.py

Outputs (copy both to android/app/src/main/assets/):
    models/gait_encoder.tflite    ← encoder only  (input: 96 features)
    models/scaler_params.json     ← feature Z-score params + suggested threshold
"""

import json, os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from generate_gait_data import NUM_FEATURES   # 96

EMBEDDING_DIM = 12   # bottleneck size


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def build_autoencoder(input_dim: int = NUM_FEATURES) -> keras.Model:
    inputs  = keras.Input(shape=(input_dim,), name="features")

    # Encoder
    x       = keras.layers.Dense(48, activation="relu",    name="enc1")(inputs)
    x       = keras.layers.Dense(24, activation="relu",    name="enc2")(x)
    encoded = keras.layers.Dense(EMBEDDING_DIM, activation="relu", name="bottleneck")(x)

    # Decoder
    x       = keras.layers.Dense(24, activation="relu",    name="dec1")(encoded)
    x       = keras.layers.Dense(48, activation="relu",    name="dec2")(x)
    decoded = keras.layers.Dense(input_dim, activation="linear", name="reconstruction")(x)

    model   = keras.Model(inputs, decoded, name="gait_autoencoder")
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return model


def build_encoder(autoencoder: keras.Model) -> keras.Model:
    """Return the encoder sub-model (input → bottleneck)."""
    return keras.Model(
        inputs  = autoencoder.input,
        outputs = autoencoder.get_layer("bottleneck").output,
        name    = "gait_encoder",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def l2_distances(embeddings: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Euclidean distance from each row of embeddings to template."""
    diff = embeddings - template[np.newaxis, :]
    return np.sqrt((diff ** 2).sum(axis=1))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs("models", exist_ok=True)

    # ── Load & normalise training data ────────────────────────────────────────
    print("Loading training data …")
    train_raw  = np.load("data/train_normal.npy")
    print(f"  Shape: {train_raw.shape}  (windows × features)")

    scale_mean = train_raw.mean(axis=0).astype(np.float32)
    scale_std  = (train_raw.std(axis=0) + 1e-8).astype(np.float32)
    train_sc   = (train_raw - scale_mean) / scale_std

    # ── Train ─────────────────────────────────────────────────────────────────
    print("\nTraining autoencoder …")
    autoencoder = build_autoencoder(NUM_FEATURES)
    autoencoder.summary()

    history = autoencoder.fit(
        train_sc, train_sc,
        epochs         = 100,
        batch_size     = 64,
        validation_split = 0.1,
        callbacks      = [
            keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(patience=4, factor=0.5, verbose=1),
        ],
        verbose = 1,
    )

    encoder = build_encoder(autoencoder)

    # ── Build enrolment template from held-out normal data ────────────────────
    print("\nBuilding enrolment template from test normal data …")
    normal_raw = np.load("data/test_normal.npy")
    normal_sc  = (normal_raw - scale_mean) / scale_std
    normal_emb = encoder.predict(normal_sc, verbose=0)

    # Use first half as "enrolment", second half as "test genuine"
    split       = len(normal_emb) // 2
    enrol_emb   = normal_emb[:split]
    test_genuine_emb = normal_emb[split:]

    template    = enrol_emb.mean(axis=0)

    enrol_dists = l2_distances(enrol_emb, template)
    suggested_threshold = float(enrol_dists.mean() + 3 * enrol_dists.std())
    print(f"  Enrolment windows : {split}")
    print(f"  Suggested threshold (mean+3σ): {suggested_threshold:.4f}")

    # ── Evaluate on all gait types ─────────────────────────────────────────────
    print("\nEvaluating L2 distances …")
    test_names = ["normal", "limp", "shuffle", "run", "ataxic"]
    colors     = ["steelblue", "tomato", "orange", "purple", "green"]
    results    = {}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for name, color in zip(test_names, colors):
        path = f"data/test_{name}.npy"
        if not os.path.exists(path):
            continue
        raw  = np.load(path)
        sc   = (raw - scale_mean) / scale_std
        emb  = encoder.predict(sc, verbose=0)
        dists = l2_distances(emb, template)
        results[name] = {"mean": float(dists.mean()), "std": float(dists.std())}
        print(f"  {name:10s}  mean={dists.mean():.4f}  std={dists.std():.4f}  "
              f"p95={np.percentile(dists, 95):.4f}")
        axes[0].hist(dists, bins=30, alpha=0.55, label=name, color=color)

    axes[0].axvline(suggested_threshold, color="red", linestyle="--",
                    linewidth=1.5, label=f"threshold={suggested_threshold:.3f}")
    axes[0].set_xlabel("L2 distance from template")
    axes[0].set_ylabel("Count")
    axes[0].set_title("L2 Distance Distribution per Gait Type")
    axes[0].legend(fontsize=8)

    axes[1].plot(history.history["loss"],     label="train")
    axes[1].plot(history.history["val_loss"], label="val")
    axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("MSE Loss")
    axes[1].set_title("Autoencoder Training Curve"); axes[1].legend()

    plt.tight_layout()
    plt.savefig("models/evaluation.png", dpi=150)
    print("  Evaluation plot → models/evaluation.png")

    # ── Save scaler params ────────────────────────────────────────────────────
    scaler_params = {
        "mean":                 scale_mean.tolist(),
        "std":                  scale_std.tolist(),
        "suggested_threshold":  suggested_threshold,
        "embedding_dim":        EMBEDDING_DIM,
        "k_ref":                5,       # must match GaitFeatureExtractor.K_REF
    }
    with open("models/scaler_params.json", "w") as f:
        json.dump(scaler_params, f, indent=2)
    print("  Scaler params    → models/scaler_params.json")

    # ── Export ENCODER to TFLite ───────────────────────────────────────────────
    print("\nExporting encoder to TFLite …")
    converter   = tf.lite.TFLiteConverter.from_keras_model(encoder)
    tflite_model = converter.convert()
    tflite_path  = "models/gait_encoder.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"  Saved {tflite_path}  ({len(tflite_model):,} bytes)")

    print("\n" + "=" * 60)
    print("NEXT STEP — copy both files to android/app/src/main/assets/:")
    print("  models/gait_encoder.tflite")
    print("  models/scaler_params.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
