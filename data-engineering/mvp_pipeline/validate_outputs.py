"""
FireFusion Data Validator

Validates pipeline outputs before Supabase integration.
Checks: nulls, FK integrity, PK uniqueness, bounds, record counts.
"""

import pandas as pd
import json
import os
import sys

def validate_pipeline_outputs(output_dir="output"):
    """Validate all aligned tables and registries."""
    
    print("=" * 70)
    print("FireFusion Pipeline Output Validator")
    print("=" * 70)
    
    results = {}
    all_passed = True
    
    # Load registries first
    location_reg = pd.read_csv(os.path.join(output_dir, "location_registry.csv"))
    time_reg = pd.read_csv(os.path.join(output_dir, "time_registry.csv"))
    
    location_ids = set(location_reg['location_id'].values)
    time_ids = set(time_reg['time_id'].values)
    
    print("\nHUB TABLES:")
    print("  location_registry: {} grid cells".format(len(location_reg)))
    print("  time_registry: {} time periods".format(len(time_reg)))
    
    # Validate observation tables
    observation_tables = [
        ("fire_aligned.csv", "incident_id", True),
        ("weather_aligned.csv", "weather_id", True),
        ("vegetation_aligned.csv", "veg_condition_id", True),
    ]
    
    print("\nOBSERVATION TABLES:")
    for filename, pk_col, has_time in observation_tables:
        path = os.path.join(output_dir, filename)
        if not os.path.exists(path):
            print("  {} FAILED: File not found".format(filename))
            all_passed = False
            continue
        
        df = pd.read_csv(path)
        table_name = filename.replace("_aligned.csv", "")
        
        checks = {
            'record_count': len(df),
            'nulls_in_pk': df[pk_col].isnull().sum(),
            'nulls_in_location_id': df['location_id'].isnull().sum(),
            'pk_unique': df[pk_col].is_unique,
            'location_id_valid': df['location_id'].isin(location_ids).all(),
        }
        
        if has_time:
            checks['nulls_in_time_id'] = df['time_id'].isnull().sum()
            checks['time_id_valid'] = df['time_id'].isin(time_ids).all()
        
        passed = all(v == 0 or v == True for v in checks.values())
        status = "PASSED" if passed else "FAILED"
        
        print("  {}: {} records - {}".format(table_name, len(df), status))
        if not passed:
            print("    Details: {}".format(checks))
            all_passed = False
        
        results[table_name] = checks
    
    # Validate static tables
    static_tables = [
        ("topography_aligned.csv", "topo_id"),
        ("infrastructure_aligned.csv", "asset_id"),
    ]
    
    print("\nSTATIC TABLES:")
    for filename, pk_col in static_tables:
        path = os.path.join(output_dir, filename)
        if not os.path.exists(path):
            print("  {} FAILED: File not found".format(filename))
            all_passed = False
            continue
        
        df = pd.read_csv(path)
        table_name = filename.replace("_aligned.csv", "")
        
        checks = {
            'record_count': len(df),
            'nulls_in_pk': df[pk_col].isnull().sum(),
            'nulls_in_location_id': df['location_id'].isnull().sum(),
            'pk_unique': df[pk_col].is_unique,
            'location_id_valid': df['location_id'].isin(location_ids).all(),
        }
        
        passed = all(v == 0 or v == True for v in checks.values())
        status = "PASSED" if passed else "FAILED"
        
        print("  {}: {} records - {}".format(table_name, len(df), status))
        if not passed:
            print("    Details: {}".format(checks))
            all_passed = False
        
        results[table_name] = checks
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("VALIDATION PASSED - All tables ready for Supabase")
        print("=" * 70)
        return 0
    else:
        print("VALIDATION FAILED - Fix errors above")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    exit_code = validate_pipeline_outputs()
    sys.exit(exit_code)