"""
FireFusion — Phase 7: Deep Learning Models (TensorFlow / Keras)
===============================================================
Trains four architectures:
1. LSTM
2. Transformer
3. CNN-LSTM Hybrid
4. TCN (Temporal CNN with dilated convolutions)

Each model uses:
- Static features injected as a dense context vector
- Temporal sequence (8 timesteps × 11 features) as sequential input
- Three output heads: severity (classification), area (regression), RoS (regression)

Outputs:
    models/{lstm,transformer,cnn_lstm,tcn}_best.keras
    outputs/07_models/{model}_history.png/.html
    outputs/07_models/{model}_results.json
    outputs/07_models/all_histories.png
"""

import os
import json
import time
import warnings
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from sklearn.metrics import (accuracy_score, f1_score,
                              mean_absolute_error, mean_squared_error, r2_score)
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

SPLIT_DIR  = "data/splits"
MODEL_DIR  = "models"
OUTPUT_DIR = "outputs/07_models"
os.makedirs(MODEL_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

EPOCHS     = 30
BATCH_SIZE = 64
LR         = 1e-3

print(f"TensorFlow version: {tf.__version__}")

# ── Load data ─────────────────────────────────────────────────────────────
print("Loading splits...")
X_static_train   = np.load(f"{SPLIT_DIR}/X_static_train.npy")
X_temporal_train = np.load(f"{SPLIT_DIR}/X_temporal_train.npy")
y_sev_train      = np.load(f"{SPLIT_DIR}/y_severity_train.npy")
y_area_train     = np.load(f"{SPLIT_DIR}/y_area_train.npy")
y_ros_train      = np.load(f"{SPLIT_DIR}/y_ros_train.npy")

X_static_test    = np.load(f"{SPLIT_DIR}/X_static_test.npy")
X_temporal_test  = np.load(f"{SPLIT_DIR}/X_temporal_test.npy")
y_sev_test       = np.load(f"{SPLIT_DIR}/y_severity_test.npy")
y_area_test      = np.load(f"{SPLIT_DIR}/y_area_test.npy")
y_ros_test       = np.load(f"{SPLIT_DIR}/y_ros_test.npy")

N_CLASSES    = len(np.unique(y_sev_train))
T, F_temp    = X_temporal_train.shape[1], X_temporal_train.shape[2]
F_static     = X_static_train.shape[1]

print(f"  X_static:   {X_static_train.shape}")
print(f"  X_temporal: {X_temporal_train.shape}")
print(f"  N_classes:  {N_CLASSES}   T={T}   F_temp={F_temp}   F_static={F_static}")

# ── Training helper ────────────────────────────────────────────────────────
def make_datasets(X_st, X_temp, y_sev, y_area, y_ros, shuffle=True):
    ds = tf.data.Dataset.from_tensor_slices((
        {"static": X_st.astype(np.float32),
         "temporal": X_temp.astype(np.float32)},
        {"severity": y_sev.astype(np.int32),
         "area":     y_area.astype(np.float32),
         "ros":      y_ros.astype(np.float32)}
    ))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(y_sev), seed=42)
    return ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

train_ds = make_datasets(X_static_train, X_temporal_train,
                          y_sev_train, y_area_train, y_ros_train)
test_ds  = make_datasets(X_static_test,  X_temporal_test,
                          y_sev_test,  y_area_test,  y_ros_test, shuffle=False)

