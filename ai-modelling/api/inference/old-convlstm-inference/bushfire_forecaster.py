"""
Bushfire ConvLSTM Forecaster Inference: pure functions over a LoadedModel bundle.
Routers call this after resolving model_id via model_loader.
"""
from typing import Any, Optional, Tuple
import numpy as np
import torch

from api.schemas.bushfire import ForecastRequest, ForecastResponse, GeoFeatureOut, ForecastPropertiesOut, DEFAULT_FEATURE_NAMES
from api.model_loader import LoadedModel


def predict_bushfire_forecast(geojson_dict: dict, bundle: LoadedModel) -> dict:
    """
    Forecast environmental variables from time-series observations using ConvLSTM.
    
    Args:
        geojson_dict: GeoJSON FeatureCollection with time-series observations
        bundle: LoadedModel bundle with model, device, scaler, metadata
    
    Returns:
        GeoJSON FeatureCollection with forecast values per feature
    """
    # Validate input
    request = ForecastRequest(**geojson_dict)
    
    # Extract observations and metadata from input features
    observations_list = []
    feature_metas = []
    
    input_steps = bundle.metadata.get("input_steps", 60)
    horizon = bundle.metadata.get("horizon", 2)
    grid_shape = bundle.metadata.get("grid_shape")  # (height, width) if gridded
    
    # Collect observations from each feature
    for feature in request.features:
        obs = np.array(feature.properties.observations, dtype=np.float32)  # [seq_len, n_features]
        
        # Enforce sequence length: pad or truncate
        seq_len = obs.shape[0]
        if seq_len < input_steps:
            # Pad with zeros at the beginning (oldest timesteps)
            pad_width = ((input_steps - seq_len, 0), (0, 0))
            obs = np.pad(obs, pad_width, mode="constant", constant_values=0.0)
        elif seq_len > input_steps:
            # Truncate to most recent timesteps
            obs = obs[-input_steps:, :]
        
        observations_list.append(obs)
        feature_metas.append({
            "id": feature.properties.id,
            "geometry": feature.geometry,
            "grid_row": feature.properties.__dict__.get("grid_row"),
            "grid_col": feature.properties.__dict__.get("grid_col"),
        })
    
    # Determine if we have grid coordinates
    has_grid_coords = any(m["grid_row"] is not None and m["grid_col"] is not None for m in feature_metas)
    
    if has_grid_coords and grid_shape:
        # Build gridded tensor: [batch, seq_len, height, width, n_features]
        x_input = _build_grid_tensor(observations_list, feature_metas, grid_shape, input_steps)
    else:
        # Fall back to batch processing: [n_samples, seq_len, n_features]
        x_input = np.stack(observations_list, axis=0)
    
    # Apply scaler if available
    if bundle.scaler is not None:
        x_input = _apply_scaler(x_input, bundle.scaler)
    
    # Convert to tensor and move to device
    x_tensor = torch.from_numpy(x_input).float().to(bundle.device)
    
    # Predict
    with torch.no_grad():
        bundle.model.eval()
        
        if len(x_input.shape) == 5:
            # Gridded: [batch, seq_len, height, width, n_features]
            # ConvLSTM expects [batch, seq_len, height, width, n_features]
            forecasts = bundle.model.predict(x_tensor).cpu().numpy()  # [batch, horizon, height, width, n_features]
        else:
            # Non-gridded batch: [n_samples, seq_len, n_features]
            # Model expects [batch, seq_len, height, width, n_features] so this will fail
            # For now, reshape to add spatial dims [n_samples, seq_len, 1, 1, n_features]
            x_tensor = x_tensor.unsqueeze(2).unsqueeze(3)  # [n_samples, seq_len, 1, 1, n_features]
            forecasts = bundle.model.predict(x_tensor).cpu().numpy()  # [n_samples, horizon, 1, 1, n_features]
            forecasts = forecasts.squeeze(axis=(2, 3))  # [n_samples, horizon, n_features]
    
    # Postprocess to GeoJSON
    output_features = _postprocess_forecasts(
        forecasts, feature_metas, has_grid_coords, grid_shape, horizon, bundle.model_id
    )
    
    response = ForecastResponse(
        type="FeatureCollection",
        features=output_features,
    )
    return response.model_dump(mode="json")


