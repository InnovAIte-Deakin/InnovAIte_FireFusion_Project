"""
Fine-tune DeBERTa for binary misinformation classification.

Training data may be CSV or JSON and must contain:
- claim: text to classify
- label: 0 for non_misinformation or 1 for misinformation

Run from the ai-modelling folder:

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
    """Set random seeds to make training more reproducible."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate training arguments before starting."""

    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")

    if args.grad_accum < 1:
        raise ValueError("--grad-accum must be at least 1")

    if args.epochs < 1:
        raise ValueError("--epochs must be at least 1")

    if args.max_len < 1:
        raise ValueError("--max-len must be at least 1")

    if args.lr <= 0:
        raise ValueError("--lr must be greater than 0")

    if not 0 < args.test_size < 1:
        raise ValueError("--test-size must be between 0 and 1")

    if not 0 <= args.warmup_ratio < 1:
        raise ValueError("--warmup-ratio must be between 0 and 1")

    if args.max_grad_norm <= 0:
        raise ValueError("--max-grad-norm must be greater than 0")

    if args.early_stopping_patience < 1:
        raise ValueError(
            "--early-stopping-patience must be at least 1"
        )

    if args.min_delta < 0:
        raise ValueError("--min-delta cannot be negative")


def validate_datasets(train_df: Any, val_df: Any) -> None:
    """Check that the prepared datasets can be used for training."""

    if train_df.empty:
        raise ValueError("The training dataset is empty")

    if val_df.empty:
        raise ValueError("The validation dataset is empty")

    train_labels = {
        int(label)
        for label in train_df["label"].unique()
    }

    if train_labels != {0, 1}:
        raise ValueError(
            "The training dataset must contain both labels: "
            "0 = non_misinformation and 1 = misinformation"
        )


def normalise_id2label(model: Any) -> dict[int, str]:
    """Return the model label mapping using integer keys."""

    raw_mapping = getattr(model.config, "id2label", None) or {}

    return {
        int(key): str(value)
        for key, value in dict(raw_mapping).items()
    }


@torch.no_grad()
def evaluate_classification(
    model: Any,
    loader: DataLoader,
    device: torch.device,
) -> dict[str, float]:
    """Calculate validation loss and classification metrics."""

    model.eval()

    all_labels: list[int] = []
    all_predictions: list[int] = []

    total_loss = 0.0
    total_examples = 0

    for batch in loader:
        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        output = model(**batch)

        batch_size = int(batch["labels"].shape[0])

        total_loss += (
            float(output.loss.detach().item())
            * batch_size
        )

        total_examples += batch_size

        predictions = torch.argmax(
            output.logits,
            dim=-1,
        )

        all_labels.extend(
            batch["labels"].detach().cpu().tolist()
        )

        all_predictions.extend(
            predictions.detach().cpu().tolist()
        )

    if total_examples == 0:
        raise ValueError(
            "The validation data loader is empty"
        )

    labels_array = np.asarray(
        all_labels,
        dtype=int,
    )

    predictions_array = np.asarray(
        all_predictions,
        dtype=int,
    )

    accuracy = float(
        accuracy_score(
            labels_array,
            predictions_array,
        )
    )

    binary_metrics = precision_recall_fscore_support(
        labels_array,
        predictions_array,
        average="binary",
        pos_label=1,
        zero_division=0,
    )

    macro_metrics = precision_recall_fscore_support(
        labels_array,
        predictions_array,
        labels=[0, 1],
        average="macro",
        zero_division=0,
    )

    return {
        "loss": total_loss / total_examples,
        "accuracy": accuracy,
        "precision_binary_pos1": float(
            binary_metrics[0]
        ),
        "recall_binary_pos1": float(
            binary_metrics[1]
        ),
        "f1_binary_pos1": float(
            binary_metrics[2]
        ),
        "macro_precision": float(
            macro_metrics[0]
        ),
        "macro_recall": float(
            macro_metrics[1]
        ),
        "macro_f1": float(
            macro_metrics[2]
        ),
    }