def compile_and_train(model, name):
    model.compile(
        optimizer=keras.optimizers.Adam(LR),
        loss={
            "severity": keras.losses.SparseCategoricalCrossentropy(from_logits=False),
            "area":     keras.losses.MeanSquaredError(),
            "ros":      keras.losses.MeanSquaredError(),
        },
        loss_weights={"severity": 1.0, "area": 0.5, "ros": 0.5},
        metrics={
            "severity": ["accuracy"],
            "area":     [keras.metrics.MeanAbsoluteError(name="mae")],
            "ros":      [keras.metrics.MeanAbsoluteError(name="mae")],
        }
    )
    cb = [
        keras.callbacks.EarlyStopping(monitor="val_severity_accuracy",
            patience=5, restore_best_weights=True, mode="max"),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
            patience=3, min_lr=1e-6),
    ]
    t0 = time.time()
    history = model.fit(train_ds, validation_data=test_ds,
                        epochs=EPOCHS, callbacks=cb, verbose=0)
    train_time = time.time() - t0
    print(f"  Trained in {train_time:.1f}s  ({len(history.history['loss'])} epochs)")
    return history, train_time

def evaluate_model(model, name):
    t0 = time.time()
    preds = model.predict(test_ds, verbose=0)
    inf_time = time.time() - t0

    y_sev_pred  = np.argmax(preds[0], axis=1)
    y_area_pred = preds[1].flatten()
    y_ros_pred  = preds[2].flatten()

    acc  = accuracy_score(y_sev_test, y_sev_pred)
    f1   = f1_score(y_sev_test, y_sev_pred, average="weighted", zero_division=0)
    mae_area  = mean_absolute_error(y_area_test, y_area_pred)
    rmse_area = np.sqrt(mean_squared_error(y_area_test, y_area_pred))
    r2_area   = r2_score(y_area_test, y_area_pred)
    mae_ros   = mean_absolute_error(y_ros_test, y_ros_pred)
    rmse_ros  = np.sqrt(mean_squared_error(y_ros_test, y_ros_pred))
    r2_ros    = r2_score(y_ros_test, y_ros_pred)

    print(f"  Severity: Acc={acc:.4f}  F1={f1:.4f}")
    print(f"  Area:     MAE={mae_area:.4f}  RMSE={rmse_area:.4f}  R²={r2_area:.4f}")
    print(f"  RoS:      MAE={mae_ros:.4f}   RMSE={rmse_ros:.4f}   R²={r2_ros:.4f}")
    print(f"  Inference: {inf_time:.3f}s  ({inf_time/len(y_sev_test)*1000:.2f}ms/sample)")

    return {
        "severity":   {"accuracy": round(acc,4), "f1_weighted": round(f1,4)},
        "area":       {"mae": round(mae_area,4), "rmse": round(rmse_area,4), "r2": round(r2_area,4)},
        "ros":        {"mae": round(mae_ros,4),  "rmse": round(rmse_ros,4),  "r2": round(r2_ros,4)},
        "inference_time_s": round(inf_time, 4),
        "ms_per_sample": round(inf_time/len(y_sev_test)*1000, 3),
    }, y_sev_pred, y_area_pred, y_ros_pred

# ── Shared output head ──────────────────────────────────────────────────────
def output_heads(x, static_out):
    merged = layers.Concatenate()([x, static_out])
    merged = layers.Dense(64, activation="relu")(merged)
    merged = layers.Dropout(0.2)(merged)
    sev  = layers.Dense(N_CLASSES, activation="softmax", name="severity")(merged)
    area = layers.Dense(1, name="area")(merged)
    ros  = layers.Dense(1, name="ros")(merged)
    return sev, area, ros

all_results   = {}
all_histories = {}
all_preds     = {}

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 1 — LSTM
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 1: LSTM ─────────────────────────────────────")
inp_temp   = keras.Input(shape=(T, F_temp), name="temporal")
inp_static = keras.Input(shape=(F_static,), name="static")

x = layers.LSTM(64, return_sequences=True)(inp_temp)
x = layers.LSTM(32)(x)
x = layers.Dropout(0.2)(x)
static_out = layers.Dense(16, activation="relu")(inp_static)
sev, area, ros = output_heads(x, static_out)

