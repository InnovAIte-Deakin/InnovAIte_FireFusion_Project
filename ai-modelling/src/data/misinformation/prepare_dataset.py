"""
Merge the raw Fake News benchmark datasets into one deduplicated
``claim``/``label`` file, then split off a stratified held-out test set.

Source files (from the team's SharePoint "Fake News Datasets" folder):
COCO.json, gossipcop.json, kaggle1.json, kaggle2.json, pheme.json, politifact.json.
Each is a JSON list of ``{"claim": str, "label": 0 | 1}`` records.

From ``ai-modelling/``, with the raw files in ``dataset/``:

  python src/data/misinformation/prepare_dataset.py \
      --dataset-dir dataset --output-dir src/data/misinformation
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.model_selection import train_test_split

DATASET_FILES = [
    "COCO.json",
    "gossipcop.json",
    "kaggle1.json",
    "kaggle2.json",
    "pheme.json",
    "politifact.json",
]


def load_records(path: Path) -> list[dict]:
    """Load a JSON list of records, recovering what it can from a file
    truncated mid-record (seen in practice with kaggle2.json after an
    incomplete SharePoint/OneDrive sync)."""
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _recover_truncated_array(text, path)


def _recover_truncated_array(text: str, path: Path) -> list[dict]:
    s = text.lstrip()
    if not s.startswith("["):
        raise ValueError(f"{path} is not a JSON array and cannot be recovered")

    decoder = json.JSONDecoder()
    idx = 1
    n = len(s)
    records: list[dict] = []
    while idx < n:
        while idx < n and s[idx] in " \t\r\n,":
            idx += 1
        if idx >= n or s[idx] == "]":
            break
        try:
            obj, end = decoder.raw_decode(s, idx)
        except json.JSONDecodeError:
            break
        records.append(obj)
        idx = end

    print(f"warning: {path.name} is truncated/invalid JSON; recovered {len(records)} complete records")
    return records


def merge_and_dedupe(dataset_dir: Path, files: list[str]) -> list[dict]:
    merged: list[dict] = []
    seen_claims: set[str] = set()
    for name in files:
        raw = load_records(dataset_dir / name)
        kept = 0
        for row in raw:
            claim = str(row["claim"]).strip()
            label = int(row["label"])
            if label not in (0, 1) or not claim or claim in seen_claims:
                continue
            seen_claims.add(claim)
            merged.append({"claim": claim, "label": label})
            kept += 1
        print(f"{name}: {len(raw)} raw -> {kept} kept")
    return merged


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset-dir", type=Path, required=True, help="Folder with the raw benchmark JSON files.")
    ap.add_argument("--output-dir", type=Path, required=True, help="Where to write train.json / test.json.")
    ap.add_argument("--test-size", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    merged = merge_and_dedupe(args.dataset_dir, DATASET_FILES)
    labels = [r["label"] for r in merged]
    train, test = train_test_split(
        merged, test_size=args.test_size, random_state=args.seed, stratify=labels
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "train.json").write_text(json.dumps(train, ensure_ascii=False), encoding="utf-8")
    (args.output_dir / "test.json").write_text(json.dumps(test, ensure_ascii=False), encoding="utf-8")
    print(f"merged={len(merged)} train={len(train)} test={len(test)}")


if __name__ == "__main__":
    main()