def train_one_epoch(
    *,
    model: Any,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    scaler: Any,
    device: torch.device,
    grad_accum: int,
    max_grad_norm: float,
    use_amp: bool,
    epoch_number: int,
    total_epochs: int,
) -> float:
    """Train one epoch and return average training loss."""

    model.train()
    optimizer.zero_grad(set_to_none=True)

    total_loss = 0.0
    total_examples = 0

    total_batches = len(loader)

    if total_batches == 0:
        raise ValueError(
            "The training data loader is empty"
        )

    incomplete_group_size = (
        total_batches % grad_accum
    )

    progress_bar = tqdm(
        loader,
        desc=(
            f"train epoch "
            f"{epoch_number}/{total_epochs}"
        ),
    )

    for step, batch in enumerate(
        progress_bar,
        start=1,
    ):
        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        accumulation_group_size = grad_accum

        if (
            incomplete_group_size
            and step
            > total_batches - incomplete_group_size
        ):
            accumulation_group_size = (
                incomplete_group_size
            )

        with torch.amp.autocast(
            device_type=device.type,
            enabled=use_amp,
        ):
            output = model(**batch)

            raw_loss = output.loss

            loss_for_backward = (
                raw_loss
                / accumulation_group_size
            )

        scaler.scale(
            loss_for_backward
        ).backward()

        batch_size = int(
            batch["labels"].shape[0]
        )

        total_loss += (
            float(raw_loss.detach().item())
            * batch_size
        )

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

            optimizer.zero_grad(
                set_to_none=True
            )

            # The scheduler must also step for the
            # final incomplete accumulation group.
            scheduler.step()

        average_loss = (
            total_loss / total_examples
        )

        progress_bar.set_postfix(
            train_loss=f"{average_loss:.4f}"
        )

    return total_loss / total_examples


