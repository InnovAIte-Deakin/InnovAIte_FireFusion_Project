"""
Fine-tune DeBERTa with two classification tasks that share one text encoder.

Recommended FireFusion setup
----------------------------
Task 1 (main): ``label``
    0 = non_misinformation
    1 = misinformation

Task 2 (auxiliary): ``misinformation_type``
    Example values: non_misinformation, false_caption, out_of_context_image,
    false_location, false_date, manipulated_image, ai_generated_image,
    fabricated_event, misleading_interpretation.

Expected CSV/JSON records look like::

    {
      "claim": "This image shows today's bushfire in Melbourne.",
      "label": 1,
      "misinformation_type": "out_of_context_image"
    }

Missing Task-2 labels are allowed and are ignored for Task-2 loss/metrics. This is
useful while the new dataset is still being annotated.

From ``ai-modelling/``::

    python src/training/deberta_train_multitask.py \
        --train data/fire_multitask_train.json \
        --val data/fire_multitask_val.json \
        --output-dir checkpoints/fire-deberta-multitask \
        --task2-field misinformation_type

Important: this is MULTITASK TEXT classification, not yet a true multimodal
text+image model. A multimodal version should add an image encoder and fuse its
features with the DeBERTa text representation.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tqdm.auto import tqdm
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.models.misinformation.deberta import DebertaMisinfoTrainConfig


IGNORE_INDEX = -100
TASK1_ID2LABEL = {0: "non_misinformation", 1: "misinformation"}
TASK1_LABEL2ID = {v: k for k, v in TASK1_ID2LABEL.items()}


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_raw_table(path: Path) -> pd.DataFrame:
    """Load a JSON list of records or a CSV without discarding extra task columns."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"{path} must contain a JSON list of records")
        return pd.DataFrame(raw)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file type: {path} (use .json or .csv)")


def normalize_multitask_table(
    df: pd.DataFrame,
    *,
    source: str,
    text_field: str,
    task1_field: str,
    task2_field: str,
) -> pd.DataFrame:
    required = {text_field, task1_field}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"{source} is missing required columns: {sorted(missing)}")

    out = pd.DataFrame()
    out["text"] = df[text_field].astype(str).str.strip()
    if bool((out["text"] == "").any()):
        raise ValueError(f"{source} contains empty text values in {text_field!r}")

    out["task1_label"] = pd.to_numeric(df[task1_field], errors="raise").astype(int)
    bad = ~out["task1_label"].isin([0, 1])
    if bool(bad.any()):
        raise ValueError(
            f"{source}: {task1_field!r} must contain only 0/1; "
            f"offending rows: {out.loc[bad].head()}"
        )

    # Task 2 is optional per row. If the column does not exist, every row is masked.
    if task2_field in df.columns:
        task2 = df[task2_field].copy()
        task2 = task2.where(task2.notna(), None)
        task2 = task2.map(lambda x: str(x).strip() if x is not None else None)
        task2 = task2.map(lambda x: None if x == "" else x)
        out["task2_raw"] = task2
    else:
        out["task2_raw"] = None

    return out.reset_index(drop=True)


def build_task2_mapping(*frames: pd.DataFrame) -> tuple[dict[str, int], dict[int, str]]:
    labels: set[str] = set()
    for frame in frames:
        labels.update(str(x) for x in frame["task2_raw"].dropna().tolist())

    if len(labels) < 2:
        raise ValueError(
            "Task 2 needs at least two labelled classes across train/validation data. "
            "Add the secondary labels or choose a different --task2-field."
        )

    ordered = sorted(labels)
    label2id = {name: idx for idx, name in enumerate(ordered)}
    id2label = {idx: name for name, idx in label2id.items()}
    return label2id, id2label


def encode_task2(frame: pd.DataFrame, label2id: dict[str, int]) -> pd.DataFrame:
    out = frame.copy()

    def encode(value: Any) -> int:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return IGNORE_INDEX
        key = str(value)
        if key not in label2id:
            raise ValueError(f"Unknown Task-2 label {key!r}; known labels: {sorted(label2id)}")
        return label2id[key]

    out["task2_label"] = out["task2_raw"].map(encode).astype(int)
    return out


