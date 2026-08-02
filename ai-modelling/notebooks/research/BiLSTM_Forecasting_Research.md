# Evaluation of BiLSTM as an Additional Layer for the Existing ConvLSTM Model

**Stream:** AI Modelling

**Authors:** Rishu Kumar Dube and Andres Gomez Perez

**Date:** 31 July 2026

---

## Purpose

This document evaluates Bidirectional Long Short-Term Memory (BiLSTM) networks as a potential additional layer for the existing ConvLSTM model used in the bushfire forecasting component of FireFusion. It examines the potential functionality BiLSTM could provide, its strengths and weaknesses within this context, possible integration with the current architecture, and an evaluation strategy for determining whether a hybrid ConvLSTM–BiLSTM model offers measurable benefits over the existing forecasting pipeline.

---

## BiLSTM Overview

Bidirectional Long Short-Term Memory (BiLSTM) is an extension of the traditional Long Short-Term Memory (LSTM) network designed to improve sequence modelling by processing temporal data in both forward and backward directions. Unlike a conventional LSTM, which learns dependencies only from past observations, a BiLSTM combines information from both directions to produce a more comprehensive representation of temporal patterns. This enables the network to capture long-range dependencies and complex sequential relationships that may not be fully represented using a single-directional model.

BiLSTM has been successfully applied to a wide range of sequence modelling tasks, including natural language processing, speech recognition, environmental forecasting, and time-series prediction. More recently, it has been incorporated into hybrid deep learning architectures, where convolutional models extract spatial features while BiLSTM refines temporal representations. This combination has shown promising results in spatiotemporal forecasting applications by leveraging the strengths of both spatial and sequential feature learning.

For FireFusion, BiLSTM is considered as a potential enhancement rather than a replacement for the existing ConvLSTM model. The motivation is to investigate whether incorporating bidirectional temporal learning can complement ConvLSTM's spatial-temporal feature extraction, leading to a richer representation of environmental dynamics and potentially improving bushfire forecasting performance. The effectiveness of this approach, however, should be validated through experimental evaluation within the FireFusion framework.

---

## Evidence from Recent Research

Recent studies indicate that hybrid deep learning architectures are becoming increasingly effective for spatiotemporal forecasting. A comprehensive review by **Andrianarivony and Akhloufi (2024)** identifies ConvLSTM and other hybrid neural networks as among the most effective approaches for wildfire spread prediction due to their ability to capture both spatial and temporal dependencies. The review also highlights hybrid architectures as a promising direction for improving prediction accuracy and robustness in complex wildfire environments.

Within the wildfire domain, **Marjani, Mahdianpari and Mohammadimanesh (2024)** proposed a CNN–BiLSTM architecture that improved near-real-time wildfire spread prediction by effectively learning spatial features and long-term temporal dependencies from environmental data. Beyond wildfire applications, **Li et al. (2025)** demonstrated that a hybrid SSA–ConvLSTM–BiLSTM architecture enhanced forecasting performance in a complex spatiotemporal prediction task, providing further evidence that combining ConvLSTM and BiLSTM can improve temporal feature learning across different environmental forecasting domains. These findings support investigating a similar hybrid architecture within FireFusion while recognising that its effectiveness must be validated using the project's own datasets.

---

## Potential Functionality in FireFusion

Integrating BiLSTM into FireFusion has the potential to enhance the existing ConvLSTM model by improving temporal feature learning from sequential environmental data. A hybrid ConvLSTM–BiLSTM architecture could provide a richer representation of wildfire dynamics by capturing more complex temporal relationships while preserving ConvLSTM's spatial modelling capabilities. This may improve the model's ability to analyse environmental variables such as weather conditions, vegetation, and historical fire progression. Recent studies have shown that hybrid deep learning architectures can effectively model these complex spatiotemporal relationships, making BiLSTM a promising enhancement for future investigation within FireFusion.

---

## Strengths

- **Enhanced temporal learning:** BiLSTM captures sequential dependencies in both forward and backward directions, providing a richer representation of temporal patterns than a standard LSTM.

