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
    DEFAULT_TASKS,
    MISSING_LABEL,
    MultiTaskDeberta,
    MultiTaskTextClsDataset,
    collate_multitask_batch,
    load_multitask_from_checkpoint,
    load_multitask_table,
)

LOGGER = logging.getLogger(__name__)

TEXT_COLUMN = "claim"

# Maps each task name to the label column expected in the test file. A task
# whose column is missing from the file is simply skipped for every row
# (see load_multitask_table) rather than failing the whole run - useful when
# a given test set only covers e.g. misinfo + urgency.
TASK_LABEL_COLUMNS = {
    "misinfo": "misinfo_label",
    "urgency": "urgency_label",
    "humanitarian": "humanitarian_label",
}

ALL_TASK_NAMES = tuple(task.name for task in DEFAULT_TASKS)

# Which class name counts as "positive" for a binary task's precision/recall/
# binary-F1. Looked up by name (not by id) so it stays correct no matter how
# deberta.py's TaskSpec happens to encode a task - misinfo uses truth-value
# labels ({0: "FALSE", 1: "TRUE"}): "FALSE" means the claim is false, i.e. it
# IS misinformation, so "FALSE" - not "TRUE" - is the positive class here.
BINARY_POSITIVE_LABEL = {"misinfo": "FALSE"}


def _resolve_positive_id(task: str, id2label: dict[int, str]) -> int | None:
    """Find the label id matching this task's configured positive class name.

    Returns None (skip binary metrics for this task) if the task has no
    configured positive class, or if none of its labels match by name -
    never falls back to guessing a label id by position.
    """
    target_name = BINARY_POSITIVE_LABEL.get(task)
    if target_name is None:
        return None
    for label_id, name in id2label.items():
        if name.strip().lower() == target_name.strip().lower():
            return label_id
    LOGGER.warning(
        "Task %r is binary but no label matches configured positive class "
        "%r (labels present: %s); skipping binary precision/recall/F1.",
        task,
        target_name,
        list(id2label.values()),
    )
    return None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate a trained multi-task DeBERTa checkpoint "
        "(misinfo / urgency / humanitarian heads)."
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to a multi-task checkpoint directory saved by "
        "save_multitask_checkpoint (must contain tasks.json + model.pt).",
    )
    parser.add_argument(
        "--test-data",
        type=Path,
        required=True,
        help="Path to a CSV or JSON test dataset with a shared text column "
        "and one label column per task being evaluated.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path where evaluation metrics will be saved as JSON.",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=ALL_TASK_NAMES,
        default=None,
        help="Which task heads to evaluate (default: every task present in "
        "both the checkpoint and the test data).",
    )
    parser.add_argument(
        "--confusion-matrix-dir",
        type=Path,
        default=None,
        help="Optional directory for per-task confusion-matrix images "
        "(written as <task>_confusion_matrix.png).",
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
        default=None,
        help="Maximum token sequence length. Defaults to the value stored "
        "in the checkpoint's tasks.json.",
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
    if not (args.checkpoint / "tasks.json").is_file():
        raise FileNotFoundError(
            f"{args.checkpoint} has no tasks.json - this looks like an older "
            "single-task checkpoint. Re-save it with save_multitask_checkpoint, "
            "or evaluate it with the single-task script instead."
        )
    if not args.test_data.is_file():
        raise FileNotFoundError(f"Test dataset does not exist: {args.test_data}")
    if args.batch_size <= 0:
        raise ValueError("batch-size must be greater than zero")
    if args.max_len is not None and args.max_len <= 0:
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
    model: MultiTaskDeberta,
    data_loader: DataLoader,
    device: torch.device,
    tasks: Sequence[str],
) -> dict[str, tuple[list[int], list[int]]]:
    """
    Run batched inference across every requested head and return, per task,
    the true and predicted label IDs - restricted to rows that actually carry
    a label for that task (MISSING_LABEL rows are excluded per task, not
    dropped from the batch as a whole).
    """
    model.to(device)
    model.eval()

    true_labels: dict[str, list[int]] = {task: [] for task in tasks}
    predicted_labels: dict[str, list[int]] = {task: [] for task in tasks}

    with torch.inference_mode():
        for batch in data_loader:
            task_label_tensors = {
                task: batch.pop(f"labels_{task}").to(device) for task in tasks
            }
            inputs = {name: tensor.to(device) for name, tensor in batch.items()}
            all_logits = model(**inputs, tasks=list(tasks))

            for task in tasks:
                labels = task_label_tensors[task]
                keep = labels != MISSING_LABEL
                if not torch.any(keep):
                    continue
                predictions = torch.argmax(all_logits[task], dim=-1)
                true_labels[task].extend(labels[keep].cpu().tolist())
                predicted_labels[task].extend(predictions[keep].cpu().tolist())

    return {task: (true_labels[task], predicted_labels[task]) for task in tasks}