class MultiTaskTextDataset(Dataset):
    def __init__(
        self,
        texts: list[str],
        task1_labels: list[int],
        task2_labels: list[int],
        tokenizer: Any,
        max_len: int,
    ) -> None:
        if not (len(texts) == len(task1_labels) == len(task2_labels)):
            raise ValueError("texts/task1_labels/task2_labels must have the same length")
        if max_len <= 0:
            raise ValueError("max_len must be greater than zero")

        self.texts = texts
        self.task1_labels = [int(x) for x in task1_labels]
        self.task2_labels = [int(x) for x in task2_labels]
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["task1_labels"] = torch.tensor(self.task1_labels[idx], dtype=torch.long)
        item["task2_labels"] = torch.tensor(self.task2_labels[idx], dtype=torch.long)
        return item


def collate_multitask_batch(batch: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    if not batch:
        raise ValueError("batch must not be empty")
    return {key: torch.stack([row[key] for row in batch], dim=0) for key in batch[0]}


class MultiTaskDeberta(nn.Module):
    """One DeBERTa encoder with two independent classification heads."""

    def __init__(
        self,
        hf_model_id: str,
        *,
        task1_num_labels: int,
        task2_num_labels: int,
        dropout: float | None = None,
    ) -> None:
        super().__init__()
        self.hf_model_id = hf_model_id
        self.encoder = AutoModel.from_pretrained(hf_model_id)
        hidden_size = int(self.encoder.config.hidden_size)

        if dropout is None:
            dropout = getattr(self.encoder.config, "classifier_dropout", None)
            if dropout is None:
                dropout = float(getattr(self.encoder.config, "hidden_dropout_prob", 0.1))

        self.dropout = nn.Dropout(float(dropout))
        self.task1_head = nn.Linear(hidden_size, task1_num_labels)
        self.task2_head = nn.Linear(hidden_size, task2_num_labels)

    def forward(
        self,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        encoder_kwargs: dict[str, Any] = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "return_dict": True,
        }
        if token_type_ids is not None:
            encoder_kwargs["token_type_ids"] = token_type_ids

        outputs = self.encoder(**encoder_kwargs)
        # DeBERTa sequence classification convention: classify from the first token.
        pooled = self.dropout(outputs.last_hidden_state[:, 0])
        return {
            "task1_logits": self.task1_head(pooled),
            "task2_logits": self.task2_head(pooled),
        }


def multitask_loss(
    outputs: dict[str, torch.Tensor],
    task1_labels: torch.Tensor,
    task2_labels: torch.Tensor,
    *,
    task1_weight: float,
    task2_weight: float,
    label_smoothing: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    task1_loss = F.cross_entropy(
        outputs["task1_logits"],
        task1_labels,
        label_smoothing=label_smoothing,
    )

    valid_task2 = task2_labels != IGNORE_INDEX
    if bool(valid_task2.any()):
        task2_loss = F.cross_entropy(
            outputs["task2_logits"][valid_task2],
            task2_labels[valid_task2],
            label_smoothing=label_smoothing,
        )
    else:
        # Keep the tensor on the same device/dtype without adding gradients.
        task2_loss = task1_loss.new_zeros(())

    total = task1_weight * task1_loss + task2_weight * task2_loss
    return total, task1_loss, task2_loss


@torch.no_grad()
def evaluate_multitask(
    model: MultiTaskDeberta,
    loader: DataLoader,
    device: torch.device,
    *,
    task1_weight: float,
    task2_weight: float,
    label_smoothing: float,
) -> dict[str, float]:
    model.eval()

    task1_true: list[int] = []
    task1_pred: list[int] = []
    task2_true: list[int] = []
    task2_pred: list[int] = []

    total_loss = 0.0
    total_task1_loss = 0.0
    total_task2_loss = 0.0
    batches = 0

    for batch in loader:
        batch = {k: v.to(device) for k, v in batch.items()}
        task1_labels = batch.pop("task1_labels")
        task2_labels = batch.pop("task2_labels")

        outputs = model(**batch)
        loss, loss1, loss2 = multitask_loss(
            outputs,
            task1_labels,
            task2_labels,
            task1_weight=task1_weight,
            task2_weight=task2_weight,
            label_smoothing=label_smoothing,
        )

        total_loss += float(loss.item())
        total_task1_loss += float(loss1.item())
        total_task2_loss += float(loss2.item())
        batches += 1

        pred1 = torch.argmax(outputs["task1_logits"], dim=-1)
        task1_true.extend(task1_labels.cpu().tolist())
        task1_pred.extend(pred1.cpu().tolist())

        valid2 = task2_labels != IGNORE_INDEX
        if bool(valid2.any()):
            pred2 = torch.argmax(outputs["task2_logits"], dim=-1)
            task2_true.extend(task2_labels[valid2].cpu().tolist())
            task2_pred.extend(pred2[valid2].cpu().tolist())

    y1 = np.asarray(task1_true, dtype=int)
    p1 = np.asarray(task1_pred, dtype=int)
    task1_prf = precision_recall_fscore_support(
        y1, p1, average="binary", pos_label=1, zero_division=0
    )
    task1_macro = precision_recall_fscore_support(
        y1, p1, average="macro", zero_division=0
    )

    metrics: dict[str, float] = {
        "loss": total_loss / max(batches, 1),
        "task1_loss": total_task1_loss / max(batches, 1),
        "task2_loss": total_task2_loss / max(batches, 1),
        "task1_accuracy": float(accuracy_score(y1, p1)),
        "task1_precision_pos1": float(task1_prf[0]),
        "task1_recall_pos1": float(task1_prf[1]),
        "task1_f1_pos1": float(task1_prf[2]),
        "task1_macro_f1": float(task1_macro[2]),
    }

    if task2_true:
        y2 = np.asarray(task2_true, dtype=int)
        p2 = np.asarray(task2_pred, dtype=int)
        task2_macro = precision_recall_fscore_support(
            y2, p2, average="macro", zero_division=0
        )
        metrics["task2_accuracy"] = float(accuracy_score(y2, p2))
        metrics["task2_macro_f1"] = float(task2_macro[2])
        metrics["task2_n"] = float(len(y2))
        metrics["joint_macro_f1"] = float(
            (metrics["task1_macro_f1"] + metrics["task2_macro_f1"]) / 2.0
        )
    else:
        metrics["task2_accuracy"] = 0.0
        metrics["task2_macro_f1"] = 0.0
        metrics["task2_n"] = 0.0
        metrics["joint_macro_f1"] = metrics["task1_macro_f1"]

    return metrics


def make_dataset(
    frame: pd.DataFrame,
    tokenizer: Any,
    max_len: int,
) -> MultiTaskTextDataset:
    return MultiTaskTextDataset(
        frame["text"].tolist(),
        frame["task1_label"].tolist(),
        frame["task2_label"].tolist(),
        tokenizer,
        max_len,
    )


def save_multitask_checkpoint(
    model: MultiTaskDeberta,
    tokenizer: Any,
    output_dir: Path,
    *,
    task2_label2id: dict[str, int],
    args: argparse.Namespace,
    best_metrics: dict[str, float],
    n_train: int,
    n_val: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save tokenizer in the root directory, encoder in a standard HF subdirectory,
    # and the complete multitask state dict for exact reconstruction.
    tokenizer.save_pretrained(output_dir)
    model.encoder.save_pretrained(output_dir / "encoder")
    torch.save(model.state_dict(), output_dir / "multitask_model.pt")

    config = {
        "architecture": "MultiTaskDeberta",
        "hf_model_id": args.hf_model_id,
        "max_len": args.max_len,
        "text_field": args.text_field,
        "task1_field": args.task1_field,
        "task2_field": args.task2_field,
        "task1_num_labels": 2,
        "task1_id2label": {str(k): v for k, v in TASK1_ID2LABEL.items()},
        "task1_label2id": TASK1_LABEL2ID,
        "task2_num_labels": len(task2_label2id),
        "task2_label2id": task2_label2id,
        "task2_id2label": {str(v): k for k, v in task2_label2id.items()},
        "task1_weight": args.task1_weight,
        "task2_weight": args.task2_weight,
        "label_smoothing": args.label_smoothing,
        "best_val_metrics": best_metrics,
        "n_train": n_train,
        "n_val": n_val,
    }
    (output_dir / "multitask_config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Fine-tune DeBERTa with two classification heads: binary misinformation "
            "+ a configurable secondary classification target."
        )
    )
    ap.add_argument("--train", type=Path, required=True)
    ap.add_argument("--val", type=Path, default=None)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--hf-model-id", type=str, default=DebertaMisinfoTrainConfig.hf_model_id)

    ap.add_argument("--text-field", type=str, default="claim")
    ap.add_argument("--task1-field", type=str, default="label")
    ap.add_argument("--task2-field", type=str, default="misinformation_type")
    ap.add_argument("--task1-weight", type=float, default=1.0)
    ap.add_argument("--task2-weight", type=float, default=1.0)

    ap.add_argument("--test-size", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-len", type=int, default=DebertaMisinfoTrainConfig.max_len)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--warmup-ratio", type=float, default=0.06)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--label-smoothing", type=float, default=0.0)
    ap.add_argument("--early-stopping-patience", type=int, default=3)
    ap.add_argument("--min-delta", type=float, default=1e-4)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--gradient-checkpointing", action="store_true")
    ap.add_argument(
        "--no-amp",
        action="store_true",
        help="Disable CUDA mixed precision; useful when debugging NaN/Inf training.",
    )
    args = ap.parse_args()

    if args.grad_accum <= 0:
        raise ValueError("--grad-accum must be >= 1")
    if args.task1_weight < 0 or args.task2_weight < 0:
        raise ValueError("Task weights must be non-negative")
    if args.task1_weight == 0 and args.task2_weight == 0:
        raise ValueError("At least one task weight must be > 0")

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}")

    raw_train = load_raw_table(args.train)
    train_df = normalize_multitask_table(
        raw_train,
        source=str(args.train),
        text_field=args.text_field,
        task1_field=args.task1_field,
        task2_field=args.task2_field,
    )

    if args.val is not None:
        raw_val = load_raw_table(args.val)
        val_df = normalize_multitask_table(
            raw_val,
            source=str(args.val),
            text_field=args.text_field,
            task1_field=args.task1_field,
            task2_field=args.task2_field,
        )
    else:
        train_df, val_df = train_test_split(
            train_df,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=train_df["task1_label"],
        )
        train_df = train_df.reset_index(drop=True)
        val_df = val_df.reset_index(drop=True)

    task2_label2id, task2_id2label = build_task2_mapping(train_df, val_df)
    train_df = encode_task2(train_df, task2_label2id)
    val_df = encode_task2(val_df, task2_label2id)

    print("Task 1 mapping:", TASK1_ID2LABEL)
    print("Task 2 mapping:", task2_id2label)
    print(
        f"train={len(train_df)} val={len(val_df)} "
        f"task2_train_labelled={(train_df['task2_label'] != IGNORE_INDEX).sum()} "
        f"task2_val_labelled={(val_df['task2_label'] != IGNORE_INDEX).sum()}"
    )

    tokenizer = AutoTokenizer.from_pretrained(args.hf_model_id)
    model = MultiTaskDeberta(
        args.hf_model_id,
        task1_num_labels=2,
        task2_num_labels=len(task2_label2id),
    )
    model.to(device)

    if args.gradient_checkpointing:
        if hasattr(model.encoder, "gradient_checkpointing_enable"):
            model.encoder.gradient_checkpointing_enable()
        if hasattr(model.encoder.config, "use_cache"):
            model.encoder.config.use_cache = False

    train_ds = make_dataset(train_df, tokenizer, args.max_len)
    val_ds = make_dataset(val_df, tokenizer, args.max_len)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_multitask_batch,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_multitask_batch,
        pin_memory=device.type == "cuda",
    )

    optim = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    updates_per_epoch = int(np.ceil(len(train_loader) / args.grad_accum))
    total_steps = max(1, updates_per_epoch * args.epochs)
    warmup_steps = int(total_steps * args.warmup_ratio)
    sched = get_linear_schedule_with_warmup(
        optim,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    use_amp = device.type == "cuda" and not args.no_amp
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_state_path = args.output_dir / ".best_multitask_state.pt"
    best_score = -1.0
    best_metrics: dict[str, float] = {}
    patience = 0

    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        running_task1 = 0.0
        running_task2 = 0.0
        optim.zero_grad(set_to_none=True)

        pbar = tqdm(train_loader, desc=f"train epoch {epoch + 1}/{args.epochs}")
        for step, batch in enumerate(pbar, start=1):
            batch = {k: v.to(device) for k, v in batch.items()}
            task1_labels = batch.pop("task1_labels")
            task2_labels = batch.pop("task2_labels")

            with torch.cuda.amp.autocast(enabled=use_amp):
                outputs = model(**batch)
                total_loss, loss1, loss2 = multitask_loss(
                    outputs,
                    task1_labels,
                    task2_labels,
                    task1_weight=args.task1_weight,
                    task2_weight=args.task2_weight,
                    label_smoothing=args.label_smoothing,
                )
                loss = total_loss / args.grad_accum

            if not bool(torch.isfinite(loss)):
                raise RuntimeError(
                    f"Non-finite loss at epoch={epoch + 1}, step={step}. "
                    "Retry with --no-amp and/or a smaller --lr."
                )

            scaler.scale(loss).backward()
            running_loss += float(total_loss.detach().item())
            running_task1 += float(loss1.detach().item())
            running_task2 += float(loss2.detach().item())

            should_update = (step % args.grad_accum == 0) or (step == len(train_loader))
            if should_update:
                scaler.unscale_(optim)
                grad_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    args.max_grad_norm,
                    error_if_nonfinite=True,
                )
                scaler.step(optim)
                scaler.update()
                optim.zero_grad(set_to_none=True)
                sched.step()
            else:
                grad_norm = torch.tensor(float("nan"))

            pbar.set_postfix(
                loss=f"{running_loss / step:.4f}",
                task1=f"{running_task1 / step:.4f}",
                task2=f"{running_task2 / step:.4f}",
                lr=f"{sched.get_last_lr()[0]:.2e}",
            )

        metrics = evaluate_multitask(
            model,
            val_loader,
            device,
            task1_weight=args.task1_weight,
            task2_weight=args.task2_weight,
            label_smoothing=args.label_smoothing,
        )

        print(
            f"epoch {epoch + 1}: "
            f"val_loss={metrics['loss']:.4f} "
            f"task1_acc={metrics['task1_accuracy']:.4f} "
            f"task1_macro_f1={metrics['task1_macro_f1']:.4f} "
            f"task2_acc={metrics['task2_accuracy']:.4f} "
            f"task2_macro_f1={metrics['task2_macro_f1']:.4f} "
            f"joint_macro_f1={metrics['joint_macro_f1']:.4f}"
        )

        score = metrics["joint_macro_f1"]
        if score > best_score + args.min_delta:
            best_score = score
            best_metrics = dict(metrics)
            torch.save(model.state_dict(), best_state_path)
            patience = 0
            print("saved new best multitask state")
        else:
            patience += 1

        if patience >= args.early_stopping_patience:
            print(
                f"early stopping after epoch {epoch + 1}; "
                f"best joint_macro_f1={best_score:.4f}"
            )
            break

    if best_state_path.exists():
        best_state = torch.load(best_state_path, map_location=device)
        model.load_state_dict(best_state)

    save_multitask_checkpoint(
        model,
        tokenizer,
        args.output_dir,
        task2_label2id=task2_label2id,
        args=args,
        best_metrics=best_metrics,
        n_train=int(len(train_df)),
        n_val=int(len(val_df)),
    )

    if best_state_path.exists():
        best_state_path.unlink()

    print(f"saved multitask model to {args.output_dir}")
    print(f"best joint_macro_f1={best_score:.4f}")


if __name__ == "__main__":
    main()
