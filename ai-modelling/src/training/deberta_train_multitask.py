"""
Train the shared DeBERTa multi-task misinformation model.

The model uses one shared DeBERTa encoder with three classification heads:
    - misinfo: 2 classes
    - urgency: 3 classes
    - humanitarian: 6 classes

Rows may contain labels for one or more tasks. Missing task labels are
represented with -100 and ignored by the corresponding loss/metrics.

Example:
    python src/training/deberta_train_multitask.py ^
        --train data/train.json ^
        --val data/val.json ^
        --output-dir checkpoints/misinfo-multitask
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

# Allow the script to be run from the repository root.
AI_MODELLING_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AI_MODELLING_ROOT))

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from src.models.misinformation.deberta import (
    DEFAULT_HF_MODEL_ID,
    MultiTaskDeberta,
    save_multitask_checkpoint,
)


MISSING_LABEL = -100


TASK_NAMES = ("misinfo", "urgency", "humanitarian")


def set_seed(seed: int) -> None:
    """Set random seeds for reproducible training."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_multitask_table(path: Path) -> list[dict[str, Any]]:
    """
    Load multi-task records from JSON or CSV.

    Each record should contain a text field named either 'claim' or 'text'.
    Task labels use:
        misinfo
        urgency
        humanitarian

    Missing task labels are allowed.
    """
    suffix = path.suffix.lower()

    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8-sig"))

        if not isinstance(raw, list):
            raise ValueError(f"{path} must contain a JSON list of records")

        records = raw

    elif suffix == ".csv":
        import pandas as pd

        records = pd.read_csv(path).to_dict(orient="records")

    else:
        raise ValueError(
            f"Unsupported file type: {path}. Use .json or .csv."
        )

    if not records:
        raise ValueError(f"{path} contains no records")

    return records


def get_text(record: dict[str, Any]) -> str:
    """Extract the text field from a training record."""
    if "claim" in record:
        text = record["claim"]
    elif "text" in record:
        text = record["text"]
    else:
        raise KeyError(
            "Each record must contain either 'claim' or 'text'."
        )

    if text is None or not str(text).strip():
        raise ValueError("Training records must contain non-empty text.")

    return str(text)


def get_label(row: dict, task: str, row_index: int) -> int:
    value = row.get(task)

    if value is None or value == "":
        return MISSING_LABEL

    try:
        label = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Row {row_index}: '{task}' must be an integer label "
            f"or missing. Got {value!r}."
        ) from exc

    max_labels = {
        "misinfo": 2,
        "urgency": 3,
        "humanitarian": 6,
    }

    if not 0 <= label < max_labels[task]:
        raise ValueError(
            f"Row {row_index}: '{task}' label {label} is invalid. "
            f"Expected 0-{max_labels[task] - 1}."
        )

    return label


