#!/usr/bin/env python3
"""
Explore dataset columns to understand the schema
"""

import pandas as pd
from nyc_opendata_client import NYCOpenDataClient

def explore_dataset_columns():
    """Explore the column structure of key datasets"""
    
    print("Exploring NYC Open Data dataset columns")
    print("=" * 50)
    
    client = NYCOpenDataClient.from_config()
    
    # Key datasets to explore
    datasets = ['hpd_registrations', 'hpd_violations', 'dob_violations', 'complaints_311']
    
    for dataset_key in datasets:
        print(f"\n--- {dataset_key.upper()} ---")
        try:
            # Get a small sample to see column structure
            data = client.get_data(dataset_key, limit=1)
            
            if not data.empty:
                print(f"✓ Dataset accessible - {len(data.columns)} columns")
                print("Columns:")
                for i, col in enumerate(data.columns, 1):
                    print(f"  {i:2d}. {col}")
                
                # Show a sample record
                print(f"\nSample record:")
                for col in data.columns[:10]:  # Show first 10 columns
                    value = data[col].iloc[0] if not pd.isna(data[col].iloc[0]) else "NULL"
                    print(f"  {col}: {value}")
                
                if len(data.columns) > 10:
                    print(f"  ... and {len(data.columns) - 10} more columns")
                    
            else:
                print("❌ No data returned")
                
        except Exception as e:
            print(f"❌ Error accessing {dataset_key}: {e}")
    
    # Now try a simple search in each working dataset
    print("\n" + "="*50)
    print("TESTING SIMPLE QUERIES")
    print("="*50)
    
    for dataset_key in datasets:
        print(f"\n--- Testing {dataset_key} ---")
        try:
            # Try to get just a few records without any WHERE clause
            data = client.get_data(dataset_key, limit=3)
            
            if not data.empty:
                print(f"✓ Successfully retrieved {len(data)} records")
                
                # Look for address-related columns
                address_cols = [col for col in data.columns if any(term in col.lower() for term in ['address', 'street', 'house', 'building'])]
                if address_cols:
                    print(f"Address-related columns: {address_cols}")
                    for col in address_cols[:3]:  # Show first 3 address columns
                        sample_values = data[col].dropna().head(3).tolist()
                        print(f"  {col}: {sample_values}")
                
                # Look for location/borough columns
                location_cols = [col for col in data.columns if any(term in col.lower() for term in ['boro', 'borough', 'zip', 'block', 'lot'])]
                if location_cols:
                    print(f"Location-related columns: {location_cols}")
                    
            else:
                print("No data returned")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    explore_dataset_columns()