lstm_model = Model(inputs=[inp_static, inp_temp], outputs=[sev, area, ros])
hist_lstm, t_lstm = compile_and_train(lstm_model, "LSTM")
lstm_model.save(f"{MODEL_DIR}/lstm_best.keras")
res_lstm, p_sev_lstm, p_area_lstm, p_ros_lstm = evaluate_model(lstm_model, "LSTM")
res_lstm["train_time_s"] = round(t_lstm, 2)
all_results["LSTM"]   = res_lstm
all_histories["LSTM"] = hist_lstm.history
all_preds["LSTM"]     = (p_sev_lstm, p_area_lstm, p_ros_lstm)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 2 — Transformer
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 2: Transformer ──────────────────────────────")
inp_temp   = keras.Input(shape=(T, F_temp), name="temporal")
inp_static = keras.Input(shape=(F_static,), name="static")

# Positional encoding
def positional_encoding(length, depth):
    positions = np.arange(length)[:, np.newaxis]
    dims = np.arange(depth)[np.newaxis, :]
    angles = positions / np.power(10000, (2 * (dims//2)) / np.float32(depth))
    angles[:, 0::2] = np.sin(angles[:, 0::2])
    angles[:, 1::2] = np.cos(angles[:, 1::2])
    return tf.cast(angles[np.newaxis, :, :], tf.float32)

x = layers.Dense(32)(inp_temp)
pos_enc = positional_encoding(T, 32)
x = x + pos_enc

# Multi-head attention block
attn_out = layers.MultiHeadAttention(num_heads=4, key_dim=8)(x, x)
x = layers.LayerNormalization()(x + attn_out)
ffn = layers.Dense(64, activation="relu")(x)
ffn = layers.Dense(32)(ffn)
x = layers.LayerNormalization()(x + ffn)
x = layers.GlobalAveragePooling1D()(x)
x = layers.Dropout(0.2)(x)

static_out = layers.Dense(16, activation="relu")(inp_static)
sev, area, ros = output_heads(x, static_out)

transformer_model = Model(inputs=[inp_static, inp_temp], outputs=[sev, area, ros])
hist_trans, t_trans = compile_and_train(transformer_model, "Transformer")
transformer_model.save(f"{MODEL_DIR}/transformer_best.keras")
res_trans, p_sev_trans, p_area_trans, p_ros_trans = evaluate_model(transformer_model, "Transformer")
res_trans["train_time_s"] = round(t_trans, 2)
all_results["Transformer"] = res_trans
all_histories["Transformer"] = hist_trans.history
all_preds["Transformer"] = (p_sev_trans, p_area_trans, p_ros_trans)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 3 — CNN-LSTM Hybrid
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 3: CNN-LSTM Hybrid ──────────────────────────")
inp_temp   = keras.Input(shape=(T, F_temp), name="temporal")
inp_static = keras.Input(shape=(F_static,), name="static")

x = layers.Conv1D(32, kernel_size=2, activation="relu", padding="same")(inp_temp)
x = layers.Conv1D(16, kernel_size=2, activation="relu", padding="same")(x)
x = layers.LSTM(32)(x)
x = layers.Dropout(0.2)(x)

static_out = layers.Dense(16, activation="relu")(inp_static)
sev, area, ros = output_heads(x, static_out)

cnn_lstm_model = Model(inputs=[inp_static, inp_temp], outputs=[sev, area, ros])
hist_cnn, t_cnn = compile_and_train(cnn_lstm_model, "CNN-LSTM")
cnn_lstm_model.save(f"{MODEL_DIR}/cnn_lstm_best.keras")
res_cnn, p_sev_cnn, p_area_cnn, p_ros_cnn = evaluate_model(cnn_lstm_model, "CNN-LSTM")
res_cnn["train_time_s"] = round(t_cnn, 2)
all_results["CNN-LSTM"] = res_cnn
all_histories["CNN-LSTM"] = hist_cnn.history
all_preds["CNN-LSTM"] = (p_sev_cnn, p_area_cnn, p_ros_cnn)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 4 — TCN (Temporal CNN with dilated convolutions)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 4: TCN (Dilated CNN) ────────────────────────")
inp_temp   = keras.Input(shape=(T, F_temp), name="temporal")
inp_static = keras.Input(shape=(F_static,), name="static")

x = inp_temp
for dilation in [1, 2, 4]:
    residual = x
    x = layers.Conv1D(32, kernel_size=2, dilation_rate=dilation,
                      activation="relu", padding="causal")(x)
    x = layers.LayerNormalization()(x)
    x = layers.Dropout(0.1)(x)
    # Residual projection if needed
    if residual.shape[-1] != 32:
        residual = layers.Conv1D(32, kernel_size=1)(residual)
    x = layers.Add()([x, residual])

x = layers.GlobalAveragePooling1D()(x)
x = layers.Dropout(0.2)(x)

static_out = layers.Dense(16, activation="relu")(inp_static)
sev, area, ros = output_heads(x, static_out)

tcn_model = Model(inputs=[inp_static, inp_temp], outputs=[sev, area, ros])
hist_tcn, t_tcn = compile_and_train(tcn_model, "TCN")
tcn_model.save(f"{MODEL_DIR}/tcn_best.keras")
res_tcn, p_sev_tcn, p_area_tcn, p_ros_tcn = evaluate_model(tcn_model, "TCN")
res_tcn["train_time_s"] = round(t_tcn, 2)
all_results["TCN"] = res_tcn
all_histories["TCN"] = hist_tcn.history
all_preds["TCN"] = (p_sev_tcn, p_area_tcn, p_ros_tcn)

# ── Save all results ───────────────────────────────────────────────────────
with open(f"{OUTPUT_DIR}/all_results.json","w") as f:
    json.dump(all_results, f, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# CHART — Training histories
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating training history charts...")

COLORS = {"LSTM":"#1F77B4","Transformer":"#FF7F0E","CNN-LSTM":"#2CA02C","TCN":"#D62728"}

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("FireFusion — Training History (All Models)", fontsize=13, fontweight="bold")

metrics = [("severity_accuracy","Val Severity Accuracy"),
           ("area_mae","Val Area MAE"),
           ("ros_mae","Val RoS MAE")]

for ax, (metric, title) in zip(axes, metrics):
    for model_name, hist in all_histories.items():
        val_key = f"val_{metric}"
        if val_key in hist:
            ax.plot(hist[val_key], label=model_name,
                    color=COLORS[model_name], linewidth=2)
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Epoch")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/all_histories.png", dpi=150, bbox_inches="tight")
plt.close()

fig_hist = make_subplots(rows=1, cols=3,
    subplot_titles=["Val Severity Accuracy","Val Area MAE","Val RoS MAE"])
for i, (metric, _) in enumerate(metrics):
    for model_name, hist in all_histories.items():
        val_key = f"val_{metric}"
        if val_key in hist:
            fig_hist.add_trace(go.Scatter(
                y=hist[val_key], mode="lines", name=model_name,
                line=dict(color=COLORS[model_name]),
                showlegend=(i==0), legendgroup=model_name
            ), row=1, col=i+1)
fig_hist.update_layout(title="Training History — All Models",
    height=450, template="plotly_white")
fig_hist.write_html(f"{OUTPUT_DIR}/all_histories.html")

print(f"\nPhase 7 complete.")
print(f"Saved models → {MODEL_DIR}/")
print(f"Saved charts + results → {OUTPUT_DIR}/")
print("\n── Summary ───────────────────────────────────────────")
for name, res in all_results.items():
    print(f"  {name:<15} Acc={res['severity']['accuracy']:.4f}  "
          f"F1={res['severity']['f1_weighted']:.4f}  "
          f"Area R²={res['area']['r2']:.4f}  "
          f"Train={res['train_time_s']:.1f}s")