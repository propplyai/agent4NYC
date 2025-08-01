#!/usr/bin/env python3
"""
Test script to investigate FDNY datasets on NYC Open Data
- Check actual column names and structure
- Test different query parameters
- Identify correct dataset IDs and search strategies
"""

import requests
import pandas as pd
import json
from nyc_opendata_client import NYCOpenDataClient

def test_dataset_structure(client, dataset_key, dataset_id):
    """Test the structure and columns of a dataset"""
    print(f"\n{'='*60}")
    print(f"TESTING DATASET: {dataset_key} ({dataset_id})")
    print(f"{'='*60}")
    
    try:
        # Method 1: Get small sample to see columns
        print(f"📊 Getting sample data to analyze structure...")
        sample_data = client.get_data(dataset_key, limit=5)
        
        if sample_data is not None and not sample_data.empty:
            print(f"✅ Dataset is accessible!")
            print(f"   Records returned: {len(sample_data)}")
            print(f"   Columns found: {len(sample_data.columns)}")
            print(f"\n📋 COLUMN NAMES:")
            for i, col in enumerate(sample_data.columns, 1):
                print(f"   {i:2d}. {col}")
            
            print(f"\n📝 SAMPLE DATA (first 2 rows):")
            for i, row in sample_data.head(2).iterrows():
                print(f"   Row {i+1}:")
                for col in sample_data.columns:
                    value = str(row[col])[:50] + '...' if len(str(row[col])) > 50 else str(row[col])
                    print(f"      {col}: {value}")
                print()
            
            return sample_data.columns.tolist()
        else:
            print(f"❌ No data returned or dataset is empty")
            return []
            
    except Exception as e:
        print(f"❌ Error accessing dataset: {e}")
        
        # Try to get more info about the error
        if "400 Client Error" in str(e):
            print(f"   → This is a 400 Client Error - likely invalid parameters or dataset ID")
        elif "404" in str(e):
            print(f"   → This is a 404 Error - dataset not found")
        elif "401" in str(e) or "403" in str(e):
            print(f"   → This is an authentication error")
        
        return []

def test_search_strategies(client, dataset_key, columns):
    """Test different search strategies for the dataset"""
    print(f"\n🔍 TESTING SEARCH STRATEGIES for {dataset_key}")
    print(f"-" * 50)
    
    # Common search fields to test
    search_fields_to_test = [
        ('bin', '4433339'),
        ('bin_number', '4433339'),
        ('buildingid', '4433339'),
        ('borough', 'MANHATTAN'),
        ('boro', '1'),
        ('block', '1073'),
        ('lot', '1'),
        ('address', '140 West 28th Street'),
        ('violation_address', '140 West 28th Street'),
        ('street_name', '28th Street'),
        ('house_number', '140')
    ]
    
    for field, value in search_fields_to_test:
        if field in columns:
            try:
                print(f"\n   🔍 Testing search by {field} = '{value}'...")
                where_clause = f"{field} = '{value}'"
                
                # Try exact match first
                result = client.get_data(dataset_key, where=where_clause, limit=5)
                
                if result is not None and not result.empty:
                    print(f"   ✅ Found {len(result)} records using {field}")
                    # Show sample result
                    if len(result) > 0:
                        sample_record = result.iloc[0]
                        print(f"      Sample: {dict(sample_record)}")
                else:
                    print(f"   ❌ No results for {field} = '{value}'")
                    
            except Exception as e:
                print(f"   ❌ Error searching by {field}: {e}")
        else:
            print(f"   ⚠️  Field '{field}' not available in dataset")

def test_metadata_endpoint(dataset_id):
    """Try to get metadata directly from Socrata API"""
    print(f"\n📋 TESTING METADATA ENDPOINT for {dataset_id}")
    print(f"-" * 50)
    
    try:
        # Socrata metadata endpoint
        metadata_url = f"https://data.cityofnewyork.us/api/views/{dataset_id}.json"
        response = requests.get(metadata_url, timeout=10)
        response.raise_for_status()
        
        metadata = response.json()
        
        print(f"✅ Metadata retrieved successfully!")
        print(f"   Dataset Name: {metadata.get('name', 'N/A')}")
        print(f"   Description: {metadata.get('description', 'N/A')}")
        print(f"   Rows: {metadata.get('rowsUpdatedAt', 'N/A')}")
        
        columns = metadata.get('columns', [])
        if columns:
            print(f"\n📋 COLUMNS FROM METADATA ({len(columns)} total):")
            for i, col in enumerate(columns, 1):
                name = col.get('name', col.get('fieldName', 'Unknown'))
                data_type = col.get('dataTypeName', 'Unknown')
                description = col.get('description', 'No description')[:60]
                print(f"   {i:2d}. {name} ({data_type}) - {description}")
        else:
            print(f"   ❌ No column information found in metadata")
            
        return metadata
        
    except Exception as e:
        print(f"❌ Error getting metadata: {e}")
        return None

