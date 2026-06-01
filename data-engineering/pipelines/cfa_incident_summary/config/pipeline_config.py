"""
Configuration for CFA Incident Summary historical pipeline.
"""

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PIPELINE_DIR / "data"
REFERENCE_DIR = DATA_DIR / "reference"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"
LOGS_DIR = PIPELINE_DIR / "logs"

DISTRICT_REGISTRY_CSV = REFERENCE_DIR / "cfa_district_registry.csv"
DEFAULT_RAW_FILE = RAW_DIR / "cfa_incident_summary.xlsx"

PROCESSED_PARQUET = PROCESSED_DIR / "cfa_incidents_ready.parquet"
PROFILE_JSON = LOGS_DIR / "cfa_incident_profile.json"
VALIDATION_JSON = LOGS_DIR / "cfa_validation_report.json"
LOAD_REPORT_JSON = LOGS_DIR / "cfa_load_report.json"

SOURCE_SYSTEM = "CFA Incident Summary"
TIMEZONE = "Australia/Melbourne"

# Expected raw column names (case-insensitive match applied in preprocess)
RAW_COLUMNS = {
    "incident_datetime": ["incident_datetime", "Incident Datetime", "INCIDENT_DATETIME"],
    "incident_no": ["incident_no", "Incident No", "INCIDENT_NO"],
    "district_no": ["District_no", "district_no", "DISTRICT_NO", "District_No"],
    "incident_type_code": ["incident_type_code", "Incident Type Code"],
    "incident_type": ["incident_type", "Incident Type"],
}

VALID_DISTRICT_NUMBERS = {
    2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 23, 24, 27
}

SUPABASE_BATCH_SIZE = 500
