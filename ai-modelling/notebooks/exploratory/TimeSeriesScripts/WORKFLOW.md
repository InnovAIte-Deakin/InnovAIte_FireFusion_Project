# FireFusion Time Series Analysis Workflow

## Overview

This directory contains an 8-phase pipeline for training and evaluating deep learning models to predict bushfire behavior (severity, area burned, and rate of spread). The workflow progresses from raw data validation through model benchmarking.

```
load_validate.py → eda.py → decomposition.py → feature_engineering.py 
                → trainsplit.py → baseline.py → dl_models.py → benchmark.py
```

---

## Phase 1: Data Loading & Validation (`load_validate.py`)

**Purpose:** Load and flatten raw GeoJSON training data into clean CSV files ready for analysis.

### Key Operations
- **Input:** `firefusion_training.geojson` (nested GeoJSON structure with multiple fire records)
- **Flattening:** Converts nested JSON objects into flat tabular format
- **Validation:** 
  - Checks for 8 expected timesteps (pre-ignition: -3 to -1, post-ignition: 0 to 3)
  - Validates 8 static terrain/fuel/fire history features
  - Validates 10 temporal weather features per timestep
  - Verifies all feature values fall within expected ranges

### Expected Features

**Static (8):** `elevation_m`, `slope_deg`, `aspect_deg`, `dist_to_water_m`, `veg_type_encoded`, `ndvi_at_ignition`, `ndwi_at_ignition`, `nbr_at_ignition`

**Temporal (10):** `max_temp_c`, `wind_speed_kmh`, `wind_dir_deg`, `rel_humidity_pct`, `precipitation_mm`, `evapotranspiration`, `soil_moisture`, `soil_temp_c`, `days_since_rain`, `years_since_last_fire`

**Targets (3):** `severity_class`, `area_ha_burned`, `rate_of_spread_ha_per_day`

### Outputs
- `data/data_flat.csv` — One row per fire record (wide format)
- `data/data_temporal.csv` — One row per timestep per fire (long format, 8× records)
- `outputs/01_validation/01_validation_report.txt` — Detailed validation summary

---

## Phase 2: Exploratory Data Analysis (`eda.py`)

**Purpose:** Understand data distributions, correlations, temporal patterns, and target label characteristics.

### Key Visualizations

1. **Distribution Plots** (12 static features)
   - Histogram distributions stratified by severity class
   - Identifies imbalanced classes and feature ranges

2. **Correlation Matrix**
   - Heatmap showing feature-to-target and feature-to-feature correlations
   - Identifies multicollinearity and highly predictive features

3. **Feature Evolution Across Timesteps**
   - Line plots showing how each feature changes over the 8-step sequence
   - Highlights temporal patterns and diurnal cycles

4. **Diurnal Patterns**
   - Separate analysis for 06:00 and 18:00 timesteps
   - Identifies time-of-day effects on weather/fire behavior

5. **Target Label Analysis**
   - Severity class distribution
   - Area burned and rate of spread histograms

### Outputs
- `outputs/02_eda/01_distributions.png/.html` — Feature distributions
- `outputs/02_eda/02_correlation_matrix.png/.html` — Correlation heatmap
- `outputs/02_eda/03_feature_evolution.png/.html` — Temporal evolution
- `outputs/02_eda/04_diurnal_patterns.png/.html` — Time-of-day patterns
- `outputs/02_eda/05_target_labels.png/.html` — Target distributions

---

## Phase 3: Temporal Decomposition & Seasonality (`decomposition.py`)

**Purpose:** Extract trend, seasonal, and residual components from the 8-step weather sequences to understand underlying patterns.

### Key Analyses

1. **STL Decomposition** (Seasonal-Trend decomposition using Loess)
   - Decomposes each feature into:
     - **Trend:** Underlying change over the 8-step sequence
     - **Seasonal (Diurnal):** Repeating patterns (06:00 vs 18:00)
     - **Residual:** Random noise/anomalies
   - Uses period=2 to capture the 06:00/18:00 cycle

2. **Autocorrelation (ACF) & Partial Autocorrelation (PACF)**
   - Measures temporal dependencies at different lags
   - Informs lag feature selection for modeling

3. **Stationarity Testing (Augmented Dickey-Fuller)**
   - Tests if each feature is stationary (constant mean/variance over time)
   - Non-stationary features may need differencing

