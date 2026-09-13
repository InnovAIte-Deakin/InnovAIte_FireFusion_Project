# -*- coding: utf-8 -*-
"""
# FireFusion — Single-Task Baseline Classification

This notebook trains a **single-task text classification baseline** using the one structured CSV dataset currently available.

### Current baseline task
- **Input:** `text`
- **Target:** `humanitarian_label`
- **Model:** `distilbert-base-uncased`
- **Split:** 70% train / 30% held-out test
- **Output:** baseline checkpoint, tokenizer, label mapping, metrics, and test predictions

> Important: the current CSV should not be used for REAL/FAKE training if `real_or_fake` contains only one class. A binary misinformation classifier requires both REAL and FAKE examples.
"""

import os
import json
import random
import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

from torch.optim import AdamW

# CONFIG
# Update DATA_PATH only if your local repository path changes.
DATA_PATH = r"SIT374-Capstone A\InnovAIte_FireFusion_Project\data-engineering\datasets\humanity_firefusion\firefusion_real_wildfire_humanitarian_corpus.csv"

MODEL_NAME = "distilbert-base-uncased"

TEXT_COLUMN = "text"
LABEL_COLUMN = "humanitarian_label"

MAX_LENGTH = 128
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5
TEST_SIZE = 0.30
RANDOM_SEED = 42

CHECKPOINT_DIR = os.path.join(
    "checkpoints",
    "humanitarian_baseline_distilbert"
)

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

print("Checkpoint directory:", CHECKPOINT_DIR)

# REPRODUCIBILITY + DEVICE
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

# LOAD THE ONE STRUCTURED DATASET
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found:\n{DATA_PATH}\n\n"
        "Update DATA_PATH in the CONFIG cell."
    )

df = pd.read_csv(DATA_PATH)

# Normalize column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)

print("DATASET INFORMATION")
print("===================")
print("Shape:", df.shape)
print("\nColumns:")
for column in df.columns:
    print("-", column)

print("\nPreview:")
display(df.head())

# VALIDATE REQUIRED COLUMNS
required_columns = [TEXT_COLUMN, LABEL_COLUMN]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}\n"
        f"Available columns: {df.columns.tolist()}"
    )

print("Required columns are available.")

# CLEAN TEXT + TARGET
working_df = df.copy()

working_df = working_df.dropna(
    subset=[TEXT_COLUMN, LABEL_COLUMN]
).copy()

working_df[TEXT_COLUMN] = (
    working_df[TEXT_COLUMN]
    .astype(str)
    .str.strip()
)

working_df[LABEL_COLUMN] = (
    working_df[LABEL_COLUMN]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Remove empty text/labels
working_df = working_df[
    (working_df[TEXT_COLUMN].str.len() > 0) &
    (working_df[LABEL_COLUMN].str.len() > 0)
].copy()

# Remove exact duplicate text so the same tweet is less likely to leak
# into both train and test.
before_dedup = len(working_df)
working_df = working_df.drop_duplicates(
    subset=[TEXT_COLUMN]
).reset_index(drop=True)
after_dedup = len(working_df)

print("Rows before exact-text deduplication:", before_dedup)
print("Rows after exact-text deduplication :", after_dedup)
print("Removed duplicates                 :", before_dedup - after_dedup)

print("\nTarget distribution:")
print(working_df[LABEL_COLUMN].value_counts())

# ENCODE HUMANITARIAN LABELS
label_encoder = LabelEncoder()

working_df["label"] = label_encoder.fit_transform(
    working_df[LABEL_COLUMN]
)

class_names = label_encoder.classes_.tolist()
NUM_LABELS = len(class_names)

if NUM_LABELS < 2:
    raise ValueError(
        f"Training stopped: '{LABEL_COLUMN}' contains only one class. "
        "A classification baseline requires at least two classes."
    )

id2label = {
    i: label
    for i, label in enumerate(class_names)
}

label2id = {
    label: i
    for i, label in id2label.items()
}

print("Number of classes:", NUM_LABELS)
print("\nLabel mapping:")
for idx, label in id2label.items():
    print(f"{idx}: {label}")

print("\nEncoded distribution:")
print(working_df["label"].value_counts().sort_index())

# CHECK WHETHER STRATIFIED 70/30 SPLIT IS SAFE
class_counts = working_df["label"].value_counts()

too_small = class_counts[class_counts < 2]

if len(too_small) > 0:
    labels_too_small = [
        id2label[int(i)] for i in too_small.index
    ]
    raise ValueError(
        "Some classes have fewer than 2 samples and cannot be "
        f"stratified: {labels_too_small}"
    )

# 70% TRAIN / 30% HELD-OUT TEST
train_df, test_df = train_test_split(
    working_df,
    test_size=TEST_SIZE,
    random_state=RANDOM_SEED,
    stratify=working_df["label"],
)

train_df = train_df.reset_index(drop=True)
test_df = test_df.reset_index(drop=True)

print("TRAIN / TEST SPLIT")
print("==================")
print(f"Total samples : {len(working_df)}")
print(
    f"Training      : {len(train_df)} "
    f"({len(train_df) / len(working_df):.1%})"
)
print(
    f"Testing       : {len(test_df)} "
    f"({len(test_df) / len(working_df):.1%})"
)

print("\nTraining label counts:")
print(
    train_df[LABEL_COLUMN]
    .value_counts()
)

print("\nTesting label counts:")
print(
    test_df[LABEL_COLUMN]
    .value_counts()
)

# TOKENIZER
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

print("Tokenizer loaded:", MODEL_NAME)

# PYTORCH DATASET
class HumanitarianTextDataset(Dataset):

    def __init__(
        self,
        dataframe,
        tokenizer,
        max_length
    ):
        self.texts = dataframe[TEXT_COLUMN].tolist()
        self.labels = dataframe["label"].tolist()
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(
                label,
                dtype=torch.long
            )
        }

