# Research: Attention Layers for Potential Bushfire Forecasting Features

**Author:** Emil Srambikudiyil Daniel  
**Project:** FireFusion – AI Modelling Stream (Bushfire Forecasting Team)  

---

# 1. Introduction

FireFusion aims to forecast bushfire behaviour using machine learning models that analyse spatial and temporal data such as satellite imagery, weather conditions, and historical fire observations. Current deep learning approaches for spatiotemporal forecasting commonly use Long Short-Term Memory (LSTM) or Convolutional Long Short-Term Memory (ConvLSTM) networks.

This research investigates whether **attention mechanisms** could improve FireFusion's forecasting performance by allowing the model to automatically focus on the most relevant information instead of treating every feature equally.

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

The outputs are combined to improve prediction quality.

---

# 4. Applications in Forecasting

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

# 5. Potential Functionality in FireFusion

Several opportunities exist for integrating attention mechanisms into FireFusion.

## 5.1 Spatial Attention

Spatial attention could help the model focus on regions where fires are actively spreading.

Potential focus areas include:

- hotspots
- fire boundaries
- dense vegetation
- high-risk terrain
- smoke movement

Benefits:

- reduces influence of irrelevant image regions
- improves feature extraction
- increases prediction accuracy

---

## 5.2 Temporal Attention

Fire behaviour depends heavily on recent environmental conditions.

Temporal attention could allow the model to prioritise:

- recent wind changes
- humidity trends
- temperature changes
- recent fire growth

rather than treating every historical observation equally.

---

## 5.3 Weather Feature Attention

Different weather variables influence bushfires differently under different conditions.

Attention mechanisms could dynamically assign importance to variables such as:

- wind speed
- wind direction
- temperature
- humidity
- rainfall
- atmospheric pressure

For example, during strong wind events, wind speed may receive higher attention than humidity.

---

## 5.4 Multi-Modal Attention

FireFusion may eventually combine multiple data sources.

Possible inputs include:

- satellite imagery
- weather forecasts
- vegetation maps
- elevation models
- fuel moisture
- historical fire records

Attention mechanisms could learn relationships between these different information sources without requiring manually engineered weighting rules.

---

# 6. Strengths

Using attention layers provides several advantages.

## Improved Feature Selection

The model automatically learns which information is most important rather than relying on manually selected features.

## Better Long-Term Dependencies

Attention helps retain useful information from earlier observations, reducing the limitations of standard recurrent networks.

## Improved Accuracy

Many recent forecasting studies report improved prediction accuracy after integrating attention modules.

## Interpretability

Attention maps provide visualisations showing which regions or features influenced predictions.

This improves transparency compared with traditional neural networks.

## Flexibility

Attention modules can often be added to existing ConvLSTM or LSTM architectures without redesigning the entire model.

---

# 7. Weaknesses

Attention mechanisms also introduce several challenges.

## Increased Computational Cost

Additional attention layers require more mathematical operations.

Training and inference become slower.

---

## Higher Memory Usage

Attention layers increase GPU memory requirements, particularly for high-resolution satellite imagery. The existing GPU allocation issue we are facing, therefore, needs to be taken into consideration.

---

## Increased Model Complexity

The model becomes more difficult to understand, debug, and optimise.

Hyperparameter tuning also becomes more challenging.

---

## Risk of Overfitting

Larger models may memorise the training data if the dataset is limited.

Regularisation and sufficient training data become increasingly important.

---

## Implementation Effort

Integrating attention into an existing ConvLSTM pipeline requires architectural modifications and additional experimentation.

---

# 8. Possible Implementation in FireFusion

A practical implementation would be to extend the current ConvLSTM architecture rather than replacing it completely.

A possible pipeline is shown below.

```
Satellite Images
        │
        ▼
Feature Extraction
        │
        ▼
ConvLSTM Layers
        │
        ▼
Spatial Attention
        │
        ▼
Temporal Attention
        │
        ▼
Prediction Layer
```

Another future architecture could incorporate multiple data sources.

```
Satellite Images
Weather Data
Vegetation Maps
Terrain Data
Historical Fire Data
        │
        ▼
Feature Fusion
        │
        ▼
Multi-Head Attention
        │
        ▼
ConvLSTM
        │
        ▼
Fire Spread Prediction
```

This staged approach would minimise disruption to the current architecture while allowing attention mechanisms to be evaluated experimentally.

---

# 9. Recommendation

Attention mechanisms appear to be a promising enhancement for FireFusion.

Among the available approaches, **spatial attention** and **temporal attention** are the most immediately applicable because bushfire forecasting depends heavily on both geographic patterns and recent environmental changes.

A recommended development strategy is:

1. Establish the current ConvLSTM model as the baseline.
2. Integrate a lightweight spatial attention module.
3. Evaluate forecasting accuracy and computational cost.
4. Add temporal attention if measurable improvements are observed.
5. Investigate multi-head attention only after validating simpler approaches.

This incremental approach reduces implementation risk while providing measurable evidence of any performance improvements.

---

# 10. Conclusion

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

6. Recent literature on attention-based spatiotemporal forecasting, remote sensing, and wildfire prediction (2022–2025).