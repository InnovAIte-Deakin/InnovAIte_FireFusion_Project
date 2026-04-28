from tensorflow import keras
from tensorflow.keras import layers

SEQ_LEN = 60
HORIZON = 2


def build_lstm_model(
    n_features: int,
    seq_len: int = SEQ_LEN,
    horizon: int = HORIZON,
    lstm1_units: int = 64,
    lstm2_units: int = 32,
    dropout: float = 0.2,
    learning_rate: float = 1e-3,
) -> keras.Model:
    model = keras.Sequential([
        layers.Input(shape=(seq_len, n_features)),
        layers.LSTM(lstm1_units, return_sequences=True),
        layers.Dropout(dropout),
        layers.LSTM(lstm2_units),
        layers.Dropout(dropout),
        layers.Dense(horizon * n_features),
        layers.Reshape((horizon, n_features)),
    ], name="bushfire_lstm")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=["mae"],
    )
    return model