4. **Deseasoning**
   - Removes seasonal (diurnal) component from temporal features
   - Creates a flattened, trend-only version of the data

### Outputs
- `outputs/03_decomposition/01_stl_decomposition.png/.html` — STL components
- `outputs/03_decomposition/02_acf_pacf.png/.html` — Autocorrelation plots
- `outputs/03_decomposition/03_stationarity_report.txt` — ADF test results
- `outputs/03_decomposition/04_deseasoned.png/.html` — Detrended features
- `data/data_deseasoned.csv` — Deseasoned feature data

---

## Phase 4: Feature Engineering (`feature_engineering.py`)

**Purpose:** Transform raw features into model-ready inputs with domain knowledge and statistical feature creation.

### Feature Transformations

1. **Lag Features** (per cell, per feature)
   - Lag-1, Lag-2: Previous timestep values
   - Captures temporal dependencies

2. **Delta Features** (rate of change)
   - First difference: $\Delta x_t = x_t - x_{t-1}$
   - Highlights rapid changes in conditions

3. **Rolling Statistics** (2-step window)
   - Rolling mean and standard deviation
   - Captures local smoothness and volatility

4. **FFDI Proxy Composite** (Fire Danger Index approximation)
   - Weighted combination of temperature, wind, humidity, soil moisture, and days-since-rain
   - Formula: `0.80×temp + 0.40×wind - 0.30×humidity - 20×moisture + 0.20×days_since_rain`
   - Clipped to [0, 120] range

5. **Normalization**
   - **Static features:** Z-score normalization (StandardScaler)
   - **Temporal features:** Min-Max scaling per feature per timestep
   - Ensures all features on comparable scales

6. **Log Transformation**
   - Area burned: Log1p transform to handle right-skewed distribution

### Output Data Structures

**Flat Format:**
- `data/data_engineered_flat.csv` — One row per fire with all engineered features

**Tensor Format:**
- `data/X_static.npy` — Shape (N, 8) — Normalized static features
- `data/X_temporal.npy` — Shape (N, 8, ~50+) — Engineered temporal sequences
- `data/y_severity.npy` — Shape (N,) — Severity class labels [1–5]
- `data/y_area.npy` — Shape (N,) — Log-transformed area burned
- `data/y_ros.npy` — Shape (N,) — Rate of spread

### Outputs
- `outputs/04_features/01_feature_importance_corr.png/.html` — Correlation-based importance
- `outputs/04_features/02_ffdi_distribution.png/.html` — FFDI proxy distribution
- `outputs/04_features/03_normalisation_check.png/.html` — Before/after normalization

---

## Phase 5: Train/Test/Holdout Split (`trainsplit.py`)

**Purpose:** Partition data into statistically representative train, test, and holdout sets while preserving class distributions.

### Splitting Strategy

**Stratified Split (70% / 20% / 10%)**
- Split 1: Separate holdout (10%) from train+test (90%) — stratified by severity class
- Split 2: Divide train+test into train (70%) and test (20%) — stratified by severity class

**Why Stratification?**
- Ensures all severity classes are represented in each split
- Prevents class imbalance from skewing evaluation metrics

### Class Distribution Preservation
Each split maintains the same proportion of each severity class as the full dataset.

### Outputs
- `data/splits/X_static_{train,test,holdout}.npy` — Static features
- `data/splits/X_temporal_{train,test,holdout}.npy` — Temporal sequences
- `data/splits/y_severity_{train,test,holdout}.npy` — Severity labels
- `data/splits/y_area_{train,test,holdout}.npy` — Area labels
- `data/splits/y_ros_{train,test,holdout}.npy` — RoS labels
- `data/splits/idx_{train,test,holdout}.npy` — Original indices for traceability
- `outputs/05_split/split_report.txt` — Detailed split statistics

---

## Phase 6: Baseline Models (`baseline.py`)

**Purpose:** Establish simple benchmark models to contextualize deep learning performance.

### Three Baseline Models

1. **Persistence Baseline**
   - Severity: Predicts majority class (most frequent class in training)
   - Area & RoS: Predicts median values
   - Provides absolute minimum performance threshold

