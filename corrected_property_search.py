#!/usr/bin/env python3
"""
Corrected Property Search - Using Real NYC Open Data Column Names
Based on actual column exploration using show_columns.py
"""

import sys
import json
from datetime import datetime
from nyc_opendata_client import NYCOpenDataClient

def search_property_with_real_columns(address: str):
    """
    Search for property using confirmed column names from NYC Open Data
    
    Args:
        address: Property address to search for
        
    Returns:
        Property information and compliance data
    """
    print(f"🏢 Searching for: {address}")
    print("=" * 60)
    
    # Initialize client
    client = NYCOpenDataClient.from_config()
    
    # Clean up address for search
    address_clean = address.upper().strip()
    
    # Remove common suffixes that interfere with search
    address_clean = address_clean.replace(', NEW YORK, NY', '').replace(', NEW YORK', '').replace(', NY', '')
    address_clean = address_clean.replace(' NEW YORK', '').replace(' NY', '')
    
    # Extract ZIP code if present
    import re
    zip_match = re.search(r'\b(\d{5})\b', address_clean)
    zip_code = zip_match.group(1) if zip_match else None
    if zip_code:
        address_clean = address_clean.replace(zip_code, '').strip()
    
    # Parse address components
    address_parts = address_clean.split(' ')
    house_number = address_parts[0] if address_parts else ""
    street_name = ' '.join(address_parts[1:]) if len(address_parts) > 1 else ""
    
    print(f"🔍 Parsed: {house_number} {street_name}")
    if zip_code:
        print(f"📮 ZIP: {zip_code}")
    
    # Step 1: Search HPD Violations (most reliable for address search)
    property_info = search_hpd_violations(client, house_number, street_name, zip_code)
    
    if not property_info:
        print("❌ Property not found in HPD violations")
        return None
    
    # Step 2: Get compliance data using confirmed columns
    compliance_data = get_compliance_data_real_columns(client, property_info)
    
    # Step 3: Structure results
    result = {
        'property_info': property_info,
        'compliance_data': compliance_data,
        'search_timestamp': datetime.now().isoformat()
    }
    
    return result

