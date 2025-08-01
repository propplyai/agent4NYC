#!/usr/bin/env python3
"""
Investigate Boiler Inspection Data for 140 West 28th Street
Determine why no boiler data is available and find last inspection
"""

import sys
from nyc_opendata_client import NYCOpenDataClient

def investigate_boiler_data():
    """Investigate boiler inspection data availability"""
    
    print("🔥 INVESTIGATING BOILER INSPECTION DATA")
    print("=" * 60)
    
    # Property details for 140 West 28th Street
    building_id = "1006242"
    address = "140 WEST 28 STREET"
    boro = "MANHATTAN"
    block = "803"
    lot = "62"
    
    print(f"🏢 Target Property: {address}")
    print(f"   Building ID: {building_id}")
    print(f"   Borough: {boro}")
    print(f"   Block/Lot: {block}/{lot}")
    
    client = NYCOpenDataClient.from_config()
    
    # Strategy 1: Search by exact BIN number
    print(f"\n🔍 STRATEGY 1: Search by BIN Number ({building_id})")
    print("-" * 40)
    
    try:
        boiler_data = client.get_data(
            'boiler_inspections',
            where=f"bin_number = '{building_id}'",
            select="tracking_number, boiler_id, inspection_date, defects_exist, report_status, bin_number",
            order="inspection_date DESC",
            limit=10
        )
        
        if boiler_data is not None and not boiler_data.empty:
            print(f"✅ Found {len(boiler_data)} boiler inspection records")
            for i, record in boiler_data.iterrows():
                print(f"   {i+1}. Date: {record.get('inspection_date', 'N/A')}")
                print(f"      Boiler ID: {record.get('boiler_id', 'N/A')}")
                print(f"      Status: {record.get('report_status', 'N/A')}")
                print(f"      Defects: {record.get('defects_exist', 'N/A')}")
        else:
            print("❌ No boiler records found for this BIN")
            
    except Exception as e:
        print(f"❌ Error with BIN search: {e}")
    
    # Strategy 2: Search nearby BIN numbers (in case of BIN mismatch)
    print(f"\n🔍 STRATEGY 2: Search Nearby BIN Numbers")
    print("-" * 40)
    
    try:
        # Try BIN numbers around our target
        bin_variations = [
            str(int(building_id) - 2),
            str(int(building_id) - 1), 
            building_id,
            str(int(building_id) + 1),
            str(int(building_id) + 2)
        ]
        
        for bin_var in bin_variations:
            print(f"   Checking BIN: {bin_var}")
            boiler_data = client.get_data(
                'boiler_inspections',
                where=f"bin_number = '{bin_var}'",
                select="tracking_number, boiler_id, inspection_date, bin_number",
                limit=5
            )
            
            if boiler_data is not None and not boiler_data.empty:
                print(f"   ✅ Found {len(boiler_data)} records for BIN {bin_var}")
                latest = boiler_data.iloc[0]
                print(f"      Latest: {latest.get('inspection_date', 'N/A')}")
            else:
                print(f"   ❌ No records for BIN {bin_var}")
                
    except Exception as e:
        print(f"❌ Error with nearby BIN search: {e}")
    
    # Strategy 3: Sample recent boiler inspections to understand data patterns
    print(f"\n🔍 STRATEGY 3: Sample Recent Boiler Inspections")
    print("-" * 40)
    
    try:
        # Get recent boiler inspections to see data patterns
        recent_boilers = client.get_data(
            'boiler_inspections',
            select="tracking_number, boiler_id, inspection_date, bin_number",
            order="inspection_date DESC",
            limit=10
        )
        
        if recent_boilers is not None and not recent_boilers.empty:
            print(f"✅ Found {len(recent_boilers)} recent boiler inspections")
            print("   Recent inspection pattern:")
            for i, record in recent_boilers.iterrows():
                date = record.get('inspection_date', 'N/A')
                bin_num = record.get('bin_number', 'N/A')
                boiler_id = record.get('boiler_id', 'N/A')
                print(f"   {i+1}. {date} | BIN: {bin_num} | Boiler: {boiler_id}")
                
        else:
            print("❌ No recent boiler inspections found")
            
    except Exception as e:
        print(f"❌ Error with recent inspections: {e}")
    
    # Strategy 4: Check if there are any boiler inspections in Manhattan
    print(f"\n🔍 STRATEGY 4: Manhattan Boiler Inspections")
    print("-" * 40)
    
    try:
        # Check for Manhattan boiler inspections (BIN numbers starting with 1)
        manhattan_boilers = client.get_data(
            'boiler_inspections',
            where="bin_number LIKE '1%'",
            select="tracking_number, boiler_id, inspection_date, bin_number",
            order="inspection_date DESC",
            limit=10
        )
        
        if manhattan_boilers is not None and not manhattan_boilers.empty:
            print(f"✅ Found {len(manhattan_boilers)} Manhattan boiler inspections")
            print("   Recent Manhattan inspections:")
            for i, record in manhattan_boilers.iterrows():
                date = record.get('inspection_date', 'N/A')
                bin_num = record.get('bin_number', 'N/A')
                print(f"   {i+1}. {date} | BIN: {bin_num}")
                
        else:
            print("❌ No Manhattan boiler inspections found")
            
    except Exception as e:
        print(f"❌ Error with Manhattan search: {e}")
    
    # Strategy 5: Check dataset metadata and total record count
    print(f"\n🔍 STRATEGY 5: Dataset Metadata Analysis")
    print("-" * 40)
    
    try:
        # Get total count of boiler inspections
        total_count = client.get_data(
            'boiler_inspections',
            select="tracking_number",
            limit=1
        )
        
        if total_count is not None:
            print("✅ Boiler inspections dataset is accessible")
            
            # Get date range of available data
            date_range = client.get_data(
                'boiler_inspections',
                select="inspection_date",
                order="inspection_date DESC",
                limit=1
            )
            
            if date_range is not None and not date_range.empty:
                latest_date = date_range.iloc[0]['inspection_date']
                print(f"   Latest inspection date in dataset: {latest_date}")
            
            # Get oldest date
            oldest_range = client.get_data(
                'boiler_inspections',
                select="inspection_date",
                order="inspection_date ASC",
                limit=1
            )
            
            if oldest_range is not None and not oldest_range.empty:
                oldest_date = oldest_range.iloc[0]['inspection_date']
                print(f"   Oldest inspection date in dataset: {oldest_date}")
                
        else:
            print("❌ Cannot access boiler inspections dataset")
            
    except Exception as e:
        print(f"❌ Error with metadata analysis: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    investigate_boiler_data()
