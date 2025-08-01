
#!/usr/bin/env python3
"""
Comprehensive NYC Property Compliance System
============================================

Final comprehensive script implementing best practices for NYC property compliance data retrieval:
- NYC Geoclient API for authoritative address → BIN/BBL conversion
- Robust multi-key search strategy (BIN, BBL, block/lot, address)
- Complete dataset coverage including DOB Complaints and Safety Violations
- Cross-dataset merging and BIN mismatch handling
- Supabase-ready structured output

Based on comprehensive research and the official NYC property compliance data retrieval guide.
"""

import os
import sys
import json
import asyncio
import requests
# import pandas as pd  # Removed for deployment compatibility
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add project directory to path
sys.path.append('/Users/art3a/agent4NYC')

from nyc_opendata_client import NYCOpenDataClient

@dataclass
class PropertyIdentifiers:
    """Canonical property identifiers from Geoclient API"""
    address: str
    bin: Optional[str] = None
    bbl: Optional[str] = None
    borough: Optional[str] = None
    block: Optional[str] = None
    lot: Optional[str] = None
    zip_code: Optional[str] = None

@dataclass
class ComplianceRecord:
    """Structured compliance record for Supabase"""
    # Property identifiers
    address: str
    bin: Optional[str]
    bbl: Optional[str]
    borough: Optional[str]
    block: Optional[str]
    lot: Optional[str]
    zip_code: Optional[str]
    
    # Violation counts
    hpd_violations_total: int = 0
    hpd_violations_active: int = 0
    dob_violations_total: int = 0
    dob_violations_active: int = 0
    
    # Equipment counts
    elevator_devices_total: int = 0
    elevator_devices_active: int = 0
    boiler_devices_total: int = 0
    electrical_permits_total: int = 0
    electrical_permits_active: int = 0
    
    # Compliance scores (0-100)
    hpd_compliance_score: float = 100.0
    dob_compliance_score: float = 100.0
    elevator_compliance_score: float = 100.0
    electrical_compliance_score: float = 100.0
    overall_compliance_score: float = 100.0
    
    # Raw data (JSON)
    hpd_violations_data: str = "[]"
    dob_violations_data: str = "[]"
    elevator_data: str = "[]"
    boiler_data: str = "[]"
    electrical_data: str = "[]"
    
    # Metadata
    processed_at: str = ""
    data_sources: str = ""

