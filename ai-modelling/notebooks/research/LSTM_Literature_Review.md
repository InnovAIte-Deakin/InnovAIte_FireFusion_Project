**Literature Review -- LSTM (RNN) Model**

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

- Forget Gate --\> removes irrelevant past information

- Input Gate -\> updates memory with new information

- Output Gate -\> produces predictions

This architecture allows LSTM to overcome the vanishing gradient
problem, enabling learning over long sequences. Research shows that LSTM
is highly effective in capturing nonlinear and non-stationary temporal
patterns, which are common in environmental datasets. (Springer, 2025)

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

These applications highlight LSTM's suitability for the FireFusion
project, where both temporal dynamics and multiple data sources are
involved.

**Advances and Hybrid Models**

Recent literature shows a shift toward hybrid and enhanced LSTM models:

- Attention-based LSTM improves focus on important time steps

- Wavelet + LSTM models enhance signal quality before prediction

- CNN + LSTM combines spatial and temporal learning

- Transformer-LSTM hybrids improve long-term forecasting

Hybrid models significantly improve performance by combining
statistical, signal processing, and deep learning techniques

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
**time-series forecasting**, particularly in complex, nonlinear
environments such as bushfire prediction. Its ability to capture
long-term dependencies makes it well-suited for the FireFusion project.

However, limitations such as computational cost, data requirements, and
lack of interpretability highlight the importance of careful
implementation and potential integration with other models.

# 

# 

# References

*MDPI.* (2024). Retrieved from MDPI:
https://www.mdpi.com/2072-4292/16/8/1467

Noble, J. (n.d.). *IBM.* Retrieved from IBM:
https://www.ibm.com/think/topics/lstm

*ScienceDirect.* (2025, December 15). Retrieved from ScienceDirect:
https://www.sciencedirect.com/science/article/abs/pii/S0168192325005039

*Springer.* (2025, June 05). Retrieved from Springer:
https://link.springer.com/article/10.1007/s12530-025-09703-y
