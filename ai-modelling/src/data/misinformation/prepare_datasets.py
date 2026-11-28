"""Prepare the training and inference files. Run this script from ai-modelling/."""
import json
import sys
from pathlib import Path

# Import the same label IDs that the model uses.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.models.misinformation.labels import HUMANITARIAN_STR2ID, URGENCY_STR2ID
from prepare_inference import clean_text, csv_rows, inference_datasets

RAW_DIR = Path("data/raw data")
OUTPUT_DIR = Path("data/misinformation")


def pheme_label(annotation):
    # PHEME stores some flags as strings and others as numbers.
    false_flag = str(annotation.get("misinformation", ""))
    true_flag = str(annotation.get("true", ""))
    if false_flag == "0" and true_flag == "1":
        return 0
    if false_flag == "1" and true_flag in ("0", ""):
        return 1
    if false_flag == "0" and true_flag in ("0", ""):
        return None  # Unverified claim
    raise ValueError(f"Unexpected PHEME flags: {false_flag!r}, {true_flag!r}")


def pheme_datasets():
    legacy = json.loads((RAW_DIR / "misinfo_unified.json").read_bytes())
    excluded = {clean_text(row["claim"]).casefold() for row in legacy}
    root = RAW_DIR / "PHEME_veracity/all-rnr-annotated-threads"
    annotations = sorted(root.glob("*/rumours/*/annotation.json"))
    if not annotations:
        raise FileNotFoundError(f"No PHEME rumour annotations under {root}")

    train = []
    validation = []
    multitask = []
    seen = {}
    for path in annotations:
        label = pheme_label(json.loads(path.read_bytes()))
        if label is None:
            continue
        thread = path.parent
        tweet = thread / "source-tweets" / f"{thread.name}.json"
        claim = clean_text(json.loads(tweet.read_bytes())["text"])
        key = claim.casefold()
        if not key or key in excluded:
            continue
        if key in seen:
            if seen[key] != label:
                raise ValueError(f"Conflicting verdicts for thread {thread.name}")
            continue
        seen[key] = label

        record = {"claim": claim, "label": label}
        if path.relative_to(root).parts[0] == "germanwings-crash-all-rnr-threads":
            validation.append(record)
        else:
            train.append(record)
            # The multitask trainer uses 0 for false and 1 for true.
            multitask.append({"claim": claim, "label": 1 - label})

    return {
        "single-task/pheme_deberta_train.json": train,
        "single-task/pheme_deberta_val.json": validation,
        "multitask/pheme_misinfo.json": multitask,
    }


def add_crisis_post(posts, text, key, category, urgency):
    record = {
        "text": text,
        "urgency": URGENCY_STR2ID[urgency],
        "humanitarian": HUMANITARIAN_STR2ID[category],
    }
    if key not in posts:
        posts[key] = record
    elif (posts[key]["urgency"] != record["urgency"]
          or posts[key]["humanitarian"] != record["humanitarian"]):
        raise ValueError(f"Conflicting crisis labels for {text!r}")


def crisis_dataset(wildfire):
    posts = {}
    paired = RAW_DIR / "CrisisTS/Multi_modal_dataset/Multi_modal_ENG/CrisisTS_Eng.csv"
    for row in csv_rows(paired, delimiter="\t"):
        text = clean_text(row["Text"])
        if not text:
            raise ValueError(f"Empty crisis text in {paired}")
        key = text.casefold()
        if key in posts and posts[key]["text"] != text:
            raise ValueError(f"Conflicting CrisisTS rows for {text!r}")
        add_crisis_post(posts, text, key, row["label_humanitarian"], row["label_urgent"])

    holdout = set()
    for split in ("validation", "test"):
        for row in csv_rows(RAW_DIR / "HumAID" / f"humaid_{split}.csv"):
            if row["class_label"] in HUMANITARIAN_STR2ID:
                # Some HumAID text has two layers of HTML escaping.
                text = clean_text(row["tweet_text"])
                holdout.add(clean_text(text).casefold())

    for row in wildfire:
        text = row["text"].strip()
        key = clean_text(text).casefold()
        category = row["humanitarian_label"]
        if not key or key in holdout or category not in HUMANITARIAN_STR2ID:
            continue
        if category == "not_humanitarian":
            urgency = "not_humanitarian"
        elif category == "rescue_volunteering_or_donation_effort":
            urgency = "not_urgent"
        else:
            urgency = "urgent"
        add_crisis_post(posts, text, key, category, urgency)
    return list(posts.values())


def save_datasets(datasets):
    OUTPUT_DIR.mkdir(parents=True)
    for name, rows in datasets.items():
        path = OUTPUT_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as file:
            if path.suffix == ".jsonl":
                for row in rows:
                    file.write(json.dumps(row, ensure_ascii=False) + "\n")
            else:
                json.dump(rows, file, indent=2, ensure_ascii=False)
                file.write("\n")


def main():
    wildfire = list(csv_rows(RAW_DIR / "firefusion_real_wildfire_humanitarian_corpus.csv"))
    datasets = pheme_datasets()
    datasets["multitask/crisis.json"] = crisis_dataset(wildfire)
    datasets.update(inference_datasets(RAW_DIR, wildfire))
    save_datasets(datasets)
    for name, rows in datasets.items():
        print(f"{name}: {len(rows):,} records")


if __name__ == "__main__":
    main()