def discover_alternative_fdny_datasets():
    """Search for alternative FDNY datasets"""
    print(f"\n🔍 SEARCHING FOR ALTERNATIVE FDNY DATASETS")
    print(f"=" * 60)
    
    # Known FDNY-related dataset IDs to test
    potential_datasets = [
        ('avgm-ztsb', 'FDNY Violations'),
        ('tsak-vtv3', 'Supposed Fire Safety Inspections'),
        ('ktas-47y7', 'Alternative FDNY Violation dataset'),
        ('ssq6-fkht', 'Bureau of Fire Prevention - Inspections'),
        ('bi53-yph3', 'Bureau of Fire Prevention - Active Violation Orders'),
        ('nvgj-hbht', 'Bureau of Fire Prevention - Building Summary'),
        ('8m42-w767', 'Fire Incident Dispatch Data'),
    ]
    
    for dataset_id, description in potential_datasets:
        print(f"\n📊 Testing {dataset_id}: {description}")
        try:
            metadata = test_metadata_endpoint(dataset_id)
            if metadata:
                # Check if it has useful fields
                columns = metadata.get('columns', [])
                column_names = [col.get('name', col.get('fieldName', '')) for col in columns]
                
                # Look for key identifying fields
                has_bin = any('bin' in col.lower() for col in column_names)
                has_address = any(any(term in col.lower() for term in ['address', 'street', 'house']) for col in column_names)
                has_block_lot = any(any(term in col.lower() for term in ['block', 'lot']) for col in column_names)
                
                print(f"   🔍 Key fields: BIN={has_bin}, Address={has_address}, Block/Lot={has_block_lot}")
                
                if has_bin or has_address or has_block_lot:
                    print(f"   ✅ This dataset looks useful for property searches!")
                else:
                    print(f"   ⚠️  Limited search capabilities")
                    
        except Exception as e:
            print(f"   ❌ Could not access {dataset_id}: {e}")

def main():
    """Main function to test FDNY datasets"""
    print("🚒 NYC OPEN DATA FDNY DATASET INVESTIGATION")
    print("=" * 80)
    
    # Initialize NYC Open Data client
    client = NYCOpenDataClient.from_config()
    
    # Test the datasets you mentioned
    datasets_to_test = [
        ('fdny_violations', 'avgm-ztsb'),
        ('fire_safety_inspections', 'tsak-vtv3')
    ]
    
    all_results = {}
    
    for dataset_key, dataset_id in datasets_to_test:
        columns = test_dataset_structure(client, dataset_key, dataset_id)
        all_results[dataset_key] = {
            'dataset_id': dataset_id,
            'columns': columns,
            'accessible': len(columns) > 0
        }
        
        if columns:
            test_search_strategies(client, dataset_key, columns)
    
    # Discover alternative datasets
    discover_alternative_fdny_datasets()
    
    # Summary
    print(f"\n" + "="*80)
    print("📊 INVESTIGATION SUMMARY")
    print("="*80)
    
    for dataset_key, info in all_results.items():
        status = "✅ ACCESSIBLE" if info['accessible'] else "❌ INACCESSIBLE"
        print(f"{dataset_key} ({info['dataset_id']}): {status}")
        if info['columns']:
            print(f"   Columns: {len(info['columns'])} found")
        else:
            print(f"   Columns: None accessible")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"1. Check the metadata endpoints for correct column names")
    print(f"2. Test alternative FDNY dataset IDs that were discovered")
    print(f"3. Use BIN, block/lot, or address-based searches depending on available columns")
    print(f"4. Consider using Bureau of Fire Prevention datasets instead of generic 'fire safety inspections'")

if __name__ == "__main__":
    main()