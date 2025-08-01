#!/usr/bin/env python3
"""
Test script for boiler data retrieval
Demonstrates the correct approach for searching NYC boiler inspection data
"""

import sys
sys.path.append('/Users/art3a/agent4NYC')
from nyc_opendata_client import NYCOpenDataClient

def test_boiler_search():
    """Test boiler search functionality"""
    
    client = NYCOpenDataClient.from_config()
    
    print("=== NYC BOILER INSPECTION DATA TEST ===")
    print()
    
    # First, show the dataset structure
    print("1. DATASET STRUCTURE:")
    print("-" * 40)
    try:
        sample = client.get_data('boiler_inspections', limit=1)
        if sample is not None and not sample.empty:
            print("Available columns:")
            for i, col in enumerate(sample.columns, 1):
                print(f"  {i:2d}. {col}")
        print()
    except Exception as e:
        print(f"Error getting dataset structure: {e}")
        return
    
    # Test with a known BIN
    print("2. TESTING BIN-BASED SEARCH:")
    print("-" * 40)
    test_bin = "1033684"  # Known BIN with boiler data
    
    try:
        data = client.get_data(
            'boiler_inspections',
            where=f"bin_number = '{test_bin}'",
            select="tracking_number, boiler_id, inspection_date, defects_exist, " +
                   "report_status, bin_number, boiler_make, pressure_type, report_type",
            order="inspection_date DESC",
            limit=20
        )
        
        if data is not None and not data.empty:
            print(f"✅ SUCCESS: Found {len(data)} boiler records for BIN {test_bin}")
            print()
            
            # Show latest inspection
            latest = data.iloc[0]
            print("Latest inspection details:")
            print(f"  Tracking Number: {latest['tracking_number']}")
            print(f"  Boiler ID: {latest['boiler_id']}")
            print(f"  Inspection Date: {latest['inspection_date']}")
            print(f"  Defects Exist: {latest['defects_exist']}")
            print(f"  Report Status: {latest['report_status']}")
            print(f"  Boiler Make: {latest['boiler_make']}")
            print(f"  Pressure Type: {latest['pressure_type']}")
            print()
            
            # Summary statistics
            accepted_reports = len(data[data['report_status'] == 'Accepted'])
            defective_boilers = len(data[data['defects_exist'] == 'Yes'])
            
            print("Summary statistics:")
            print(f"  Total inspections: {len(data)}")
            print(f"  Accepted reports: {accepted_reports}")
            print(f"  Inspections with defects: {defective_boilers}")
            print(f"  Defect rate: {defective_boilers/len(data)*100:.1f}%")
            
        else:
            print(f"❌ No boiler records found for BIN {test_bin}")
            
    except Exception as e:
        print(f"❌ Error in BIN search: {e}")
    
    print()
    
    # Demonstrate why address search doesn't work
    print("3. WHY ADDRESS SEARCH FAILS:")
    print("-" * 40)
    print("❌ The boiler dataset does NOT contain address fields like:")
    print("   - house_number")
    print("   - street_name") 
    print("   - address")
    print()
    print("✅ Boiler searches can ONLY be performed using:")
    print("   - bin_number (Building Identification Number)")
    print()
    print("📋 To find boiler data for an address:")
    print("   1. First get the BIN using HPD violations or other datasets")
    print("   2. Then search boiler data using that BIN")
    
    print()
    
    # Test the failing address search to demonstrate
    print("4. DEMONSTRATING ADDRESS SEARCH FAILURE:")
    print("-" * 40)
    try:
        failed_data = client.get_data(
            'boiler_inspections',
            where="house_number = '140' AND street_name LIKE '%WEST 28%'",
            limit=1
        )
        print("This should not work...")
    except Exception as e:
        print(f"✅ Expected error: {e}")
        print("   This confirms that address fields don't exist in the boiler dataset")

if __name__ == "__main__":
    test_boiler_search()