# DATA LOADERS
train_dataset = HumanitarianTextDataset(
    train_df,
    tokenizer,
    MAX_LENGTH
)

test_dataset = HumanitarianTextDataset(
    test_df,
    tokenizer,
    MAX_LENGTH
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

print("Train batches:", len(train_loader))
print("Test batches :", len(test_loader))

# SINGLE-TASK CLASSIFICATION MODEL
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS,
    id2label=id2label,
    label2id=label2id,
)

model.to(device)

optimizer = AdamW(
    model.parameters(),
    lr=LEARNING_RATE
)

print("Model:", MODEL_NAME)
print("Classification head outputs:", NUM_LABELS)

# TRAIN BASELINE
print("START TRAINING")

training_history = []

for epoch in range(EPOCHS):

    model.train()
    total_loss = 0.0

    for batch_idx, batch in enumerate(train_loader):

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        if batch_idx % 50 == 0:
            print(
                f"Epoch {epoch + 1}/{EPOCHS} | "
                f"Batch {batch_idx}/{len(train_loader)} | "
                f"Loss: {loss.item():.4f}"
            )

    average_loss = total_loss / len(train_loader)

    training_history.append({
        "epoch": epoch + 1,
        "train_loss": average_loss
    })

    print(
        f"Epoch {epoch + 1} average training loss: "
        f"{average_loss:.4f}\n"
    )

print("Training completed.")

# EVALUATE ON THE HELD-OUT 30% TEST SET
print("TESTING")
model.eval()

all_predictions = []
all_labels = []
all_probabilities = []

with torch.no_grad():

    for batch in test_loader:

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )

        predictions = torch.argmax(
            probabilities,
            dim=1
        )

        all_predictions.extend(
            predictions.cpu().numpy().tolist()
        )

        all_labels.extend(
            labels.cpu().numpy().tolist()
        )

        all_probabilities.extend(
            probabilities.cpu().numpy().tolist()
        )

print("Evaluation completed.")

# METRICS
accuracy = accuracy_score(
    all_labels,
    all_predictions
)

precision_weighted, recall_weighted, f1_weighted, _ = (
    precision_recall_fscore_support(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0
    )
)

precision_macro, recall_macro, f1_macro, _ = (
    precision_recall_fscore_support(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )
)

print("TEST RESULTS")
print(f"Accuracy          : {accuracy:.4f}")
print(f"Precision weighted: {precision_weighted:.4f}")
print(f"Recall weighted   : {recall_weighted:.4f}")
print(f"F1 weighted       : {f1_weighted:.4f}")
print(f"F1 macro          : {f1_macro:.4f}")

print("\nClassification Report:\n")

