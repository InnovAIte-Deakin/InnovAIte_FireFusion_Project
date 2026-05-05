import torch
import torch.nn as nn
import numpy as np

class FireLSTM(nn.Module):

    def __init__(self, input_size=10, hidden_size=32, num_layers=2):
        super(FireLSTM, self).__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )

        self.fc = nn.Sequential(
            nn.Linear(hidden_size + 6, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )

    def forward(self, weather_seq, static_features):

        lstm_out, _ = self.lstm(weather_seq)

        last_hidden = lstm_out[:, -1, :]

        combined = torch.cat((last_hidden, static_features), dim=1)

        output = self.fc(combined)

        return output


model = FireLSTM()
model.eval()


def prepare_weather_tensor(weather_sequence):

    features = []

    for day in weather_sequence:

        features.append([
            day.max_temp_c,
            day.wind_speed_kmh,
            day.wind_dir_deg,
            day.rel_humidity_pct,
            day.precipitation_mm,
            day.evapotranspiration,
            day.soil_moisture,
            day.soil_temp_c,
            day.days_since_rain,
            day.day
        ])

    arr = np.array(features)

    tensor = torch.tensor(arr, dtype=torch.float32).unsqueeze(0)

    return tensor


def prepare_static_tensor(props):

    terrain = props.static_terrain
    bio = props.biological_fuel
    ignition = props.ignition_risk

    static_features = [
        terrain.elevation_m,
        terrain.slope_deg,
        terrain.aspect_deg,
        terrain.dist_to_water_m,
        bio.ndvi_at_ignition or 0,
        ignition.dist_to_powerlines_m
    ]

    return torch.tensor([static_features], dtype=torch.float32)


def predict_fire(feature):

    weather_tensor = prepare_weather_tensor(
        feature.properties.weather_sequence_7d
    )

    static_tensor = prepare_static_tensor(
        feature.properties
    )

    with torch.no_grad():

        output = model(weather_tensor, static_tensor)

    severity, area, spread = output.numpy()[0]

    return {
        "predicted_severity": float(severity),
        "predicted_area_ha": float(area),
        "predicted_spread_rate": float(spread)
    }