def _build_grid_tensor(
    observations_list: list[np.ndarray],
    feature_metas: list[dict],
    grid_shape: Tuple[int, int],
    input_steps: int,
) -> np.ndarray:
    """
    Build a gridded tensor from observations indexed by grid_row/grid_col.
    
    Args:
        observations_list: List of [seq_len, n_features] arrays
        feature_metas: List of dicts with grid_row, grid_col
        grid_shape: (height, width)
        input_steps: Sequence length
    
    Returns:
        [batch=1, seq_len, height, width, n_features] tensor
    """
    height, width = grid_shape
    n_features = observations_list[0].shape[1]
    
    # Initialize grid with NaNs
    grid = np.full((input_steps, height, width, n_features), np.nan, dtype=np.float32)
    
    # Fill grid cells
    for obs, meta in zip(observations_list, feature_metas):
        row = meta.get("grid_row")
        col = meta.get("grid_col")
        if row is not None and col is not None:
            grid[:, row, col, :] = obs
    
    # Add batch dimension
    return grid[np.newaxis, ...]  # [1, seq_len, height, width, n_features]


def _apply_scaler(x: np.ndarray, scaler: Any) -> np.ndarray:
    """
    Apply scaler to input tensor, handling both gridded and batch shapes.
    
    Args:
        x: Input array (gridded or batch)
        scaler: Fitted sklearn scaler
    
    Returns:
        Scaled array with same shape
    """
    original_shape = x.shape
    n_features = original_shape[-1]
    
    # Flatten all dimensions except features
    x_flat = x.reshape(-1, n_features)
    
    # Apply scaler
    x_scaled = scaler.transform(x_flat)
    
    # Reshape back
    return x_scaled.reshape(original_shape)


def _postprocess_forecasts(
    forecasts: np.ndarray,
    feature_metas: list[dict],
    has_grid_coords: bool,
    grid_shape: Optional[Tuple[int, int]],
    horizon: int,
    model_id: str,
) -> list[GeoFeatureOut]:
    """
    Convert forecast arrays back to GeoJSON features.
    
    Args:
        forecasts: [batch, horizon, height, width, n_features] or [n_samples, horizon, n_features]
        feature_metas: List of feature metadata
        has_grid_coords: Whether features have grid coordinates
        grid_shape: (height, width) if gridded
        horizon: Forecast horizon
        model_id: Model ID for response
    
    Returns:
        List of GeoFeatureOut
    """
    output_features = []
    
    if has_grid_coords and grid_shape and len(forecasts.shape) == 5:
        # Gridded forecasts: [batch, horizon, height, width, n_features]
        # Extract per-feature forecasts from grid
        for meta in feature_metas:
            row = meta.get("grid_row")
            col = meta.get("grid_col")
            if row is not None and col is not None:
                # Extract this cell's forecast [horizon, n_features]
                forecast_vals = forecasts[0, :, row, col, :].tolist()
                risk_score = float(np.mean(forecast_vals))  # Aggregate across features and time
                
                props_out = ForecastPropertiesOut(
                    id=meta["id"],
                    forecast=forecast_vals,
                    risk_score=risk_score,
                    model_id=model_id,
                )
                feature_out = GeoFeatureOut(
                    type="Feature",
                    geometry=meta["geometry"],
                    properties=props_out.model_dump(mode="json", exclude_none=True),
                )
                output_features.append(feature_out)
    else:
        # Non-gridded batch forecasts: [n_samples, horizon, n_features]
        for i, meta in enumerate(feature_metas):
            forecast_vals = forecasts[i, :, :].tolist()  # [horizon, n_features]
            risk_score = float(np.mean(forecast_vals))
            
            props_out = ForecastPropertiesOut(
                id=meta["id"],
                forecast=forecast_vals,
                model_id=model_id,
            )
            feature_out = GeoFeatureOut(
                type="Feature",
                geometry=meta["geometry"],
                properties=props_out.model_dump(mode="json", exclude_none=True),
            )
            output_features.append(feature_out)
    
    return output_features