def calculate_task_metrics(
    task: str,
    true_labels: Sequence[int],
    predicted_labels: Sequence[int],
    id2label: dict[int, str],
) -> dict[str, Any]:
    """
    Calculate metrics for a single task head. Binary precision/recall/F1 are
    only added for 2-class heads with a configured positive class (misinfo);
    multi-class heads (urgency, humanitarian) rely on macro/weighted F1
    instead, since "binary" precision isn't meaningful once there are 3+
    classes.
    """
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true_labels and predicted_labels must have the same length")
    if not true_labels:
        raise ValueError(
            "No labelled examples for this task in the test dataset - check "
            "that its label column is present and populated."
        )

    label_ids = sorted(id2label)
    target_names = [id2label[label_id] for label_id in label_ids]

    matrix = confusion_matrix(true_labels, predicted_labels, labels=label_ids)
    report = classification_report(
        true_labels,
        predicted_labels,
        labels=label_ids,
        target_names=target_names,
        output_dict=True,
        zero_division=0,
    )

    metrics: dict[str, Any] = {
        "num_examples": len(true_labels),
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_f1_score": f1_score(
            true_labels,
            predicted_labels,
            labels=label_ids,
            average="macro",
            zero_division=0,
        ),
        "weighted_f1_score": f1_score(
            true_labels,
            predicted_labels,
            labels=label_ids,
            average="weighted",
            zero_division=0,
        ),
        "confusion_matrix": matrix,
        "classification_report": report,
    }

    if len(label_ids) == 2:
        pos_id = _resolve_positive_id(task, id2label)
        if pos_id is not None:
            metrics["positive_class"] = id2label[pos_id]
            metrics["precision"] = precision_score(
                true_labels, predicted_labels, pos_label=pos_id, average="binary", zero_division=0
            )
            metrics["recall"] = recall_score(
                true_labels, predicted_labels, pos_label=pos_id, average="binary", zero_division=0
            )
            metrics["binary_f1_score"] = f1_score(
                true_labels, predicted_labels, pos_label=pos_id, average="binary", zero_division=0
            )

    return make_json_serializable(metrics)


def save_confusion_matrix(
    matrix: Sequence[Sequence[int]],
    target_names: Sequence[str],
    title: str,
    output_path: Path,
) -> None:
    """Save a labelled confusion matrix as an image for one task."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay

    output_path.parent.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay(
        confusion_matrix=np.asarray(matrix, dtype=int),
        display_labels=list(target_names),
    )
    figure, axis = plt.subplots(figsize=(7, 6))
    display.plot(ax=axis, cmap="Blues", values_format="d", colorbar=False)
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    """Load the checkpoint and test data, run inference, and save results."""
    validate_args(args)
    device = select_device(args.device)
    LOGGER.info("Using device: %s", device)

    tokenizer, model, checkpoint_max_len = load_multitask_from_checkpoint(
        args.checkpoint, device=device
    )
    max_len = args.max_len if args.max_len is not None else checkpoint_max_len

    requested_tasks = args.tasks if args.tasks is not None else list(model.tasks)
    unknown = [task for task in requested_tasks if task not in model.tasks]
    if unknown:
        raise ValueError(
            f"Checkpoint has no head(s) for {unknown}; "
            f"available heads: {sorted(model.tasks)}"
        )

    task_label_cols = {
        task: TASK_LABEL_COLUMNS[task]
        for task in requested_tasks
        if task in TASK_LABEL_COLUMNS
    }
    test_frame = load_multitask_table(
        args.test_data,
        text_col=TEXT_COLUMN,
        task_label_cols=task_label_cols,
    )

    # Drop any requested task that turned out to have zero usable labels in
    # this particular file, rather than failing the whole evaluation run.
    tasks = [
        task
        for task in requested_tasks
        if not bool((test_frame[f"label_{task}"] == MISSING_LABEL).all())
    ]
    skipped = sorted(set(requested_tasks) - set(tasks))
    if skipped:
        LOGGER.warning(
            "Skipping task(s) with no usable labels in %s: %s",
            args.test_data,
            skipped,
        )
    if not tasks:
        raise ValueError(f"No requested task has usable labels in {args.test_data}")

    dataset = MultiTaskTextClsDataset(
        texts=test_frame["text"].tolist(),
        task_labels={task: test_frame[f"label_{task}"].tolist() for task in tasks},
        tokenizer=tokenizer,
        max_len=max_len,
    )
    data_loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        collate_fn=collate_multitask_batch,
    )

    predictions = generate_predictions(
        model=model,
        data_loader=data_loader,
        device=device,
        tasks=tasks,
    )

    results: dict[str, Any] = {
        "checkpoint": str(args.checkpoint.resolve()),
        "test_dataset": str(args.test_data.resolve()),
        "device": str(device),
        "text_field": TEXT_COLUMN,
        "tasks": {},
    }

    if args.confusion_matrix_dir is not None:
        args.confusion_matrix_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        true_l, pred_l = predictions[task]
        id2label = model.tasks[task].id2label
        task_metrics = calculate_task_metrics(task, true_l, pred_l, id2label)

        results["tasks"][task] = {
            "label_mapping": {str(k): v for k, v in id2label.items()},
            "num_test_examples": task_metrics["num_examples"],
            "metrics": task_metrics,
        }

        if args.confusion_matrix_dir is not None:
            label_ids = sorted(id2label)
            image_path = args.confusion_matrix_dir / f"{task}_confusion_matrix.png"
            save_confusion_matrix(
                task_metrics["confusion_matrix"],
                [id2label[i] for i in label_ids],
                f"{task} - Test Confusion Matrix",
                image_path,
            )
            LOGGER.info("Saved %s confusion matrix to %s", task, image_path)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    LOGGER.info("Saved evaluation metrics to %s", args.output_json)

    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    args = parse_args(argv)
    results = evaluate(args)

    for task, task_results in results["tasks"].items():
        metrics = task_results["metrics"]
        if "binary_f1_score" in metrics:
            LOGGER.info(
                "[%s] n=%d Accuracy=%.4f | Precision=%.4f | Recall=%.4f | "
                "Binary F1=%.4f | Macro F1=%.4f",
                task,
                metrics["num_examples"],
                metrics["accuracy"],
                metrics["precision"],
                metrics["recall"],
                metrics["binary_f1_score"],
                metrics["macro_f1_score"],
            )
        else:
            LOGGER.info(
                "[%s] n=%d Accuracy=%.4f | Macro F1=%.4f | Weighted F1=%.4f",
                task,
                metrics["num_examples"],
                metrics["accuracy"],
                metrics["macro_f1_score"],
                metrics["weighted_f1_score"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
