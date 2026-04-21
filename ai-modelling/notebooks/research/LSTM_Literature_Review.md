**Literature Review – LSTM (RNN) Model**

**Introduction**

The goal of this literature review is to analyse how Long Short-Term
Memory (LSTM) models, a type of Recurrent Neural Network (RNN), are used
for time-series forecasting, particularly in our project FireFusion.
Time-series forecasting plays a critical role in environmental
modelling, particularly in applications such as weather prediction,
disaster management, and wildfire forecasting. Traditional statistical
models like ARIMA struggle with nonlinear and complex temporal patterns,
which has led to the adoption of deep learning approaches such as Long
Short-Term Memory (LSTM) networks. (Noble)

**Overview of LSTM (RNN) and architecture**

LSTM is a specialised type of Recurrent Neural Network designed to
handle sequential and time-dependent data. Unlike traditional RNNs,
LSTMs overcome the vanishing gradient problem, allowing them to learn
long-term dependencies in data. LSTM networks extend traditional RNNs by
introducing memory cells and gating mechanisms, which regulate
information flow:

- Forget Gate –\> removes irrelevant past information

- Input Gate -\> updates memory with new information

- Output Gate -\> produces predictions

This architecture allows LSTM to overcome the vanishing gradient
problem, enabling learning over long sequences. Research shows that LSTM
is highly effective in capturing nonlinear and non-stationary temporal
patterns, which are common in environmental datasets. (Springer, 2025)

**LSTM Model Architecture**

Below is a simplified architecture flow for the proposed LSTM model in
FireFusion:

Input Layer (Multivariate Time-Series Data)

↓

Data Preprocessing

(Normalisation, Feature Engineering, Windowing)

↓

LSTM Layer(s)

(Hidden Units capturing temporal dependencies)

↓

Dropout Layer (Regularisation)

↓

Dense Layer (Fully Connected)

↓

Output Layer

(Fire Risk Prediction / Forecast Value)

Input Tensor Example:

- Shape: (batch_size, time_steps, features)

- Features: temperature, humidity, wind speed, fire history

This diagram helps visualise how temporal data flows through the network
and supports your **data fusion strategy (multiple features over
time)**.

**Performance of LSTM in Time-Series Forecasting**

Several studies show that LSTM performs better than conventional models:

- In energy forecasting tasks, LSTM outperforms ARIMA and SARIMA in
  prediction accuracy. (Springer, 2025)

- It captures correlations between variables like temperature, humidity,
  and wind by efficiently modelling multivariate time-series data.

- In complicated stochastic contexts where patterns change over time,
  LSTM works well.

Furthermore, LSTM works exceptionally well for multi-step forecasting,
especially when paired with more complex architectures like
encoder-decoder models or bidirectional LSTM.

**Applications in Environmental and Wildfire Prediction**

LSTM has been widely applied in environmental modelling:

- Weather and Environmental Forecasting

<!-- -->

- Used for predicting fog, temperature, and atmospheric conditions

- Demonstrates superior performance compared to traditional ML methods
  (ScienceDirect, 2025)

<!-- -->

- Bushfire and Wildfire Prediction

<!-- -->

- LSTM models can analyse meteorological + historical fire data to
  predict fire risk

- Integration with remote sensing data improves prediction accuracy

- Hybrid models like CNN-BiLSTM capture both spatial (images) and
  temporal (time-series) features (MDPI, 2024)

<!-- -->

- Long-Term Fire Risk Modelling

<!-- -->

- LSTM has been used to reconstruct long-term fire risk trajectories
  using climate and satellite data (ScienceDirect, 2025)

These applications highlight LSTM’s suitability for the FireFusion
project, where both temporal dynamics and multiple data sources are
involved.

**Comparative Analysis: LSTM vs Baseline Models**

| **Model** | **Strengths** | **Weaknesses** | **Why LSTM is Better** |
|----|----|----|----|
| **ARIMA** | Simple, interpretable | Cannot handle nonlinear/multivariate data | LSTM captures nonlinear temporal patterns |
| **Linear Regression** | Fast, simple | Poor performance on sequential data | LSTM models time dependencies |
| **Random Forest** | Good for tabular data | No temporal memory | LSTM retains sequence information |
| **LSTM** | Handles sequence + nonlinear data | Computationally expensive | Best suited for time-series forecasting |
| **Transformer** | Strong long-range modelling | High complexity, data heavy | LSTM more practical for MVP |

