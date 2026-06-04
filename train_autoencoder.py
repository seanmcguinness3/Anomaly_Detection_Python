"""
Trains a dense autoencoder on normal gait feature vectors, evaluates on
anomalous gait, and exports both the TFLite model and scaler parameters.

Run after generate_gait_data.py:
    python generate_gait_data.py
    python train_autoencoder.py

Outputs (copy both to android/app/src/main/assets/):
    models/gait_autoencoder.tflite
    models/scaler_params.json
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras

NUM_FEATURES = 18   # 6 stats × 3 axes — must match GaitFeatureExtractor.kt
BOTTLENECK = 6


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def build_autoencoder(input_dim: int = NUM_FEATURES) -> keras.Model:
    inputs = keras.Input(shape=(input_dim,), name="features")
    # Encoder
    x = keras.layers.Dense(12, activation="relu", name="enc1")(inputs)
    encoded = keras.layers.Dense(BOTTLENECK, activation="relu", name="bottleneck")(x)
    # Decoder
    x = keras.layers.Dense(12, activation="relu", name="dec1")(encoded)
    decoded = keras.layers.Dense(input_dim, activation="linear", name="reconstruction")(x)

    model = keras.Model(inputs, decoded, name="gait_autoencoder")
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs("models", exist_ok=True)

    # ---- Load & scale training data ----------------------------------------
    print("Loading training data ...")
    train_raw = np.load("data/train_normal.npy")
    print(f"  Shape: {train_raw.shape}")

    scale_mean = train_raw.mean(axis=0).astype(np.float32)
    scale_std = (train_raw.std(axis=0) + 1e-8).astype(np.float32)
    train_scaled = (train_raw - scale_mean) / scale_std

    scaler_params = {
        "mean": scale_mean.tolist(),
        "std":  scale_std.tolist(),
    }
    with open("models/scaler_params.json", "w") as f:
        json.dump(scaler_params, f, indent=2)
    print("  Scaler params saved → models/scaler_params.json")

    # ---- Train ---------------------------------------------------------------
    print("\nTraining autoencoder ...")
    model = build_autoencoder(NUM_FEATURES)
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(patience=4, factor=0.5, verbose=1),
    ]
    history = model.fit(
        train_scaled, train_scaled,
        epochs=100,
        batch_size=64,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=1,
    )

    # ---- Evaluate on test sets -----------------------------------------------
    print("\nEvaluating reconstruction errors ...")
    test_names = ["normal", "limp", "shuffle", "run", "ataxic"]
    results = {}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = ["steelblue", "tomato", "orange", "purple", "green"]

    all_errors = []
    all_labels = []

    for name, color in zip(test_names, colors):
        path = f"data/test_{name}.npy"
        if not os.path.exists(path):
            continue
        data = np.load(path)
        scaled = (data - scale_mean) / scale_std
        reconstructed = model.predict(scaled, verbose=0)
        errors = np.mean((scaled - reconstructed) ** 2, axis=1)
        results[name] = {"mean": float(errors.mean()), "std": float(errors.std())}
        print(f"  {name:10s}  mean={errors.mean():.4f}  std={errors.std():.4f}  "
              f"p95={np.percentile(errors, 95):.4f}")
        axes[0].hist(errors, bins=40, alpha=0.55, label=name, color=color)
        all_errors.extend(errors.tolist())
        all_labels.extend([name] * len(errors))

    axes[0].set_xlabel("Reconstruction Error (MSE)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Error Distribution per Gait Type")
    axes[0].legend()

    axes[1].plot(history.history["loss"], label="train")
    axes[1].plot(history.history["val_loss"], label="val")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("MSE Loss")
    axes[1].set_title("Training Curve")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("models/evaluation.png", dpi=150)
    print("\n  Evaluation plot saved → models/evaluation.png")

    # Suggest a threshold based on normal test errors
    normal_errors = np.load("data/test_normal.npy")
    normal_errors_scaled = (normal_errors - scale_mean) / scale_std
    normal_rec = model.predict(normal_errors_scaled, verbose=0)
    normal_mse = np.mean((normal_errors_scaled - normal_rec) ** 2, axis=1)
    suggested_threshold = float(normal_mse.mean() + 3 * normal_mse.std())
    print(f"\n  Suggested base threshold (mean+3σ on normal): {suggested_threshold:.4f}")
    scaler_params["suggested_threshold"] = suggested_threshold
    with open("models/scaler_params.json", "w") as f:
        json.dump(scaler_params, f, indent=2)

    # ---- Export to TFLite ----------------------------------------------------
    print("\nExporting to TFLite ...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    tflite_path = "models/gait_autoencoder.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"  TFLite model saved → {tflite_path}  ({len(tflite_model):,} bytes)")

    print("\n" + "=" * 60)
    print("NEXT STEP — copy both files to the Android assets folder:")
    print("  models/gait_autoencoder.tflite  →  android/app/src/main/assets/")
    print("  models/scaler_params.json       →  android/app/src/main/assets/")
    print("=" * 60)


if __name__ == "__main__":
    main()
