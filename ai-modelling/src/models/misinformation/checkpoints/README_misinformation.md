# Misinformation Baseline — Training Run Log

Single-task DeBERTa-v3-large binary classifier (`misinformation` / `non_misinformation`),
trained on Google Colab (Tesla T4 GPU) as the baseline checkpoint for the
`[Misinformation] Train the baseline model` task.

## Dataset

Merged from six benchmark sources (COCO, GossipCop, PolitiFact, PHEME, kaggle1,
kaggle2), deduplicated, and split into a 90% training set / 10% stratified
held-out test set. See `src/data/misinformation/prepare_dataset.py` for the
reproducible merge/split script.

- Total merged records: 44,028 (23,382 non_misinformation / 20,646 misinformation)
- Training split: 39,625
- Held-out test split: 4,403

## Training configuration

- Base model: `microsoft/deberta-v3-large`
- Script: `src/training/deberta_train.py`
- Epochs: 4 (no early stopping triggered — metrics improved every epoch)
- Batch size: 8, gradient accumulation: 2 (effective batch size 16)
- Runtime: ~45 minutes/epoch on a T4 GPU (~3 hours total)

### Per-epoch validation (internal 10% split of the training set)

| Epoch | Loss | Val Accuracy | Val Macro F1 | Val F1 (misinformation) |
|---|---|---|---|---|
| 1 | 0.3164 | 0.8955 | 0.8955 | 0.8943 |
| 2 | 0.2671 | 0.9018 | 0.9018 | 0.9038 |
| 3 | 0.2438 | 0.9036 | 0.9036 | 0.9053 |
| 4 | 0.2240 | 0.9059 | 0.9059 | 0.9074 |

## Held-out test results

Evaluated with `src/models/misinformation/deberta_evaluate.py` on the 4,403-example
held-out test set (never seen during training or validation):

```
Accuracy=0.9021 | Precision=0.8393 | Recall=0.9787 | Binary F1=0.9036 | Macro F1=0.9021
```

### Per-class report

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| non_misinformation | 0.978 | 0.834 | 0.901 | 2,338 |
| misinformation | 0.839 | 0.979 | 0.904 | 2,065 |
| **Accuracy** | | | **0.902** | 4,403 |
| **Macro avg** | 0.909 | 0.907 | 0.902 | 4,403 |
| **Weighted avg** | 0.913 | 0.902 | 0.902 | 4,403 |

### Interpretation

The model is biased toward flagging content as misinformation: it catches 97.9% of
true misinformation (high recall on the harmful class) at the cost of misclassifying
~16.6% of legitimate content as misinformation. Whether that trade-off is acceptable
depends on how false positives are handled downstream (e.g. human review before any
action is taken on a flagged post).

## Known issues encountered

- `kaggle2.json` (one of the six raw source files from SharePoint) was truncated
  mid-download; `prepare_dataset.py` recovers all complete records and drops the
  final incomplete one automatically.
- `kaggle1.json` and `kaggle2.json` overlap heavily (same underlying corpus
  re-uploaded); deduplication by exact claim text removed ~39,000 near-duplicate
  records before merging.
- Newer `transformers` releases can load a checkpoint's weights in fp16 by default,
  which crashes `GradScaler.unscale_()` with "Attempting to unscale FP16 gradients."
  Fixed in `deberta.py`'s `build_fresh_classifier` by forcing `torch_dtype=torch.float32`.

## Reproducing this run

```bash
# from ai-modelling/, with the six raw dataset files in dataset/
python src/data/misinformation/prepare_dataset.py --dataset-dir dataset --output-dir src/data/misinformation

python -m src.training.deberta_train \
  --train src/data/misinformation/train.json \
  --output-dir src/models/misinformation/checkpoints/misinfo-deberta-baseline \
  --epochs 4 --batch-size 8 --grad-accum 2

python -m src.models.misinformation.deberta_evaluate \
  --checkpoint src/models/misinformation/checkpoints/misinfo-deberta-baseline \
  --test-data src/data/misinformation/test.json \
  --output-json src/models/misinformation/checkpoints/misinfo-deberta-baseline/eval_metrics.json \
  --confusion-matrix-image src/models/misinformation/checkpoints/misinfo-deberta-baseline/confusion_matrix.png
```

A Colab notebook wrapping these steps (with GPU runtime, Drive mount, and automatic
train/test split) is available at `ai-modelling/notebooks/train_baseline_misinfo_colab.ipynb`.

The trained checkpoint itself (`misinfo-deberta-baseline/`, ~1.7GB) is not committed
to git — it's backed up on the team's shared Google Drive at
`MyDrive/FireFusion/misinfo-deberta-baseline.zip`.