LSTM outperforms baselines because it retains memory across time steps,
which is essential for bushfire prediction.

**Pros and Cons Summary Table (LSTM)**

| **Aspect** | **Advantages** | **Limitations** |
|----|----|----|
| **Training Stability** | Handles long-term dependencies well | Sensitive to hyperparameters |
| **Accuracy** | High accuracy for time-series data | Requires high-quality data |
| **Computation** | Efficient for moderate datasets | High training cost |
| **Inference Latency** | Moderate | Slower than simple models |
| **Scalability** | Works with multivariate data | Needs optimisation for large-scale deployment |
| **Interpretability** | Learns complex patterns | Black-box nature |

**Relevant GitHub Implementations**

These repositories provide practical implementations of LSTM and
variants:

- <https://github.com/jaungiers/LSTM-Neural-Network-for-Time-Series-Prediction>

- <https://github.com/yasasmahima/Inferno-Forest_Fire_Prediction>

- <https://github.com/NourozR/Stock-Price-Prediction-LSTM>

- <https://github.com/TeaPearce/precipitation-prediction-convLSTM-keras>

These can help:

- Understand implementation structure

- Reuse components for FireFusion

- Accelerate Sprint 2 development

**Advances and Hybrid Models**

Recent literature shows a shift toward hybrid and enhanced LSTM models:

- Attention-based LSTM improves focus on important time steps

- Wavelet + LSTM models enhance signal quality before prediction

- CNN + LSTM combines spatial and temporal learning

- Transformer-LSTM hybrids improve long-term forecasting

Hybrid models significantly improve performance by combining
statistical, signal processing, and deep learning techniques

**Advanced Variants: ConvLSTM (Spatial + Temporal Learning)**

ConvLSTM extends LSTM by replacing matrix multiplication with
**convolution operations**, making it suitable for **spatial-temporal
data**.

Why ConvLSTM is Important for FireFusion

- Bushfires spread **geographically across regions (grid-based)**

- Weather + satellite data have **spatial structure**

- ConvLSTM captures:

  - Temporal patterns (time-series)

  - Spatial relationships (neighbouring regions)

Architecture Insight

Input: (time_steps, height, width, channels)

↓

ConvLSTM Layer

↓

Feature Maps (Spatial + Temporal)

↓

Dense Layer

↓

Prediction (Fire Spread / Risk)

This is highly relevant for modelling fire spread direction and
intensity across regions.

**Limitations of LSTM Models**

Despite strong performance, LSTM has several limitations:

- Computational Complexity

<!-- -->

- LSTM requires high computational power and training time due to
  multiple gates and parameters (MDPI, 2024)

<!-- -->

- Data Dependency

<!-- -->

- Requires large, high-quality datasets

- Performs poorly with limited or noisy data

<!-- -->

- Overfitting Risk

<!-- -->

- High model complexity increases risk of overfitting, especially with
  small datasets (Springer, 2025)

<!-- -->

- Lack of Interpretability

<!-- -->

- LSTM is a black-box model, making it difficult to explain predictions

- This is a major issue in critical applications like disaster
  management (Springer, 2025)

<!-- -->

- Sensitivity to Hyperparameters

<!-- -->

- Performance depends heavily on tuning (learning rate, sequence length,
  hidden units) (Springer, 2025)

**Case Study – LSTM for Forest Fire Prediction**

A relevant study, “Forest Fire Prediction using LSTM” (Natekar, Patil,
Nair, & Roychowdhury, 2021), demonstrates the practical application of
LSTM models in wildfire prediction systems.

Methodology

The study uses:

- Meteorological data (temperature, humidity, wind speed)

- Historical fire occurrence data

These inputs are processed as time-series sequences, allowing the LSTM
model to learn temporal patterns and relationships between environmental
variables.

The model architecture follows a standard pipeline:

- Input: Multivariate time-series data

- Processing: LSTM layers capturing temporal dependencies

