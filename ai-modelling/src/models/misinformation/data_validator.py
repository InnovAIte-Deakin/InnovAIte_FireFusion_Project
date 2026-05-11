"""
Data Validation Script

This script validates a generated JSON dataset before it is passed to downstream components.

It checks that the dataset follows the expected input data schema, including:
- Required fields
- Controlled vocabulary values
- Text length constraints
- Timestamp format
- Source credibility range
- Theme coverage
- Split and label distribution

If validation passes, a cleaned JSON file is produced along with a validation report.

Input:
- A JSON file containing social media posts data

Output:
- A cleaned JSON file
- A validation report

Usage:
- Basic validation:
  python data_validator.py --input firefusion_synthetic_posts.json

Arguments:
- --input
  Path to the generated input dataset file.

- --output
  Path where the cleaned validated dataset will be saved.
  Default: validated_output.json

- --report
  Path where the validation report will be saved.
  Default: validation_report.txt
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd


# --- SCHEMA CONFIGURATION ---
# Required fields must exist and must not contain missing values.

REQUIRED_COLUMNS = [
    "post_id",
    "text",
    "label",
    "platform",
    "narrative_theme",
    "timestamp_simulated",
    "language",
    "generation_template",
    "split",
]

# Optional fields may be missing from the dataset.
# If present, they are validated where rules are defined.
OPTIONAL_COLUMNS = [
    "location_mentioned",
    "source_credibility",
]

EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


# --- CONTROLLED VOCABULARIES ---

ALLOWED_VALUES = {
    "label": ["misinformation", "credible", "unverified"],
    "platform": ["twitter", "facebook", "reddit", "news_article", "official_agency"],
    "narrative_theme": [
        "arson_blame",
        "govt_inaction",
        "evacuation_false",
        "fire_extent_exaggeration",
        "official_update",
        "factual_report",
        "unrelated",
    ],
    "split": ["train", "val", "test"],
    "language": ["en"],
}


# --- VALIDATION CONSTANTS ---

MIN_TEXT_LENGTH = 20
MAX_TEXT_LENGTH = 300

POST_ID_PATTERN = r"^fp_[a-fA-F0-9]{8}$"

TIMESTAMP_START = pd.Timestamp("2019-01-01", tz="UTC")
TIMESTAMP_END = pd.Timestamp("2023-12-31 23:59:59", tz="UTC")

THEME_MIN_COVERAGE = 0.05

EXPECTED_SPLIT_DISTRIBUTION = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15,
}

EXPECTED_LABEL_DISTRIBUTION = {
    "misinformation": 0.60,
    "credible": 0.30,
    "unverified": 0.10,
}

DISTRIBUTION_TOLERANCE = 0.05


# --- HELPER FUNCTIONS ---

def count_missing_values(series: pd.Series) -> int:
    """
    Count missing values in a column.

    Empty strings and whitespace-only strings are treated as missing.
    """
    return series.fillna("").astype(str).str.strip().eq("").sum()


def add_error(errors: list, message: str):
    """Add an error message."""
    errors.append(message)


def add_warning(warnings: list, message: str):
    """Add a warning message."""
    warnings.append(message)


# --- VALIDATION RULES ---
# Each rule checks one aspect of the dataset.
# To add a new rule later, create a new function and add it to VALIDATION_RULES.


def check_dataset_not_empty(df: pd.DataFrame, errors: list, warnings: list):
    """Check that the dataset contains at least one row."""
    if df.empty:
        add_error(errors, "Dataset is empty.")


def check_expected_columns_exist(df: pd.DataFrame, errors: list, warnings: list):
    """Check that all required columns are present."""
    missing_required = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_required:
        add_error(errors, f"Missing required columns: {missing_required}")


def check_extra_columns(df: pd.DataFrame, errors: list, warnings: list):
    """Warn if unexpected columns are present."""
    extra_columns = [col for col in df.columns if col not in EXPECTED_COLUMNS]

    if extra_columns:
        add_warning(
            warnings,
            f"Unexpected extra columns found and excluded from output: {extra_columns}"
        )


def check_required_columns_not_empty(df: pd.DataFrame, errors: list, warnings: list):
    """Check that required columns do not contain missing values."""
    for col in REQUIRED_COLUMNS:
        missing_count = count_missing_values(df[col])

        if missing_count > 0:
            add_error(
                errors,
                f"Missing values found in required field '{col}': {missing_count}"
            )


def check_post_id_unique(df: pd.DataFrame, errors: list, warnings: list):
    """Check that post_id values are unique across the full dataset."""
    duplicate_post_ids = df["post_id"].duplicated().sum()

    if duplicate_post_ids > 0:
        add_error(errors, f"Duplicate post_id values found: {duplicate_post_ids}")


def check_post_id_format(df: pd.DataFrame, errors: list, warnings: list):
    """Check that post_id follows the expected format: fp_{uuid4_short}."""
    invalid_mask = ~df["post_id"].astype(str).str.match(POST_ID_PATTERN)
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        invalid_examples = (
            df.loc[invalid_mask, "post_id"]
            .dropna()
            .unique()
            .tolist()[:5]
        )

        add_error(
            errors,
            f"Invalid post_id format found: {invalid_count}. "
            f"Expected format: fp_ followed by 8 hexadecimal characters. "
            f"Examples: {invalid_examples}"
        )


def check_text_length(df: pd.DataFrame, errors: list, warnings: list):
    """Check that text length is within the required range."""
    text_lengths = df["text"].fillna("").astype(str).str.strip().str.len()

    too_short = text_lengths.lt(MIN_TEXT_LENGTH).sum()
    too_long = text_lengths.gt(MAX_TEXT_LENGTH).sum()

    if too_short > 0:
        add_error(
            errors,
            f"Text values shorter than {MIN_TEXT_LENGTH} characters found: {too_short}"
        )

    if too_long > 0:
        add_error(
            errors,
            f"Text values longer than {MAX_TEXT_LENGTH} characters found: {too_long}"
        )


def check_enum_values(df: pd.DataFrame, errors: list, warnings: list):
    """Check that controlled vocabulary fields contain only allowed values."""
    for col, allowed_values in ALLOWED_VALUES.items():
        invalid_mask = ~df[col].isin(allowed_values)
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            invalid_examples = (
                df.loc[invalid_mask, col]
                .dropna()
                .unique()
                .tolist()[:5]
            )

            add_error(
                errors,
                f"Invalid values found in '{col}': {invalid_count}. "
                f"Allowed values: {allowed_values}. "
                f"Examples: {invalid_examples}"
            )


def check_timestamp_simulated(df: pd.DataFrame, errors: list, warnings: list):
    """
    Check timestamp_simulated format and date range.

    Invalid datetime format is an error.
    Values outside the 2019–2023 window are warnings.
    """
    timestamps = pd.to_datetime(df["timestamp_simulated"], errors="coerce", utc=True)

    invalid_count = timestamps.isna().sum()
    if invalid_count > 0:
        add_error(errors, f"Invalid timestamp_simulated values found: {invalid_count}")
        return

    outside_range = ((timestamps < TIMESTAMP_START) | (timestamps > TIMESTAMP_END)).sum()

    if outside_range > 0:
        add_warning(
            warnings,
            f"timestamp_simulated values outside 2019–2023 window found: {outside_range}"
        )


def check_source_credibility(df: pd.DataFrame, errors: list, warnings: list):
    """
    Check source_credibility if the column is present.

    Values must be numeric and within the range 0.0–1.0.
    Missing or empty values are allowed because the field is optional.
    """
    if "source_credibility" not in df.columns:
        return

    values = df["source_credibility"]

    # Treat NaN, empty strings, and whitespace-only values as missing.
    non_missing = values[
        values.notna() & values.astype(str).str.strip().ne("")
    ]

    if non_missing.empty:
        return

    scores = pd.to_numeric(non_missing, errors="coerce")

    invalid_numeric = scores.isna().sum()
    if invalid_numeric > 0:
        add_error(errors, f"Invalid source_credibility values found: {invalid_numeric}")
        return

    out_of_range = ((scores < 0.0) | (scores > 1.0)).sum()
    if out_of_range > 0:
        add_error(
            errors,
            f"source_credibility values outside 0.0–1.0 range found: {out_of_range}"
        )


def check_theme_coverage_in_train(df: pd.DataFrame, errors: list, warnings: list):
    """
    Check that each narrative theme has at least 5% coverage in the training split.
    """
    train_df = df[df["split"] == "train"]

    if train_df.empty:
        add_warning(warnings, "Training split is empty; theme coverage could not be checked.")
        return

    theme_shares = train_df["narrative_theme"].value_counts(normalize=True)

    for theme in ALLOWED_VALUES["narrative_theme"]:
        actual_share = theme_shares.get(theme, 0.0)

        if actual_share < THEME_MIN_COVERAGE:
            add_warning(
                warnings,
                f"Theme '{theme}' has low coverage in training split: "
                f"{actual_share:.2%} (minimum expected: {THEME_MIN_COVERAGE:.0%})"
            )


def check_split_distribution(df: pd.DataFrame, errors: list, warnings: list):
    """
    Check that train/val/test distribution is approximately 70/15/15 ±5%.
    """
    split_shares = df["split"].value_counts(normalize=True)

    for split, expected_share in EXPECTED_SPLIT_DISTRIBUTION.items():
        actual_share = split_shares.get(split, 0.0)

        if abs(actual_share - expected_share) > DISTRIBUTION_TOLERANCE:
            add_warning(
                warnings,
                f"Split '{split}' distribution is {actual_share:.2%}; "
                f"expected approximately {expected_share:.2%} ±{DISTRIBUTION_TOLERANCE:.0%}."
            )


def check_label_distribution_by_split(df: pd.DataFrame, errors: list, warnings: list):
    """
    Check label distribution inside each split against the target distribution.
    """
    for split in ALLOWED_VALUES["split"]:
        split_df = df[df["split"] == split]

        if split_df.empty:
            add_warning(
                warnings,
                f"Split '{split}' is empty; label distribution could not be checked."
            )
            continue

        label_shares = split_df["label"].value_counts(normalize=True)

        for label, expected_share in EXPECTED_LABEL_DISTRIBUTION.items():
            actual_share = label_shares.get(label, 0.0)

            if abs(actual_share - expected_share) > DISTRIBUTION_TOLERANCE:
                add_warning(
                    warnings,
                    f"Label '{label}' in split '{split}' is {actual_share:.2%}; "
                    f"expected approximately {expected_share:.2%} ±{DISTRIBUTION_TOLERANCE:.0%}."
                )


# --- RULES LIST ---
# Rules are executed in this order.
# Column and required-value checks run first so later rules can safely access fields.

VALIDATION_RULES = [
    check_dataset_not_empty,
    check_expected_columns_exist,
    check_extra_columns,
    check_required_columns_not_empty,
    check_post_id_unique,
    check_post_id_format,
    check_text_length,
    check_enum_values,
    check_timestamp_simulated,
    check_source_credibility,
    check_theme_coverage_in_train,
    check_split_distribution,
    check_label_distribution_by_split,
]


# --- VALIDATION RUNNER ---

def validate_data(df: pd.DataFrame):
    """Run all validation rules and return errors and warnings."""
    errors = []
    warnings = []

    # Run basic checks first.
    check_dataset_not_empty(df, errors, warnings)
    check_expected_columns_exist(df, errors, warnings)

    # Stop early if the dataset is empty or required columns are missing.
    # This prevents later rules from crashing when columns do not exist.
    if errors:
        return errors, warnings

    # Run remaining rules.
    for rule in VALIDATION_RULES[2:]:
        rule(df, errors, warnings)

    return errors, warnings


# --- CLEAN OUTPUT GENERATION ---

def create_clean_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return only expected columns in the defined schema order.

    Optional columns are included only if they exist in the input dataset.
    Extra columns are excluded.
    """
    output_columns = [col for col in EXPECTED_COLUMNS if col in df.columns]
    return df[output_columns].copy()


