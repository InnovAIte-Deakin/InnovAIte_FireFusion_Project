# Research: Attention Layers for Potential Bushfire Forecasting Features

**Author:** Emil Srambikudiyil Daniel  
**Project:** FireFusion – AI Modelling Stream (Bushfire Forecasting Team)  

---

# 1. Introduction

This document investigates attention mechanisms with the specific goal of improving the current **FireFusion ConvLSTM** forecasting model.
Rather than providing a general survey alone, this document evaluates how attention can be integrated into the existing architecture,
identifies the most suitable mechanism for FireFusion, and proposes a practical implementation approach.

The current FireFusion model consists of two stacked ConvLSTM layers followed by dropout and a 1×1 convolution projection layer for
forecasting. This architecture is efficient and well suited to modelling spatiotemporal environmental data, but like many ConvLSTM models it may
struggle to capture long-range spatial dependencies when information must travel through recurrent hidden states.

---

# 2. What are Attention Layers?

Attention is a deep learning mechanism that enables a model to learn which parts of the input data are most important when making a prediction.

Traditional recurrent neural networks attempt to compress all previous information into a hidden state. As the input sequence becomes longer, important information can become diluted or forgotten.

Attention addresses this limitation by assigning different importance (weights) to different inputs.

Instead of asking:

> "What did I remember?"

the model asks:

> "Which previous information is most useful for making this prediction?"

For bushfire prediction, this means the model may learn that:

- recent wind direction is highly important,
- nearby active fire fronts deserve more attention,
- older weather observations contribute less,
- certain vegetation types are more significant than others.

---

# 3. Types of Attention

## 3.1 Temporal Attention

Temporal attention focuses on the most important time steps within historical data.

Example:

Instead of treating the last 24 hours equally, the model may determine that observations from the previous 2–4 hours are most relevant for predicting future fire spread.

Potential uses:

- weather history
- fire progression
- wind changes
- humidity changes

---

## 3.2 Spatial Attention

Spatial attention identifies important locations within an image.

For satellite imagery, not every pixel contributes equally.

The model may focus on:

- active fire edges
- hotspots
- dry vegetation
- steep terrain
- smoke movement

while giving less importance to unaffected regions.

---

## 3.3 Self-Attention

Self-attention allows every input element to interact with every other input element.

This mechanism forms the basis of Transformer architectures and is effective at learning long-range relationships.

---

## 3.4 Multi-Head Attention

Multi-head attention applies multiple attention mechanisms simultaneously.

Each attention head can learn different relationships, for example:

- one head focuses on weather,
- another focuses on vegetation,
- another focuses on fire boundaries.

These mechanisms remain relevant, but the remainder of this document focuses on which is most appropriate for FireFusion.

---

# 4. Existing Research

