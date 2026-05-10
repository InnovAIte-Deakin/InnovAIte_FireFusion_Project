"""Train BushfireRiskClassifier (forecast-only): env + fire → labels, 4D grid, y_forecast windows.

Run from ``ai-modelling``: ``python -m src.training.ts_classifier_train``

Default data paths match ``train.py``. Pass ``--merged-csv`` to use one long-format file
(``grid_id``, ``datetime``, features, ``is_burning``) instead.
"""
import pickle
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch import Tensor, nn, optim
from torch.utils.data import DataLoader, Dataset

PathLike = Union[str, Path]

_TRAIN_ROOT = Path(__file__).resolve().parent
_SRC = _TRAIN_ROOT.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models.bushfire.risk_classifier import BushfireRiskClassifier, RiskClassifierConfig

ENV_CSV_PATHS = [
    # "src/data/bushfire/ERA5_Land/FireFusion_ERA5_Land_Victoria_2018_Jan_Jun_12Hourly_5kmGrid.csv"
    "src/data/bushfire/ERA5_Land/FireFusion_ERA5_Land_Victoria_2018_Jul_Dec_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2019_Jan_Jun_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2019_Jul_Dec_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2020_Jan_Jun_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2020_Jul_Dec_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2021_Jan_Jun_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2021_Jul_Dec_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2022_Jan_Jun_12Hourly_5kmGrid.csv",
    # "src/data/bushfire/ERA5data/FireFusion_ERA5_Land_Victoria_2022_Jul_Dec_12Hourly_5kmGrid.csv",
]
FIRE_CSV_PATH = "src/data/bushfire/satellite_detections_within_fires.csv"
ENV_CUTOFF_DEFAULT = "2018-07-26"

CHECKPOINT_DIR = "src/models/bushfire/advanced_classifier/classifier_checkpoints"
DEFAULT_RISK_CLASSIFIER_PATH = os.path.join(CHECKPOINT_DIR, "risk_classifier.pth")

FEATURE_COLS = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]

LABEL_COL = "is_burning"
TIME_COL = "datetime"