- **Complementary to ConvLSTM:** While ConvLSTM extracts spatial-temporal features, BiLSTM can further refine temporal information without replacing the existing architecture.

- **Improved modelling of environmental dynamics:** BiLSTM is well suited for learning relationships between evolving variables such as weather conditions, vegetation, and historical fire behaviour.

- **Automatic temporal representation learning:** Reduces dependence on manually engineered lag features and rolling window statistics.

- **Native multivariate sequence processing:** Multiple environmental variables can be processed simultaneously as parallel input features.

- **Flexible integration:** BiLSTM integrates naturally with convolutional architectures, making it suitable as an additional layer rather than a replacement.

- **Strong research support:** Recent studies have demonstrated promising results using hybrid ConvLSTM–BiLSTM architectures across multiple spatiotemporal forecasting applications.


## Weaknesses

- **Higher computational cost:** Adding a BiLSTM layer increases the number of model parameters, resulting in greater computational and memory requirements during training and inference.

- **Longer training time:** The additional network complexity may increase training time, particularly when working with large spatiotemporal datasets.

- **Risk of overfitting:** More complex architectures require sufficient training data and appropriate regularisation to prevent overfitting.

- **No spatial awareness:** BiLSTM models temporal dependencies only. Spatial relationships are still learned by the ConvLSTM layer.

- **Experimental validation required:** Although hybrid architectures have shown promising results in previous studies, their effectiveness within FireFusion must be validated using the project's datasets and evaluation metrics before adoption.

- **Additional implementation complexity:** Integrating an extra recurrent layer increases the overall model complexity and computational requirements.

---

## Proposed Implementation

### Current FireFusion ConvLSTM Architecture

FireFusion currently uses a ConvLSTM-based forecasting pipeline to model spatiotemporal environmental data. Sequential inputs, including weather conditions and historical fire information, are processed by the ConvLSTM model to learn both spatial and temporal relationships before generating bushfire predictions. The forecasting model is integrated with the project's API, allowing prediction results to be consumed by the Backend and Frontend components.

```text
Current FireFusion Pipeline

Environmental Data
        │
        ▼
 Data Preprocessing
        │
        ▼
    ConvLSTM
        │
        ▼
 Bushfire Prediction
        │
        ▼
     FastAPI API
        │
        ▼
 Backend / Frontend
```

### Proposed ConvLSTM–BiLSTM Architecture

The proposed architecture extends the current FireFusion forecasting pipeline by introducing a **BiLSTM layer after the ConvLSTM module**. ConvLSTM continues to learn spatial-temporal features from sequential environmental data, while the BiLSTM refines the extracted temporal representations by processing sequence information in both forward and backward directions. This hybrid architecture preserves the strengths of the existing ConvLSTM model while enhancing its ability to capture complex temporal dependencies before generating the final bushfire prediction.

```text
              Proposed FireFusion Pipeline

         Environmental Data
                 │
                 ▼
        Data Preprocessing
                 │
                 ▼
            ConvLSTM Layer
      (Spatial + Temporal Features)
                 │
                 ▼
            BiLSTM Layer
    (Temporal Feature Refinement)
                 │
                 ▼
          Dense / Output Layer
                 │
                 ▼
        Bushfire Prediction
                 │
                 ▼
             FastAPI API
                 │
                 ▼
       Backend / Frontend
```

The proposed architecture should be considered an experimental enhancement rather than a replacement for the existing forecasting model. Its effectiveness should be determined through controlled experiments using FireFusion's datasets and benchmarked against the current ConvLSTM implementation before any production adoption.

---

## Model Evaluation

The proposed ConvLSTM–BiLSTM model should be evaluated against the current ConvLSTM baseline using the same training and testing datasets. Performance should be assessed using regression metrics such as **Mean Squared Error (MSE)**, **Root Mean Squared Error (RMSE)**, and **Mean Absolute Error (MAE)** to measure prediction accuracy.

Computational performance should also be considered by comparing training time, inference time, memory usage, and model complexity. The hybrid model should only be considered for adoption if it demonstrates a meaningful improvement in forecasting performance while maintaining acceptable computational efficiency.

