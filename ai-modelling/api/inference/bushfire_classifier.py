"""
Bushfire TCN classifier inference: pure functions over a LoadedModel bundle.
Routers call this after resolving model_id via model_loader.
"""
from typing import Any, Optional
import numpy as np
import torch

from api.schemas.bushfire import ForecastRequest, ForecastResponse, GeoFeatureOut, ForecastPropertiesOut, DEFAULT_FEATURE_NAMES
from api.model_loader import LoadedModel


from api.model_loader import list_models
from api.inference.bushfire_forecaster import predict_bushfire_forecast

def _prob_to_label_index(prob: float) -> int:
    if prob < 0.2: return 0
    if prob < 0.4: return 1
    if prob < 0.6: return 2
    if prob < 0.8: return 3
    return 4

def predict_bushfire_classify(geojson_dict: dict, bundle: LoadedModel) -> dict:
    request = ForecastRequest(**geojson_dict)
    # find forecaster bundle (use the first loaded forecaster)
    forecasters = [m for m in list_models(domain="bushfire") if m.kind == "bushfire_forecaster"]
    if not forecasters:
        raise RuntimeError("no bushfire forecaster loaded for combined inference")
    forecaster_bundle = forecasters[0]

    # call forecaster to get forecasts (returns FeatureCollection dict)
    forecast_fc = predict_bushfire_forecast(geojson_dict, forecaster_bundle)
    # map id -> forecast array
    fc_map = {
        f["properties"].get("id"): np.array(f["properties"]["forecast"], dtype=np.float32)
        for f in forecast_fc["features"]
    }

    lookback = bundle.metadata.get("lookback_steps", 60)
    horizon = list(fc_map.values())[0].shape[0]  # e.g. 2
    outputs = []

    observations_list = []
    ids = []
    geometries = []
    for feat in request.features:
        fid = feat.properties.id
        hist = np.array(feat.properties.observations, dtype=np.float32)  # [seq_len, n_features]
        # ensure we have at least lookback steps (pad/truncate same policy as before)
        if hist.shape[0] < lookback:
            pad = ((lookback - hist.shape[0], 0), (0, 0))
            hist = np.pad(hist, pad, mode="constant", constant_values=0.0)
        else:
            hist = hist[-lookback:, :]

        fc = fc_map.get(fid)
        if fc is None:
            raise KeyError(f"forecast missing for feature id={fid}")

        # Build sequence: history_last_lookback + first (horizon-1) forecast steps
        if horizon > 1:
            seq = np.concatenate([hist, fc[: (horizon - 1), :]], axis=0)  # shape [lookback + horizon -1, n_features]
        else:
            seq = hist  # horizon == 1

        observations_list.append(seq)
        ids.append(fid)
        geometries.append(feat.geometry)

    # Stack batch
    x_batch = np.stack(observations_list, axis=0)  # [n_samples, L, n_features]

    # apply scaler if present on classifier bundle
    if bundle.scaler is not None:
        n_samples, L, n_features = x_batch.shape
        x_flat = x_batch.reshape(-1, n_features)
        x_flat = bundle.scaler.transform(x_flat)
        x_batch = x_flat.reshape(n_samples, L, n_features)

    x_tensor = torch.from_numpy(x_batch).float().to(bundle.device)
    with torch.no_grad():
        bundle.model.eval()
        probs = bundle.model(x_tensor).cpu().numpy()  # expected shape [n_samples, horizon, 1] -> squeeze to [n_samples, horizon]
        probs = probs.squeeze(-1)

    # Build GeoJSON response: per-feature risk_probabilities and risk_levels (ints)
    out_features = []
    for i, fid in enumerate(ids):
        prob_vec = probs[i].tolist()  # length = horizon
        label_vec = [_prob_to_label_index(p) for p in prob_vec]
        props = {
            "id": fid,
            "risk_probabilities": prob_vec,
            "risk_levels": label_vec,
            "model_id": bundle.model_id,
        }
        out_features.append({
            "type": "Feature",
            "geometry": geometries[i],
            "properties": props,
        })

    return {"type": "FeatureCollection", "features": out_features}


