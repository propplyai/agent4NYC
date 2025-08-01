#!/usr/bin/env python3
"""
Investigate Elevator Data for 140 West 28th Street
Check for elevator devices, inspections, and compliance status
"""

import sys
from nyc_opendata_client import NYCOpenDataClient

def investigate_elevators_140_west28():
    """Investigate elevator data for 140 West 28th Street"""
    
    print("🛗 INVESTIGATING ELEVATOR DATA FOR 140 WEST 28TH STREET")
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
    
    # First, confirm elevator dataset columns
    print(f"\n🔍 ELEVATOR DATASET COLUMNS")
    print("-" * 40)
    
    try:
        sample_data = client.get_data('elevator_inspections', limit=1)
        
        if sample_data is not None and not sample_data.empty:
            print(f"✅ Elevator dataset accessible - {len(sample_data.columns)} columns")
            print("   All columns:")
            for i, col in enumerate(sample_data.columns, 1):
                print(f"     {i:2d}. {col}")
        else:
            print("❌ Cannot access elevator dataset")
            return
            
    except Exception as e:
        print(f"❌ Error accessing elevator dataset: {e}")
        return
    
    # Strategy 1: Search by BIN number
    print(f"\n🔍 STRATEGY 1: Search by BIN ({building_id})")
    print("-" * 40)
    
    try:
        elevator_data = client.get_data(
            'elevator_inspections',
            where=f"bin = '{building_id}'",
            select="device_number, device_type, device_status, status_date, house_number, street_name, borough",
            order="status_date DESC",
            limit=20
        )
        
        if elevator_data is not None and not elevator_data.empty:
            print(f"✅ Found {len(elevator_data)} elevator records for BIN {building_id}")
            
            # Show all elevator devices
            for i, record in elevator_data.iterrows():
                device_num = record.get('device_number', 'N/A')
                device_type = record.get('device_type', 'N/A')
                status = record.get('device_status', 'N/A')
                date = record.get('status_date', 'N/A')
                house = record.get('house_number', 'N/A')
                street = record.get('street_name', 'N/A')
                
                print(f"   {i+1}. Device: {device_num}")
                print(f"      Type: {device_type}")
                print(f"      Status: {status}")
                print(f"      Date: {date}")
                print(f"      Address: {house} {street}")
                print()
                
        else:
            print("❌ No elevator records found for this BIN")
            
    except Exception as e:
        print(f"❌ Error with BIN search: {e}")
    
    # Strategy 2: Search by Block/Lot (in case BIN doesn't match)
    print(f"\n🔍 STRATEGY 2: Search by Block/Lot ({block}/{lot})")
    print("-" * 40)
    
    try:
        elevator_data = client.get_data(
            'elevator_inspections',
            where=f"block = '{block}' AND lot = '{lot}'",
            select="device_number, device_type, device_status, status_date, bin, house_number, street_name",
            order="status_date DESC",
            limit=20
        )
        
        if elevator_data is not None and not elevator_data.empty:
            print(f"✅ Found {len(elevator_data)} elevator records for Block {block}, Lot {lot}")
            
            for i, record in elevator_data.iterrows():
                device_num = record.get('device_number', 'N/A')
                device_type = record.get('device_type', 'N/A')
                status = record.get('device_status', 'N/A')
                date = record.get('status_date', 'N/A')
                bin_num = record.get('bin', 'N/A')
                house = record.get('house_number', 'N/A')
                street = record.get('street_name', 'N/A')
                
                print(f"   {i+1}. Device: {device_num} (BIN: {bin_num})")
                print(f"      Type: {device_type}")
                print(f"      Status: {status}")
                print(f"      Date: {date}")
                print(f"      Address: {house} {street}")
                print()
                
        else:
            print("❌ No elevator records found for this Block/Lot")
            
    except Exception as e:
        print(f"❌ Error with Block/Lot search: {e}")
    
    # Strategy 3: Search by address components
    print(f"\n🔍 STRATEGY 3: Search by Address (140 WEST 28)")
    print("-" * 40)
    
    try:
        elevator_data = client.get_data(
            'elevator_inspections',
            where="house_number = '140' AND street_name LIKE '%WEST 28%'",
            select="device_number, device_type, device_status, status_date, bin, house_number, street_name, borough",
            order="status_date DESC",
            limit=20
        )
        
        if elevator_data is not None and not elevator_data.empty:
            print(f"✅ Found {len(elevator_data)} elevator records for address search")
            
            for i, record in elevator_data.iterrows():
                device_num = record.get('device_number', 'N/A')
                device_type = record.get('device_type', 'N/A')
                status = record.get('device_status', 'N/A')
                date = record.get('status_date', 'N/A')
                bin_num = record.get('bin', 'N/A')
                house = record.get('house_number', 'N/A')
                street = record.get('street_name', 'N/A')
                borough = record.get('borough', 'N/A')
                
                print(f"   {i+1}. Device: {device_num} (BIN: {bin_num})")
                print(f"      Type: {device_type}")
                print(f"      Status: {status}")
                print(f"      Date: {date}")
                print(f"      Address: {house} {street}, {borough}")
                print()
                
        else:
            print("❌ No elevator records found for address search")
            
    except Exception as e:
        print(f"❌ Error with address search: {e}")
    
    # Strategy 4: Check nearby BINs (like we did for boilers)
    print(f"\n🔍 STRATEGY 4: Check Nearby BINs")
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
            elevator_data = client.get_data(
                'elevator_inspections',
                where=f"bin = '{bin_var}'",
                select="device_number, device_type, device_status, status_date, house_number, street_name",
                limit=5
            )
            
            if elevator_data is not None and not elevator_data.empty:
                print(f"   ✅ Found {len(elevator_data)} records for BIN {bin_var}")
                latest = elevator_data.iloc[0]
                device_num = latest.get('device_number', 'N/A')
                status = latest.get('device_status', 'N/A')
                date = latest.get('status_date', 'N/A')
                address = f"{latest.get('house_number', '')} {latest.get('street_name', '')}"
                print(f"      Latest: Device {device_num}, Status: {status}, Date: {date}")
                print(f"      Address: {address}")
            else:
                print(f"   ❌ No records for BIN {bin_var}")
                
    except Exception as e:
        print(f"❌ Error with nearby BIN search: {e}")
    
    # Strategy 5: Sample recent Manhattan elevator inspections
    print(f"\n🔍 STRATEGY 5: Recent Manhattan Elevator Activity")
    print("-" * 40)
    
    try:
        # Get recent Manhattan elevator inspections
        recent_elevators = client.get_data(
            'elevator_inspections',
            where="borough = 'MANHATTAN'",
            select="device_number, device_type, device_status, status_date, bin, house_number, street_name",
            order="status_date DESC",
            limit=10
        )
        
        if recent_elevators is not None and not recent_elevators.empty:
            print(f"✅ Found {len(recent_elevators)} recent Manhattan elevator records")
            print("   Recent Manhattan elevator activity:")
            for i, record in recent_elevators.iterrows():
                date = record.get('status_date', 'N/A')
                bin_num = record.get('bin', 'N/A')
                device_num = record.get('device_number', 'N/A')
                address = f"{record.get('house_number', '')} {record.get('street_name', '')}"
                status = record.get('device_status', 'N/A')
                print(f"   {i+1}. {date} | BIN: {bin_num} | Device: {device_num}")
                print(f"       Address: {address} | Status: {status}")
                
        else:
            print("❌ No recent Manhattan elevator records found")
            
    except Exception as e:
        print(f"❌ Error with Manhattan elevator search: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 ELEVATOR INVESTIGATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    investigate_elevators_140_west28()
