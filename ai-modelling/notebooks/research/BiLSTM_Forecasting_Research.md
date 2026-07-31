# BiLSTM — Research for Potential Forecasting Features

**Stream:** AI Modelling
**Author:** RISHU KUMAR DUBE and ANDRES GOMEZ PEREZ
**Date:** 31 July 2026

---

## Purpose

This document evaluates Bidirectional Long Short-Term Memory (BiLSTM) networks as a candidate architecture for the bushfire forecasting component of FireFusion. It covers the functionality BiLSTM could provide, its strengths and weaknesses in this context, and a proposed implementation approach.

---

## 1. What BiLSTM Is

BiLSTM stands for Bidirectional Long Short-Term Memory. It is a recurrent neural network architecture designed for sequential data, where the ordering of observations carries information — a series of daily weather observations, for example.

A standard LSTM is causal: it processes a sequence in one direction, and its hidden state at any timestep depends only on the inputs that preceded it. A BiLSTM runs two independent LSTMs over the same sequence, one forward and one backward, and concatenates their hidden states at each timestep.

The result is that every timestep is represented using context from both directions, rather than from preceding timesteps alone.

### 1.1 Causality and the forecast origin

Because the backward pass consumes information from later timesteps, BiLSTM is often described as non-causal and therefore unsuitable for forecasting. This objection is worth addressing directly, since it is the most likely challenge to the approach.

The backward pass does read later timesteps, but only within data that has already been observed at the forecast origin.

To make this concrete: suppose the model receives a window of the previous seven days and predicts day eight.

- Days one to seven are all historical. Actual measurements exist for each of them.
- The backward pass allows day three to be encoded with context from days four to seven. Those timesteps are future relative to day three, but they are past relative to the forecast origin, so no unobserved information is used.
- Day eight, the prediction target, never enters the input window.

The design is therefore sound, but only because of how the windowing is constructed. It fails under three conditions:

1. The input window overlaps the target timestep.
2. The dataset is split randomly rather than chronologically, allowing the model to train on later seasons and be evaluated on earlier ones.
3. Normalisation statistics are fitted on the full dataset rather than the training partition alone.

Each of these introduces look-ahead bias, producing validation metrics that are inflated and will not survive deployment. The risk is genuine rather than theoretical, but it is entirely avoidable with disciplined data handling.

---

## 2. Potential Functionality

BiLSTM could support the following within FireFusion.

### Weather-driven risk forecasting

A sliding window of recent daily conditions — temperature, relative humidity, wind speed and direction, rainfall, drought factor and fuel indices — mapped to a risk estimate for the following day. Input tensor of shape `(window_length, n_features)`, output a scalar risk value per location.

### Automatic temporal feature learning

Bushfire risk is driven by conditions accumulating over time: consecutive dry days, a sustained heatwave, progressive fuel drying. A BiLSTM learns these dependencies from the raw sequence, reducing the amount of manual feature engineering needed to construct lag variables and rolling aggregates.

This reduces the need for engineered features but does not eliminate it. Established domain indices such as drought factor and dead fuel moisture content still tend to improve performance and should be supplied as inputs rather than left for the network to infer from first principles.

### Sensor gap-filling and imputation

Weather station records contain missing observations. Because the BiLSTM conditions on context from both directions, it is well suited to reconstructing missing values within a gap — this is the standard application of bidirectionality and the one use case where it is unambiguously the correct choice. It would benefit the Data Engineering stream regardless of what is decided about the forecasting model.

### Temporal encoder within a hybrid architecture

The BiLSTM can serve as the temporal component of a hybrid model, paired with a CNN, U-Net or ConvLSTM handling the spatial component. This is the pattern used in the published wildfire spread literature.

### Text classification for the misinformation stream

Natural language is also sequential. The same architecture can act as a baseline classifier over word embeddings for the misinformation detection workflow, allowing the team to develop one approach and apply it across two components of the project.

---

## 3. Strengths

- **Automatic representation learning over the temporal axis**, reducing dependence on hand-crafted lag features and rolling window statistics.
- **Full-window contextual encoding**, so each timestep is represented relative to the entire observed sequence rather than only its history. This helps the model identify the temporal regime — a building heatwave versus a cooling trend — rather than only the trajectory so far.
- **Mature tooling and literature.** First-class support in TensorFlow and PyTorch, and a substantial published base, which makes implementation realistic within a single trimester.
- **Precedent in wildfire research.** Bidirectional LSTM modules appear in published wildfire spread prediction models, including hybrid CNN-BiLSTM architectures evaluated on Australian fire data.
- **Native multivariate input handling.** Meteorological, terrain and fuel variables are supplied as parallel input channels without restructuring.
- **Cross-stream reusability**, covering both the forecasting and misinformation components.
- **Composable** with convolutional or attention-based modules if the project scales beyond the prototype.
- **Modest compute footprint** relative to transformer architectures — trainable on a single GPU, or on CPU at the data volumes involved here.

