# Evaluation of BiLSTM as an Additional Layer for the Existing ConvLSTM Model

**Stream:** AI Modelling

**Author:** Rishu Kumar Dube and Andres Gomez Perez

**Date:** 31 July 2026

---

## Purpose

This document evaluates Bidirectional Long Short-Term Memory (BiLSTM) networks as a potential additional layer for the existing ConvLSTM model used in the bushfire forecasting component of FireFusion. It covers the functionality BiLSTM could provide, its strengths and weaknesses in this context, possible integration with the current architecture, and the expected benefits and trade-offs of adopting a hybrid ConvLSTM-BiLSTM approach.

---

## 1. What BiLSTM Is

BiLSTM stands for Bidirectional Long Short-Term Memory. It is a recurrent neural network architecture designed for sequential data, where the ordering of observations carries information—for example, a series of daily weather observations.

A standard LSTM is causal: it processes a sequence in one direction, and its hidden state at any timestep depends only on the inputs that preceded it. A BiLSTM runs two independent LSTMs over the same sequence, one forward and one backward, and concatenates their hidden states at each timestep.

The result is that every timestep is represented using context from both directions, rather than from preceding timesteps alone.

### 1.1 Causality and the Forecast Origin

Because the backward pass consumes information from later timesteps, BiLSTM is often described as non-causal and therefore unsuitable for forecasting. This objection is worth addressing directly, since it is the most likely challenge to the approach.

The backward pass does read later timesteps, but only within data that has already been observed at the forecast origin.

To make this concrete: suppose the model receives a window of the previous seven days and predicts day eight.

- Days one to seven are all historical. Actual measurements exist for each of them.
- The backward pass allows day three to be encoded with context from days four to seven. Those timesteps are future relative to day three, but they are past relative to the forecast origin, so no unobserved information is used.
- Day eight, the prediction target, never enters the input window.

In the hybrid architecture proposed in Section 5, the BiLSTM does not read raw observations at all. It operates over the sequence of feature representations produced by the ConvLSTM from the observed input window, so the same reasoning applies: bidirectional encoding is confined entirely to the observed window, and the forecast horizon lies outside it.

The design is therefore sound, but only because of how the windowing is constructed. It fails under three conditions:

1. The input window overlaps the target timestep.
2. The dataset is split randomly rather than chronologically, allowing the model to train on later seasons and be evaluated on earlier ones.
3. Normalisation statistics are fitted on the full dataset rather than the training partition alone.

Each of these introduces look-ahead bias, producing validation metrics that are inflated and will not survive deployment. The risk is genuine rather than theoretical, but it is entirely avoidable with disciplined data handling.

---

## 2. Potential Functionality

BiLSTM could support the following within FireFusion.

### Weather-driven Risk Forecasting

A sliding window of recent daily conditions—temperature, relative humidity, wind speed and direction, rainfall, drought factor and fuel indices—mapped to a risk estimate for the following day.

**Input:** `(window_length, n_features)`

**Output:** scalar risk value per location.

### Automatic Temporal Feature Learning

Bushfire risk is driven by conditions accumulating over time: consecutive dry days, a sustained heatwave, progressive fuel drying. A BiLSTM learns these dependencies from the raw sequence, reducing the amount of manual feature engineering needed to construct lag variables and rolling aggregates.

This reduces the need for engineered features but does not eliminate it. Established domain indices such as drought factor and dead fuel moisture content still tend to improve performance and should be supplied as inputs rather than left for the network to infer from first principles.

### Sensor Gap-filling and Imputation

Weather station records contain missing observations. Because the BiLSTM conditions on context from both directions, it is well suited to reconstructing missing values within a gap. This is the standard application of bidirectionality and the one use case where it is unambiguously the correct choice rather than merely defensible. It is also independent of the architectural question addressed in Section 5, and would support the Data Engineering pipeline regardless of the outcome of that evaluation.

### Temporal Encoder Within a Hybrid Architecture

The BiLSTM can serve as the temporal component of a hybrid model, paired with a CNN, U-Net or ConvLSTM handling the spatial component. This is the pattern used in the published wildfire spread literature and the basis of the proposal developed in Section 5.

---

## 3. Strengths

