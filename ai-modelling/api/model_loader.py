"""
Load Hugging Face checkpoints declared in ``api/config/models.yaml``.

Extend ``_load_one`` when adding new ``kind`` values (e.g. bushfire torch checkpoints).
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import yaml

_API_DIR = Path(__file__).resolve().parent
_AI_MODELLING_ROOT = _API_DIR.parent

if str(_AI_MODELLING_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_MODELLING_ROOT))

from src.models.misinformation.deberta import (
    DebertaMisinfoTrainConfig,
    load_classifier_from_checkpoint,
)


@dataclass(frozen=True)
class LoadedModel:
    """Runtime bundle for one loaded checkpoint."""

    model_id: str
    domain: str
    kind: str
    tokenizer: Any
    model: Any
    device: torch.device
    max_len: int
    checkpoint_path: Path


_REGISTRY: dict[str, LoadedModel] = {}
_LOAD_ERRORS: list[str] = []


def _resolve_checkpoint(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    p = Path(path_value)
    if p.is_absolute():
        return p
    return (_AI_MODELLING_ROOT / p).resolve()


def _load_deberta_sequence_binary(model_id: str, domain: str, ckpt: Path) -> LoadedModel:
    if not ckpt.is_dir():
        raise FileNotFoundError(f"Checkpoint not found for '{model_id}': {ckpt}")
    tokenizer, model = load_classifier_from_checkpoint(ckpt)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    meta_path = ckpt / "training_meta.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        max_len = int(meta.get("max_len", DebertaMisinfoTrainConfig.max_len))
    else:
        max_len = DebertaMisinfoTrainConfig.max_len
    return LoadedModel(
        model_id=model_id,
        domain=domain,
        kind="deberta_sequence_binary",
        tokenizer=tokenizer,
        model=model,
        device=device,
        max_len=max_len,
        checkpoint_path=ckpt,
    )


def _load_one(entry: dict[str, Any]) -> LoadedModel | None:
    model_id = str(entry["id"])
    domain = str(entry.get("domain", "unknown"))
    kind = str(entry.get("kind", ""))
    enabled = bool(entry.get("enabled", True))

    if not enabled:
        return None

    if kind == "placeholder":
        return None

    if kind == "deberta_sequence_binary":
        ckpt = _resolve_checkpoint(entry.get("checkpoint"))
        if ckpt is None:
            raise ValueError(f"model '{model_id}': deberta_sequence_binary requires checkpoint")
        return _load_deberta_sequence_binary(model_id, domain, ckpt)

    raise ValueError(f"model '{model_id}': unknown kind '{kind}'")


def load_models(config_path: Path | None = None) -> dict[str, LoadedModel]:
    """
    Load all enabled models from YAML. Safe to call from FastAPI lifespan.
    """
    global _REGISTRY, _LOAD_ERRORS
    _REGISTRY = {}
    _LOAD_ERRORS = []

    cfg_path = config_path or (_API_DIR / "config" / "models.yaml")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "models" not in raw:
        raise ValueError(f"{cfg_path} must be a mapping with a 'models' list")

    for entry in raw["models"]:
        if not isinstance(entry, dict):
            continue
        try:
            loaded = _load_one(entry)
            if loaded is not None:
                mid = loaded.model_id
                if mid in _REGISTRY:
                    raise ValueError(f"duplicate model id: {mid}")
                _REGISTRY[mid] = loaded
        except Exception as e:  # noqa: BLE001
            _LOAD_ERRORS.append(f"{entry.get('id', '?')}: {e}")

    return _REGISTRY.copy()


def get_model(model_id: str) -> LoadedModel:
    if model_id not in _REGISTRY:
        raise KeyError(f"unknown model_id={model_id!r}; loaded: {list(_REGISTRY.keys())}")
    return _REGISTRY[model_id]


def list_models(*, domain: str | None = None) -> list[LoadedModel]:
    out = list(_REGISTRY.values())
    if domain is not None:
        out = [m for m in out if m.domain == domain]
    return out


def default_model_id_for_domain(domain: str) -> str:
    models = list_models(domain=domain)
    if not models:
        raise RuntimeError(f"no loaded models for domain={domain!r}")
    return models[0].model_id


def is_ready() -> bool:
    return bool(_REGISTRY)


def load_errors() -> list[str]:
    return list(_LOAD_ERRORS)