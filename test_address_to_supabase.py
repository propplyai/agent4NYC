#!/usr/bin/env python3
"""
Test script for address_to_supabase.py
Demonstrates how to use the standalone address processor
"""

import asyncio
import sys
import os

# Add project directory to path
sys.path.append('/Users/art3a/agent4NYC')

from address_to_supabase import AddressToSupabaseProcessor

async def test_address_processing():
    """Test the address processing functionality"""
    
    # Test addresses
    test_addresses = [
        "555 Washington Ave, Brooklyn, NY 11238",
        "1662 Park Avenue, New York, NY 10035",
        "23-12 31 St, Astoria, NY 11106"
    ]
    
    processor = AddressToSupabaseProcessor()
    
    for address in test_addresses:
        print(f"\n🧪 TESTING ADDRESS: {address}")
        print("=" * 60)
        
        try:
            # Process the address
            record = await processor.process_address(address)
            
            if 'error' in record:
                print(f"❌ Error processing {address}: {record['error']}")
                continue
            
            # Display key results
            print(f"✅ Successfully processed: {address}")
            print(f"📋 BIN: {record.get('bin', 'N/A')}")
            print(f"🏢 Building Class: {record.get('building_class', 'N/A')}")
            print(f"📊 Overall Score: {record.get('overall_compliance_score', 0):.1f}/100")
            
            # Show compliance breakdown
            print(f"\n📈 Compliance Breakdown:")
            print(f"   HPD Score: {record.get('hpd_compliance_score', 0):.1f}/100")
            print(f"   DOB Score: {record.get('dob_compliance_score', 0):.1f}/100")
            print(f"   Elevator Score: {record.get('elevator_compliance_score', 0):.1f}/100")
            print(f"   Boiler Score: {record.get('boiler_compliance_score', 0):.1f}/100")
            
            # Show violation counts
            print(f"\n📋 Violation Summary:")
            print(f"   HPD Violations: {record.get('hpd_violations_total', 0)} total, {record.get('hpd_violations_active', 0)} active")
            print(f"   DOB Violations: {record.get('dob_violations_total', 0)} total, {record.get('dob_violations_active', 0)} active")
            print(f"   Elevator Devices: {record.get('elevator_devices_total', 0)} total, {record.get('elevator_devices_active', 0)} active")
            print(f"   Boiler Devices: {record.get('boiler_devices_total', 0)} total")
            
            # Note: In a real scenario, you would save to Supabase here
            print(f"💾 Ready for Supabase insertion")
            
        except Exception as e:
            print(f"❌ Error testing {address}: {e}")

def show_usage_examples():
    """Show usage examples for the standalone script"""
    
    print("\n📖 USAGE EXAMPLES")
    print("=" * 60)
    
    examples = """
    # Basic usage - process single address
    python address_to_supabase.py "140 West 28th Street, New York, NY"
    
    # Process different address formats
    python address_to_supabase.py "1662 Park Avenue, NY 10035"
    python address_to_supabase.py "123 Main St, Brooklyn, NY 11201"
    
    # The script will:
    1. Find the property BIN using NYC property data
    2. Query 6 different NYC Open Data datasets
    3. Calculate compliance scores for each category
    4. Structure data for Supabase table
    5. Insert/update the record in Supabase
    """
    
    print(examples)

def show_supabase_table_structure():
    """Show the Supabase table structure that will be created"""
    
    print("\n🗄️ SUPABASE TABLE STRUCTURE")
    print("=" * 60)
    
    table_structure = """
    Table: property_compliance
    
    PROPERTY INFO:
    ├── address (TEXT) - Full street address
    ├── bin (TEXT) - Building Identification Number
    ├── bbl (TEXT) - Borough-Block-Lot
    ├── borough (TEXT) - NYC Borough
    ├── building_class (TEXT) - Building classification
    ├── year_built (INTEGER) - Construction year
    ├── num_floors (INTEGER) - Number of floors
    └── units_total (INTEGER) - Total residential units
    
    COMPLIANCE COUNTS:
    ├── hpd_violations_total (INTEGER)
    ├── hpd_violations_active (INTEGER)
    ├── dob_violations_total (INTEGER)
    ├── dob_violations_active (INTEGER)
    ├── elevator_devices_total (INTEGER)
    ├── elevator_devices_active (INTEGER)
    ├── boiler_devices_total (INTEGER)
    ├── fire_safety_inspections_total (INTEGER)
    └── cooling_towers_total (INTEGER)
    
    COMPLIANCE SCORES:
    ├── hpd_compliance_score (FLOAT) - 0-100 score
    ├── dob_compliance_score (FLOAT) - 0-100 score
    ├── elevator_compliance_score (FLOAT) - 0-100 score
    ├── boiler_compliance_score (FLOAT) - 0-100 score
    └── overall_compliance_score (FLOAT) - Weighted average
    
    RAW DATA (JSONB):
    ├── hpd_violations_data - Full HPD violation records
    ├── dob_violations_data - Full DOB violation records
    ├── elevator_data - Elevator inspection records
    ├── boiler_data - Boiler inspection records
    ├── fire_safety_data - Fire safety inspection records
    └── cooling_tower_data - Cooling tower registration data
    
    METADATA:
    ├── processed_at (TIMESTAMP) - When data was processed
    ├── data_source (TEXT) - Always 'NYC_Open_Data'
    ├── created_at (TIMESTAMP) - Record creation time
    └── updated_at (TIMESTAMP) - Last update time
    """
    
    print(table_structure)

async def main():
    """Main test function"""
    
    print("🧪 ADDRESS TO SUPABASE PROCESSOR - TEST SUITE")
    print("=" * 70)
    
    # Show usage examples
    show_usage_examples()
    
    # Show table structure
    show_supabase_table_structure()
    
    # Test address processing (without actually saving to Supabase)
    await test_address_processing()
    
    print(f"\n✅ TEST COMPLETE")
    print("To actually process an address and save to Supabase, run:")
    print("python address_to_supabase.py 'YOUR_ADDRESS_HERE'")

if __name__ == "__main__":
    asyncio.run(main())