def predict_bushfire_classify_from_forecast(
    forecast_fc: dict,
    original_geojson: dict,
    bundle: LoadedModel,
) -> dict:
    """
    Given a forecaster FeatureCollection (forecast_fc) and the original
    input GeoJSON (original_geojson), build the classifier input windows
    and return per-feature, per-forecast-step probabilities and discrete labels.
    """
    request = ForecastRequest(**original_geojson)
    # build id->forecast map (use id if present else index)
    fc_features = forecast_fc.get("features", [])
    fc_map = {}
    for idx, f in enumerate(fc_features):
        props = f.get("properties", {}) if isinstance(f, dict) else {}
        fid = props.get("id") if isinstance(props, dict) else None
        if fid is None:
            fid = str(idx)
        fc_map[fid] = np.array(props["forecast"], dtype=np.float32)

    lookback = int(bundle.metadata.get("lookback_steps", 60))
    # horizon from forecast (assume all have same horizon)
    sample_fc = next(iter(fc_map.values()), None)
    if sample_fc is None:
        raise RuntimeError("no forecasts returned by forecaster")
    horizon = int(sample_fc.shape[0])

    observations_list = []
    ids = []
    geometries = []

    for idx, feat in enumerate(request.features):
        fid = feat.properties.id or str(idx)
        hist = np.array(feat.properties.observations, dtype=np.float32)  # [seq_len, n_features]
        # pad/truncate to lookback
        if hist.shape[0] < lookback:
            pad = ((lookback - hist.shape[0], 0), (0, 0))
            hist = np.pad(hist, pad, mode="constant", constant_values=0.0)
        else:
            hist = hist[-lookback :, :]

        fc = fc_map.get(fid)
        if fc is None:
            # fallback by order
            if idx < len(fc_features):
                fc = np.array(fc_features[idx]["properties"]["forecast"], dtype=np.float32)
            else:
                raise KeyError(f"missing forecast for feature id={fid}")

        # build sequence length = lookback + horizon - 1
        if horizon > 1:
            seq = np.concatenate([hist, fc[: (horizon - 1), :]], axis=0)
        else:
            seq = hist

        observations_list.append(seq)
        ids.append(fid)
        geometries.append(feat.geometry)

    x_batch = np.stack(observations_list, axis=0)  # [n_samples, L, n_features]

    # apply scaler if available
    if bundle.scaler is not None:
        n_samples, L, n_features = x_batch.shape
        x_flat = x_batch.reshape(-1, n_features)
        x_flat = bundle.scaler.transform(x_flat)
        x_batch = x_flat.reshape(n_samples, L, n_features)

    x_tensor = torch.from_numpy(x_batch).float().to(bundle.device)

    with torch.no_grad():
        bundle.model.eval()
        out = bundle.model(x_tensor)
        out_np = out.cpu().numpy()

        # Normalize output to shape [n_samples, horizon]
        if out_np.ndim == 3 and out_np.shape[-1] == 1:
            probs = out_np.squeeze(-1)
        elif out_np.ndim == 2 and out_np.shape[1] >= 1:
            # either (n_samples, horizon) or (n_samples, 1)
            if out_np.shape[1] == 1:
                probs = out_np.squeeze(-1)[:, None]
            else:
                probs = out_np
        elif out_np.ndim == 1:
            probs = out_np[:, None]
        else:
            # fallback: try per-step sliding windows using internal method if available
            if horizon > 1 and hasattr(bundle.model, "_forward_single"):
                steps = []
                for t in range(horizon):
                    window = x_tensor[:, t : t + lookback, :]
                    step_np = bundle.model._forward_single(window).cpu().numpy().squeeze(-1)
                    steps.append(step_np)
                probs = np.stack(steps, axis=1)
            else:
                raise RuntimeError("unexpected classifier output shape")

    # map probabilities -> discrete risk levels (0..4) per your thresholds
    def prob_to_level(p: float) -> int:
        if p < 0.2:
            return 0
        if p < 0.4:
            return 1
        if p < 0.6:
            return 2
        if p < 0.8:
            return 3
        return 4

    features_out = []
    for i, fid in enumerate(ids):
        prob_vec = probs[i].tolist()
        level_vec = [prob_to_level(float(p)) for p in prob_vec]
        props = {
            "id": fid,
            "risk_probabilities": prob_vec,
            "risk_levels": level_vec,
            "model_id": bundle.model_id,
        }
        features_out.append({"type": "Feature", "geometry": geometries[i], "properties": props})

    return {"type": "FeatureCollection", "features": features_out}