def verify_saved_checkpoint(
    checkpoint_dir: Path,
    expected_id2label: dict[int, str],
) -> tuple[Any, Any]:
    """
    Reopen the saved model using the shared checkpoint
    loading function and verify its structure.
    """

    tokenizer, model = (
        load_classifier_from_checkpoint(
            checkpoint_dir
        )
    )

    num_labels = int(
        getattr(
            model.config,
            "num_labels",
            0,
        )
    )

    if num_labels != 2:
        raise RuntimeError(
            "Reloaded checkpoint does not contain "
            "a two-label classifier"
        )

    reloaded_id2label = normalise_id2label(
        model
    )

    if reloaded_id2label != expected_id2label:
        raise RuntimeError(
            "Reloaded checkpoint label mapping "
            "does not match the training model. "
            f"Found: {reloaded_id2label}"
        )

    encoded = tokenizer(
        "Checkpoint verification sample.",
        truncation=True,
        max_length=16,
        return_tensors="pt",
    )

    with torch.no_grad():
        logits = model(**encoded).logits

    if tuple(logits.shape) != (1, 2):
        raise RuntimeError(
            "Reloaded checkpoint produced an "
            f"unexpected logits shape: "
            f"{tuple(logits.shape)}"
        )

    return tokenizer, model


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fine-tune DeBERTa for binary "
            "misinformation classification using "
            "claim and label fields."
        )
    )

    parser.add_argument(
        "--train",
        type=Path,
        required=True,
        help="Training CSV or JSON file",
    )

    parser.add_argument(
        "--val",
        type=Path,
        default=None,
        help=(
            "Optional separate validation "
            "CSV or JSON file"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Checkpoint output directory",
    )

    parser.add_argument(
        "--hf-model-id",
        type=str,
        default=(
            DebertaMisinfoTrainConfig.hf_model_id
        ),
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
        default=(
            DebertaMisinfoTrainConfig.max_len
        ),
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

    args = parser.parse_args()

    validate_arguments(args)
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

        split_method = (
            "separate_validation_file"
        )

    else:
        label_counts = (
            train_df["label"].value_counts()
        )

        if (
            len(label_counts) < 2
            or int(label_counts.min()) < 2
        ):
            raise ValueError(
                "A stratified split requires "
                "both labels and at least two "
                "examples of each label. "
                "Provide more data or use --val."
            )

        try:
            train_df, val_df = (
                train_test_split(
                    train_df,
                    test_size=args.test_size,
                    random_state=args.seed,
                    stratify=train_df["label"],
                )
            )

        except ValueError as error:
            raise ValueError(
                "Unable to create a stratified "
                "training and validation split. "
                "Increase the dataset size, change "
                "--test-size, or provide --val."
            ) from error

        split_method = (
            "stratified_train_validation_split"
        )

    train_df = train_df.reset_index(
        drop=True
    )

    val_df = val_df.reset_index(
        drop=True
    )

    validate_datasets(
        train_df,
        val_df,
    )

    tokenizer, model = (
        build_fresh_classifier(
            args.hf_model_id
        )
    )

    expected_id2label = (
        normalise_id2label(model)
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

    optimizer_steps_per_epoch = int(
        np.ceil(
            len(train_loader)
            / args.grad_accum
        )
    )

    total_optimizer_steps = max(
        1,
        optimizer_steps_per_epoch
        * args.epochs,
    )

    warmup_steps = int(
        total_optimizer_steps
        * args.warmup_ratio
    )

    scheduler = (
        get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=(
                total_optimizer_steps
            ),
        )
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

    history: list[
        dict[str, float | int]
    ] = []

    patience = 0
    epochs_completed = 0

    for epoch_index in range(args.epochs):
        epoch_number = epoch_index + 1
        epochs_completed = epoch_number

        train_loss = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            device=device,
            grad_accum=args.grad_accum,
            max_grad_norm=args.max_grad_norm,
            use_amp=use_amp,
            epoch_number=epoch_number,
            total_epochs=args.epochs,
        )

        validation_metrics = (
            evaluate_classification(
                model,
                val_loader,
                device,
            )
        )

        epoch_result = {
            "epoch": epoch_number,
            "train_loss": train_loss,
            **validation_metrics,
        }

        history.append(epoch_result)

        print(
            f"Epoch {epoch_number}/"
            f"{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss="
            f"{validation_metrics['loss']:.4f} | "
            f"val_accuracy="
            f"{validation_metrics['accuracy']:.4f} | "
            f"val_macro_f1="
            f"{validation_metrics['macro_f1']:.4f} | "
            f"val_precision_pos1="
            f"{validation_metrics['precision_binary_pos1']:.4f} | "
            f"val_recall_pos1="
            f"{validation_metrics['recall_binary_pos1']:.4f}"
        )

        improved = (
            validation_metrics["macro_f1"]
            > best_macro_f1
            + args.min_delta
        )

        if improved:
            best_macro_f1 = (
                validation_metrics["macro_f1"]
            )

            best_epoch = epoch_number

            best_metrics = dict(
                validation_metrics
            )

            patience = 0

            model.save_pretrained(
                args.output_dir
            )

            tokenizer.save_pretrained(
                args.output_dir
            )

            print(
                "Saved new best checkpoint to "
                f"{args.output_dir}"
            )

        else:
            patience += 1

        if (
            patience
            >= args.early_stopping_patience
        ):
            print(
                "Early stopping triggered after "
                f"{args.early_stopping_patience} "
                "epoch(s) without improvement."
            )

            break

    if best_epoch == 0:
        raise RuntimeError(
            "Training finished without "
            "producing a checkpoint"
        )

    # Remove the current model from memory before
    # reopening the saved best checkpoint.
    del model

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    (
        reloaded_tokenizer,
        reloaded_model,
    ) = verify_saved_checkpoint(
        args.output_dir,
        expected_id2label,
    )

    reloaded_model.to(device)

    final_validation = (
        evaluate_classification(
            reloaded_model,
            val_loader,
            device,
        )
    )

    metadata = {
        "checkpoint_reload_verified": True,
        "hf_model_id": args.hf_model_id,
        "label_mapping": {
            str(key): value
            for key, value
            in expected_id2label.items()
        },
        "data": {
            "train_path": str(args.train),
            "validation_path": (
                str(args.val)
                if args.val is not None
                else None
            ),
            "split_method": split_method,
            "test_size": (
                args.test_size
                if args.val is None
                else None
            ),
            "text_field": "claim",
            "label_field": "label",
            "n_train": int(len(train_df)),
            "n_validation": int(len(val_df)),
        },
        "training_settings": {
            "seed": args.seed,
            "max_len": args.max_len,
            "batch_size": args.batch_size,
            "gradient_accumulation_steps": (
                args.grad_accum
            ),
            "effective_batch_size": (
                args.batch_size
                * args.grad_accum
            ),
            "epochs_requested": args.epochs,
            "epochs_completed": (
                epochs_completed
            ),
            "learning_rate": args.lr,
            "weight_decay": (
                args.weight_decay
            ),
            "warmup_ratio": (
                args.warmup_ratio
            ),
            "warmup_steps": warmup_steps,
            "optimizer_steps_per_epoch": (
                optimizer_steps_per_epoch
            ),
            "total_optimizer_steps_planned": (
                total_optimizer_steps
            ),
            "max_grad_norm": (
                args.max_grad_norm
            ),
            "early_stopping_patience": (
                args.early_stopping_patience
            ),
            "min_delta": args.min_delta,
            "num_workers": args.num_workers,
            "gradient_checkpointing": (
                args.gradient_checkpointing
            ),
            "mixed_precision": use_amp,
            "device": str(device),
        },
        "best_epoch": best_epoch,
        "best_validation": best_metrics,
        "final_validation_after_reload": (
            final_validation
        ),
        "history": history,
    }

    metadata_path = (
        args.output_dir
        / "training_meta.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Checkpoint reload verification: passed"
    )

    print(
        f"Best epoch: {best_epoch} | "
        f"final_val_loss="
        f"{final_validation['loss']:.4f} | "
        f"final_val_accuracy="
        f"{final_validation['accuracy']:.4f} | "
        f"final_val_macro_f1="
        f"{final_validation['macro_f1']:.4f}"
    )

    print(
        "Saved model and tokenizer to: "
        f"{args.output_dir}"
    )

    print(
        "Saved training metadata to: "
        f"{metadata_path}"
    )

    del reloaded_model
    del reloaded_tokenizer


if __name__ == "__main__":
    main()