import os
import sys
import yaml
from supabase import create_client, Client
from typing import Dict, List, Tuple

# Core columns required for all datasets
CORE_COLUMNS = {
    "incident_id": "int8",
    "location_id": "int8",
    "time_id": "int8",
    "original_latitude": "float8",
    "original_longitude": "float8",
    "acq_date": "date",
    "acq_time": "text",
}

# Map Supabase types to simplified types for comparison
TYPE_MAPPING = {
    "int2": "int",
    "int4": "int",
    "int8": "int",
    "float4": "float",
    "float8": "float",
    "text": "text",
    "varchar": "text",
    "date": "date",
    "timestamp": "timestamp",
    "timestamptz": "timestamp",
}


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def connect_supabase() -> Client:
    """Connect to Supabase using environment variables."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables not set")
    
    return create_client(url, key)


def normalize_type(db_type: str) -> str:
    """Normalize database type to simplified form."""
    return TYPE_MAPPING.get(db_type, db_type)


def get_table_schema(client: Client, table_name: str) -> Dict[str, str]:
    """Fetch table schema from Supabase (column names and types)."""
    response = client.table(table_name).select("*", count="exact").limit(0).execute()
    
    # Extract column information from response
    if not response.data and not response.count:
        raise ValueError(f"Table '{table_name}' not found or is empty")
    
    # Supabase doesn't directly expose schema via client, so we query information schema
    schema_query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{}'
    ORDER BY ordinal_position
    """.format(table_name)
    
    result = client.postgrest.select("*").execute()
    
    # Fallback: attempt direct schema inspection
    try:
        schema = client.table(table_name).schema()
        columns = {}
        for col in schema.get("columns", []):
            columns[col["name"]] = col["type"]
        return columns
    except:
        # Alternative: manually inspect first row structure
        response = client.table(table_name).select("*").limit(1).execute()
        if response.data:
            return {key: type(value).__name__ for key, value in response.data[0].items()}
        return {}


def validate_schema(client: Client, table_name: str, config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that table has all required columns with correct types.
    
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    try:
        # Fetch table schema
        schema = get_table_schema(client, table_name)
    except Exception as e:
        return False, [f"Failed to fetch schema: {str(e)}"]
    
    if not schema:
        return False, [f"Could not determine schema for table '{table_name}'"]
    
    # Check core columns
    for col_name, expected_type in CORE_COLUMNS.items():
        if col_name not in schema:
            errors.append(f"MISSING: Core column '{col_name}' not found")
        else:
            db_type = normalize_type(schema[col_name])
            expected_normalized = normalize_type(expected_type)
            if db_type != expected_normalized:
                errors.append(
                    f"TYPE MISMATCH: Column '{col_name}' is {db_type}, expected {expected_normalized}"
                )
    
    # Check dataset-specific columns from config
    dataset_columns = config.get("columns", {})
    for col_name, col_def in dataset_columns.items():
        if col_name not in schema:
            errors.append(f"MISSING: Dataset column '{col_name}' not found")
        else:
            expected_type = col_def.get("type", "text")
            db_type = normalize_type(schema[col_name])
            expected_normalized = normalize_type(expected_type)
            if db_type != expected_normalized:
                errors.append(
                    f"TYPE MISMATCH: Column '{col_name}' is {db_type}, expected {expected_normalized}"
                )
    
    # Check for unexpected extra columns (optional warning)
    expected_cols = set(CORE_COLUMNS.keys()) | set(dataset_columns.keys())
    extra_cols = set(schema.keys()) - expected_cols
    if extra_cols:
        for col in extra_cols:
            errors.append(f"EXTRA: Unexpected column '{col}' found in table")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    config_path = "config.yaml"
    
    # Allow config path via command line argument
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Load config
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config: {e}")
        sys.exit(1)
    
    table_name = config.get("table_name")
    if not table_name:
        print("Error: 'table_name' not specified in config.yaml")
        sys.exit(1)
    
    # Connect to Supabase
    try:
        client = connect_supabase()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Validate schema
    print(f"Validating schema for table: {table_name}")
    is_valid, errors = validate_schema(client, table_name, config)
    
    # Report results
    if is_valid:
        print(f"✓ Schema validation passed for '{table_name}'")
        sys.exit(0)
    else:
        print(f"✗ Schema validation FAILED for '{table_name}':")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
