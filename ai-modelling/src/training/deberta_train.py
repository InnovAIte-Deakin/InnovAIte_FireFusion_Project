"""
Train the DeBERTa misinformation classifier.

The training data must be a CSV or JSON file containing:
- claim: text to classify
- label: 0 for non_misinformation or 1 for misinformation

Example:

python src/training/deberta_train.py \
    --train data/train.json \
    --output-dir checkpoints/misinfo-deberta
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
from transformers import get_linear_schedule_with_warmup


_ROOT = Path(__file__).resolve().parents[2]

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


from src.models.misinformation.deberta import (
    DebertaMisinfoTrainConfig,
    TextClsDataset,
    build_fresh_classifier,
    collate_text_cls_batch,
    load_classifier_from_checkpoint,
    load_table,
)


def set_seed(seed: int) -> None:
    """Set random seeds for reproducible training."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@torch.no_grad()
def evaluate_model(
    model: Any,
    data_loader: DataLoader,
    device: torch.device,
) -> dict[str, float]:
    """Calculate validation loss and classification metrics."""

    model.eval()

    total_loss = 0.0
    total_examples = 0
    labels: list[int] = []
    predictions: list[int] = []

    for batch in data_loader:
        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        output = model(**batch)
        batch_size = batch["labels"].size(0)

        total_loss += output.loss.item() * batch_size
        total_examples += batch_size

        predicted_labels = torch.argmax(
            output.logits,
            dim=-1,
        )

        labels.extend(
            batch["labels"].cpu().tolist()
        )

        predictions.extend(
            predicted_labels.cpu().tolist()
        )

    if total_examples == 0:
        raise ValueError("Validation dataset is empty.")

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="binary",
            pos_label=1,
            zero_division=0,
        )
    )

    _, _, macro_f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            labels=[0, 1],
            average="macro",
            zero_division=0,
        )
    )

    return {
        "loss": float(total_loss / total_examples),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "macro_f1": float(macro_f1),
    }