### Expected Benefits and Trade-offs

| Aspect | Current ConvLSTM | Proposed ConvLSTM–BiLSTM |
|---|---|---|
| Spatial feature learning | Strong | Strong |
| Temporal feature learning | Good | Potentially improved through bidirectional sequence modelling |
| Model complexity | Lower | Higher |
| Training time | Lower | Higher |
| Inference cost | Lower | Higher |
| Memory requirements | Lower | Higher |
| Overfitting risk | Lower | Higher, given the limited dataset |
| Forecasting performance | Baseline | Potential improvement, subject to experimental validation |

Based on the current literature, integrating a BiLSTM layer appears technically promising. However, the available evidence is not sufficient to justify replacing the existing ConvLSTM model without experimental validation using the FireFusion dataset and benchmarking against the current baseline.

The additional model capacity is the principal risk. The proposed hybrid introduces a substantial number of parameters into a model already trained on a limited record of Victorian fire seasons. Therefore, any improvement in validation performance must be assessed against the possibility that the model is fitting the training distribution more closely rather than generalising better.

### Controlled Evaluation Strategy

The proposed ConvLSTM–BiLSTM model should be evaluated against the current ConvLSTM baseline using the same training, validation, and testing datasets. To ensure a fair comparison, both models should follow identical data preprocessing, partitioning strategies, and evaluation procedures, with the architecture being the only variable under investigation.

**Training configuration.** The proposed model should follow the same optimisation strategy and hyperparameter configuration as the existing ConvLSTM implementation wherever possible. This ensures that any observed performance differences are attributable to the architectural modification rather than changes in the training process.

**Evaluation metrics.** Forecasting performance should be assessed using **Mean Squared Error (MSE)**, **Root Mean Squared Error (RMSE)**, and **Mean Absolute Error (MAE)**. If spatial prediction outputs are generated, additional metrics such as **Intersection over Union (IoU)** may also be considered to evaluate spatial prediction quality.

**Reproducibility.** Each architecture should be trained using multiple random seeds, with results reported as the mean and standard deviation. This reduces the influence of training variability and provides a more reliable comparison between models.

**Computational performance.** In addition to prediction accuracy, computational efficiency should be evaluated by comparing training time, inference latency, memory usage, and model complexity. These measurements help determine whether any improvement in forecasting performance justifies the additional computational cost introduced by the BiLSTM layer.

---

## Conclusion and Recommendation

The literature reviewed in this investigation indicates that BiLSTM is a promising enhancement for spatiotemporal forecasting, particularly when integrated with convolutional architectures. Recent studies have demonstrated that hybrid models can improve temporal feature learning and forecasting performance in wildfire and other environmental prediction tasks, supporting the investigation of similar approaches within FireFusion.

Based on the current evidence, integrating a BiLSTM layer into FireFusion's existing ConvLSTM pipeline represents a technically sound direction for future development. However, adoption should only be considered after experimental validation demonstrates a meaningful improvement over the current ConvLSTM model using the project's datasets and evaluation strategy.

If the hybrid architecture improves forecasting performance while maintaining acceptable computational efficiency and generalisation, it could become a valuable enhancement to FireFusion's bushfire forecasting system.

---

## References

Andrianarivony HS and Akhloufi MA (2024) ‘Machine learning and deep learning for wildfire spread prediction: a review’, *Fire*, 7(12):482, doi:10.3390/fire7120482

Li W, Zhu H, Yang F, Wen C, Shi S, Zhao D, He C and Li Z (2025) ‘Storm-time ionospheric model over Yunnan-Sichuan area of China based on the SSA-ConvLSTM-BiLSTM algorithm’, *GPS Solutions*, 29(2):77, doi:10.1007/s10291-025-01836-6

Marjani M, Mahdianpari M and Mohammadimanesh F (2024) ‘CNN-BiLSTM: a novel deep learning model for near-real-time daily wildfire spread prediction’, *Remote Sensing*, 16(8):1467, doi:10.3390/rs16081467