- **Automatic representation learning over the temporal axis**, reducing dependence on hand-crafted lag features and rolling window statistics.
- **Full-window contextual encoding**, allowing each timestep to be represented relative to the entire observed sequence.
- **Mature tooling and literature**, with first-class support in TensorFlow and PyTorch.
- **Precedent in wildfire research**, including hybrid CNN-BiLSTM architectures.
- **Native multivariate input handling.**
- **Composable** with convolutional or attention-based modules.
- **Modest compute footprint** relative to transformer architectures.

On the final point, BiLSTM has lower memory requirements than a transformer, but its sequential computation cannot be parallelised across timesteps, so a transformer may still converge faster in wall-clock time.

---

## 4. Weaknesses

- **No spatial awareness.** A BiLSTM only models time. It has no concept of terrain, fuel continuity or where one location sits relative to another, which is why it works alongside the ConvLSTM rather than in place of it.
- **Data requirements.** Deep sequence models overfit on small datasets, and the Victorian fire record is limited. Severe seasons are rare, so there are few examples of the cases that matter most.
- **Doubled parameter count.** Two networks are trained instead of one, so training is slower and overfitting is more likely.
- **Poor interpretability.** The model cannot explain its predictions, which is a problem when emergency decision-makers have to justify their actions. Attention layers or SHAP would partly address this.
- **Sequential computation.** Timesteps must be processed in order, so training and inference are both slower than parallel architectures.
- **Susceptibility to look-ahead bias.** If the windowing or the data split is set up incorrectly, results look strong but are invalid. The three failure modes are listed in Section 1.1.
- **May not outperform classical baselines.** On datasets of this size, gradient-boosted trees often match deep models at a fraction of the cost.
- **Spatial sampling bias in the training data.** Victorian weather stations are dense around Melbourne and Geelong and sparse in the northeast, where many large fires occur. The model inherits that bias, and overall metrics will hide poor performance in under-sampled regions.

---

## 5. Evaluation of BiLSTM Integration into the Existing ConvLSTM Model

### 5.1 Current FireFusion ConvLSTM Architecture

The existing forecasting model uses a ConvLSTM, which replaces the matrix multiplications inside a standard LSTM cell with convolution operations. This allows the cell to maintain a spatial hidden state, so spatial and temporal dependencies are learned jointly rather than in separate stages.

The implementation takes an input tensor of shape `(batch, timesteps, height, width, channels)`, where the spatial dimensions correspond to the gridded study area and the channels carry the stacked input variables—meteorological drivers, terrain features and fuel indices. One or more ConvLSTM layers extract spatiotemporal features, followed by a convolutional or dense head producing the forecast output.

The architecture is well suited to modelling how fire risk propagates across neighbouring cells. Its temporal modelling, however, is causal and single-pass: each timestep is encoded using only the timesteps preceding it, and the representation of an early day in the window is never revised in light of how the sequence developed afterwards.

### 5.2 Potential Contribution of BiLSTM

The limitation identified above is where a BiLSTM could contribute.

The ConvLSTM produces a sequence of spatiotemporal feature representations, one per input timestep. Under the current design, the output head consumes only the final timestep or a simple aggregation across them. A BiLSTM placed after the ConvLSTM would instead process that full sequence in both directions before the forecast is produced.

Three specific contributions follow:

**Sequence-level context.** Each encoded timestep is interpreted relative to the whole observed window rather than only what preceded it, which helps distinguish a risk profile that is building from one that is subsiding.

**Refinement of early-window representations.** In a causal encoder, features extracted from the first timestep are fixed at the moment they are computed. The backward pass allows them to be re-encoded with knowledge of how the remainder of the window developed, which is relevant when fire weather builds progressively across several days.

**A dedicated temporal stage.** The ConvLSTM currently carries both the spatial and the temporal load. Separating these concerns gives each component a narrower task and allows temporal depth to be tuned without altering the spatial configuration.

These are hypotheses rather than established results, and form the basis for the evaluation proposed in Section 6.

### 5.3 Proposed ConvLSTM-BiLSTM Architecture

A potential integration strategy is to preserve the existing ConvLSTM architecture as the primary spatiotemporal feature extractor and introduce a BiLSTM layer after the ConvLSTM output.

#### Proposed Architecture

