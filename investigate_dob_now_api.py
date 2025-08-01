#!/usr/bin/env python3
"""
Investigate DOB NOW API datasets for recent compliance data
Check if we can access DOB NOW: Safety Boiler and other compliance datasets
"""

import sys
from nyc_opendata_client import NYCOpenDataClient

def investigate_dob_now_datasets():
    """Investigate DOB NOW datasets available through NYC Open Data API"""
    
    print("🏗️ INVESTIGATING DOB NOW DATASETS")
    print("=" * 60)
    
    client = NYCOpenDataClient.from_config()
    
    # Check available datasets in our client
    print("Available datasets in NYC Open Data client:")
    for key, config in client.datasets.items():
        print(f"   {key}: {config['id']} - {config['name']}")
    
    # Test key DOB NOW datasets that are already configured
    test_datasets = {
        'boiler_inspections': 'DOB NOW: Safety Boiler (already configured)',
        'elevator_inspections': 'Elevator Inspections (already configured)', 
        'dob_violations': 'DOB Violations (already configured)',
        'hpd_violations': 'HPD Violations (already configured)'
    }
    
    # Test each dataset
    for dataset_key, description in test_datasets.items():
        print(f"\n🔍 Testing {dataset_key}")
        print(f"    {description}")
        print("-" * 40)
        
        try:
            # Try to get a sample record to see columns
            data = client.get_data(dataset_key, limit=1)
            
            if data is not None and not data.empty:
                print(f"✅ Dataset accessible - {len(data.columns)} columns")
                print("   Columns:")
                for i, col in enumerate(data.columns[:10], 1):  # Show first 10 columns
                    print(f"     {i:2d}. {col}")
                if len(data.columns) > 10:
                    print(f"     ... and {len(data.columns) - 10} more columns")
                
                # Show sample data
                print("   Sample record:")
                for col in data.columns[:5]:  # Show first 5 columns
                    value = data[col].iloc[0] if not data[col].isna().iloc[0] else "NULL"
                    print(f"     {col}: {value}")
                    
            else:
                print("❌ No data returned")
                
        except Exception as e:
            print(f"❌ Error accessing dataset: {e}")
    
    # Now specifically test DOB NOW Safety Boiler for our target property
    print(f"\n" + "="*60)
    print("🔥 TESTING DOB NOW SAFETY BOILER FOR 140 WEST 28TH STREET")
    print("="*60)
    
    # Property details
    building_id = "1006242"
    address = "140 WEST 28 STREET"
    
    try:
        # Check if DOB NOW Safety Boiler dataset has different column names
        print(f"🔍 Checking DOB NOW Safety Boiler columns...")
        sample_data = client.get_data('boiler_inspections', limit=5)
        
        if sample_data is not None and not sample_data.empty:
            print(f"✅ DOB NOW Safety Boiler accessible")
            print("   All columns:")
            for i, col in enumerate(sample_data.columns, 1):
                print(f"     {i:2d}. {col}")
            
            # Look for BIN-related columns
            bin_columns = [col for col in sample_data.columns if 'bin' in col.lower()]
            address_columns = [col for col in sample_data.columns if any(term in col.lower() for term in ['address', 'street', 'house'])]
            
            print(f"\n   BIN-related columns: {bin_columns}")
            print(f"   Address-related columns: {address_columns}")
            
            # Try different search strategies
            search_strategies = []
            
            # Strategy 1: If there's a bin column
            if bin_columns:
                for bin_col in bin_columns:
                    search_strategies.append((f"Search by {bin_col}", f"{bin_col} = '{building_id}'"))
            
            # Strategy 2: If there are address columns
            if address_columns:
                for addr_col in address_columns:
                    search_strategies.append((f"Search by {addr_col}", f"{addr_col} LIKE '%140%' AND {addr_col} LIKE '%28%'"))
            
            # Test each search strategy
            for strategy_name, where_clause in search_strategies:
                print(f"\n   🔍 {strategy_name}")
                print(f"      Query: {where_clause}")
                
                try:
                    results = client.get_data('boiler_inspections', where=where_clause, limit=10)
                    
                    if results is not None and not results.empty:
                        print(f"      ✅ Found {len(results)} records!")
                        
                        # Show sample results
                        for i, record in results.iterrows():
                            print(f"         {i+1}. Record details:")
                            for col in results.columns[:5]:  # Show first 5 columns
                                value = record[col] if not record[col] is None else "NULL"
                                print(f"            {col}: {value}")
                            print()
                            
                        break  # Stop after first successful strategy
                    else:
                        print(f"      ❌ No records found")
                        
                except Exception as e:
                    print(f"      ❌ Search error: {e}")
            
        else:
            print("❌ Cannot access DOB NOW Safety Boiler dataset")
            
    except Exception as e:
        print(f"❌ Error with DOB NOW Safety Boiler investigation: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 DOB NOW INVESTIGATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    investigate_dob_now_datasets()
