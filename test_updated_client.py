#!/usr/bin/env python3
"""
Test script for the updated NYC Open Data client with corrected FDNY dataset configurations
"""

from nyc_opendata_client import NYCOpenDataClient

def test_updated_fdny_client():
    """Test the updated NYC Open Data client with corrected FDNY datasets"""
    
    print("🧪 TESTING UPDATED NYC OPEN DATA CLIENT")
    print("=" * 80)
    
    # Initialize client
    client = NYCOpenDataClient.from_config()
    
    # Show available FDNY datasets
    print("\n📊 AVAILABLE FDNY DATASETS:")
    print("-" * 40)
    
    fdny_datasets = {k: v for k, v in client.datasets.items() if 'fdny' in k.lower() or 'fire' in k.lower()}
    
    for key, info in fdny_datasets.items():
        print(f"\n🚒 {key}")
        print(f"   ID: {info['id']}")
        print(f"   Name: {info['name']}")
        print(f"   Description: {info['description']}")
        
        if 'search_fields' in info:
            print(f"   Search Fields: {list(info['search_fields'].keys())}")
    
    # Test 1: Search FDNY violations by location
    print(f"\n" + "="*60)
    print("TEST 1: FDNY VIOLATIONS BY LOCATION")
    print("="*60)
    
    test_cases = [
        {
            'name': 'Block/Lot Search (Manhattan Block 1073, Lot 1)',
            'params': {'borough': 'MANHATTAN', 'block': '1073', 'lot': '1'}
        },
        {
            'name': 'Address Search (140 West 28th Street, Manhattan)', 
            'params': {'borough': 'MANHATTAN', 'address': '140 West 28th Street'}
        },
        {
            'name': 'Borough Only Search (Manhattan)',
            'params': {'borough': 'MANHATTAN'}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['name']}")
        try:
            violations = client.search_fdny_violations_by_location(**test_case['params'])
            
            if violations is not None and not violations.empty:
                print(f"   ✅ Found {len(violations)} violations")
                
                # Show sample
                if len(violations) > 0:
                    sample = violations.iloc[0]
                    print(f"   📝 Sample violation:")
                    print(f"      Ticket: {sample.get('ticket_number', 'N/A')}")
                    print(f"      Date: {sample.get('violation_date', 'N/A')}")
                    print(f"      Location: {sample.get('violation_location_house', '')} {sample.get('violation_location_street_name', '')}")
                    print(f"      Amount: ${sample.get('total_violation_amount', 'N/A')}")
            else:
                print(f"   ❌ No violations found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 2: Search fire prevention by BIN
    print(f"\n" + "="*60)
    print("TEST 2: FIRE PREVENTION BY BIN")
    print("="*60)
    
    test_bin = "4433339"  # 140 West 28th Street
    print(f"\n🔍 Searching fire prevention data for BIN {test_bin}")
    
    try:
        fire_prev_results = client.search_fire_prevention_by_bin(test_bin)
        
        total_records = sum(len(df) for df in fire_prev_results.values() if not df.empty)
        print(f"\n📊 Total fire prevention records found: {total_records}")
        
        for dataset_name, df in fire_prev_results.items():
            if not df.empty:
                print(f"\n📋 {dataset_name} ({len(df)} records):")
                sample = df.iloc[0]
                print(f"   Sample: {dict(list(sample.items())[:3])}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Dataset information verification
    print(f"\n" + "="*60)
    print("TEST 3: DATASET CONFIGURATION VERIFICATION")
    print("="*60)
    
    expected_datasets = [
        'fdny_violations',
        'fdny_violations_simple', 
        'fire_prevention_inspections',
        'fire_prevention_violations',
        'fire_prevention_summary'
    ]
    
    for dataset_key in expected_datasets:
        if dataset_key in client.datasets:
            dataset = client.datasets[dataset_key]
            print(f"\n✅ {dataset_key}")
            print(f"   ID: {dataset['id']}")
            print(f"   Has search fields: {'search_fields' in dataset}")
            
            if 'search_fields' in dataset:
                search_fields = dataset['search_fields']
                print(f"   Search capabilities: {list(search_fields.keys())}")
        else:
            print(f"\n❌ Missing dataset: {dataset_key}")
    
    print(f"\n" + "="*80)
    print("✅ TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_updated_fdny_client()