Recent work has shown that integrating attention with ConvLSTM improves wildfire prediction performance by allowing the network to model
long-range spatial relationships that standard convolution kernels may miss. In particular, the reviewer-recommended paper integrates
self-attention directly with ConvLSTM units and demonstrates improved wildfire spread prediction compared with a baseline ConvLSTM. [(*Masrur, Yu and Taylor, 2024*)](https://www.sciencedirect.com/science/article/pii/S1574954124003029)


The paper evaluates both Pairwise Self-Attention and Patchwise Self-Attention. Both outperform a standard ConvLSTM, demonstrating that
attention helps the model capture important spatial interactions during fire spread. [(*Masrur, Yu and Taylor, 2024*)](https://www.sciencedirect.com/science/article/pii/S1574954124003029)

------------------------------------------------------------------------

# 5. Applications in Forecasting

Attention mechanisms have been successfully applied in several forecasting domains.

Examples include:

- weather forecasting
- precipitation prediction
- flood forecasting
- traffic forecasting
- video prediction
- remote sensing
- wildfire prediction
- climate modelling

Many recent forecasting models combine ConvLSTM with attention modules to improve spatial and temporal feature extraction.

---

# 6. FireFusion Current Architecture

The current implementation is:

``` text
Input Weather Sequence
        │
        ▼
ConvLSTM Layer 1
        │
     Dropout
        │
        ▼
ConvLSTM Layer 2
        │
     Dropout
        │
        ▼
1×1 Convolution Projection
        │
        ▼
Forecast
```

The model processes every timestep through the first ConvLSTM, passes
the outputs through a second ConvLSTM, and finally projects the last
hidden representation into future predictions.

Strengths:

-   Simple architecture
-   Efficient inference
-   Easy to maintain

Limitations:

-   Long-range spatial interactions are compressed into the hidden
    state.
-   Important regions may receive equal importance as less informative
    regions.
-   Model interpretability is limited.

------------------------------------------------------------------------

# 7. Recommended Attention Mechanism

Based on the literature and FireFusion's current architecture,
**Self-Attention** is recommended as the first attention mechanism to
investigate.

Reasons:

-   Learns long-range spatial relationships.
-   Preserves compatibility with the existing ConvLSTM design.
-   Supported by recent wildfire forecasting literature.
    fileciteturn3file0L2-L15

Future work may also investigate combinations of spatial and temporal
attention after an initial self-attention implementation.

------------------------------------------------------------------------
``` text
                FireFusion ConvLSTM with Proposed Self-Attention

┌────────────────────────────┐
│  Input Weather Sequence    │
│ (T timesteps × H × W × C)  │
└────────────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│      ConvLSTM Layer 1       │
│  Extract low-level spatial  │
│ and temporal representations│
└─────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│        Dropout Layer       │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│      ConvLSTM Layer 2      │
│ Learn higher-level spatio- │
│ temporal feature maps      │
└────────────────────────────┘
              │
              ▼
╔════════════════════════════╗
║  Proposed Self-Attention   ║
║         Module             ║
║                            ║
║ • Re-weight important      ║
║   spatial regions          ║
║ • Capture long-range       ║
║   dependencies             ║
║ • Emphasise informative    ║
║   feature representations  ║
╚════════════════════════════╝
              │
              ▼
┌────────────────────────────┐
│   1×1 Convolution Layer    │
│ (Projection to Forecast)   │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ Predicted Fire Risk Maps   │
│      (Forecast Horizon)    │
└────────────────────────────┘
```

The highlighted self-attention module is the only additional component introduced into the existing FireFusion architecture. It operates on the learned spatiotemporal representation produced by the second ConvLSTM layer before the final projection stage. This minimises changes to the existing model while allowing the network to emphasise informative spatial and temporal features prior to prediction.

------------------------------------------------------------------------

# 9. Example Pseudocode

``` python
features = ConvLSTM1(x)
features = Dropout(features)

features = ConvLSTM2(features)

features = SelfAttention(features)

prediction = Projection(features)

return prediction
```

This pseudocode illustrates the proposed integration rather than a
production implementation.

------------------------------------------------------------------------

# 10. What Should the Attention Learn?

FireFusion should investigate attention over:

-   **Spatial locations** (important fire regions)
-   **Timesteps** (critical historical observations)
-   **Weather variables/channels** (wind, humidity, temperature, etc.)

An initial implementation should prioritise self-attention over the
learned ConvLSTM feature representation before exploring hybrid
spatial-temporal approaches.

------------------------------------------------------------------------

# 11. Implementation Considerations

Potential benefits:

-   Better modelling of long-range fire spread.
-   Improved representation of important weather patterns.
-   Increased model interpretability through attention maps.

Potential challenges:

-   Increased GPU memory usage.
-   Longer training time.
-   Additional model complexity.
-   Increased risk of overfitting on limited datasets.

Future experiments should compare:

-   Baseline ConvLSTM
-   ConvLSTM + Self-Attention

using the project's forecasting metrics together with training time,
inference time and memory usage.

------------------------------------------------------------------------

# 12. Recommendation

Based on the current FireFusion implementation and recent wildfire
forecasting research, a lightweight self-attention module inserted after
the second ConvLSTM layer and before the projection layer is recommended
as the initial implementation.

This approach requires minimal modification to the existing architecture
while addressing one of ConvLSTM's key limitations: modelling long-range
spatiotemporal dependencies. If future experiments demonstrate
measurable improvements, more advanced combinations of spatial, temporal
or channel attention can then be investigated.


------------------------------------------------------------------------

# 13. Conclusion

Attention mechanisms enable neural networks to focus on the most informative parts of their input, making them particularly suitable for complex spatiotemporal forecasting problems.

For FireFusion, attention has the potential to improve prediction accuracy by emphasising important spatial regions, recent environmental conditions, and critical weather variables.

Although attention increases computational requirements and implementation complexity, the potential gains in forecasting performance make it a worthwhile area for future experimentation.

---

# References

1. Vaswani, A., et al. (2017). [*Attention Is All You Need*](https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf). Advances in Neural Information Processing Systems (NeurIPS).

2. Shi, X., et al. (2015). [*Convolutional LSTM Network: A Machine Learning Approach for Precipitation Nowcasting*](https://proceedings.neurips.cc/paper_files/paper/2015/file/07563a3fe3bbe7e3ba84431ad9d055af-Paper.pdf). NeurIPS.

3. Bahdanau, D., Cho, K., & Bengio, Y. (2015). [*Neural Machine Translation by Jointly Learning to Align and Translate*](https://iclr.cc/archive/www/lib/exe/fetch.php%3Fmedia=iclr2015:bahdanau-iclr2015.pdf). ICLR.

4. Lin, T. Y., et al. (2017). [*Focal Loss for Dense Object Detection*](https://arxiv.org/pdf/1708.02002). IEEE ICCV.

5. Dosovitskiy, A., et al. (2021). [*An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale*](https://arxiv.org/pdf/2010.11929). ICLR.

6. Masrur et al. (2024). [*Capturing and interpreting wildfire spread dynamics: attention-based spatiotemporal models using ConvLSTM networks*](https://www.sciencedirect.com/science/article/pii/S1574954124003029). ScienceDirect.