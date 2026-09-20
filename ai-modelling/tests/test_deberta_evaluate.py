import pytest

from src.models.misinformation.deberta_evaluate import calculate_metrics


def test_calculate_metrics_perfect_predictions():
    results = calculate_metrics(
        true_labels=[0, 0, 1, 1],
        predicted_labels=[0, 0, 1, 1],
    )

    overall = results["overall_metrics"]

    assert overall["accuracy"] == pytest.approx(1.0)
    assert overall["binary_precision"] == pytest.approx(1.0)
    assert overall["binary_recall"] == pytest.approx(1.0)
    assert overall["binary_f1_score"] == pytest.approx(1.0)
    assert overall["macro_f1_score"] == pytest.approx(1.0)

    assert results["per_class_metrics"]["non_misinformation"]["f1_score"] == pytest.approx(1.0)
    assert results["per_class_metrics"]["misinformation"]["f1_score"] == pytest.approx(1.0)
    assert results["confusion_matrix"] == [[2, 0], [0, 2]]
    assert "classification_report" in results
    assert "classification_report_text" in results


def test_calculate_metrics_imperfect_predictions():
    results = calculate_metrics(
        true_labels=[0, 0, 1, 1],
        predicted_labels=[0, 1, 1, 1],
    )

    overall = results["overall_metrics"]

    assert overall["accuracy"] == pytest.approx(0.75)
    assert results["per_class_metrics"]["non_misinformation"]["support"] == 2
    assert results["per_class_metrics"]["misinformation"]["support"] == 2
    assert results["confusion_matrix"] == [[1, 1], [0, 2]]


def test_calculate_metrics_rejects_mismatched_lengths():
    with pytest.raises(
        ValueError,
        match="must have the same length",
    ):
        calculate_metrics(
            true_labels=[0, 1],
            predicted_labels=[0],
        )


def test_calculate_metrics_rejects_empty_dataset():
    with pytest.raises(
        ValueError,
        match="empty test dataset",
    ):
        calculate_metrics(
            true_labels=[],
            predicted_labels=[],
        )