On the final point, BiLSTM has lower memory requirements than a transformer, but its sequential computation cannot be parallelised across timesteps, so a transformer may still converge faster in wall-clock time. The advantage lies in resource constraints rather than throughput.

---

## 4. Weaknesses

- **No spatial awareness.** A BiLSTM models temporal dependencies only. It has no representation of terrain, fuel continuity, slope, aspect, or the geographic relationship between adjacent cells. Fire spread is fundamentally a spatiotemporal process, so this is a substantive architectural limitation and the main reason the literature pairs BiLSTM with a CNN or U-Net rather than using it alone.
- **Data requirements.** Deep sequence models overfit on small datasets, and the publicly available Victorian fire record is limited. Severe fire seasons are rare events, which means the training distribution contains few examples of precisely the cases with the highest operational significance.
- **Doubled parameter count** relative to an equivalent unidirectional LSTM. Two networks are trained instead of one, increasing training time and overfitting risk on a constrained dataset.
- **Poor interpretability.** The model is effectively a black box, which is difficult to defend in a safety-critical domain where emergency decision-makers must justify their actions. Attention mechanisms or post-hoc attribution methods such as SHAP would partially mitigate this.
- **Sequential computation.** Timesteps cannot be processed in parallel, giving slower training and higher inference latency than parallel architectures.
- **Susceptibility to look-ahead bias.** The three specific failure modes are set out in Section 1.1.
- **May not outperform classical baselines.** On tabular datasets of this scale, gradient-boosted tree ensembles frequently match or exceed deep sequence models at substantially lower computational cost.
- **Spatial sampling bias in the training data.** Victorian weather station coverage is dense around Melbourne and Geelong and sparse across the northeast, where a disproportionate share of large fires occur. Any model trained on this distribution inherits that bias, and evaluation metrics computed across all stations will understate error in the under-sampled regions.

---

## 5. Implementation Approach

### 5.1 Tools

Python, with TensorFlow/Keras or PyTorch, plus pandas, NumPy and scikit-learn for preprocessing and evaluation.

### 5.2 Prediction target

The target variable must be agreed before implementation begins, as it determines the output layer, loss function, evaluation metrics and API schema.

The configuration below assumes binary classification: for a given location and day, whether fire activity occurred. If the team prefers a continuous fire danger value such as FFDI, the output layer becomes `Dense(1)` with linear activation and the loss changes to Huber, which is more robust than MSE to the extreme-value outliers characteristic of fire weather data.

### 5.3 Steps

**1. Data preparation**

Assemble daily records combining meteorological variables, fuel and drought indices, and static terrain features. Handle missing values, and apply cyclical encoding to wind direction using sine and cosine components so that 359° and 1° are represented as adjacent rather than maximally distant.

**2. Feature scaling**

Standardise continuous features. Fit the scaler on the training partition only and apply the fitted transform to validation and test partitions.

**3. Sequence windowing**

Construct fixed-length sliding windows, producing an input tensor of shape `(n_samples, window_length, n_features)` with the subsequent timestep as the target. The target must always fall outside the input window.

**4. Chronological partitioning**

Train on earlier fire seasons and evaluate on later ones. Random splitting is invalid for time-series data, as temporal autocorrelation between adjacent windows leaks information across the partition boundary.

**5. Model architecture**

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Bidirectional, LSTM, Dense, Dropout
from tensorflow.keras.metrics import AUC, Recall, Precision

