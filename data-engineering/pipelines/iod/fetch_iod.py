"""
FireFusion Data Engineering Pipeline — Indian Ocean Dipole (IOD) Data Ingestion & Processing
Dataset: Indian Ocean Dipole Mode Index (DMI)
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import urllib.request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Base directories following repository architecture
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
DATASETS_IOD_DIR = os.path.join(BASE_DIR, "datasets", "iod")

DATE_STAMP = datetime.now().strftime("%Y%m%d")

# Official NOAA PSL Live Data Endpoints (HadISST 1.1)
NOAA_DMI_WEST_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmiwest.had.long.data"
NOAA_DMI_EAST_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmieast.had.long.data"

# Number of latest years to extract and process (30 years for AI model training)
LATEST_YEARS_COUNT = 30


def create_directories():
    """Ensure all required output directories exist."""
    for folder in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DATASETS_IOD_DIR]:
        os.makedirs(folder, exist_ok=True)
        logger.info(f"Directory verified: {folder}")


def fetch_noaa_psl_series(url):
    """Fetch and parse NOAA PSL ASCII time-series file dynamically."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        lines = resp.read().decode("utf-8").splitlines()
        
    data_rows = []
    for line in lines[1:]:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] in ["-9999", "-9999.000"] or "DMI" in parts[0] or "Created" in parts[0] or "using" in parts[0] or "Timeseries" in parts[0] or "http" in parts[0] or "Preliminary" in parts[0]:
            break
        if len(parts) == 13:
            year = int(parts[0])
            vals = [float(x) for x in parts[1:]]
            data_rows.append([year] + vals)
            
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df = pd.DataFrame(data_rows, columns=["Year"] + months)
    df_long = pd.melt(df, id_vars=["Year"], value_vars=months, var_name="Month_Name", value_name="val")
    df_long.loc[df_long["val"] <= -99, "val"] = np.nan
    return df_long


def fetch_raw_data():
    """
    Stage 2: Extraction — Fetch live dataset dynamically from NOAA PSL endpoints and preserve in data/raw/.
    """
    raw_filename = f"iod_dmi_raw_{DATE_STAMP}.csv"
    raw_filepath = os.path.join(RAW_DATA_DIR, raw_filename)
    
    logger.info("Fetching live dataset dynamically from NOAA PSL endpoints...")
    df_w = fetch_noaa_psl_series(NOAA_DMI_WEST_URL).rename(columns={"val": "west"})
    df_e = fetch_noaa_psl_series(NOAA_DMI_EAST_URL).rename(columns={"val": "east"})
    
    df_merged = pd.merge(df_w, df_e, on=["Year", "Month_Name"])
    df_merged["dmi_anomaly"] = (df_merged["west"] - df_merged["east"]).round(3)
    df_clean_raw = df_merged.dropna(subset=["dmi_anomaly"])
    
    # Save raw extracted data
    df_clean_raw.to_csv(raw_filepath, index=False)
    logger.info(f"Live raw dataset preserved in: {raw_filepath} ({len(df_clean_raw)} total records)")
    return raw_filepath


def assign_iod_phase(anom):
    """Derive IOD Phase categorisation based on BOM / NOAA DMI thresholds."""
    if pd.isna(anom):
        return 'Neutral'
    elif anom >= 0.40:
        return 'Positive IOD'
    elif anom <= -0.40:
        return 'Negative IOD'
    else:
        return 'Neutral'


