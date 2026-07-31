from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader

from src.models.misinformation.deberta import (
    DEFAULT_ID2LABEL,
    DEFAULT_LABEL2ID,
    TextClsDataset,
    collate_text_cls_batch,
    load_classifier_from_checkpoint,
    load_table,
)

LOGGER = logging.getLogger(__name__)

TEXT_COLUMN = "claim"
LABEL_COLUMN = "label"
LABEL_IDS = sorted(DEFAULT_ID2LABEL)
TARGET_NAMES = [DEFAULT_ID2LABEL[label_id] for label_id in LABEL_IDS]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate a trained DeBERTa misinformation classifier."
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to the trained Hugging Face checkpoint directory.",
    )
    parser.add_argument(
        "--test-data",
        type=Path,
        required=True,
        help="Path to a CSV or JSON test dataset containing claim and label columns.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path where evaluation metrics will be saved as JSON.",
    )
    parser.add_argument(
        "--confusion-matrix-image",
        type=Path,
        default=None,
        help="Optional path for a PNG/JPG/PDF confusion-matrix image.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Inference batch size (default: 16).",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=256,
        help="Maximum token sequence length (default: 256).",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="Number of DataLoader workers (default: 0).",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Execution device. 'auto' uses CUDA when available, otherwise CPU.",
    )
    return parser.parse_args(argv)


def select_device(requested: str) -> torch.device:
    """Select CUDA when available and safely fall back to CPU otherwise."""
    if requested == "cpu":
        return torch.device("cpu")

    if torch.cuda.is_available():
        return torch.device("cuda")

    if requested == "cuda":
        LOGGER.warning("CUDA was requested but is unavailable; falling back to CPU.")
    return torch.device("cpu")


def validate_args(args: argparse.Namespace) -> None:
    """Validate paths and numeric command-line arguments."""
    if not args.checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint path does not exist: {args.checkpoint}")
    if not args.checkpoint.is_dir():
        raise NotADirectoryError(
            f"Checkpoint path must be a directory: {args.checkpoint}"
        )
    if not args.test_data.is_file():
        raise FileNotFoundError(f"Test dataset does not exist: {args.test_data}")
    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than zero")
    if args.max_len <= 0:
        raise ValueError("max-len must be greater than zero")
    if args.num_workers < 0:
        raise ValueError("num-workers must be zero or greater")