model = Sequential([
    Input(shape=(window_length, n_features)),
    Bidirectional(LSTM(64)),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=[
        AUC(curve='PR', name='pr_auc'),
        Recall(name='recall'),
        Precision(name='precision')
    ]
)
```

The AUC metric is configured for the precision-recall curve rather than the default ROC curve. Under severe class imbalance, ROC-AUC is dominated by the majority class and yields an optimistic figure that conceals poor minority-class performance, making PR-AUC the appropriate measure here.

**6. Training**

Adam optimiser with an initial learning rate of 1e-3 and learning rate reduction on plateau. Early stopping on validation loss with a patience of around ten epochs. Apply class weighting, as days with fire activity are heavily outnumbered by days without. Fix and record random seeds for reproducibility.

**7. Evaluation**

Report precision, recall, F1 and PR-AUC rather than raw accuracy. Under class imbalance, a degenerate classifier predicting the majority class at every timestep achieves high accuracy while detecting nothing of operational value.

**8. Baseline comparison**

Evaluate all of the following on identical partitions using identical metrics:

1. **Persistence or climatology** — the naive forecast, either the previous day's value or the seasonal mean for that date. Computationally free, and the honest performance floor. If the model does not beat this, no other comparison is meaningful.
2. **Gradient-boosted trees** — XGBoost or LightGBM on flattened window features.
3. **Unidirectional LSTM**, matched for approximate parameter count.
4. **BiLSTM.**

---

## 6. Recommendation

BiLSTM warrants prototyping, but it should be evaluated empirically rather than assumed to be the optimal architecture.

Proposed sequence of work:

1. Establish the performance floor with a persistence or climatology baseline.
2. Establish a classical baseline using gradient-boosted trees or Random Forest.
3. Evaluate the sequence models — LSTM, GRU and BiLSTM — on identical windowed data with identical metrics.
4. Consider a hybrid architecture incorporating a spatial component, if the preceding stages demonstrate that sequence modelling adds measurable value and the schedule permits.

Independently of the above, BiLSTM should be adopted now for imputation of missing sensor observations. That application carries none of the causality concerns raised in Section 1.1 and would benefit the Data Engineering stream immediately.

The value of this work lies in producing a fair, documented comparison with limitations stated explicitly, rather than selecting an architecture and constructing a justification afterwards. If BiLSTM does not outperform the simpler baselines, that finding should be reported. A clearly evidenced negative result is a legitimate outcome for this sprint.

---

## 7. Integration Considerations

**Model output** is a risk score per location per day, attachable as a property on GeoJSON features for rendering by the Frontend stream.

**Inference cost** is a single forward pass per prediction. The complete input window must be processed in both directions before an output is produced, but at the window lengths proposed here latency remains well within dashboard refresh requirements.

**Data dependency:** generating a prediction requires the most recent N days of features to be available for every location at inference time. This constrains ETL design, storage layout and refresh scheduling, and must be agreed with the Data Engineering stream during pipeline specification.

**Scope:** this is a prototype for feasibility assessment. Any output surfaced on the dashboard requires an explicit statement that it is not an operational forecast and must not be relied upon for emergency decision-making.

---

## 8. Conclusion

BiLSTM is a credible candidate for the temporal component of bushfire risk forecasting. Its principal advantage is that it learns patterns of accumulation — sustained dry periods, progressive fuel drying, building heat — directly from sequential data, without those relationships being specified through manual feature engineering. Its principal limitation is that it models the temporal axis alone and holds no representation of spatial structure, which is central to fire behaviour.

On that basis, BiLSTM is recommended for inclusion in the modelling experiments as one candidate among several, benchmarked against a persistence baseline, a classical model, and a unidirectional sequence model. Adopting it without that comparison would not be supported by the evidence reviewed here.

**Next steps for the AI Modelling stream:**

1. Confirm the availability, spatial resolution and temporal span of Victorian fire and weather data.
2. Agree the prediction target and forecast horizon with the industry mentor. This blocks the API schema and should be resolved first.
3. Implement the persistence and classical baselines described in Section 6.
4. Determine whether an explainability component is required for the final deliverable.
5. Confirm the spatial unit of analysis — weather station, grid cell, or LGA — as all downstream design depends on it.

---

## 9. References

1. Marjani, M., Mahdianpari, M., Mohammadimanesh, F. (2024). *CNN-BiLSTM: A Novel Deep Learning Model for Near-Real-Time Daily Wildfire Spread Prediction.* Remote Sensing, 16(8), 1467.
2. Andrianarivony, H. S., Akhloufi, M. A. (2024). *Machine Learning and Deep Learning for Wildfire Spread Prediction: A Review.* Fire, 7(12), 482.
3. Hochreiter, S., Schmidhuber, J. (1997). *Long Short-Term Memory.* Neural Computation, 9(8).
4. Schuster, M., Paliwal, K. (1997). *Bidirectional Recurrent Neural Networks.* IEEE Transactions on Signal Processing, 45(11).