def long_df_to_grid_tensors(
    df: pd.DataFrame,
    grid_h: int,
    grid_w: int,
    feature_cols: Sequence[str],
    *,
    label_col: str = LABEL_COL,
    time_col: str = TIME_COL,
    max_rows: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Long-format table → ``feat[T,H,W,C]``, ``lab[T,H,W]`` integer labels."""
    d = df if max_rows is None else df.iloc[:max_rows].copy()
    d[time_col] = pd.to_datetime(d[time_col])
    d = d.sort_values(time_col).reset_index(drop=True)
    for col in feature_cols:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d[label_col] = pd.to_numeric(d[label_col], errors="coerce")
    d = d.dropna(subset=list(feature_cols) + [label_col]).reset_index(drop=True)

    unique_times = sorted(d[time_col].unique())
    time_to_idx = {t: i for i, t in enumerate(unique_times)}
    t_count = len(unique_times)
    gids_sorted = sorted(d["grid_id"].unique())
    need = grid_h * grid_w
    if len(gids_sorted) < need:
        raise ValueError(f"Need {need} distinct grid_id (H*W), got {len(gids_sorted)}")
    use_gids = gids_sorted[:need]
    gid_to_ij = {g: divmod(k, grid_w) for k, g in enumerate(use_gids)}

    n_chan = len(feature_cols)
    feat = np.zeros((t_count, grid_h, grid_w, n_chan), dtype=np.float32)
    lab = np.zeros((t_count, grid_h, grid_w), dtype=np.float64)

    sub = d[d["grid_id"].isin(use_gids)].copy()
    sub["t_idx"] = sub[time_col].map(time_to_idx)
    sub = sub.dropna(subset=["t_idx"])
    sub["t_idx"] = sub["t_idx"].astype(int)
    sub = sub.drop_duplicates(subset=["t_idx", "grid_id"], keep="last")

    for _, row in sub.iterrows():
        t_i = int(row["t_idx"])
        gi, gj = gid_to_ij[row["grid_id"]]
        feat[t_i, gi, gj, :] = row[list(feature_cols)].to_numpy(dtype=np.float32)
        lab[t_i, gi, gj] = float(row[label_col])

    return feat, np.rint(lab).astype(np.int64)


def load_env_concat(
    paths: Sequence[PathLike],
    feature_cols: Sequence[str],
    *,
    cutoff: Optional[pd.Timestamp],
) -> pd.DataFrame:
    need_cols = ["datetime", "grid_id", *feature_cols, ".geo"]
    frames: List[pd.DataFrame] = []
    for raw in paths:
        p = Path(raw)
        header = pd.read_csv(p, nrows=0)
        usecols = [c for c in need_cols if c in header.columns]
        if "datetime" not in usecols or "grid_id" not in usecols:
            raise ValueError(f"{p}: need datetime and grid_id")
        if ".geo" not in usecols:
            raise ValueError(f"{p}: need .geo for spatial join")
        part = pd.read_csv(p, usecols=usecols)
        frames.append(part)
        print(f"  env: {p.name} — {len(part):,} rows")

    out = pd.concat(frames, ignore_index=True)
    out["datetime"] = pd.to_datetime(out["datetime"])
    if cutoff is not None:
        out = out[out["datetime"] <= cutoff]
    out = out.dropna(subset=list(feature_cols)).drop_duplicates(["grid_id", "datetime"]).reset_index(drop=True)
    print(f"  env merged: {len(out):,} rows | {out['datetime'].min().date()} → {out['datetime'].max().date()}")
    return out


def load_fire(csv_path: PathLike) -> pd.DataFrame:
    p = Path(csv_path)
    df = pd.read_csv(p, usecols=["datetime", "daynight", "is_burning", "geometry"])
    df["datetime"] = pd.to_datetime(df["datetime"]) + pd.to_timedelta(df["daynight"] * 12, unit="h")
    print(f"  fire: {len(df):,} rows | {df['datetime'].min().date()} → {df['datetime'].max().date()}")
    return df[["datetime", "is_burning", "geometry"]]


def attach_fire_grid_ids(env_df: pd.DataFrame, fire_df: pd.DataFrame) -> pd.DataFrame:
    import geopandas as gpd
    from shapely import wkt
    from shapely.geometry import Polygon

    if ".geo" not in env_df.columns:
        raise ValueError("env needs .geo for spatial join")

    def parse_geo(s: str):
        try:
            return Polygon(json.loads(s)["coordinates"][0])
        except Exception:
            return None

    env_geo = env_df[["grid_id", ".geo"]].drop_duplicates("grid_id").copy()
    env_geo["geometry"] = env_geo[".geo"].apply(parse_geo)
    env_geo = env_geo.dropna(subset=["geometry"])
    grid_gdf = gpd.GeoDataFrame(env_geo[["grid_id", "geometry"]], crs="EPSG:4326")

    f = fire_df.copy().reset_index(drop=True)
    f["geometry"] = f["geometry"].apply(wkt.loads)
    fire_gdf = gpd.GeoDataFrame(f, crs="EPSG:4326")
    fire_gdf["centroid"] = fire_gdf.geometry.to_crs("EPSG:3857").centroid.to_crs("EPSG:4326")
    joined = gpd.sjoin(fire_gdf.set_geometry("centroid"), grid_gdf, how="left", predicate="within")
    f["grid_id"] = joined["grid_id"].values
    n_bad = f["grid_id"].isna().sum()
    if n_bad:
        print(f"  warning: {n_bad} fires not matched to a cell")
    f = f.dropna(subset=["grid_id"])
    print(f"  fires matched to grid: {len(f):,}")
    return f


def merge_env_fire_labels(
    env_df: pd.DataFrame, fire_df: pd.DataFrame, feature_cols: Sequence[str]
) -> pd.DataFrame:
    fire_peak = fire_df.groupby(["grid_id", "datetime"], as_index=False)["is_burning"].max()
    spine = env_df[["grid_id", "datetime", *feature_cols]].merge(fire_peak, on=["grid_id", "datetime"], how="left")
    spine[LABEL_COL] = spine["is_burning"].fillna(0).astype(np.int8)
    # spine = spine.drop(columns=["is_burning"])
    pos = int(spine[LABEL_COL].sum())
    print(f"  labelled rows: {len(spine):,} | positives: {pos:,} ({100 * pos / max(len(spine), 1):.3f}%)")
    return spine


def build_training_table_firefusion(
    env_paths: Sequence[PathLike],
    fire_path: PathLike,
    feature_cols: Sequence[str],
    *,
    cutoff: Optional[pd.Timestamp],
) -> pd.DataFrame:
    env_df = load_env_concat(env_paths, feature_cols, cutoff=cutoff)
    fire_raw = load_fire(fire_path)
    fire_grid = attach_fire_grid_ids(env_df, fire_raw)
    return merge_env_fire_labels(env_df, fire_grid, feature_cols)


def window_origins(split: str, t: int, seq_len: int, horizon: int, train_frac: float, val_frac: float) -> List[int]:
    tr = int(t * train_frac)
    va = int(t * (train_frac + val_frac))
    o: List[int] = []
    if split == "train":
        o = list(range(0, tr - seq_len - horizon + 1))
    elif split == "val":
        lo, hi = max(0, tr - seq_len), va - seq_len - horizon
        for s in range(lo, hi + 1):
            if s + seq_len + horizon <= va and s + seq_len >= tr:
                o.append(s)
    elif split == "test":
        lo = max(0, va - seq_len)
        for s in range(lo, t - seq_len - horizon + 1):
            if s + seq_len >= va:
                o.append(s)
    else:
        raise ValueError(split)
    return o


class ForecastWindowDataset(Dataset):
    """``y_forecast`` = feat[t0:t0+H]; targets = labels same slice (ConvLSTM-shaped input)."""

    def __init__(self, feat: np.ndarray, lab: np.ndarray, origins: Sequence[int], seq_len: int, horizon: int):
        self.feat = np.ascontiguousarray(feat, np.float32)
        self.lab = np.ascontiguousarray(lab, np.int64)
        self.origins = list(origins)
        self.seq_len = seq_len
        self.horizon = horizon

    def __len__(self) -> int:
        return len(self.origins)

    def __getitem__(self, i: int) -> Tuple[Tensor, Tensor]:
        s = self.origins[i]
        t0 = s + self.seq_len
        y = self.feat[t0 : t0 + self.horizon].copy()
        tgt = self.lab[t0 : t0 + self.horizon].copy()
        return torch.from_numpy(y), torch.from_numpy(tgt)


def _zeros_x_hist(bs: int, h: int, w: int, cin: int, device: torch.device, dtype: torch.dtype) -> Tensor:
    return torch.zeros(bs, 1, h, w, cin, device=device, dtype=dtype)


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    opt: optim.Optimizer,
    lam: float,
    dev: torch.device,
    gh: int,
    gw: int,
    cin: int,
) -> float:
    model.train()
    tot, n = 0.0, 0
    for yf, tgt in loader:
        yf, tgt = yf.to(dev), tgt.to(dev)
        b = yf.shape[0]
        xpad = _zeros_x_hist(b, gh, gw, cin, dev, yf.dtype)
        opt.zero_grad(set_to_none=True)
        logits, emb = model.forward_with_aux(xpad, yf)
        loss = F.cross_entropy(logits.permute(0, 4, 1, 2, 3), tgt) + lam * emb
        loss.backward()
        opt.step()
        tot += loss.item()
        n += 1
    return tot / max(n, 1)


@torch.no_grad()
def eval_epoch(model: nn.Module, loader: DataLoader, dev: torch.device, gh: int, gw: int, cin: int) -> float:
    model.eval()
    tot, n = 0.0, 0
    for yf, tgt in loader:
        yf, tgt = yf.to(dev), tgt.to(dev)
        b = yf.shape[0]
        xpad = _zeros_x_hist(b, gh, gw, cin, dev, yf.dtype)
        logits, _ = model.forward_with_aux(xpad, yf)
        tot += F.cross_entropy(logits.permute(0, 4, 1, 2, 3), tgt).item()
        n += 1
    return tot / max(n, 1)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--grid-h", type=int, default=16)
    p.add_argument("--grid-w", type=int, default=16)
    p.add_argument("--seq-len", type=int, default=0)
    p.add_argument("--horizon", type=int, default=2)

    p.add_argument("--train-frac", type=float, default=0.7)
    p.add_argument("--val-frac", type=float, default=0.15)

    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--embed-lambda", type=float, default=0.1)
    p.add_argument("--device", default=None)

    p.add_argument("--num-groups", type=int, default=4)
    p.add_argument("--d-model", type=int, default=32)
    p.add_argument("--e-layers", type=int, default=2)

    p.add_argument("--env-cutoff", default=ENV_CUTOFF_DEFAULT)  # keep if you change it sometimes
    p.add_argument("--max-rows", type=int, default=None)        # keep for debugging
    p.add_argument("--out", default="")                         # optional override; else default path

    return p.parse_args()


def resolve_out(path: str) -> str:
    return path.strip() or DEFAULT_RISK_CLASSIFIER_PATH


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feats = FEATURE_COLS
    c = len(feats)

    cfg = RiskClassifierConfig(
        history_steps=1,
        forecast_horizon=args.horizon,
        in_channels=c,
        out_channels=c,
        num_classes=2,
        num_groups=args.num_groups,
        d_model=args.d_model,
        e_layers=args.e_layers,
        depths=tuple(2 for _ in range(args.e_layers)),
    )
    model = BushfireRiskClassifier(cfg).to(device)
    opt = optim.Adam(model.parameters(), lr=args.lr)

    cutoff = pd.Timestamp(args.env_cutoff) if str(args.env_cutoff).strip() else None
    table = build_training_table_firefusion(
        ENV_CSV_PATHS,
        Path(FIRE_CSV_PATH),
        feats,
        cutoff=cutoff,
    )
    df = table if args.max_rows is None else table.iloc[: args.max_rows]
    feat4, lab4 = long_df_to_grid_tensors(df, args.grid_h, args.grid_w, feats)

    t_tot = feat4.shape[0]
    gh, gw = args.grid_h, args.grid_w
    tr_i = window_origins("train", t_tot, args.seq_len, args.horizon, args.train_frac, args.val_frac)
    va_i = window_origins("val", t_tot, args.seq_len, args.horizon, args.train_frac, args.val_frac)

    train_ld = DataLoader(
        ForecastWindowDataset(feat4, lab4, tr_i, args.seq_len, args.horizon),
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_ld = DataLoader(
        ForecastWindowDataset(feat4, lab4, va_i, args.seq_len, args.horizon),
        batch_size=args.batch_size,
        shuffle=False,
    )
    print(f"T={t_tot}, train_windows={len(tr_i)}, val_windows={len(va_i)}")

    for ep in range(1, args.epochs + 1):
        tr = train_epoch(model, train_ld, opt, args.embed_lambda, device, gh, gw, c)
        va = eval_epoch(model, val_ld, device, gh, gw, c)
        print(f"epoch {ep}/{args.epochs} train_loss={tr:.5f} val_loss={va:.5f}")

    outp = resolve_out(args.out)
    Path(outp).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    # 1) model checkpoint (.pth/.pt)
    torch.save(
        {
            "classifier_state_dict": model.state_dict(),
            "risk_config": cfg,
        },
        outp,
    )
    # 2) preprocessing/config metadata (.pkl)
    preprocess_out = str(Path(outp).with_suffix("")) + "_preprocess.pkl"
    preprocess_payload = {
        "feature_cols": FEATURE_COLS,
        "label_col": LABEL_COL,
        "time_col": TIME_COL,
        "grid_h": args.grid_h,
        "grid_w": args.grid_w,
        "seq_len": args.seq_len,
        "horizon": args.horizon,
        "train_frac": args.train_frac,
        "val_frac": args.val_frac,
        "env_cutoff": args.env_cutoff,
        "env_csv_paths": ENV_CSV_PATHS,
        "fire_csv_path": FIRE_CSV_PATH,
    }
    with open(preprocess_out, "wb") as f:
        pickle.dump(preprocess_payload, f)
    print("saved model:", outp)
    print("saved preprocess:", preprocess_out)


if __name__ == "__main__":
    main()