2. **Logistic Regression + Ridge Regression**
   - Flattens temporal data: (N, 8, 11) → (N, 88)
   - Logistic Regression for severity classification
   - Ridge Regression for area and rate of spread
   - Linear model baseline

3. **Random Forest**
   - Ensemble of decision trees on flattened features
   - Captures non-linear relationships
   - Provides feature importance rankings
   - RandomForestClassifier for severity
   - RandomForestRegressor for area and RoS

### Evaluation Metrics

**Classification (Severity):**
- Accuracy: Overall correctness
- F1-Score (weighted): Handles class imbalance

**Regression (Area, RoS):**
- MAE: Mean Absolute Error
- RMSE: Root Mean Squared Error
- R²: Coefficient of determination

### Outputs
- `outputs/06_baseline/baseline_results.json` — All metrics as JSON
- `outputs/06_baseline/01_confusion_matrix.png/.html` — Classification confusion
- `outputs/06_baseline/02_regression_scatter.png/.html` — Predictions vs actuals
- `outputs/06_baseline/03_feature_importance.png/.html` — Random Forest importance

---

## Phase 7: Deep Learning Models (`dl_models.py`)

**Purpose:** Train state-of-the-art deep learning architectures that leverage temporal sequences and static context.

### Model Architectures

All models combine:
- **Static context:** 8 features → Dense layer → context vector
- **Temporal sequence:** 8 timesteps × ~50 features → Sequential input
- **Multi-output heads:** 3 tasks (severity, area, RoS)

#### 1. **LSTM** (Long Short-Term Memory)
- Bidirectional LSTM layers to capture long-term temporal dependencies
- Static context merged before final dense layers
- Good baseline for sequential data

#### 2. **Transformer**
- Multi-head self-attention mechanism
- Captures relationships between all timestep pairs
- Positional encoding for temporal ordering
- State-of-the-art for many sequence tasks

#### 3. **CNN-LSTM Hybrid**
- 1D Convolutions extract local temporal patterns
- LSTM layers capture long-term dependencies
- Combines strengths of both architectures

#### 4. **TCN** (Temporal Convolutional Network)
- Dilated 1D convolutions for large receptive fields
- Causal convolutions (no information leakage)
- Residual connections for training stability
- Often more efficient than RNNs

### Training Configuration
- **Epochs:** 30
- **Batch size:** 64
- **Learning rate:** 1e-3
- **Optimizer:** Adam
- **Loss weights:** Severity=1.0, Area=0.5, RoS=0.5 (prioritizes classification)

### Regularization
- Dropout layers in most architectures
- Early stopping on validation loss
- Batch normalization for faster convergence

### Outputs
- `models/{lstm,transformer,cnn_lstm,tcn}_best.keras` — Trained model weights
- `outputs/07_models/{model}_history.png/.html` — Training curves (loss & metrics)
- `outputs/07_models/{model}_results.json` — Test set metrics
- `outputs/07_models/all_histories.png` — Comparison of training curves

---

## Phase 8: Benchmarking Report (`benchmark.py`)

**Purpose:** Consolidate all model results into a comprehensive comparison and identify top performers.

### Benchmarking Metrics

Compared across all 7 models (3 baseline + 4 DL):
- **Severity Accuracy & F1-Score**
- **Area MAE, RMSE, R²**
- **RoS MAE, RMSE, R²**
- **Inference Time** (milliseconds per sample)
- **Training Time** (seconds)

### Visualizations

1. **Accuracy Comparison Bar Chart**
   - Ranked by severity classification accuracy
   - Color-coded by model type (baseline vs deep learning)

2. **Regression Performance Radar Chart**
   - Multi-metric comparison (normalized scales)
   - Easy identification of model strengths/weaknesses

3. **Inference Speed Comparison**
   - Latency vs accuracy trade-off
   - Identifies fastest models for deployment

4. **Regression Scatter Plots**
   - Predictions vs actual values for area and RoS
   - Visual assessment of prediction quality

### Outputs
- `outputs/08_benchmark/01_accuracy_comparison.png/.html` — Classification comparison
- `outputs/08_benchmark/02_regression_comparison.png/.html` — Regression performance
- `outputs/08_benchmark/03_radar_chart.html` — Multi-metric radar plot
- `outputs/08_benchmark/04_inference_speed.png/.html` — Latency analysis
- `outputs/08_benchmark/benchmark_report.txt` — Ranked summary table

