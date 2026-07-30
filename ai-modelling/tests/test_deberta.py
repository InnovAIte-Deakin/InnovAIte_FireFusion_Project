from types import SimpleNamespace

import pytest
import torch

from src.models.misinformation.deberta import (
    TextClsDataset,
    classify_text,
    collate_text_cls_batch,
)


class DummyTokenizer:
    def __call__(
        self,
        text,
        truncation,
        padding,
        max_length,
        return_tensors,
    ):
        return {
            "input_ids": torch.ones((1, max_length), dtype=torch.long),
            "attention_mask": torch.ones((1, max_length), dtype=torch.long),
        }


class DummyModel:
    def __init__(self):
        self.config = SimpleNamespace(
            id2label={0: "non_misinformation", 1: "misinformation"}
        )
        self.eval_called = False

    def eval(self):
        self.eval_called = True

    def __call__(self, **kwargs):
        return SimpleNamespace(logits=torch.tensor([[0.2, 1.8]]))


def test_dataset_rejects_mismatched_texts_and_labels():
    with pytest.raises(
        ValueError,
        match="texts and labels must have the same length",
    ):
        TextClsDataset(
            texts=["claim one", "claim two"],
            labels=[1],
            tokenizer=DummyTokenizer(),
            max_len=8,
        )


def test_dataset_rejects_invalid_max_len():
    with pytest.raises(ValueError, match="max_len must be greater than zero"):
        TextClsDataset(
            texts=["claim"],
            labels=[1],
            tokenizer=DummyTokenizer(),
            max_len=0,
        )


def test_dataset_returns_tokenized_item_and_label():
    dataset = TextClsDataset(
        texts=["A bushfire warning was issued."],
        labels=[1],
        tokenizer=DummyTokenizer(),
        max_len=8,
    )

    item = dataset[0]

    assert len(dataset) == 1
    assert item["input_ids"].shape == (8,)
    assert item["attention_mask"].shape == (8,)
    assert item["labels"].item() == 1


def test_collate_text_cls_batch_stacks_items():
    batch = [
        {
            "input_ids": torch.tensor([1, 2]),
            "attention_mask": torch.tensor([1, 1]),
            "labels": torch.tensor(0),
        },
        {
            "input_ids": torch.tensor([3, 4]),
            "attention_mask": torch.tensor([1, 1]),
            "labels": torch.tensor(1),
        },
    ]

    result = collate_text_cls_batch(batch)

    assert result["input_ids"].shape == (2, 2)
    assert result["attention_mask"].shape == (2, 2)
    assert result["labels"].tolist() == [0, 1]


def test_collate_text_cls_batch_rejects_empty_batch():
    with pytest.raises(ValueError, match="batch must not be empty"):
        collate_text_cls_batch([])


@pytest.mark.parametrize("text", ["", "   ", None])
def test_classify_text_rejects_invalid_text(text):
    with pytest.raises(ValueError, match="text must be a non-empty string"):
        classify_text(
            text,
            tokenizer=DummyTokenizer(),
            model=DummyModel(),
            device=torch.device("cpu"),
            max_len=8,
        )


def test_classify_text_rejects_invalid_max_len():
    with pytest.raises(ValueError, match="max_len must be greater than zero"):
        classify_text(
            "A valid claim",
            tokenizer=DummyTokenizer(),
            model=DummyModel(),
            device=torch.device("cpu"),
            max_len=0,
        )


def test_classify_text_returns_expected_prediction_structure():
    model = DummyModel()

    result = classify_text(
        "The emergency warning has been issued.",
        tokenizer=DummyTokenizer(),
        model=model,
        device=torch.device("cpu"),
        max_len=8,
    )

    assert model.eval_called is True
    assert result["label_id"] == 1
    assert result["label"] == "misinformation"
    assert 0.0 <= result["confidence"] <= 1.0
    assert set(result["probabilities"]) == {
        "non_misinformation",
        "misinformation",
    }
    assert sum(result["probabilities"].values()) == pytest.approx(1.0)