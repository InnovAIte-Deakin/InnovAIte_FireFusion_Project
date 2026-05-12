"""
DeBERTa v3-large: model wiring and data objects that feed the classifier.

Checkpoints from ``build_fresh_classifier`` / ``save_pretrained`` include ``id2label``
and ``label2id`` on the model config. Training loops, metrics, and seeding live in
``src/training/train_deberta.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_HF_MODEL_ID = "microsoft/deberta-v3-large"

DEFAULT_ID2LABEL = {0: "non_misinformation", 1: "misinformation"}
DEFAULT_LABEL2ID = {v: k for k, v in DEFAULT_ID2LABEL.items()}


@dataclass(frozen=True)
class DebertaMisinfoTrainConfig:
    hf_model_id: str = DEFAULT_HF_MODEL_ID
    max_len: int = 256
    num_labels: int = 2


def load_table(path: Path, text_col: str, label_col: str) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"{path} must contain a JSON list of records")
        df = pd.DataFrame(raw)
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {path} (use .json or .csv)")

    if text_col not in df.columns or label_col not in df.columns:
        raise KeyError(f"{path} must have columns {text_col!r} and {label_col!r}; got {list(df.columns)}")

    out = pd.DataFrame({"text": df[text_col].astype(str), "label": df[label_col]})
    out["label"] = pd.to_numeric(out["label"], errors="raise").astype(int)
    bad = ~out["label"].isin([0, 1])
    if bool(bad.any()):
        raise ValueError(f"Labels must be 0 or 1; offending rows: {out.loc[bad].head()}")
    return out.reset_index(drop=True)


class TextClsDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[int], tokenizer: Any, max_len: int):
        self.texts = texts
        self.labels = [int(x) for x in labels]
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def collate_text_cls_batch(batch: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [k for k in batch[0].keys() if k != "labels"]
    out: dict[str, Any] = {}
    for k in keys:
        out[k] = torch.stack([b[k] for b in batch], dim=0)
    out["labels"] = torch.stack([b["labels"] for b in batch], dim=0)
    return out


def build_fresh_classifier(
    hf_model_id: str = DEFAULT_HF_MODEL_ID,
    *,
    num_labels: int = 2,
    id2label: dict[int, str] | None = None,
    label2id: dict[str, int] | None = None,
) -> tuple[Any, Any]:
    id2label = id2label or DEFAULT_ID2LABEL
    label2id = label2id or DEFAULT_LABEL2ID
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
    model = AutoModelForSequenceClassification.from_pretrained(
        hf_model_id,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )
    return tokenizer, model


def load_classifier_from_checkpoint(checkpoint_dir: Path | str) -> tuple[Any, Any]:
    path = Path(checkpoint_dir)
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path)
    return tokenizer, model


@torch.no_grad()
def classify_text(
    text: str,
    *,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    max_len: int,
) -> dict[str, Any]:
    """
    Tokenize a single string and run the classifier head (softmax probs).
    API layers can add severity, rationale, etc.
    """
    model.eval()
    enc = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=max_len,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    logits = model(**enc).logits
    probs = torch.softmax(logits, dim=-1).squeeze(0)
    label_id = int(torch.argmax(probs).item())
    raw_map = getattr(model.config, "id2label", None) or {}
    id2label: dict[int, str] = {int(k): str(v) for k, v in dict(raw_map).items()}
    label_name = id2label.get(label_id, str(label_id))
    probabilities = {id2label.get(i, f"class_{i}"): float(probs[i].item()) for i in range(probs.shape[0])}
    return {
        "label_id": label_id,
        "label": label_name,
        "confidence": float(probs[label_id].item()),
        "probabilities": probabilities,
    }