```text
Input  (batch, timesteps, height, width, channels)
   │
   ▼
ConvLSTM  (return_sequences=True)
   │
   ▼
Spatial reduction
   │
   ▼
BiLSTM  (batch, timesteps, features)
   │
   ▼
Dense head
   │
   ▼
Output
```

The `return_sequences=True` setting on the ConvLSTM is required. Without it, only the final timestep is passed forward and the BiLSTM receives no sequence to process.

#### Spatial Reduction

The ConvLSTM returns feature maps retaining height and width dimensions, whereas a BiLSTM expects a sequence of shape `(timesteps, features)`. An intermediate layer must therefore collapse the spatial axes. The choice determines how much spatial structure is carried into the temporal stage:

| Option | Effect | Consideration |
|---------|--------|---------------|
| `TimeDistributed(GlobalAveragePooling2D())` | Averages each feature map to one value per channel | Simplest; discards spatial detail |
| `TimeDistributed(Flatten())` | Retains all spatial detail | Feature dimension becomes very large; high overfitting risk |
| `TimeDistributed(Conv2D + Pooling)` | Learned reduction | Balanced, but adds parameters |

Global average pooling is proposed as the initial configuration, as it carries the lowest overfitting risk on a dataset of this size. The learned reduction is the natural subsequent variant should initial results prove favourable.

A minimal implementation:

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Input, ConvLSTM2D, BatchNormalization, TimeDistributed,
    GlobalAveragePooling2D, Bidirectional, LSTM, Dropout, Dense
)

model = Sequential([
    Input(shape=(timesteps, height, width, channels)),

    ConvLSTM2D(filters=32, kernel_size=(3, 3),
               padding='same', return_sequences=True),
    BatchNormalization(),

    TimeDistributed(GlobalAveragePooling2D()),

    Bidirectional(LSTM(64)),
    Dropout(0.3),

    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])
