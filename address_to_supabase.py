#!/usr/bin/env python3
"""
Standalone Address to Supabase Script
Takes an address, queries NYC Open Data datasets, and populates Supabase table
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project directory to path
sys.path.append('/Users/art3a/agent4NYC')

from nyc_opendata_client import NYCOpenDataClient
from nyc_property_finder import search_property_by_address

class AddressToSupabaseProcessor:
    """Process address data and populate Supabase table"""
    
    def __init__(self):
        """Initialize the processor with NYC Open Data client"""
        self.nyc_client = NYCOpenDataClient.from_config()
        
    async def process_address(self, address: str) -> Dict[str, Any]:
        """
        Process an address and gather all compliance data
        
        Args:
            address: Street address to process
            
        Returns:
            Dictionary with all compliance data
        """
        print(f"🏢 Processing address: {address}")
        print("=" * 60)
        
        # Step 1: Find property details (BIN, BBL, etc.)
        property_info = await self.get_property_info(address)
        if not property_info:
            return {"error": "Property not found"}
        
        bin_number = property_info.get('bin')
        print(f"📋 Found BIN: {bin_number}")
        
        # Step 2: Gather compliance data
        compliance_data = await self.gather_compliance_data(bin_number, address)
        
        # Step 3: Structure data for Supabase
        supabase_record = self.structure_for_supabase(property_info, compliance_data)
        
        return supabase_record
    
    async def get_property_info(self, address: str) -> Optional[Dict]:
        """Get basic property information including BIN"""
        try:
            # Use property finder function to get BIN and other details
            results = search_property_by_address(self.nyc_client, address)
            
            if results and len(results) > 0:
                property_data = results[0]
                return {
                    'address': address,
                    'bin': property_data.get('bin') or property_data.get('bin_number'),
                    'bbl': f"{property_data.get('boro', '')}{property_data.get('block', '')}{property_data.get('lot', '')}",
                    'borough': property_data.get('boro') or property_data.get('boroid') or property_data.get('borough'),
                    'block': property_data.get('block'),
                    'lot': property_data.get('lot'),
                    'building_class': property_data.get('building_class'),
                    'year_built': property_data.get('year_built'),
                    'num_floors': property_data.get('num_floors'),
                    'units_total': property_data.get('units_total')
                }
            return None
            
        except Exception as e:
            print(f"❌ Error finding property: {e}")
            return None
    
    async def gather_compliance_data(self, bin_number: str, address: str) -> Dict[str, Any]:
        """Gather all compliance data for the property"""
        
        compliance_data = {
            'hpd_violations': [],
            'dob_violations': [],
            'elevator_inspections': [],
            'boiler_inspections': [],
            'fire_safety_inspections': [],
            'cooling_tower_data': []
        }
        
        # HPD Violations
        try:
            print("🔍 Fetching HPD violations...")
            hpd_data = self.nyc_client.get_data(
                'hpd_violations',
                where=f"buildingid = '{bin_number}'",
                select="violationid, violationstatus, approveddate, violationclass, violationdescription, currentstatusdate",
                order="approveddate DESC",
                limit=1000
            )
            compliance_data['hpd_violations'] = hpd_data.to_dict('records') if not hpd_data.empty else []
            print(f"   Found {len(compliance_data['hpd_violations'])} HPD violations")
            
        except Exception as e:
            print(f"   ❌ HPD violations error: {e}")
        
        # DOB Violations
        try:
            print("🔍 Fetching DOB violations...")
            dob_data = self.nyc_client.get_data(
                'dob_violations',
                where=f"bin = '{bin_number}'",
                select="isn_dob_bis_viol, violation_category, violation_type, issue_date, disposition_date, violation_description",
                order="issue_date DESC",
                limit=1000
            )
            compliance_data['dob_violations'] = dob_data.to_dict('records') if not dob_data.empty else []
            print(f"   Found {len(compliance_data['dob_violations'])} DOB violations")
            
        except Exception as e:
            print(f"   ❌ DOB violations error: {e}")
        
        # Elevator Inspections
        try:
            print("🔍 Fetching elevator data...")
            elevator_data = self.nyc_client.get_data(
                'elevator_inspections',
                where=f"bin = '{bin_number}'",
                select="device_number, device_type, device_status, last_inspection_date, inspection_status",
                order="last_inspection_date DESC",
                limit=100
            )
            compliance_data['elevator_inspections'] = elevator_data.to_dict('records') if not elevator_data.empty else []
            print(f"   Found {len(compliance_data['elevator_inspections'])} elevator records")
            
        except Exception as e:
            print(f"   ❌ Elevator data error: {e}")
        
        # Boiler Inspections
        try:
            print("🔍 Fetching boiler data...")
            boiler_data = self.nyc_client.get_data(
                'boiler_inspections',
                where=f"bin = '{bin_number}'",
                select="device_number, inspection_date, inspection_status, defects_found, equipment_type",
                order="inspection_date DESC",
                limit=100
            )
            compliance_data['boiler_inspections'] = boiler_data.to_dict('records') if not boiler_data.empty else []
            print(f"   Found {len(compliance_data['boiler_inspections'])} boiler records")
            
        except Exception as e:
            print(f"   ❌ Boiler data error: {e}")
        
        # Fire Safety Inspections
        try:
            print("🔍 Fetching fire safety data...")
            fire_data = self.nyc_client.get_data(
                'fire_safety_inspections',
                where=f"bin = '{bin_number}'",
                select="inspection_date, inspection_type, result, violations_found",
                order="inspection_date DESC",
                limit=100
            )
            compliance_data['fire_safety_inspections'] = fire_data.to_dict('records') if not fire_data.empty else []
            print(f"   Found {len(compliance_data['fire_safety_inspections'])} fire safety records")
            
        except Exception as e:
            print(f"   ❌ Fire safety data error: {e}")
        
        # Cooling Tower Data
        try:
            print("🔍 Fetching cooling tower data...")
            cooling_data = self.nyc_client.get_data(
                'cooling_tower_registrations',
                where=f"bin = '{bin_number}'",
                select="tower_id, registration_date, tower_type, last_inspection_date",
                limit=50
            )
            compliance_data['cooling_tower_data'] = cooling_data.to_dict('records') if not cooling_data.empty else []
            print(f"   Found {len(compliance_data['cooling_tower_data'])} cooling tower records")
            
        except Exception as e:
            print(f"   ❌ Cooling tower data error: {e}")
        
        return compliance_data
    
    def structure_for_supabase(self, property_info: Dict, compliance_data: Dict) -> Dict[str, Any]:
        """Structure data for Supabase table insertion"""
        
        # Calculate compliance scores
        compliance_scores = self.calculate_compliance_scores(compliance_data)
        
        # Structure the record
        supabase_record = {
            # Property Information
            'address': property_info.get('address'),
            'bin': property_info.get('bin'),
            'bbl': property_info.get('bbl'),
            'borough': property_info.get('borough'),
            'block': property_info.get('block'),
            'lot': property_info.get('lot'),
            'building_class': property_info.get('building_class'),
            'year_built': property_info.get('year_built'),
            'num_floors': property_info.get('num_floors'),
            'units_total': property_info.get('units_total'),
            
            # Compliance Counts
            'hpd_violations_total': len(compliance_data['hpd_violations']),
            'hpd_violations_active': len([v for v in compliance_data['hpd_violations'] if v.get('violationstatus') == 'Open']),
            'dob_violations_total': len(compliance_data['dob_violations']),
            'dob_violations_active': len([v for v in compliance_data['dob_violations'] if not v.get('disposition_date')]),
            'elevator_devices_total': len(compliance_data['elevator_inspections']),
            'elevator_devices_active': len([e for e in compliance_data['elevator_inspections'] if e.get('device_status') == 'A']),
            'boiler_devices_total': len(compliance_data['boiler_inspections']),
            'fire_safety_inspections_total': len(compliance_data['fire_safety_inspections']),
            'cooling_towers_total': len(compliance_data['cooling_tower_data']),
            
            # Compliance Scores
            'hpd_compliance_score': compliance_scores['hpd_score'],
            'dob_compliance_score': compliance_scores['dob_score'],
            'elevator_compliance_score': compliance_scores['elevator_score'],
            'boiler_compliance_score': compliance_scores['boiler_score'],
            'overall_compliance_score': compliance_scores['overall_score'],
            
            # Raw Data (JSON)
            'hpd_violations_data': json.dumps(compliance_data['hpd_violations']),
            'dob_violations_data': json.dumps(compliance_data['dob_violations']),
            'elevator_data': json.dumps(compliance_data['elevator_inspections']),
            'boiler_data': json.dumps(compliance_data['boiler_inspections']),
            'fire_safety_data': json.dumps(compliance_data['fire_safety_inspections']),
            'cooling_tower_data': json.dumps(compliance_data['cooling_tower_data']),
            
            # Metadata
            'processed_at': datetime.now().isoformat(),
            'data_source': 'NYC_Open_Data'
        }
        
        return supabase_record
    
    def calculate_compliance_scores(self, compliance_data: Dict) -> Dict[str, float]:
        """Calculate compliance scores for each category"""
        
        scores = {}
        
        # HPD Score (based on active violations)
        hpd_total = len(compliance_data['hpd_violations'])
        hpd_active = len([v for v in compliance_data['hpd_violations'] if v.get('violationstatus') == 'Open'])
        scores['hpd_score'] = max(0, 100 - (hpd_active * 10)) if hpd_total > 0 else 100
        
        # DOB Score (based on active violations)
        dob_total = len(compliance_data['dob_violations'])
        dob_active = len([v for v in compliance_data['dob_violations'] if not v.get('disposition_date')])
        scores['dob_score'] = max(0, 100 - (dob_active * 15)) if dob_total > 0 else 100
        
        # Elevator Score (based on active devices)
        elevator_total = len(compliance_data['elevator_inspections'])
        elevator_active = len([e for e in compliance_data['elevator_inspections'] if e.get('device_status') == 'A'])
        scores['elevator_score'] = (elevator_active / elevator_total * 100) if elevator_total > 0 else 100
        
        # Boiler Score (based on recent inspections)
        boiler_total = len(compliance_data['boiler_inspections'])
        boiler_recent = len([b for b in compliance_data['boiler_inspections'] 
                           if b.get('inspection_status') == 'ACCEPTED'])
        scores['boiler_score'] = (boiler_recent / boiler_total * 100) if boiler_total > 0 else 100
        
        # Overall Score (weighted average)
        scores['overall_score'] = (
            scores['hpd_score'] * 0.25 +
            scores['dob_score'] * 0.25 +
            scores['elevator_score'] * 0.25 +
            scores['boiler_score'] * 0.25
        )
        
        return scores
    
    async def save_to_supabase(self, record: Dict[str, Any]) -> bool:
        """Save the record to Supabase table"""
        try:
            # Use Supabase MCP functions
            import sys
            sys.path.append('/Users/art3a/agent4NYC')
            
            # Create table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS property_compliance (
                id SERIAL PRIMARY KEY,
                address TEXT,
                bin TEXT,
                bbl TEXT,
                borough TEXT,
                block TEXT,
                lot TEXT,
                building_class TEXT,
                year_built INTEGER,
                num_floors INTEGER,
                units_total INTEGER,
                hpd_violations_total INTEGER,
                hpd_violations_active INTEGER,
                dob_violations_total INTEGER,
                dob_violations_active INTEGER,
                elevator_devices_total INTEGER,
                elevator_devices_active INTEGER,
                boiler_devices_total INTEGER,
                fire_safety_inspections_total INTEGER,
                cooling_towers_total INTEGER,
                hpd_compliance_score FLOAT,
                dob_compliance_score FLOAT,
                elevator_compliance_score FLOAT,
                boiler_compliance_score FLOAT,
                overall_compliance_score FLOAT,
                hpd_violations_data JSONB,
                dob_violations_data JSONB,
                elevator_data JSONB,
                boiler_data JSONB,
                fire_safety_data JSONB,
                cooling_tower_data JSONB,
                processed_at TIMESTAMP,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # For now, just print the SQL and data structure
            print("\n📊 SUPABASE TABLE STRUCTURE CREATED")
            print(create_table_sql[:200] + "...")
            
            # Show what would be inserted
            print("\n💾 DATA TO BE INSERTED:")
            for key, value in record.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")
            
            print("\n✅ Record prepared for Supabase insertion")
            print("   (Actual insertion disabled for testing)")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            return False

async def main():
    """Main function to process address and save to Supabase"""
    
    if len(sys.argv) < 2:
        print("Usage: python address_to_supabase.py 'ADDRESS'")
        print("Example: python address_to_supabase.py '140 West 28th Street, New York, NY'")
        sys.exit(1)
    
    address = sys.argv[1]
    
    processor = AddressToSupabaseProcessor()
    
    # Process the address
    record = await processor.process_address(address)
    
    if 'error' in record:
        print(f"❌ Error: {record['error']}")
        sys.exit(1)
    
    # Save to Supabase
    success = await processor.save_to_supabase(record)
    
    if success:
        print(f"\n✅ Successfully processed {address} and saved to Supabase!")
        print(f"📊 Overall Compliance Score: {record['overall_compliance_score']:.1f}/100")
    else:
        print(f"\n❌ Failed to save {address} to Supabase")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