def search_hpd_violations(client, house_number: str, street_name: str, zip_code: str = None):
    """Search HPD violations using confirmed column names"""
    
    print("\n🔍 Searching HPD Violations...")
    print("   Columns: buildingid, housenumber, streetname, boro, block, lot, zip")
    
    try:
        # Strategy 1: Exact house number and partial street name match
        where_clause = f"housenumber = '{house_number}' AND streetname LIKE '%{street_name}%'"
        if zip_code:
            where_clause += f" AND zip = '{zip_code}'"
        
        print(f"   Query: {where_clause}")
        
        data = client.get_data(
            'hpd_violations',
            where=where_clause,
            select="buildingid, housenumber, streetname, boro, block, lot, zip",
            limit=5
        )
        
        if data is not None and not data.empty:
            # Return first match
            match = data.iloc[0].to_dict()
            print(f"✅ Found: {match.get('housenumber')} {match.get('streetname')}")
            print(f"   Building ID: {match.get('buildingid')}")
            print(f"   Borough: {match.get('boro')}")
            print(f"   Block/Lot: {match.get('block')}/{match.get('lot')}")
            return match
        
        # Strategy 2: Try partial street name only
        print("   Trying partial street name search...")
        street_parts = street_name.split(' ')
        if len(street_parts) > 1:
            main_street = street_parts[0]  # Use first word
            where_clause = f"housenumber = '{house_number}' AND streetname LIKE '%{main_street}%'"
            
            data = client.get_data(
                'hpd_violations',
                where=where_clause,
                select="buildingid, housenumber, streetname, boro, block, lot, zip",
                limit=5
            )
            
            if data is not None and not data.empty:
                match = data.iloc[0].to_dict()
                print(f"✅ Found (partial): {match.get('housenumber')} {match.get('streetname')}")
                return match
        
        print("   No matches found in HPD violations")
        return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def get_compliance_data_real_columns(client, property_info: dict):
    """Get compliance data using confirmed column names"""
    
    compliance_data = {
        'hpd_violations': [],
        'dob_violations': [],
        'elevator_inspections': [],
        'boiler_inspections': []
    }
    
    building_id = property_info.get('buildingid')
    boro = property_info.get('boro')
    block = property_info.get('block')
    lot = property_info.get('lot')
    
    # HPD Violations (using buildingid)
    try:
        print(f"\n🔍 Fetching HPD violations for Building ID: {building_id}")
        hpd_data = client.get_data(
            'hpd_violations',
            where=f"buildingid = '{building_id}'",
            select="violationid, violationstatus, currentstatus, approveddate, novdescription, rentimpairing",
            order="approveddate DESC",
            limit=100
        )
        
        if hpd_data is not None and not hpd_data.empty:
            compliance_data['hpd_violations'] = hpd_data.to_dict('records')
        
        print(f"   ✅ Found {len(compliance_data['hpd_violations'])} HPD violations")
        
    except Exception as e:
        print(f"   ❌ HPD violations error: {e}")
    
    # DOB Violations (using boro, block, lot)
    try:
        print(f"\n🔍 Fetching DOB violations for {boro} Block:{block} Lot:{lot}")
        
        # Map borough name to number for DOB dataset
        boro_map = {'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3', 'QUEENS': '4', 'STATEN ISLAND': '5'}
        boro_num = boro_map.get(boro, boro)
        
        dob_data = client.get_data(
            'dob_violations',
            where=f"boro = '{boro_num}' AND block = '{block}' AND lot = '{lot}'",
            select="isn_dob_bis_viol, violation_category, violation_type, issue_date, disposition_comments, description",
            order="issue_date DESC",
            limit=100
        )
        
        if dob_data is not None and not dob_data.empty:
            compliance_data['dob_violations'] = dob_data.to_dict('records')
        
        print(f"   ✅ Found {len(compliance_data['dob_violations'])} DOB violations")
        
    except Exception as e:
        print(f"   ❌ DOB violations error: {e}")
    
    # Elevator Inspections (using bin - confirmed column name)
    try:
        print(f"\n🔍 Fetching elevator data for BIN: {building_id}")
        elevator_data = client.get_data(
            'elevator_inspections',
            where=f"bin = '{building_id}'",
            select="device_number, device_type, device_status, status_date, house_number, street_name",
            limit=50
        )
        
        if elevator_data is not None and not elevator_data.empty:
            compliance_data['elevator_inspections'] = elevator_data.to_dict('records')
        
        print(f"   ✅ Found {len(compliance_data['elevator_inspections'])} elevator records")
        
    except Exception as e:
        print(f"   ❌ Elevator data error: {e}")
    
    # Boiler Inspections (using bin_number - confirmed column name)
    try:
        print(f"\n🔍 Fetching boiler data for BIN: {building_id}")
        boiler_data = client.get_data(
            'boiler_inspections',
            where=f"bin_number = '{building_id}'",
            select="tracking_number, boiler_id, inspection_date, defects_exist, report_status",
            order="inspection_date DESC",
            limit=50
        )
        
        if boiler_data is not None and not boiler_data.empty:
            compliance_data['boiler_inspections'] = boiler_data.to_dict('records')
        
        print(f"   ✅ Found {len(compliance_data['boiler_inspections'])} boiler records")
        
    except Exception as e:
        print(f"   ❌ Boiler data error: {e}")
    
    return compliance_data