```

### 5.4 Expected Benefits and Trade-offs

| Aspect | Current ConvLSTM | Proposed ConvLSTM + BiLSTM |
|---------|------------------|----------------------------|
| Spatial feature learning | Strong | Strong |
| Temporal feature learning | Good | Potentially improved through bidirectional sequence modelling |
| Model complexity | Lower | Higher |
| Training time | Lower | Higher |
| Inference cost | Lower | Higher |
| Memory requirements | Lower | Higher |
| Overfitting risk | Lower | Higher, given the limited dataset |
| Forecasting performance | Baseline | Potential improvement (to be validated experimentally) |

Based on the current literature, integrating a BiLSTM layer appears technically promising; however, the available evidence is not sufficient to justify replacing the existing ConvLSTM model without experimental validation using the FireFusion dataset and benchmarking against the current baseline.

The additional model capacity is the principal risk. The proposed hybrid introduces a substantial number of parameters into a model already training on a limited record of Victorian fire seasons, so any improvement in validation performance must be assessed against the possibility that the model is fitting the training distribution more closely rather than generalising better.

---

## 6. Implementation Approach

### 6.1 Development Tools

Python 3.10 or later with TensorFlow/Keras, matching the framework used by the existing ConvLSTM implementation so that both models share the same data pipeline and training harness. Supporting libraries: pandas and NumPy for data handling, scikit-learn for metrics and preprocessing, and matplotlib for results visualisation.

Experiment tracking should record, for every run, the training and evaluation window, the feature set, all hyperparameters, the random seed and the resulting metrics. Without this the comparison in Section 6.3 cannot be substantiated.

Development follows the project version control guidelines, on a task branch created from `developer` and merged by pull request after review.

### 6.2 Evaluation Strategy

The comparison must be controlled. All models are trained on identical data partitions, with identical preprocessing, identical random seeds and identical evaluation metrics. The only variable is the temporal stage under test.

**Data preparation and partitioning.** Reuse the existing ConvLSTM pipeline without modification. Confirm that it applies chronological partitioning—training on earlier fire seasons, evaluating on later ones—since random splitting allows temporal autocorrelation between adjacent windows to leak information across the partition boundary. Normalisation statistics must be fitted on the training partition only.

**Training configuration.** Adam optimiser at an initial learning rate of 1e-3 with reduction on plateau, early stopping on validation loss with a patience of approximately ten epochs, and class weighting applied, as days with fire activity are heavily outnumbered by days without.

**Metrics.** Report precision, recall, F1 and PR-AUC rather than raw accuracy. Under this degree of class imbalance a model predicting the majority class at every timestep achieves high accuracy while detecting nothing of operational value. PR-AUC is preferred to ROC-AUC because ROC-AUC is dominated by the majority class and yields an optimistic figure that conceals poor minority-class performance. For spatial outputs, also report IoU against observed burn extents.

**Repeated runs.** Each architecture is trained across multiple random seeds and results reported as mean and standard deviation. On a dataset of this size, run-to-run variance may exceed the difference between architectures, and a single training run per model would not support a conclusion either way.

**Computational measurements.** Record training time to convergence, inference latency per prediction, peak memory usage and total parameter count for each model. The trade-offs summarised in Section 5.4 are only meaningful once measured rather than assumed.

### 6.3 Proposed Evaluation Steps

1. Review the existing ConvLSTM implementation and document its current configuration.
2. Establish the baseline by retraining the current ConvLSTM on the agreed partitions and recording its metrics.
3. Add a persistence or climatology reference—the previous timestep's value, or the seasonal mean for the corresponding date—to establish the performance floor.
4. Implement the ConvLSTM-BiLSTM hybrid described in Section 5.3, using global average pooling as the spatial reduction step.
5. Implement a ConvLSTM with a unidirectional LSTM as a control, so that any improvement can be attributed to bidirectionality rather than to the addition of a temporal stage.
6. Train all models on identical data, seeds and configuration, repeated across multiple seeds.
7. Compare forecasting performance using the metrics defined in Section 6.2.
8. Measure and compare the computational trade-offs.
9. Recommend adoption, rejection, or further work on the basis of the measured results.

A clearly evidenced negative result is a legitimate outcome. If the hybrid does not improve on the current ConvLSTM, that finding should be reported directly and the additional complexity rejected.

---

## 7. Conclusion

This research evaluated the potential integration of a BiLSTM layer into the existing ConvLSTM architecture used for bushfire forecasting in FireFusion. The literature indicates that hybrid ConvLSTM-BiLSTM models can provide richer spatiotemporal feature representations by combining ConvLSTM's ability to extract spatial and temporal patterns with BiLSTM's bidirectional sequence learning. Recent studies have reported improved prediction performance using this hybrid approach in complex spatiotemporal forecasting tasks. The integration is technically straightforward, requires no change to the existing data pipeline or output contract, and can be evaluated as a controlled comparison against the current model.

However, these benefits are accompanied by increased computational complexity, training cost and a materially higher parameter count, which raises overfitting risk on a dataset as limited as the Victorian fire record. Therefore, the proposed architecture should be considered as a potential enhancement to the current ConvLSTM model and validated experimentally using the FireFusion dataset before any deployment decision is made.

Independently of that decision, BiLSTM is recommended for imputation of missing sensor observations, as described in Section 2. That application carries none of the causality considerations discussed in Section 1.1 and would support the Data Engineering pipeline immediately.

---

## References

1. Marjani M, Mahdianpari M and Mohammadimanesh F (2024) *CNN-BiLSTM: A Novel Deep Learning Model for Near-Real-Time Daily Wildfire Spread Prediction*. Remote Sensing, 16(8), 1467.

2. Andrianarivony HS and Akhloufi MA (2024) *Machine Learning and Deep Learning for Wildfire Spread Prediction: A Review*. Fire, 7(12), 482.

3. Hochreiter S and Schmidhuber J (1997) *Long Short-Term Memory*. Neural Computation, 9(8).

4. Schuster M and Paliwal K (1997) *Bidirectional Recurrent Neural Networks*. IEEE Transactions on Signal Processing, 45(11).

5. Li W, Zhu H, Yang F, Wen C, Shi S, Zhao D, He C and Li Z (2025) *Storm-time ionospheric model over Yunnan-Sichuan area of China based on the SSA-ConvLSTM-BiLSTM algorithm*. GPS Solutions, 29:77. https://doi.org/10.1007/s10291-025-01836-6. Cited as evidence for the ConvLSTM-BiLSTM architectural pattern in spatiotemporal forecasting; the application domain is ionospheric modelling rather than wildfire, so it supports the structural approach rather than fire-specific results.