def make_json_serializable(value: Any) -> Any:
    """Recursively convert NumPy values into standard JSON-compatible values."""
    if isinstance(value, dict):
        return {str(key): make_json_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_serializable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def generate_predictions(
    *,
    model: Any,
    data_loader: DataLoader,
    device: torch.device,
) -> tuple[list[int], list[int]]:
    """Run batched inference and return true and predicted label IDs."""
    model.to(device)
    model.eval()

    true_labels: list[int] = []
    predicted_labels: list[int] = []

    with torch.inference_mode():
        for batch in data_loader:
            labels = batch.pop("labels").to(device)
            inputs = {name: tensor.to(device) for name, tensor in batch.items()}
            logits = model(**inputs).logits
            predictions = torch.argmax(logits, dim=-1)

            true_labels.extend(labels.cpu().tolist())
            predicted_labels.extend(predictions.cpu().tolist())

    return true_labels, predicted_labels


def calculate_metrics(
    true_labels: Sequence[int],
    predicted_labels: Sequence[int],
) -> dict[str, Any]:
    """Calculate the requested binary and macro evaluation metrics."""
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true_labels and predicted_labels must have the same length")
    if not true_labels:
        raise ValueError("Cannot calculate metrics for an empty test dataset")

    matrix = confusion_matrix(true_labels, predicted_labels, labels=LABEL_IDS)
    report = classification_report(
        true_labels,
        predicted_labels,
        labels=LABEL_IDS,
        target_names=TARGET_NAMES,
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "precision": precision_score(
            true_labels,
            predicted_labels,
            pos_label=1,
            average="binary",
            zero_division=0,
        ),
        "recall": recall_score(
            true_labels,
            predicted_labels,
            pos_label=1,
            average="binary",
            zero_division=0,
        ),
        "binary_f1_score": f1_score(
            true_labels,
            predicted_labels,
            pos_label=1,
            average="binary",
            zero_division=0,
        ),
        "macro_f1_score": f1_score(
            true_labels,
            predicted_labels,
            labels=LABEL_IDS,
            average="macro",
            zero_division=0,
        ),
        "confusion_matrix": matrix,
        "classification_report": report,
    }
    return make_json_serializable(metrics)


def save_confusion_matrix(
    matrix: Sequence[Sequence[int]],
    output_path: Path,
) -> None:
    """Save a labelled confusion matrix as an image."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay

    output_path.parent.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay(
        confusion_matrix=np.asarray(matrix, dtype=int),
        display_labels=TARGET_NAMES,
    )
    figure, axis = plt.subplots(figsize=(7, 6))
    display.plot(ax=axis, cmap="Blues", values_format="d", colorbar=False)
    axis.set_title("DeBERTa Test Confusion Matrix")
    figure.tight_layout()
    figure.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    """Load the checkpoint and test data, run inference, and save results."""
    validate_args(args)
    device = select_device(args.device)
    LOGGER.info("Using device: %s", device)

    tokenizer, model = load_classifier_from_checkpoint(args.checkpoint)

    # Keep evaluation output aligned with the project's shared binary mapping,
    # even if an older checkpoint contains generic LABEL_0/LABEL_1 names.
    model.config.id2label = dict(DEFAULT_ID2LABEL)
    model.config.label2id = dict(DEFAULT_LABEL2ID)

    num_labels = int(getattr(model.config, "num_labels", len(LABEL_IDS)))
    if num_labels != len(LABEL_IDS):
        raise ValueError(
            f"Expected a binary classifier with {len(LABEL_IDS)} labels, "
            f"but checkpoint reports {num_labels}"
        )

    test_frame = load_table(
        args.test_data,
        text_col=TEXT_COLUMN,
        label_col=LABEL_COLUMN,
    )
    if test_frame.empty:
        raise ValueError(f"Test dataset is empty: {args.test_data}")

    dataset = TextClsDataset(
        texts=test_frame["text"].tolist(),
        labels=test_frame["label"].tolist(),
        tokenizer=tokenizer,
        max_len=args.max_len,
    )
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        collate_fn=collate_text_cls_batch,
    )

    true_labels, predicted_labels = generate_predictions(
        model=model,
        data_loader=data_loader,
        device=device,
    )
    metrics = calculate_metrics(true_labels, predicted_labels)

    results: dict[str, Any] = {
        "checkpoint": str(args.checkpoint.resolve()),
        "test_dataset": str(args.test_data.resolve()),
        "num_test_examples": len(true_labels),
        "device": str(device),
        "text_field": TEXT_COLUMN,
        "target_field": LABEL_COLUMN,
        "label_mapping": {
            str(label_id): DEFAULT_ID2LABEL[label_id] for label_id in LABEL_IDS
        },
        "metrics": metrics,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    LOGGER.info("Saved evaluation metrics to %s", args.output_json)

    if args.confusion_matrix_image is not None:
        save_confusion_matrix(
            metrics["confusion_matrix"],
            args.confusion_matrix_image,
        )
        LOGGER.info(
            "Saved confusion matrix image to %s", args.confusion_matrix_image
        )

    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    args = parse_args(argv)
    results = evaluate(args)

    metrics = results["metrics"]
    LOGGER.info(
        "Accuracy=%.4f | Precision=%.4f | Recall=%.4f | Binary F1=%.4f | Macro F1=%.4f",
        metrics["accuracy"],
        metrics["precision"],
        metrics["recall"],
        metrics["binary_f1_score"],
        metrics["macro_f1_score"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