def display_results(result: dict):
    """Display search results in a formatted way"""
    
    if not result:
        print("❌ No results to display")
        return
    
    property_info = result['property_info']
    compliance_data = result['compliance_data']
    
    print("\n" + "="*60)
    print("📊 PROPERTY COMPLIANCE REPORT (REAL DATA)")
    print("="*60)
    
    # Property Summary
    print(f"🏢 PROPERTY:")
    print(f"   Address: {property_info.get('housenumber')} {property_info.get('streetname')}")
    print(f"   Building ID: {property_info.get('buildingid')}")
    print(f"   Borough: {property_info.get('boro')}")
    print(f"   Block/Lot: {property_info.get('block')}/{property_info.get('lot')}")
    print(f"   ZIP Code: {property_info.get('zip')}")
    
    # Compliance Summary
    print(f"\n📈 COMPLIANCE SUMMARY:")
    hpd_total = len(compliance_data['hpd_violations'])
    hpd_active = len([v for v in compliance_data['hpd_violations'] 
                     if v.get('violationstatus') in ['Open', 'ACTIVE']])
    
    dob_total = len(compliance_data['dob_violations'])
    dob_active = len([v for v in compliance_data['dob_violations'] 
                     if not v.get('disposition_comments')])
    
    elevator_total = len(compliance_data['elevator_inspections'])
    elevator_active = len([e for e in compliance_data['elevator_inspections'] 
                          if e.get('device_status') == 'A'])
    
    boiler_total = len(compliance_data['boiler_inspections'])
    
    print(f"   HPD Violations: {hpd_total} total, {hpd_active} active")
    print(f"   DOB Violations: {dob_total} total, {dob_active} active")
    print(f"   Elevator Devices: {elevator_total} total, {elevator_active} active")
    print(f"   Boiler Inspections: {boiler_total} records")
    
    # Sample Data
    if hpd_total > 0:
        print(f"\n🔍 SAMPLE HPD VIOLATIONS:")
        for i, violation in enumerate(compliance_data['hpd_violations'][:3], 1):
            status = violation.get('violationstatus', 'N/A')
            date = violation.get('approveddate', 'N/A')
            desc = violation.get('novdescription', 'N/A')[:60] + '...' if violation.get('novdescription') else 'N/A'
            print(f"   {i}. Status: {status} | Date: {date}")
            print(f"      Description: {desc}")
    
    if dob_total > 0:
        print(f"\n🏗️ SAMPLE DOB VIOLATIONS:")
        for i, violation in enumerate(compliance_data['dob_violations'][:3], 1):
            vtype = violation.get('violation_type', 'N/A')
            date = violation.get('issue_date', 'N/A')
            category = violation.get('violation_category', 'N/A')
            print(f"   {i}. Type: {vtype} | Date: {date} | Category: {category}")
    
    if elevator_total > 0:
        print(f"\n🛗 ELEVATOR DEVICES:")
        for i, device in enumerate(compliance_data['elevator_inspections'][:5], 1):
            device_num = device.get('device_number', 'N/A')
            device_type = device.get('device_type', 'N/A')
            status = device.get('device_status', 'N/A')
            print(f"   {i}. Device: {device_num} | Type: {device_type} | Status: {status}")
    
    if boiler_total > 0:
        print(f"\n🔥 BOILER INSPECTIONS:")
        for i, inspection in enumerate(compliance_data['boiler_inspections'][:3], 1):
            boiler_id = inspection.get('boiler_id', 'N/A')
            date = inspection.get('inspection_date', 'N/A')
            defects = inspection.get('defects_exist', 'N/A')
            print(f"   {i}. Boiler: {boiler_id} | Date: {date} | Defects: {defects}")
    
    print(f"\n✅ Report generated at: {result['search_timestamp']}")

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python corrected_property_search.py 'ADDRESS'")
        print("Example: python corrected_property_search.py '1662 Park Avenue, New York, NY 10035'")
        sys.exit(1)
    
    address = sys.argv[1]
    
    # Search property with real column names
    result = search_property_with_real_columns(address)
    
    if result:
        # Display results
        display_results(result)
        
        # Save to file
        output_file = f"property_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Full report saved to: {output_file}")
        print(f"🎯 SUCCESS: Found real data for {address}")
        
    else:
        print(f"\n❌ FAILED: Could not find property data for {address}")
        sys.exit(1)

if __name__ == "__main__":
    main()