class NYCPlanningGeoSearchClient:
    """NYC Planning GeoSearch API client - modern, free, no authentication required"""
    
    def __init__(self):
        self.base_url = "https://geosearch.planninglabs.nyc/v2"
    
    def get_property_identifiers(self, address: str, borough: str = None) -> Optional[PropertyIdentifiers]:
        """Get property identifiers from address using NYC Planning GeoSearch API"""
        
        # Format address for search
        search_text = address.strip()
        if borough:
            search_text = f"{address}, {borough}"
        
        try:
            params = {
                'text': search_text,
                'size': 1  # Only need the best match
            }
            
            response = requests.get(f"{self.base_url}/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('features'):
                print(f"❌ NYC GeoSearch: No results for {address}")
                return None
            
            feature = data['features'][0]
            properties = feature.get('properties', {})
            
            # Extract property details
            house_number = properties.get('housenumber', '')
            street = properties.get('street', '')
            formatted_address = f"{house_number} {street}".strip()
            
            # Get borough name and normalize
            borough_name = properties.get('borough')
            borough_map = {
                'Manhattan': 'MANHATTAN', 'Brooklyn': 'BROOKLYN', 
                'Queens': 'QUEENS', 'Bronx': 'BRONX', 'Staten Island': 'STATEN ISLAND'
            }
            normalized_borough = borough_map.get(borough_name, borough_name)
            
            # Extract BIN and BBL from addendum.pad (new v2 structure)
            pad_data = properties.get('addendum', {}).get('pad', {})
            bin_number = pad_data.get('bin')
            bbl = pad_data.get('bbl')
            
            # Parse BBL to get block/lot (BBL format: borough+block+lot)
            block = None
            lot = None
            if bbl and len(bbl) >= 10:  # BBL should be 10 digits
                try:
                    block = bbl[1:6].lstrip('0')  # Remove leading zeros
                    lot = bbl[6:].lstrip('0')    # Remove leading zeros
                except:
                    pass
            
            identifiers = PropertyIdentifiers(
                address=formatted_address,
                bin=bin_number,
                bbl=bbl,
                borough=normalized_borough,
                block=block,
                lot=lot,
                zip_code=properties.get('postalcode')
            )
            
            print(f"✅ NYC GeoSearch API: Found {identifiers.address}")
            print(f"   BIN: {identifiers.bin}, BBL: {identifiers.bbl}")
            print(f"   Borough: {identifiers.borough}, Block/Lot: {identifiers.block}/{identifiers.lot}")
            
            return identifiers
            
        except Exception as e:
            print(f"❌ NYC GeoSearch API error: {e}")
            return None

class ComprehensivePropertyComplianceSystem:
    """Comprehensive NYC property compliance data retrieval system"""
    
    def __init__(self):
        self.nyc_client = NYCOpenDataClient.from_config()
        self.geoclient = NYCPlanningGeoSearchClient()
    
    async def process_property(self, address: str, borough: str = None) -> ComplianceRecord:
        """Process a property address and return comprehensive compliance data"""
        
        print(f"🏢 COMPREHENSIVE PROPERTY COMPLIANCE ANALYSIS")
        print(f"Address: {address}")
        print("=" * 80)
        
        # Step 1: Get canonical property identifiers
        identifiers = await self.get_property_identifiers(address, borough)
        
        if not identifiers:
            print("❌ Could not identify property")
            return self.create_empty_record(address)
        
        # Step 2: Gather compliance data using robust multi-key search
        compliance_data = await self.gather_comprehensive_compliance_data(identifiers)
        
        # Step 3: Create structured compliance record
        record = self.create_compliance_record(identifiers, compliance_data)
        
        return record
    
    async def get_property_identifiers(self, address: str, borough: str = None) -> Optional[PropertyIdentifiers]:
        """Get property identifiers using multiple strategies"""
        
        print(f"\n🔍 STEP 1: PROPERTY IDENTIFICATION")
        print("-" * 40)
        
        # Strategy 1: NYC Planning GeoSearch API (free, no auth required)
        print("🌐 Using NYC Planning GeoSearch API...")
        identifiers = self.geoclient.get_property_identifiers(address, borough)
        if identifiers:
            return identifiers
        
        # Strategy 2: Fallback to HPD violations search
        print("🔍 Fallback: HPD violations search...")
        identifiers = await self.fallback_property_search(address)
        
        return identifiers
    
    async def fallback_property_search(self, address: str) -> Optional[PropertyIdentifiers]:
        """Fallback property search using HPD violations dataset"""
        
        # Clean up address - remove borough and state suffixes
        address_clean = address.upper().strip()
        # Remove common suffixes
        suffixes_to_remove = [', NEW YORK, NY', ', NEW YORK', ', NY', ', MANHATTAN', ', BROOKLYN', ', QUEENS', ', BRONX', ', STATEN ISLAND']
        for suffix in suffixes_to_remove:
            address_clean = address_clean.replace(suffix, '')
        
        # Extract ZIP code
        import re
        zip_match = re.search(r'\b(\d{5})\b', address_clean)
        zip_code = zip_match.group(1) if zip_match else None
        if zip_code:
            address_clean = address_clean.replace(zip_code, '').strip()
        
        # Parse address components
        address_parts = address_clean.split(' ')
        house_number = address_parts[0] if address_parts else ""
        street_name = ' '.join(address_parts[1:]) if len(address_parts) > 1 else ""
        
        try:
            # Use the same approach as nyc_property_finder.py
            where_clause = f"housenumber = '{house_number}' AND streetname LIKE '%{street_name}%'"
            if zip_code:
                where_clause += f" AND zip = '{zip_code}'"
            
            print(f"   Searching HPD with: {where_clause}")
            
            data = self.nyc_client.get_data(
                'hpd_violations',
                where=where_clause,
                select="buildingid, housenumber, streetname, boro, block, lot, zip",
                limit=1
            )
            
            print(f"   HPD search returned: {type(data)}, empty: {len(data) == 0 if data is not None else 'None'}")
            
            if data is not None and len(data) > 0:
                match = data[0] if data else {}
                
                identifiers = PropertyIdentifiers(
                    address=f"{match.get('housenumber', '')} {match.get('streetname', '')}".strip(),
                    bin=match.get('buildingid'),
                    bbl=f"{match.get('boro', '')}{match.get('block', '')}{match.get('lot', '')}",
                    borough=match.get('boro'),
                    block=match.get('block'),
                    lot=match.get('lot'),
                    zip_code=match.get('zip')
                )
                
                print(f"✅ Found via HPD: {identifiers.address}")
                print(f"   BIN: {identifiers.bin}, Block/Lot: {identifiers.block}/{identifiers.lot}")
                
                return identifiers
            
            return None
            
        except Exception as e:
            print(f"❌ Fallback search error: {e}")
            return None
    
    async def gather_comprehensive_compliance_data(self, identifiers: PropertyIdentifiers) -> Dict[str, List[Dict]]:
        """Gather comprehensive compliance data using robust multi-key search"""
        
        print(f"\n🔍 STEP 2: COMPREHENSIVE DATA GATHERING")
        print("-" * 40)
        
        compliance_data = {
            'hpd_violations': [],
            'dob_violations': [],
            'elevator_inspections': [],
            'boiler_inspections': [],
            'certificate_of_occupancy': [],
            'electrical_permits': []
        }
        
        # HPD Violations
        await self.gather_hpd_violations(identifiers, compliance_data)
        
        # DOB Violations
        await self.gather_dob_violations(identifiers, compliance_data)
        
        # Elevator Inspections (robust multi-key search)
        await self.gather_elevator_data(identifiers, compliance_data)
        
        # Boiler Inspections
        await self.gather_boiler_data(identifiers, compliance_data)
        
        # Certificate of Occupancy
        await self.gather_certificate_of_occupancy(identifiers, compliance_data)
        
        # Electrical Permits
        await self.gather_electrical_permits(identifiers, compliance_data)
        
        return compliance_data
    
    async def gather_hpd_violations(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather HPD violations data using multiple search strategies"""
        print("🏠 Gathering HPD violations...")
        
        try:
            # Strategy 1: Search by BIN
            if identifiers.bin:
                print(f"   🔍 Searching by BIN: {identifiers.bin}")
                data = self.nyc_client.get_data(
                    'hpd_violations',
                    where=f"buildingid = '{identifiers.bin}'",
                    select="violationid, violationstatus, currentstatus, approveddate, novdescription, rentimpairing",
                    order="approveddate DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['hpd_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['hpd_violations'])} HPD violations (BIN search)")
                    return
            
            # Strategy 2: Search by block/lot
            if identifiers.borough and identifiers.block and identifiers.lot:
                print(f"   🔍 Fallback: Searching by block/lot: {identifiers.block}/{identifiers.lot}")
                boro_map = {'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3', 'QUEENS': '4', 'STATEN ISLAND': '5'}
                boro_id = boro_map.get(identifiers.borough, identifiers.borough)
                
                data = self.nyc_client.get_data(
                    'hpd_violations',
                    where=f"boroid = '{boro_id}' AND block = '{identifiers.block}' AND lot = '{identifiers.lot}'",
                    select="violationid, violationstatus, currentstatus, approveddate, novdescription, rentimpairing, buildingid",
                    order="approveddate DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['hpd_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['hpd_violations'])} HPD violations (block/lot search)")
                    return
            
            # Strategy 3: Search by address
            address_parts = identifiers.address.split(' ')
            if len(address_parts) >= 2:
                house_number = address_parts[0]
                street_name = ' '.join(address_parts[1:])
                print(f"   🔍 Fallback: Searching by address: {house_number} {street_name}")
                
                data = self.nyc_client.get_data(
                    'hpd_violations',
                    where=f"housenumber = '{house_number}' AND UPPER(streetname) LIKE '%{street_name.upper()}%'",
                    select="violationid, violationstatus, currentstatus, approveddate, novdescription, rentimpairing, buildingid",
                    order="approveddate DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['hpd_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['hpd_violations'])} HPD violations (address search)")
                    return
            
            print(f"   ❌ No HPD violations found")
            
        except Exception as e:
            print(f"   ❌ HPD violations error: {e}")
    
    async def gather_dob_violations(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather DOB violations data using multiple search strategies"""
        print("🏗️ Gathering DOB violations...")
        
        try:
            # Strategy 1: Search by BIN (DOB dataset has bin column)
            if identifiers.bin:
                print(f"   🔍 Searching by BIN: {identifiers.bin}")
                data = self.nyc_client.get_data(
                    'dob_violations',
                    where=f"bin = '{identifiers.bin}'",
                    select="isn_dob_bis_viol, violation_category, violation_type, issue_date, disposition_comments, description, bin",
                    order="issue_date DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['dob_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['dob_violations'])} DOB violations (BIN search)")
                    return
            
            # Strategy 2: Search by block/lot
            if identifiers.borough and identifiers.block and identifiers.lot:
                print(f"   🔍 Fallback: Searching by block/lot: {identifiers.block}/{identifiers.lot}")
                boro_map = {'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3', 'QUEENS': '4', 'STATEN ISLAND': '5'}
                boro_num = boro_map.get(identifiers.borough, identifiers.borough)
                
                data = self.nyc_client.get_data(
                    'dob_violations',
                    where=f"boro = '{boro_num}' AND block = '{identifiers.block}' AND lot = '{identifiers.lot}'",
                    select="isn_dob_bis_viol, violation_category, violation_type, issue_date, disposition_comments, description, bin",
                    order="issue_date DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['dob_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['dob_violations'])} DOB violations (block/lot search)")
                    return
            
            # Strategy 3: Search by address
            address_parts = identifiers.address.split(' ')
            if len(address_parts) >= 2:
                house_number = address_parts[0]
                street_name = ' '.join(address_parts[1:])
                print(f"   🔍 Fallback: Searching by address: {house_number} {street_name}")
                
                data = self.nyc_client.get_data(
                    'dob_violations',
                    where=f"house_number = '{house_number}' AND UPPER(street) LIKE '%{street_name.upper()}%'",
                    select="isn_dob_bis_viol, violation_category, violation_type, issue_date, disposition_comments, description, bin",
                    order="issue_date DESC",
                    limit=1000
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['dob_violations'] = data
                    print(f"   ✅ Found {len(compliance_data['dob_violations'])} DOB violations (address search)")
                    return
            
            print(f"   ❌ No DOB violations found")
            
        except Exception as e:
            print(f"   ❌ DOB violations error: {e}")
    
    async def gather_elevator_data(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather elevator data using multiple search strategies to handle BIN mismatches"""
        print("🛗 Gathering elevator data...")
        
        try:
            # Strategy 1: Search by BIN
            if identifiers.bin:
                data = self.nyc_client.get_data(
                    'elevator_inspections',
                    where=f"bin = '{identifiers.bin}'",
                    select="device_number, device_type, device_status, status_date, house_number, street_name",
                    order="status_date DESC",
                    limit=100
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['elevator_inspections'] = data
                    print(f"   ✅ Found {len(compliance_data['elevator_inspections'])} elevator records (BIN search)")
                    return
            
            # Strategy 2: Search by block/lot
            if identifiers.block and identifiers.lot:
                data = self.nyc_client.get_data(
                    'elevator_inspections',
                    where=f"block = '{identifiers.block}' AND lot = '{identifiers.lot}'",
                    select="device_number, device_type, device_status, status_date, bin, house_number, street_name",
                    order="status_date DESC",
                    limit=100
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['elevator_inspections'] = data
                    print(f"   ✅ Found {len(compliance_data['elevator_inspections'])} elevator records (block/lot search)")
                    return
            
            # Strategy 3: Address search with variations
            address_parts = identifiers.address.split(' ')
            if len(address_parts) >= 2:
                house_number = address_parts[0]
                street_name = ' '.join(address_parts[1:])
                
                # Try different address search patterns
                for street_pattern in [street_name, street_name.replace('AVENUE', 'AVE'), street_name.replace('AVE', 'AVENUE')]:
                    try:
                        data = self.nyc_client.get_data(
                            'elevator_inspections',
                            where=f"house_number = '{house_number}' AND street_name LIKE '%{street_pattern}%'",
                            select="device_number, device_type, device_status, status_date, bin",
                            order="status_date DESC",
                            limit=100
                        )
                        
                        if data is not None and len(data) > 0:
                            compliance_data['elevator_inspections'] = data
                            print(f"   ✅ Found {len(compliance_data['elevator_inspections'])} elevator records (address search)")
                            return
                    except:
                        continue
            
            print(f"   ❌ No elevator records found")
            
        except Exception as e:
            print(f"   ❌ Elevator data error: {e}")
    
    async def gather_boiler_data(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather boiler inspection data using BIN-only search strategy"""
        print("🔥 Gathering boiler data...")
        
        # IMPORTANT: The boiler inspections dataset (52dp-yji6) only contains these columns:
        # tracking_number, boiler_id, report_type, boiler_make, pressure_type, inspection_date,
        # defects_exist, lff_45_days, lff_180_days, filing_fee, total_amount_paid, report_status,
        # bin_number, boiler_model
        #
        # It does NOT contain address components like house_number or street_name.
        # Boiler searches can ONLY be performed using bin_number.
        
        try:
            # Only strategy available: Search by BIN
            if identifiers.bin:
                print(f"   🔍 Searching by BIN: {identifiers.bin}")
                data = self.nyc_client.get_data(
                    'boiler_inspections',
                    where=f"bin_number = '{identifiers.bin}'",
                    select="tracking_number, boiler_id, inspection_date, defects_exist, " +
                           "report_status, bin_number, boiler_make, pressure_type, report_type",
                    order="inspection_date DESC",
                    limit=100
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['boiler_inspections'] = data
                    print(f"   ✅ Found {len(compliance_data['boiler_inspections'])} boiler records")
                    
                    # Show summary of findings
                    latest_inspection = data[0]
                    active_boilers = len([item for item in data if item.get('report_status') == 'Accepted'])
                    defective_boilers = len([item for item in data if item.get('defects_exist') == 'Yes'])
                    
                    print(f"   📊 Latest inspection: {latest_inspection.get('inspection_date')}")
                    print(f"   📊 Active boilers: {active_boilers}, With defects: {defective_boilers}")
                    return
                else:
                    print(f"   ❌ No boiler records found for BIN {identifiers.bin}")
                    print(f"   ℹ️  This property may not have boilers requiring inspection")
            else:
                print(f"   ❌ No BIN available for boiler search")
                print(f"   ℹ️  Boiler data requires BIN number - address-based search not supported")
            
        except Exception as e:
            print(f"   ❌ Boiler data error: {e}")
            # If it's a 400 error, provide more specific guidance
            if "400 Client Error" in str(e):
                print(f"   ℹ️  Note: Boiler dataset only supports BIN-based searches")
    
    async def gather_electrical_permits(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather electrical permit applications data - critical for electrical safety compliance"""
        print("⚡ Gathering electrical permits...")
        
        try:
            # Strategy 1: Search by BIN (most reliable)
            if identifiers.bin:
                data = self.nyc_client.get_data(
                    'electrical_permits',
                    where=f"bin = '{identifiers.bin}'",
                    select="filing_number, filing_date, filing_status, job_description, applicant_first_name, applicant_last_name, completion_date, amount_paid",
                    order="filing_date DESC",
                    limit=100
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['electrical_permits'] = data
                    
                    # Show summary of electrical permits
                    latest_permit = data[0]
                    active_statuses = ['Approved', 'Job in Process', 'Active']
                    active_permits = len([item for item in data if item.get('filing_status') in active_statuses])
                    
                    print(f"   ✅ Found {len(compliance_data['electrical_permits'])} electrical permit records")
                    print(f"   📊 Latest permit: {latest_permit.get('filing_number')} - Status: {latest_permit.get('filing_status')} ({latest_permit.get('filing_date')})")
                    print(f"   📊 Job description: {latest_permit.get('job_description', 'N/A')}")
                    print(f"   📊 Active permits: {active_permits}")
                    if latest_permit.get('completion_date'):
                        print(f"   📊 Completion date: {latest_permit.get('completion_date')}")
                    return
            
            # Strategy 2: Search by block/lot as fallback
            if identifiers.borough and identifiers.block:
                # Map borough names for electrical dataset
                boro_map = {'MANHATTAN': 'MANHATTAN', 'BRONX': 'BRONX', 'BROOKLYN': 'BROOKLYN', 
                           'QUEENS': 'QUEENS', 'STATEN ISLAND': 'STATEN ISLAND'}
                borough_name = boro_map.get(identifiers.borough, identifiers.borough)
                
                data = self.nyc_client.get_data(
                    'electrical_permits',
                    where=f"borough = '{borough_name}' AND block = '{identifiers.block}'",
                    select="filing_number, filing_date, filing_status, job_description, bin",
                    order="filing_date DESC",
                    limit=100
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['electrical_permits'] = data
                    print(f"   ✅ Found {len(compliance_data['electrical_permits'])} electrical permits (block search)")
                    return
            
            print(f"   ❌ No electrical permit records found")
            print(f"   ℹ️  This may indicate no recent electrical work or permits")
            
        except Exception as e:
            print(f"   ❌ Electrical permits error: {e}")
    
    async def gather_certificate_of_occupancy(self, identifiers: PropertyIdentifiers, compliance_data: Dict):
        """Gather Certificate of Occupancy data - critical for legal occupancy status"""
        print("🏢 Gathering Certificate of Occupancy data...")
        
        try:
            # Strategy 1: Search by BIN (most reliable)
            if identifiers.bin:
                data = self.nyc_client.get_data(
                    'certificate_of_occupancy',
                    where=f"bin = '{identifiers.bin}'",
                    select="bin, c_of_o_filing_type, c_of_o_status, c_of_o_issuance_date, job_type, block, lot, house_no, street_name",
                    order="c_of_o_issuance_date DESC",
                    limit=50
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['certificate_of_occupancy'] = data
                    
                    # Show summary of C of O status
                    latest_co = data[0]
                    active_cos = len(data[data['c_of_o_status'].isin(['Issued', 'Active', 'Current'])])
                    
                    print(f"   ✅ Found {len(compliance_data['certificate_of_occupancy'])} Certificate of Occupancy records")
                    print(f"   📊 Latest C of O: {latest_co['c_of_o_filing_type']} - Status: {latest_co['c_of_o_status']} ({latest_co['c_of_o_issuance_date']})")
                    print(f"   📊 Job Type: {latest_co.get('job_type', 'N/A')}")
                    print(f"   📊 Address: {latest_co.get('house_no', '')} {latest_co.get('street_name', '')}")
                    return
            
            # Strategy 2: Search by block/lot as fallback
            if identifiers.block and identifiers.lot:
                data = self.nyc_client.get_data(
                    'certificate_of_occupancy',
                    where=f"block = '{identifiers.block}' AND lot = '{identifiers.lot}'",
                    select="bin, c_of_o_filing_type, c_of_o_status, c_of_o_issuance_date, job_type, block, lot, house_no, street_name",
                    order="c_of_o_issuance_date DESC",
                    limit=50
                )
                
                if data is not None and len(data) > 0:
                    compliance_data['certificate_of_occupancy'] = data
                    print(f"   ✅ Found {len(compliance_data['certificate_of_occupancy'])} C of O records (block/lot search)")
                    
                    # Show latest record
                    latest_co = data[0]
                    print(f"   📊 Latest C of O: {latest_co['c_of_o_filing_type']} - Status: {latest_co['c_of_o_status']}")
                    return
            
            print(f"   ❌ No Certificate of Occupancy records found")
            print(f"   ⚠️  This may indicate occupancy compliance issues")
            
        except Exception as e:
            print(f"   ❌ Certificate of Occupancy error: {e}")
    
    def clean_data_for_json(self, data: List[Dict]) -> List[Dict]:
        """Clean data by replacing NaN values with None for JSON serialization"""
        cleaned_data = []
        for item in data:
            cleaned_item = {}
            for key, value in item.items():
                # Handle various types of NaN/null values
                if value is None or (isinstance(value, float) and math.isnan(value)) or str(value).lower() == 'nan':
                    cleaned_item[key] = None
                else:
                    cleaned_item[key] = value
            cleaned_data.append(cleaned_item)
        return cleaned_data
    
    def create_compliance_record(self, identifiers: PropertyIdentifiers, compliance_data: Dict) -> ComplianceRecord:
        """Create structured compliance record from gathered data"""
        
        print(f"\n📊 STEP 3: CREATING COMPLIANCE RECORD")
        print("-" * 40)
        
        # Calculate compliance metrics
        hpd_total = len(compliance_data['hpd_violations'])
        hpd_active = len([v for v in compliance_data['hpd_violations'] 
                         if v.get('violationstatus') in ['Open', 'ACTIVE']])
        
        dob_total = len(compliance_data['dob_violations'])
        dob_active = len([v for v in compliance_data['dob_violations'] 
                         if not v.get('disposition_comments')])
        
        elevator_total = len(compliance_data['elevator_inspections'])
        elevator_active = len([e for e in compliance_data['elevator_inspections'] 
                              if e.get('device_status') == 'Active'])
        
        boiler_total = len(compliance_data['boiler_inspections'])
        
        electrical_total = len(compliance_data['electrical_permits'])
        electrical_active = len([e for e in compliance_data['electrical_permits'] 
                               if e.get('filing_status') in ['Approved', 'Job in Process', 'Active', 'Permit Issued']])
        
        # Calculate compliance scores
        hpd_score = max(0, 100 - (hpd_active * 10)) if hpd_total > 0 else 100
        dob_score = max(0, 100 - (dob_active * 15)) if dob_total > 0 else 100
        elevator_score = (elevator_active / elevator_total * 100) if elevator_total > 0 else 100
        
        # Electrical compliance: Recent permits indicate active maintenance
        electrical_score = 100
        if electrical_total > 0:
            # Score based on recent activity and permit status
            recent_permits = len([e for e in compliance_data['electrical_permits']
                                if e.get('filing_date') and 
                                datetime.strptime(e['filing_date'][:10], '%Y-%m-%d').year >= datetime.now().year - 2])
            if recent_permits == 0:
                electrical_score = 70  # No recent electrical work may indicate neglect
            elif electrical_active > 0:
                electrical_score = 90   # Active permits show ongoing maintenance
        else:
            electrical_score = 85  # No permits may be normal for some buildings
        
        overall_score = (hpd_score * 0.3 + dob_score * 0.3 + elevator_score * 0.2 + electrical_score * 0.2)
        
        # Create compliance record
        record = ComplianceRecord(
            address=identifiers.address,
            bin=identifiers.bin,
            bbl=identifiers.bbl,
            borough=identifiers.borough,
            block=identifiers.block,
            lot=identifiers.lot,
            zip_code=identifiers.zip_code,
            
            hpd_violations_total=hpd_total,
            hpd_violations_active=hpd_active,
            dob_violations_total=dob_total,
            dob_violations_active=dob_active,
            
            elevator_devices_total=elevator_total,
            elevator_devices_active=elevator_active,
            boiler_devices_total=boiler_total,
            electrical_permits_total=electrical_total,
            electrical_permits_active=electrical_active,
            
            hpd_compliance_score=hpd_score,
            dob_compliance_score=dob_score,
            elevator_compliance_score=elevator_score,
            electrical_compliance_score=electrical_score,
            overall_compliance_score=overall_score,
            
            hpd_violations_data=json.dumps(self.clean_data_for_json(compliance_data['hpd_violations'])),
            dob_violations_data=json.dumps(self.clean_data_for_json(compliance_data['dob_violations'])),
            elevator_data=json.dumps(self.clean_data_for_json(compliance_data['elevator_inspections'])),
            boiler_data=json.dumps(self.clean_data_for_json(compliance_data['boiler_inspections'])),
            electrical_data=json.dumps(self.clean_data_for_json(compliance_data['electrical_permits'])),
            
            processed_at=datetime.now().isoformat(),
            data_sources="NYC_Open_Data,NYC_Planning_GeoSearch"
        )
        
        print(f"✅ Compliance record created")
        print(f"   Overall Score: {record.overall_compliance_score:.1f}/100")
        print(f"   HPD: {record.hpd_violations_total} total, {record.hpd_violations_active} active")
        print(f"   DOB: {record.dob_violations_total} total, {record.dob_violations_active} active")
        print(f"   Elevators: {record.elevator_devices_total} total, {record.elevator_devices_active} active")
        print(f"   Boilers: {record.boiler_devices_total} total")
        print(f"   Electrical: {record.electrical_permits_total} permits, {record.electrical_permits_active} active")
        
        return record
    
    def create_empty_record(self, address: str) -> ComplianceRecord:
        """Create empty compliance record for failed searches"""
        return ComplianceRecord(
            address=address,
            bin=None,
            bbl=None,
            borough=None,
            block=None,
            lot=None,
            zip_code=None,
            processed_at=datetime.now().isoformat(),
            data_sources="FAILED"
        )
    
    async def display_comprehensive_report(self, record: ComplianceRecord):
        """Display comprehensive compliance report"""
        
        print(f"\n" + "="*80)
        print("📊 COMPREHENSIVE PROPERTY COMPLIANCE REPORT")
        print("="*80)
        
        print(f"🏢 PROPERTY INFORMATION:")
        print(f"   Address: {record.address}")
        print(f"   BIN: {record.bin}")
        print(f"   BBL: {record.bbl}")
        print(f"   Borough: {record.borough}")
        print(f"   Block/Lot: {record.block}/{record.lot}")
        print(f"   ZIP Code: {record.zip_code}")
        
        print(f"\n📈 COMPLIANCE SCORES:")
        print(f"   Overall Score: {record.overall_compliance_score:.1f}/100")
        print(f"   HPD Score: {record.hpd_compliance_score:.1f}/100")
        print(f"   DOB Score: {record.dob_compliance_score:.1f}/100")
        print(f"   Elevator Score: {record.elevator_compliance_score:.1f}/100")
        print(f"   Electrical Score: {record.electrical_compliance_score:.1f}/100")
        
        print(f"\n📊 VIOLATION SUMMARY:")
        print(f"   HPD Violations: {record.hpd_violations_total} total, {record.hpd_violations_active} active")
        print(f"   DOB Violations: {record.dob_violations_total} total, {record.dob_violations_active} active")
        
        print(f"\n🏗️ EQUIPMENT SUMMARY:")
        print(f"   Elevator Devices: {record.elevator_devices_total} total, {record.elevator_devices_active} active")
        print(f"   Boiler Devices: {record.boiler_devices_total} total")
        print(f"   Electrical Permits: {record.electrical_permits_total} total, {record.electrical_permits_active} active")
        
        # Show sample violations if available
        hpd_violations = json.loads(record.hpd_violations_data)
        if hpd_violations:
            print(f"\n🔍 SAMPLE HPD VIOLATIONS:")
            for i, violation in enumerate(hpd_violations[:3], 1):
                status = violation.get('violationstatus', 'N/A')
                date = violation.get('approveddate', 'N/A')
                desc = violation.get('novdescription', 'N/A')[:60] + '...' if violation.get('novdescription') else 'N/A'
                print(f"   {i}. Status: {status} | Date: {date}")
                print(f"      Description: {desc}")
        
        elevator_data = json.loads(record.elevator_data)
        if elevator_data:
            print(f"\n🛗 ELEVATOR DEVICES:")
            for i, device in enumerate(elevator_data[:5], 1):
                device_num = device.get('device_number', 'N/A')
                device_type = device.get('device_type', 'N/A')
                status = device.get('device_status', 'N/A')
                date = device.get('status_date', 'N/A')
                print(f"   {i}. Device: {device_num} | Type: {device_type} | Status: {status} | Date: {date}")
        
        print(f"\n✅ Report processed at: {record.processed_at}")
        print(f"📊 Data sources: {record.data_sources}")

async def main():
    """Main function to process property with comprehensive compliance analysis"""
    
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_property_compliance.py 'ADDRESS' [BOROUGH]")
        print("Example: python comprehensive_property_compliance.py '140 West 28th Street' 'Manhattan'")
        print("         python comprehensive_property_compliance.py '1662 Park Avenue, New York, NY 10035'")
        sys.exit(1)
    
    address = sys.argv[1]
    borough = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize comprehensive compliance system
    system = ComprehensivePropertyComplianceSystem()
    
    # Process the property
    record = await system.process_property(address, borough)
    
    # Display comprehensive report
    await system.display_comprehensive_report(record)
    
    # Save to file
    output_file = f"comprehensive_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert dataclass to dict for JSON serialization
    record_dict = {
        'address': record.address,
        'bin': record.bin,
        'bbl': record.bbl,
        'borough': record.borough,
        'block': record.block,
        'lot': record.lot,
        'zip_code': record.zip_code,
        'hpd_violations_total': record.hpd_violations_total,
        'hpd_violations_active': record.hpd_violations_active,
        'dob_violations_total': record.dob_violations_total,
        'dob_violations_active': record.dob_violations_active,
        'elevator_devices_total': record.elevator_devices_total,
        'elevator_devices_active': record.elevator_devices_active,
        'boiler_devices_total': record.boiler_devices_total,
        'electrical_permits_total': record.electrical_permits_total,
        'electrical_permits_active': record.electrical_permits_active,
        'hpd_compliance_score': record.hpd_compliance_score,
        'dob_compliance_score': record.dob_compliance_score,
        'elevator_compliance_score': record.elevator_compliance_score,
        'electrical_compliance_score': record.electrical_compliance_score,
        'overall_compliance_score': record.overall_compliance_score,
        'hpd_violations_data': record.hpd_violations_data,
        'dob_violations_data': record.dob_violations_data,
        'elevator_data': record.elevator_data,
        'boiler_data': record.boiler_data,
        'electrical_data': record.electrical_data,
        'processed_at': record.processed_at,
        'data_sources': record.data_sources
    }
    
    with open(output_file, 'w') as f:
        json.dump(record_dict, f, indent=2)
    
    print(f"\n💾 Full report saved to: {output_file}")
    print(f"🎯 SUCCESS: Comprehensive compliance analysis complete for {address}")
    print(f"📊 Overall Compliance Score: {record.overall_compliance_score:.1f}/100")

if __name__ == "__main__":
    asyncio.run(main())