def transform_and_standardise(raw_filepath, num_years=LATEST_YEARS_COUNT):
    """
    Stage 4: Transformation — Filter for the latest N years, clean, and align with FireFusion Star Schema & Time_Registry.
    Classifies IOD Phase and computes lag features.
    """
    logger.info(f"Transforming raw dataset: {raw_filepath}")
    
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    df_long = pd.read_csv(raw_filepath)
    df_long['month'] = df_long['Month_Name'].map(month_map)
    df_long['year'] = df_long['Year'].astype(int)
    
    # Dynamically determine the latest N years
    max_year = df_long['year'].max()
    min_latest_year = max_year - (num_years - 1)
    logger.info(f"Filtering dataset dynamically for the latest {num_years} years ({min_latest_year} to {max_year})...")
    
    # Filter dataset for latest N years
    df_filtered = df_long[df_long['year'] >= min_latest_year].copy()
    
    # Construct Year-Month string ('YYYY-MM')
    df_filtered['record_year_month'] = df_filtered['year'].astype(str) + '-' + df_filtered['month'].astype(str).str.zfill(2)
    
    # Construct standard month-start datetime ('YYYY-MM-01 00:00:00')
    df_filtered['datetime_record'] = pd.to_datetime(df_filtered['record_year_month'] + '-01 00:00:00')
    
    # Calculate integer time_id following team Time_Registry standard (YYYYMMDDHH)
    df_filtered['time_id'] = df_filtered['datetime_record'].dt.strftime('%Y%m0100').astype(int)
    
    # Ensure numeric DMI Anomaly
    df_filtered['dmi_anomaly'] = pd.to_numeric(df_filtered['dmi_anomaly'], errors='coerce')
    
    # Apply IOD Phase categorisation
    df_filtered['iod_phase'] = df_filtered['dmi_anomaly'].apply(assign_iod_phase)
    
    # Sort chronologically before calculating lag features
    df_sorted = df_filtered.sort_values('datetime_record').reset_index(drop=True)
    
    # Derive 6-month pre-conditioning lag feature (dmi_lag6m)
    df_sorted['dmi_lag6m'] = df_sorted['dmi_anomaly'].shift(6)
    
    # Data Lineage origin tag
    df_sorted['original_source'] = 'NOAA_PSL_DMI'
    
    # Generate explicit Primary Key iod_id
    df_sorted['iod_id'] = range(1, len(df_sorted) + 1)
    
    # Select final schema-aligned columns
    final_cols = ['iod_id', 'time_id', 'datetime_record', 'record_year_month', 'dmi_anomaly', 'iod_phase', 'dmi_lag6m', 'original_source']
    df_clean = df_sorted[final_cols]
    
    # 1. Save processed CSV file to data/processed/
    processed_filename = f"iod_dmi_processed_{DATE_STAMP}.csv"
    processed_filepath = os.path.join(PROCESSED_DATA_DIR, processed_filename)
    df_clean.to_csv(processed_filepath, index=False)
    logger.info(f"Processed dataset ({len(df_clean)} records across latest {num_years} years) saved to: {processed_filepath}")
    
    # 2. Save dataset copy to datasets/iod/
    iod_dataset_filename = f"iod_dmi_{DATE_STAMP}.csv"
    iod_dataset_path = os.path.join(DATASETS_IOD_DIR, iod_dataset_filename)
    df_clean.to_csv(iod_dataset_path, index=False)
    logger.info(f"Standard dataset copy saved to: {iod_dataset_path}")
    
    return df_clean


def validate_dataset(df):
    """
    Stage 5: Quality Assurance & Validation.
    """
    logger.info("Executing Quality Assurance & Validation checks...")
    
    # Check 1: Record count
    assert len(df) > 0, "Validation Failed: Dataset is empty."
    logger.info(f"Validation Check 1 Passed: {len(df)} monthly records processed.")
    
    # Check 2: Required columns present
    required_cols = ['iod_id', 'time_id', 'datetime_record', 'record_year_month', 'dmi_anomaly', 'iod_phase', 'dmi_lag6m', 'original_source']
    for col in required_cols:
        assert col in df.columns, f"Validation Failed: Missing column '{col}'"
    logger.info("Validation Check 2 Passed: All required schema columns present.")
    
    # Check 3: Phase classification counts
    phase_counts = df['iod_phase'].value_counts().to_dict()
    logger.info(f"Validation Check 3 Passed: IOD Phase Distribution -> {phase_counts}")
    
    # Check 4: Null values in PK / Time_ID
    assert df['iod_id'].isnull().sum() == 0, "Validation Failed: Null values found in iod_id"
    assert df['time_id'].isnull().sum() == 0, "Validation Failed: Null values found in time_id"
    logger.info("Validation Check 4 Passed: Primary key and time_id non-null verification clean.")


def main():
    logger.info("Starting Indian Ocean Dipole (IOD) Data Engineering Pipeline...")
    create_directories()
    raw_path = fetch_raw_data()
    df_clean = transform_and_standardise(raw_path, num_years=LATEST_YEARS_COUNT)
    validate_dataset(df_clean)
    logger.info("INDIAN OCEAN DIPOLE (IOD) DATA PIPELINE COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