print(
    classification_report(
        all_labels,
        all_predictions,
        labels=list(range(NUM_LABELS)),
        target_names=class_names,
        zero_division=0
    )
)

cm = confusion_matrix(
    all_labels,
    all_predictions,
    labels=list(range(NUM_LABELS))
)

print("Confusion matrix:")
print(cm)

# SAVE BASELINE CHECKPOINT
# Hugging Face format
model.save_pretrained(
    CHECKPOINT_DIR
)

tokenizer.save_pretrained(
    CHECKPOINT_DIR
)

# Save label mapping
label_mapping_path = os.path.join(
    CHECKPOINT_DIR,
    "label_mapping.json"
)

with open(
    label_mapping_path,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        {
            "id2label": {
                str(k): v
                for k, v in id2label.items()
            },
            "label2id": label2id,
            "text_column": TEXT_COLUMN,
            "target_column": LABEL_COLUMN,
        },
        f,
        indent=2,
        ensure_ascii=False
    )

# Save a PyTorch training checkpoint as well
checkpoint_path = os.path.join(
    CHECKPOINT_DIR,
    "baseline_checkpoint.pt"
)

torch.save(
    {
        "epoch": EPOCHS,
        "model_name": MODEL_NAME,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "num_labels": NUM_LABELS,
        "id2label": id2label,
        "label2id": label2id,
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "metrics": {
            "accuracy": accuracy,
            "precision_weighted": precision_weighted,
            "recall_weighted": recall_weighted,
            "f1_weighted": f1_weighted,
            "f1_macro": f1_macro,
        },
        "training_history": training_history,
    },
    checkpoint_path
)

print("Baseline checkpoint saved to:")
print(CHECKPOINT_DIR)
print("\nPyTorch checkpoint:")
print(checkpoint_path)

# SAVE METRICS + TEST PREDICTIONS
metrics = {
    "model_name": MODEL_NAME,
    "task": "humanitarian_label_classification",
    "num_labels": NUM_LABELS,
    "train_samples": len(train_df),
    "test_samples": len(test_df),
    "test_size": TEST_SIZE,
    "random_seed": RANDOM_SEED,
    "accuracy": accuracy,
    "precision_weighted": precision_weighted,
    "recall_weighted": recall_weighted,
    "f1_weighted": f1_weighted,
    "precision_macro": precision_macro,
    "recall_macro": recall_macro,
    "f1_macro": f1_macro,
}

metrics_path = os.path.join(
    CHECKPOINT_DIR,
    "metrics.json"
)

with open(
    metrics_path,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        metrics,
        f,
        indent=2
    )

predictions_df = test_df.copy()

predictions_df["predicted_label_id"] = (
    all_predictions
)

predictions_df["predicted_label"] = [
    id2label[int(pred)]
    for pred in all_predictions
]

predictions_df["prediction_confidence"] = [
    float(max(probabilities))
    for probabilities in all_probabilities
]

# predictions_path = os.path.join(
#     CHECKPOINT_DIR,
#     "test_predictions.csv"
# )

# predictions_df.to_csv(
#     predictions_path,
#     index=False
# )

# print("Saved:")
# print("-", metrics_path)
# print("-", predictions_path)

# LOAD THE SAVED BASELINE AND TEST A SINGLE SENTENCE
loaded_tokenizer = AutoTokenizer.from_pretrained(
    CHECKPOINT_DIR
)

loaded_model = AutoModelForSequenceClassification.from_pretrained(
    CHECKPOINT_DIR
)

loaded_model.to(device)
loaded_model.eval()

sample_text = (
    "Residents have been advised to evacuate "
    "because of the nearby wildfire."
)

inputs = loaded_tokenizer(
    sample_text,
    return_tensors="pt",
    truncation=True,
    padding=True,
    max_length=MAX_LENGTH
)

inputs = {
    key: value.to(device)
    for key, value in inputs.items()
}

with torch.no_grad():
    outputs = loaded_model(**inputs)

probabilities = torch.softmax(
    outputs.logits,
    dim=1
)[0]

predicted_id = int(
    torch.argmax(probabilities).item()
)

predicted_label = loaded_model.config.id2label[
    predicted_id
]

confidence = float(
    probabilities[predicted_id].item()
)

print("Text:")
print(sample_text)

print("\nPrediction:")
print("Label     :", predicted_label)
print("Confidence:", round(confidence, 4))