---

## Data Flow Diagram

```
firefusion_training.geojson
        ↓
    [load_validate.py]
        ↓
    data_flat.csv ─────────────→ [eda.py]
    data_temporal.csv                ↓
        ↓                    EDA visualizations
    [decomposition.py]              ↓
        ↓                    data_deseasoned.csv
    STL analysis               ↓
        ↓                [feature_engineering.py]
    [feature_engineering.py]       ↓
        ↓               X_static.npy, X_temporal.npy
    Engineered features        y_severity/area/ros.npy
        ↓                      ↓
    [trainsplit.py]    Train/test/holdout indices
        ↓                      ↓
    Train/test splits     ┌─────┴─────┬──────────┐
        ↓                 ↓           ↓          ↓
    [baseline.py]   [dl_models.py] (LSTM, Transformer, CNN-LSTM, TCN)
        ↓                 ↓
    Baseline results  DL results & models
        ↓                 ↓
        └────────┬────────┘
                 ↓
            [benchmark.py]
                 ↓
         Comprehensive comparison report
```

---

## Running the Pipeline

### Sequential Execution
```bash
# From the project root
cd ai-modelling/notebooks/exploratory/TimeSeriesScripts

# Run in order
python load_validate.py
python eda.py
python decomposition.py
python feature_engineering.py
python trainsplit.py
python baseline.py
python dl_models.py
python benchmark.py
```

### Individual Script Dependencies
- **eda.py** requires: `load_validate.py`
- **decomposition.py** requires: `load_validate.py`
- **feature_engineering.py** requires: `load_validate.py`, `decomposition.py`
- **trainsplit.py** requires: `feature_engineering.py`
- **baseline.py** requires: `trainsplit.py`
- **dl_models.py** requires: `trainsplit.py`
- **benchmark.py** requires: `baseline.py`, `dl_models.py`

### Output Directory Structure
```
outputs/
├── 01_validation/          [load_validate.py]
├── 02_eda/                 [eda.py]
├── 03_decomposition/       [decomposition.py]
├── 04_features/            [feature_engineering.py]
├── 05_split/               [trainsplit.py]
├── 06_baseline/            [baseline.py]
├── 07_models/              [dl_models.py]
└── 08_benchmark/           [benchmark.py]

data/
├── data_flat.csv           [load_validate.py]
├── data_temporal.csv       [load_validate.py]
├── data_deseasoned.csv     [decomposition.py]
├── data_engineered_flat.csv [feature_engineering.py]
├── X_static.npy            [feature_engineering.py]
├── X_temporal.npy          [feature_engineering.py]
├── y_*.npy                 [feature_engineering.py]
└── splits/                 [trainsplit.py]

models/
├── lstm_best.keras         [dl_models.py]
├── transformer_best.keras  [dl_models.py]
├── cnn_lstm_best.keras     [dl_models.py]
└── tcn_best.keras          [dl_models.py]
```

---

## Key Design Decisions

1. **Stratified Splitting:** Preserves class distribution across train/test/holdout
2. **Multi-task Learning:** Single model predicts three related fire behavior metrics
3. **Static + Temporal Fusion:** Combines contextual geographic/fuel data with temporal weather sequence
4. **Normalization:** Independent scaling of static and temporal features
5. **Ensemble Baseline:** Random Forest provides both performance comparison and feature importance
6. **FFDI Composite:** Domain-inspired feature encoding fire danger principles
7. **Lag/Delta Features:** Temporal self-features capture velocity and acceleration

---

## Success Metrics

**Target Performance:**
- Severity classification: >80% accuracy (baseline: ~25% for majority class)
- Area prediction: R² >0.6 (baseline: <0.3)
- RoS prediction: R² >0.5 (baseline: <0.2)

**Model Efficiency:**
- Inference <100ms per sample
- Training <5 minutes on CPU / <1 minute on GPU

---

## Future Extensions

- **Hyperparameter tuning:** GridSearch/RandomSearch on learning rates, architectures
- **Class balancing:** SMOTE, weighted loss functions, or undersampling
- **Ensembling:** Combine best DL models with voting/stacking
- **Attention visualization:** Interpret which timesteps/features matter most
- **Geographic validation:** Holdout by region rather than random samples
- **Real-time prediction:** Deploy best model as REST API