def train_epoch(
    model: Any,
    data_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    scaler: Any,
    device: torch.device,
    grad_accum: int,
    max_grad_norm: float,
    use_amp: bool,
    epoch: int,
    total_epochs: int,
) -> float:
    """Train the model for one epoch."""

    model.train()
    optimizer.zero_grad(set_to_none=True)

    total_loss = 0.0
    total_examples = 0
    total_batches = len(data_loader)

    progress = tqdm(
        data_loader,
        desc=f"Training epoch {epoch}/{total_epochs}",
    )

    for step, batch in enumerate(
        progress,
        start=1,
    ):
        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        # Use the real size of the final accumulation group
        incomplete_group_size = total_batches % grad_accum

        if (
            incomplete_group_size
            and step > total_batches - incomplete_group_size
        ):
            accumulation_size = incomplete_group_size
        else:
            accumulation_size = grad_accum

        with torch.amp.autocast(
            device_type=device.type,
            enabled=use_amp,
        ):
            output = model(**batch)
            raw_loss = output.loss
            loss = raw_loss / accumulation_size

        scaler.scale(loss).backward()

        batch_size = batch["labels"].size(0)

        total_loss += raw_loss.item() * batch_size
        total_examples += batch_size

        should_update = (
            step % grad_accum == 0
            or step == total_batches
        )

        if should_update:
            scaler.unscale_(optimizer)

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_grad_norm,
            )

            scaler.step(optimizer)
            scaler.update()

            optimizer.zero_grad(set_to_none=True)

            # Update the scheduler after every optimiser step
            scheduler.step()

        average_loss = total_loss / total_examples

        progress.set_postfix(
            train_loss=f"{average_loss:.4f}"
        )

    return total_loss / total_examples


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Train DeBERTa for binary misinformation "
            "classification."
        )
    )

    parser.add_argument(
        "--train",
        type=Path,
        required=True,
        help="Training CSV or JSON file.",
    )

    parser.add_argument(
        "--val",
        type=Path,
        default=None,
        help="Optional validation CSV or JSON file.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory used to save the checkpoint.",
    )

    parser.add_argument(
        "--hf-model-id",
        type=str,
        default=DebertaMisinfoTrainConfig.hf_model_id,
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.1,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--max-len",
        type=int,
        default=DebertaMisinfoTrainConfig.max_len,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--grad-accum",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=4,
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
        default=0.06,
    )

    parser.add_argument(
        "--max-grad-norm",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--early-stopping-patience",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--min-delta",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--gradient-checkpointing",
        action="store_true",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1.")

    if args.grad_accum < 1:
        raise ValueError("--grad-accum must be at least 1.")

    if args.epochs < 1:
        raise ValueError("--epochs must be at least 1.")

    if not 0 < args.test_size < 1:
        raise ValueError("--test-size must be between 0 and 1.")

    set_seed(args.seed)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Using device: {device}")

    train_df = load_table(
        args.train,
        "claim",
        "label",
    )

    if args.val is not None:
        val_df = load_table(
            args.val,
            "claim",
            "label",
        )

        split_method = "separate_validation_file"

    else:
        label_counts = train_df["label"].value_counts()

        if (
            len(label_counts) != 2
            or label_counts.min() < 2
        ):
            raise ValueError(
                "A stratified split needs both labels "
                "and at least two examples of each label."
            )

        train_df, val_df = train_test_split(
            train_df,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=train_df["label"],
        )

        split_method = "stratified_split"

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    tokenizer, model = build_fresh_classifier(
        args.hf_model_id
    )

    model.to(device)

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    train_dataset = TextClsDataset(
        train_df["text"].tolist(),
        train_df["label"].tolist(),
        tokenizer,
        args.max_len,
    )

    val_dataset = TextClsDataset(
        val_df["text"].tolist(),
        val_df["label"].tolist(),
        tokenizer,
        args.max_len,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_text_cls_batch,
        pin_memory=device.type == "cuda",
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_text_cls_batch,
        pin_memory=device.type == "cuda",
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    steps_per_epoch = int(
        np.ceil(
            len(train_loader) / args.grad_accum
        )
    )

    total_steps = max(
        1,
        steps_per_epoch * args.epochs,
    )

    warmup_steps = int(
        total_steps * args.warmup_ratio
    )

    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    use_amp = device.type == "cuda"

    scaler = torch.amp.GradScaler(
        device=device.type,
        enabled=use_amp,
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    best_macro_f1 = -1.0
    best_epoch = 0
    best_metrics: dict[str, float] = {}
    history: list[dict[str, float | int]] = []

    patience = 0
    epochs_completed = 0

    for epoch in range(1, args.epochs + 1):
        epochs_completed = epoch

        train_loss = train_epoch(
            model=model,
            data_loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            device=device,
            grad_accum=args.grad_accum,
            max_grad_norm=args.max_grad_norm,
            use_amp=use_amp,
            epoch=epoch,
            total_epochs=args.epochs,
        )

        val_metrics = evaluate_model(
            model,
            val_loader,
            device,
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                **val_metrics,
            }
        )

        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} | "
            f"accuracy={val_metrics['accuracy']:.4f} | "
            f"macro_f1={val_metrics['macro_f1']:.4f} | "
            f"precision={val_metrics['precision']:.4f} | "
            f"recall={val_metrics['recall']:.4f}"
        )

        improved = (
            val_metrics["macro_f1"]
            > best_macro_f1 + args.min_delta
        )

        if improved:
            best_macro_f1 = val_metrics["macro_f1"]
            best_epoch = epoch
            best_metrics = dict(val_metrics)
            patience = 0

            model.save_pretrained(args.output_dir)
            tokenizer.save_pretrained(args.output_dir)

            print(
                f"Saved best checkpoint to "
                f"{args.output_dir}"
            )

        else:
            patience += 1

        if patience >= args.early_stopping_patience:
            print("Early stopping triggered.")
            break

    if best_epoch == 0:
        raise RuntimeError(
            "Training finished without saving a checkpoint."
        )
    # Free memory before checking the saved model
    del optimizer
    del scheduler
    del scaler
    del model

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # Reload the checkpoint to confirm that it works
    _, reloaded_model = load_classifier_from_checkpoint(
        args.output_dir
    )

    if reloaded_model.config.num_labels != 2:
        raise RuntimeError(
            "Reloaded checkpoint has an incorrect "
            "number of labels."
        )

    reloaded_model.to(device)

    final_metrics = evaluate_model(
        reloaded_model,
        val_loader,
        device,
    )

    label_mapping = {
        str(key): value
        for key, value
        in reloaded_model.config.id2label.items()
    }

    metadata = {
        "hf_model_id": args.hf_model_id,
        "checkpoint_reload_verified": True,
        "label_mapping": label_mapping,
        "data": {
            "train_path": str(args.train),
            "validation_path": (
                str(args.val)
                if args.val is not None
                else None
            ),
            "split_method": split_method,
            "text_field": "claim",
            "label_field": "label",
            "train_size": len(train_df),
            "validation_size": len(val_df),
        },
        "training_settings": {
            "seed": args.seed,
            "max_len": args.max_len,
            "batch_size": args.batch_size,
            "gradient_accumulation_steps": args.grad_accum,
            "effective_batch_size": (
                args.batch_size * args.grad_accum
            ),
            "epochs_requested": args.epochs,
            "epochs_completed": epochs_completed,
            "learning_rate": args.lr,
            "weight_decay": args.weight_decay,
            "warmup_ratio": args.warmup_ratio,
            "gradient_checkpointing": (
                args.gradient_checkpointing
            ),
            "device": str(device),
        },
        "best_epoch": best_epoch,
        "best_validation": best_metrics,
        "final_validation": final_metrics,
        "history": history,
    }

    metadata_path = (
        args.output_dir / "training_meta.json"
    )

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("Checkpoint reload verification: passed")

    print(
        f"Final validation | "
        f"loss={final_metrics['loss']:.4f} | "
        f"accuracy={final_metrics['accuracy']:.4f} | "
        f"macro_f1={final_metrics['macro_f1']:.4f}"
    )

    print(f"Saved model to: {args.output_dir}")
    print(f"Saved metadata to: {metadata_path}")


if __name__ == "__main__":
    main()