- Output: Fire occurrence prediction (classification or risk level)

Key Findings

- LSTM achieved higher prediction accuracy compared to traditional
  machine learning models due to its ability to retain temporal memory.

- The model effectively captured relationships between weather variables
  and fire occurrence, improving forecasting reliability.

- Performance improved when multiple environmental features were
  combined, highlighting the importance of multivariate data.

Technical Insight

The study reinforces that:

- Forest fire prediction is inherently a time-series problem influenced
  by multiple interacting variables.

- LSTM models are well-suited because they can capture long-term
  dependencies and nonlinear relationships.

- Feature selection (e.g., wind + temperature interaction) plays a
  critical role in improving model performance.

Limitations Identified in the Study

- Model performance depends heavily on data quality and availability

- Requires careful tuning of hyperparameters

- Limited interpretability for decision-making contexts

Relevance to FireFusion

This case study directly supports the design choices for FireFusion:

- Confirms that LSTM is suitable as a baseline model for bushfire
  forecasting

- Validates the use of weather + historical fire data as key inputs

- Supports the need for multivariate time-series modelling

- Reinforces the importance of integrating predictions into a
  decision-support system

**Key Findings from Literature**

From reviewing research papers, the following insights are identified:

- LSTM models outperform traditional models (e.g., linear regression) in
  time-series prediction tasks

- Hybrid models (e.g., CNN + LSTM) improve performance for spatial +
  temporal data

- Data preprocessing (normalisation, handling missing values)
  significantly affects accuracy

- Model performance depends on sequence length, feature selection, and
  training data quality

**Research Gaps**

The literature identifies several gaps:

- Lack of guidelines for selecting appropriate models based on data
  characteristics

- Limited research on interpretability of deep learning models in
  disaster systems

- Challenges in real-time deployment due to computational cost

- Need for better integration of physical models + AI models

**Application Strategy for FireFusion**

Based on the literature, LSTM is a strong candidate for FireFusion:

**Proposed Approach**

- Use historical data and bushfire datasets

- Preprocess data (cleaning, normalisation, feature selection)

- Train an LSTM model for time-series forecasting

- Evaluate using metrics such as RMSE and MAE

- Integrate predictions into the FireFusion dashboard

**Potential Enhancements**

- Use CNN-LSTM for spatial + temporal modelling

- Apply attention mechanisms for better feature selection

- Combine with domain knowledge (fire behaviour models)

**Critical Evaluation**

While LSTM is powerful, it is not always the best solution:

- For simple datasets, traditional models may perform equally well

- For long-range forecasting, newer models like Transformers may
  outperform LSTM

- For high-stakes decisions, lack of interpretability can be a concern

Therefore, LSTM should be used as part of a balanced, hybrid approach
rather than a standalone solution.

**Conclusion**

The literature confirms that LSTM is a highly effective model for
time-series forecasting, particularly in complex, nonlinear environments
such as bushfire prediction. Its ability to capture long-term
dependencies makes it well-suited for the FireFusion project. Based on
the literature and comparative analysis, LSTM is selected as the
baseline model for FireFusion due to its ability to capture temporal
dependencies in multivariate data. However, for improved
spatial-temporal modelling of bushfire spread, ConvLSTM is identified as
a strong candidate for future iterations

However, limitations such as computational cost, data requirements, and
lack of interpretability highlight the importance of careful
implementation and potential integration with other models.

# 

# 

# References

*MDPI.* (2024). Retrieved from MDPI:
https://www.mdpi.com/2072-4292/16/8/1467

Natekar, S., Patil, S., Nair, A., & Roychowdhury, S. (2021). *IEEE.*
Retrieved from IEEE Explore:
https://ieeexplore.ieee.org/document/9456113

Noble, J. (n.d.). *IBM.* Retrieved from IBM:
https://www.ibm.com/think/topics/lstm

*ScienceDirect.* (2025, December 15). Retrieved from ScienceDirect:
https://www.sciencedirect.com/science/article/abs/pii/S0168192325005039

*Springer.* (2025, June 05). Retrieved from Springer:
https://link.springer.com/article/10.1007/s12530-025-09703-y