class MultiTaskTextClsDataset(Dataset):
    """Tokenized dataset for the three multi-task classification heads."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: Any,
        max_len: int,
    ) -> None:
        if not records:
            raise ValueError("records must not be empty")

        if max_len <= 0:
            raise ValueError("max_len must be greater than zero")

        self.records = records
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        record = self.records[idx]
        text = get_text(record)

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value in encoded.items()
        }

        for task_name in TASK_NAMES:
            item[f"{task_name}_labels"] = torch.tensor(
                get_label(record, task_name, idx),
                dtype=torch.long,
            )

        return item


def collate_multitask_batch(
    batch: list[dict[str, Any]],
) -> dict[str, Any]:
    """Collate tokenized inputs and task-specific labels."""
    if not batch:
        raise ValueError("batch must not be empty")

    input_keys = [
        key
        for key in batch[0]
        if not key.endswith("_labels")
    ]

    output: dict[str, Any] = {}

    for key in input_keys:
        output[key] = torch.stack(
            [item[key] for item in batch],
            dim=0,
        )

    for task_name in TASK_NAMES:
        key = f"{task_name}_labels"
        output[key] = torch.stack(
            [item[key] for item in batch],
            dim=0,
        )

    return output


def move_batch_to_device(
    batch: dict[str, Any],
    device: torch.device,
) -> dict[str, Any]:
    """Move all tensors in a batch to the selected device."""
    return {
        key: value.to(device)
        for key, value in batch.items()
    }


def compute_multitask_loss(
    logits: dict[str, torch.Tensor],
    batch: dict[str, Any],
) -> tuple[torch.Tensor, list[str]]:
    """
    Calculate the mean cross-entropy across active tasks.

    A task is active only when at least one valid label is present in
    the current batch.
    """
    losses: list[torch.Tensor] = []
    active_tasks: list[str] = []

    for task_name in TASK_NAMES:
        labels = batch[f"{task_name}_labels"]

        valid = labels != MISSING_LABEL

        if not bool(valid.any()):
            continue

        task_loss = torch.nn.functional.cross_entropy(
            logits[task_name],
            labels,
            ignore_index=MISSING_LABEL,
        )

        losses.append(task_loss)
        active_tasks.append(task_name)

    if not losses:
        raise ValueError(
            "Batch contains no labels for any multi-task head."
        )

    return torch.stack(losses).mean(), active_tasks


def evaluate(
    model: MultiTaskDeberta,
    loader: DataLoader,
    device: torch.device,
) -> dict[str, Any]:
    """Evaluate loss, accuracy and macro F1 for each available task."""
    model.eval()

    total_loss = 0.0
    batches = 0

    predictions: dict[str, list[int]] = {
        task: [] for task in TASK_NAMES
    }
    targets: dict[str, list[int]] = {
        task: [] for task in TASK_NAMES
    }

    with torch.no_grad():
        for batch in loader:
            batch = move_batch_to_device(batch, device)

            logits = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                token_type_ids=batch.get("token_type_ids"),
            )

            loss, _ = compute_multitask_loss(logits, batch)

            total_loss += float(loss.item())
            batches += 1

            for task_name in TASK_NAMES:
                labels = batch[f"{task_name}_labels"]
                valid = labels != MISSING_LABEL

                if not bool(valid.any()):
                    continue

                preds = torch.argmax(
                    logits[task_name],
                    dim=-1,
                )

                predictions[task_name].extend(
                    preds[valid].cpu().tolist()
                )
                targets[task_name].extend(
                    labels[valid].cpu().tolist()
                )

    metrics: dict[str, Any] = {
        "loss": total_loss / max(batches, 1),
        "tasks": {},
    }

    macro_f1_values: list[float] = []

    for task_name in TASK_NAMES:
        y_true = targets[task_name]
        y_pred = predictions[task_name]

        if not y_true:
            continue

        accuracy = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )

        metrics["tasks"][task_name] = {
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
            "samples": len(y_true),
        }

        macro_f1_values.append(float(macro_f1))

    metrics["mean_macro_f1"] = (
        float(np.mean(macro_f1_values))
        if macro_f1_values
        else 0.0
    )

    return metrics


def train_one_epoch(
    model: MultiTaskDeberta,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    device: torch.device,
    gradient_accumulation_steps: int,
) -> float:
    """Train the model for one epoch."""
    model.train()

    running_loss = 0.0
    optimizer.zero_grad(set_to_none=True)

    progress = tqdm(
        loader,
        desc="Training",
        leave=False,
    )

    for step, batch in enumerate(progress, start=1):
        batch = move_batch_to_device(batch, device)

        logits = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            token_type_ids=batch.get("token_type_ids"),
        )

        loss, active_tasks = compute_multitask_loss(
            logits,
            batch,
        )

        scaled_loss = loss / gradient_accumulation_steps
        scaled_loss.backward()

        if (
            step % gradient_accumulation_steps == 0
            or step == len(loader)
        ):
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=1.0,
            )

            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)

        running_loss += float(loss.item())

        progress.set_postfix(
            loss=f"{loss.item():.4f}",
            tasks=",".join(active_tasks),
        )

    return running_loss / max(len(loader), 1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train the FireFusion multi-task DeBERTa model."
    )

    parser.add_argument(
        "--train",
        type=Path,
        required=True,
        help="Training dataset (.json or .csv).",
    )

    parser.add_argument(
        "--val",
        type=Path,
        required=True,
        help="Validation dataset (.json or .csv).",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the best model checkpoint.",
    )

    parser.add_argument(
        "--hf-model-id",
        default=DEFAULT_HF_MODEL_ID,
        help="Hugging Face DeBERTa model identifier.",
    )

    parser.add_argument(
        "--max-len",
        type=int,
        default=256,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=2e-5,
    )

    parser.add_argument(
        "--weight-decay",
        type=float,
        default=0.01,
    )

    parser.add_argument(
        "--warmup-ratio",
        type=float,
        default=0.1,
    )

    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=2,
        help="Early-stopping patience measured in epochs.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero")

    if args.epochs <= 0:
        raise ValueError("--epochs must be greater than zero")

    if args.gradient_accumulation_steps <= 0:
        raise ValueError(
            "--gradient-accumulation-steps must be greater than zero"
        )

    if not 0 <= args.warmup_ratio < 1:
        raise ValueError("--warmup-ratio must be in [0, 1)")

    set_seed(args.seed)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")
    print(f"Loading tokenizer: {args.hf_model_id}")

    tokenizer = AutoTokenizer.from_pretrained(
        args.hf_model_id
    )

    train_records = load_multitask_table(args.train)
    val_records = load_multitask_table(args.val)

    print(f"Training records: {len(train_records)}")
    print(f"Validation records: {len(val_records)}")

    train_dataset = MultiTaskTextClsDataset(
        train_records,
        tokenizer,
        args.max_len,
    )

    val_dataset = MultiTaskTextClsDataset(
        val_records,
        tokenizer,
        args.max_len,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_multitask_batch,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_multitask_batch,
    )

    print("Building multi-task DeBERTa model...")

    model = MultiTaskDeberta(
        args.hf_model_id
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    total_optimizer_steps = (
        (len(train_loader) + args.gradient_accumulation_steps - 1)
        // args.gradient_accumulation_steps
    ) * args.epochs

    warmup_steps = int(
        total_optimizer_steps * args.warmup_ratio
    )

    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_optimizer_steps,
    )

    best_f1 = -float("inf")
    epochs_without_improvement = 0

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    history: list[dict[str, Any]] = []

    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")

        train_loss = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
        )

        val_metrics = evaluate(
            model=model,
            loader=val_loader,
            device=device,
        )

        mean_macro_f1 = val_metrics["mean_macro_f1"]

        epoch_result = {
            "epoch": epoch,
            "train_loss": train_loss,
            "validation": val_metrics,
        }

        history.append(epoch_result)

        print(f"Train loss: {train_loss:.4f}")
        print(f"Validation loss: {val_metrics['loss']:.4f}")
        print(
            f"Validation mean macro F1: "
            f"{mean_macro_f1:.4f}"
        )

        for task_name, task_metrics in val_metrics["tasks"].items():
            print(
                f"  {task_name}: "
                f"accuracy={task_metrics['accuracy']:.4f}, "
                f"macro_f1={task_metrics['macro_f1']:.4f}, "
                f"samples={task_metrics['samples']}"
            )

        if mean_macro_f1 > best_f1:
            best_f1 = mean_macro_f1
            epochs_without_improvement = 0

            print("New best model. Saving checkpoint...")

            save_multitask_checkpoint(
                model=model,
                tokenizer=tokenizer,
                output_dir=args.output_dir,
                max_len=args.max_len,
            )

            (args.output_dir / "training_config.json").write_text(
                json.dumps(
                    vars(args),
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            (args.output_dir / "training_history.json").write_text(
                json.dumps(
                    history,
                    indent=2,
                ),
                encoding="utf-8",
            )

        else:
            epochs_without_improvement += 1

            if epochs_without_improvement >= args.patience:
                print("Early stopping triggered.")
                break

    print("\nTraining complete.")
    print(f"Best validation mean macro F1: {best_f1:.4f}")
    print(f"Checkpoint: {args.output_dir}")


if __name__ == "__main__":
    main()