# --- REPORT GENERATION ---

def write_report(report_path, input_path, output_path, df, errors, warnings):
    """Write a human-readable validation report."""
    status = "FAILED" if errors else "PASSED"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("DATA VALIDATION REPORT\n")
        file.write("=" * 40 + "\n\n")

        file.write(f"Status: {status}\n")
        file.write(f"Input file: {input_path}\n")
        file.write(f"Output file: {output_path}\n\n")

        file.write("Errors:\n")
        if errors:
            for error in errors:
                file.write(f"- {error}\n")
        else:
            file.write("- None\n")

        file.write("\nWarnings:\n")
        if warnings:
            for warning in warnings:
                file.write(f"- {warning}\n")
        else:
            file.write("- None\n")


# --- MAIN ENTRY POINT ---
# Handles command-line arguments and pipeline behavior.

def main():
    parser = argparse.ArgumentParser(
        description="Validate a generated JSON dataset against the expected schema."
    )

    parser.add_argument("--input", required=True, help="Path to input JSON file.")
    parser.add_argument(
        "--output",
        default="validated_data.json",
        help="Path to cleaned output JSON file.",
    )
    parser.add_argument(
        "--report",
        default="validation_report.txt",
        help="Path to validation report file.",
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    # Check input file exists.
    if not input_path.exists():
        print(f"Validation failed: file not found: {input_path}")
        sys.exit(1)

    # Load JSON file.
    try:
        df = pd.read_json(input_path)
    except Exception as e:
        print(f"Validation failed: could not read JSON file: {e}")
        sys.exit(1)

    # Run validation.
    errors, warnings = validate_data(df)

    # Create cleaned output only if validation passes.
    if not errors:
        clean_df = create_clean_output(df)
        clean_df.to_json(args.output, orient="records", indent=2, force_ascii=False)

    # Always write a validation report.
    write_report(args.report, args.input, args.output, df, errors, warnings)

    # Exit code controls pipeline behavior.
    if errors:
        print("Validation Failed.\n")

        print("Errors:")
        for error in errors:
            print(f"- {error}")

        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")

        print(f"\nReport saved to: {args.report}")
        sys.exit(1)

    print("Validation Passed.")
    print(f"Cleaned output saved to: {args.output}")
    print(f"Report saved to: {args.report}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()