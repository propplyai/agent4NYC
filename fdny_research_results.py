#!/usr/bin/env python3
"""
FDNY Dataset Research Results and Corrected Implementation
=========================================================

Based on comprehensive research of NYC Open Data FDNY datasets, this script provides:
1. Corrected dataset information with actual column names
2. Working search strategies for each dataset
3. Direct API calls with proper parameters
4. Solutions for the 400 Client Error issues

RESEARCH FINDINGS:
- avgm-ztsb (FDNY Violations): NO BIN support, uses block/lot and address
- tsak-vtv3: NOT fire safety inspections (it's construction contracts!)
- Alternative datasets with BIN support available
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional

class FDNYDatasetResearcher:
    """Research-based FDNY dataset client with correct column names and search methods"""
    
    def __init__(self, api_key_id: str = None, api_key_secret: str = None):
        self.base_url = "https://data.cityofnewyork.us/resource"
        self.auth = (api_key_id, api_key_secret) if api_key_id and api_key_secret else None
        
        # CORRECTED DATASET CONFIGURATIONS based on research
        self.fdny_datasets = {
            'fdny_violations_full': {
                'id': 'avgm-ztsb',
                'name': 'FDNY Violations (OATH ECB Hearings)',
                'description': 'Complete FDNY violations with hearing results and payments',
                'column_count': 78,
                'supports_bin': False,
                'supports_block_lot': True,
                'supports_address': True,
                'key_columns': {
                    'ticket_number': 'ticket_number',
                    'violation_date': 'violation_date', 
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no',
                    'lot': 'violation_location_lot_no',
                    'house_number': 'violation_location_house',
                    'street_name': 'violation_location_street_name',
                    'zip_code': 'violation_location_zip_code',
                    'violation_desc': 'violation_description',
                    'amount': 'total_violation_amount',
                    'status': 'hearing_status'
                }
            },
            'fdny_violations_simple': {
                'id': 'ktas-47y7',
                'name': 'FDNY Violations (Simplified)',
                'description': 'Simplified FDNY violations dataset',
                'column_count': 15,
                'supports_bin': False,
                'supports_block_lot': True,
                'supports_address': True,
                'key_columns': {
                    'ticket_number': 'ticket_number',
                    'violation_date': 'violation_date',
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no',
                    'lot': 'violation_location_lot_no',
                    'house_number': 'violation_location_house',
                    'amount': 'total_violation_amount'
                }
            },
            'fire_prevention_inspections': {
                'id': 'ssq6-fkht',
                'name': 'Bureau of Fire Prevention - Inspections (Historical)',
                'description': 'Fire prevention inspections - HISTORICAL DATA ONLY',
                'column_count': 20,
                'supports_bin': True,
                'supports_block_lot': False,
                'supports_address': True,
                'status': 'HISTORICAL - NO NEW DATA ADDED',
                'key_columns': {
                    'account_id': 'ACCT_ID',
                    'owner_name': 'OWNER_NAME',
                    'last_visit': 'LAST_VISIT_DT',
                    'last_inspection': 'LAST_FULL_INSP_DT',
                    'inspection_status': 'LAST_INSP_STAT',
                    'address': 'PREM_ADDR',
                    'bin': 'BIN',
                    'bbl': 'BBL',
                    'borough': 'BOROUGH'
                }
            },
            'fire_prevention_violations': {
                'id': 'bi53-yph3',
                'name': 'Bureau of Fire Prevention - Active Violation Orders (Historical)',
                'description': 'Active violation orders from Bureau of Fire Prevention',
                'column_count': 21,
                'supports_bin': True,
                'supports_block_lot': False,
                'supports_address': True,
                'status': 'HISTORICAL - NO NEW DATA ADDED',
                'key_columns': {
                    'violation_id': 'VIO_ID',
                    'violation_number': 'VIOLATION_NUM',
                    'violation_desc': 'VIO_LAW_DESC',
                    'violation_date': 'VIO_DATE',
                    'action': 'ACTION',
                    'address': 'PREM_ADDR',
                    'bin': 'BIN',
                    'bbl': 'BBL',
                    'borough': 'BOROUGH'
                }
            },
            'fire_prevention_summary': {
                'id': 'nvgj-hbht',
                'name': 'Bureau of Fire Prevention - Building Summary (Historical)',
                'description': 'Building summary with sprinkler/standpipe info and violation counts',
                'column_count': 16,
                'supports_bin': True,
                'supports_block_lot': True,
                'supports_address': False,
                'status': 'HISTORICAL - NO NEW DATA ADDED',
                'key_columns': {
                    'bin': 'BIN',
                    'bbl': 'BBL',
                    'block': 'BLOCK',
                    'lot': 'LOT',
                    'borough': 'BOROUGH',
                    'violation_notices': 'NUM_OF_VIOLATION_NOTICES',
                    'violation_orders': 'NUM_OF_VIOLATION_ORDER',
                    'sprinkler_type': 'SPRINKLER_TYPE',
                    'standpipe_type': 'STANDPIPE_TYPE'
                }
            },
            'fire_incident_dispatch': {
                'id': '8m42-w767',
                'name': 'Fire Incident Dispatch Data',
                'description': 'Fire incident response data (aggregated locations for privacy)',
                'column_count': 29,
                'supports_bin': False,
                'supports_block_lot': False,
                'supports_address': False,
                'note': 'Locations aggregated for privacy - limited search capabilities',
                'key_columns': {
                    'incident_id': 'STARFIRE_INCIDENT_ID',
                    'incident_date': 'INCIDENT_DATETIME',
                    'borough': 'INCIDENT_BOROUGH',
                    'zipcode': 'ZIPCODE',
                    'classification': 'INCIDENT_CLASSIFICATION'
                }
            }
        }
        
        # WRONG DATASET - This was the source of confusion!
        self.wrong_datasets = {
            'tsak-vtv3': {
                'actual_name': 'Upcoming contracts to be awarded (CIP)',
                'actual_description': 'School construction projects - NOT fire safety inspections!',
                'why_wrong': 'This dataset contains upcoming school construction contracts, not fire safety data'
            }
        }
    
    def get_dataset_info(self) -> Dict:
        """Get comprehensive information about FDNY datasets"""
        return {
            'correct_datasets': self.fdny_datasets,
            'wrong_datasets': self.wrong_datasets
        }
    
    def search_fdny_violations_by_block_lot(self, borough: str, block: str, lot: str, 
                                           dataset_type: str = 'full') -> pd.DataFrame:
        """
        Search FDNY violations by borough/block/lot
        
        Args:
            borough: Borough name (MANHATTAN, BROOKLYN, QUEENS, BRONX, STATEN ISLAND)
            block: Block number
            lot: Lot number  
            dataset_type: 'full' (avgm-ztsb) or 'simple' (ktas-47y7)
        """
        
        dataset_key = 'fdny_violations_full' if dataset_type == 'full' else 'fdny_violations_simple'
        dataset = self.fdny_datasets[dataset_key]
        
        print(f"🔍 Searching {dataset['name']} by block/lot...")
        print(f"   Borough: {borough}, Block: {block}, Lot: {lot}")
        
        try:
            # Normalize borough name
            borough = borough.upper()
            if borough in ['MN', 'MANHATTAN']:
                borough = 'MANHATTAN'
            elif borough in ['BK', 'BROOKLYN']:
                borough = 'BROOKLYN'
            elif borough in ['QN', 'QUEENS']:
                borough = 'QUEENS'
            elif borough in ['BX', 'BRONX']:
                borough = 'BRONX'
            elif borough in ['SI', 'STATEN ISLAND']:
                borough = 'STATEN ISLAND'
            
            # Format block and lot with leading zeros as expected by the dataset
            block_padded = block.zfill(5)  # Block numbers are 5 digits
            lot_padded = lot.zfill(4)      # Lot numbers are 4 digits
            
            # Build the query
            where_clause = (f"{dataset['key_columns']['borough']} = '{borough}' AND "
                          f"{dataset['key_columns']['block']} = '{block_padded}' AND "
                          f"{dataset['key_columns']['lot']} = '{lot_padded}'")
            
            # Select key fields
            select_fields = [
                dataset['key_columns']['ticket_number'],
                dataset['key_columns']['violation_date'],
                dataset['key_columns']['borough'],
                dataset['key_columns']['block'],
                dataset['key_columns']['lot'],
                dataset['key_columns']['house_number'],
                dataset['key_columns']['street_name'],
                dataset['key_columns']['amount'],
                dataset['key_columns'].get('violation_desc', ''),
                dataset['key_columns'].get('status', '')
            ]
            select_fields = [f for f in select_fields if f]  # Remove empty fields
            
            url = f"{self.base_url}/{dataset['id']}.json"
            params = {
                '$where': where_clause,
                '$select': ', '.join(select_fields),
                '$limit': 100,
                '$order': f"{dataset['key_columns']['violation_date']} DESC"
            }
            
            response = requests.get(url, params=params, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                df = pd.DataFrame(data)
                print(f"   ✅ Found {len(df)} FDNY violations")
                return df
            else:
                print(f"   ❌ No FDNY violations found for this location")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ❌ Error searching FDNY violations: {e}")
            return pd.DataFrame()
    
    def search_fire_prevention_by_bin(self, bin_number: str) -> Dict[str, pd.DataFrame]:
        """
        Search Bureau of Fire Prevention datasets by BIN
        
        Args:
            bin_number: Building Identification Number
            
        Returns:
            Dictionary with results from different fire prevention datasets
        """
        
        results = {}
        bin_datasets = ['fire_prevention_inspections', 'fire_prevention_violations', 'fire_prevention_summary']
        
        print(f"🔍 Searching Bureau of Fire Prevention datasets by BIN: {bin_number}")
        print("⚠️  Note: These are historical datasets (no longer updated)")
        
        for dataset_key in bin_datasets:
            dataset = self.fdny_datasets[dataset_key]
            print(f"\n📊 Searching {dataset['name']}...")
            
            try:
                where_clause = f"{dataset['key_columns']['bin']} = '{bin_number}'"
                
                # Select relevant fields for each dataset
                if dataset_key == 'fire_prevention_inspections':
                    select_fields = [
                        dataset['key_columns']['account_id'],
                        dataset['key_columns']['owner_name'],
                        dataset['key_columns']['last_visit'],
                        dataset['key_columns']['last_inspection'],
                        dataset['key_columns']['inspection_status'],
                        dataset['key_columns']['address'],
                        dataset['key_columns']['bin'],
                        dataset['key_columns']['borough']
                    ]
                elif dataset_key == 'fire_prevention_violations':
                    select_fields = [
                        dataset['key_columns']['violation_id'],
                        dataset['key_columns']['violation_number'],
                        dataset['key_columns']['violation_desc'],
                        dataset['key_columns']['violation_date'],
                        dataset['key_columns']['action'],
                        dataset['key_columns']['address'],
                        dataset['key_columns']['bin'],
                        dataset['key_columns']['borough']
                    ]
                else:  # fire_prevention_summary
                    select_fields = [
                        dataset['key_columns']['bin'],
                        dataset['key_columns']['bbl'],
                        dataset['key_columns']['borough'],
                        dataset['key_columns']['violation_notices'],
                        dataset['key_columns']['violation_orders'],
                        dataset['key_columns']['sprinkler_type'],
                        dataset['key_columns']['standpipe_type']
                    ]
                
                url = f"{self.base_url}/{dataset['id']}.json"
                params = {
                    '$where': where_clause,
                    '$select': ', '.join(select_fields),
                    '$limit': 100
                }
                
                response = requests.get(url, params=params, auth=self.auth, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data:
                    df = pd.DataFrame(data)
                    results[dataset_key] = df
                    print(f"   ✅ Found {len(df)} records")
                    
                    # Show sample data
                    if len(df) > 0:
                        sample = df.iloc[0].to_dict()
                        print(f"   📝 Sample: {dict(list(sample.items())[:3])}...")
                else:
                    print(f"   ❌ No records found")
                    results[dataset_key] = pd.DataFrame()
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[dataset_key] = pd.DataFrame()
        
        return results
    
    def search_fdny_violations_by_address(self, address: str, borough: str = None) -> pd.DataFrame:
        """
        Search FDNY violations by address components
        
        Args:
            address: Street address (e.g., "140 West 28th Street")
            borough: Borough name (optional)
        """
        
        print(f"🔍 Searching FDNY violations by address: {address}")
        if borough:
            print(f"   Borough filter: {borough}")
        
        # Parse address
        address_parts = address.strip().split(' ')
        house_number = address_parts[0] if address_parts else ""
        street_name = ' '.join(address_parts[1:]) if len(address_parts) > 1 else ""
        
        try:
            dataset = self.fdny_datasets['fdny_violations_full']
            where_parts = []
            
            if house_number:
                where_parts.append(f"{dataset['key_columns']['house_number']} = '{house_number}'")
            
            if street_name:
                # Use UPPER for case-insensitive search
                where_parts.append(f"UPPER({dataset['key_columns']['street_name']}) LIKE UPPER('%{street_name}%')")
            
            if borough:
                borough = borough.upper()
                where_parts.append(f"{dataset['key_columns']['borough']} = '{borough}'")
            
            if not where_parts:
                print("   ❌ No valid address components found")
                return pd.DataFrame()
            
            where_clause = ' AND '.join(where_parts)
            
            select_fields = [
                dataset['key_columns']['ticket_number'],
                dataset['key_columns']['violation_date'],
                dataset['key_columns']['borough'],
                dataset['key_columns']['house_number'],
                dataset['key_columns']['street_name'],
                dataset['key_columns']['violation_desc'],
                dataset['key_columns']['amount'],
                dataset['key_columns']['status']
            ]
            
            url = f"{self.base_url}/{dataset['id']}.json"
            params = {
                '$where': where_clause,
                '$select': ', '.join(select_fields),
                '$limit': 100,
                '$order': f"{dataset['key_columns']['violation_date']} DESC"
            }
            
            response = requests.get(url, params=params, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                df = pd.DataFrame(data)
                print(f"   ✅ Found {len(df)} FDNY violations")
                return df
            else:
                print(f"   ❌ No FDNY violations found for this address")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ❌ Error searching by address: {e}")
            return pd.DataFrame()
    
    def print_dataset_summary(self):
        """Print a comprehensive summary of FDNY datasets"""
        
        print("🚒 NYC OPEN DATA FDNY DATASETS - RESEARCH RESULTS")
        print("=" * 80)
        
        print("\n✅ CORRECT FDNY DATASETS:")
        print("-" * 40)
        
        for key, dataset in self.fdny_datasets.items():
            print(f"\n📊 {dataset['name']}")
            print(f"   ID: {dataset['id']}")
            print(f"   Columns: {dataset['column_count']}")
            print(f"   Description: {dataset['description']}")
            print(f"   Supports BIN: {'✅' if dataset['supports_bin'] else '❌'}")
            print(f"   Supports Block/Lot: {'✅' if dataset['supports_block_lot'] else '❌'}")  
            print(f"   Supports Address: {'✅' if dataset['supports_address'] else '❌'}")
            
            if 'status' in dataset:
                print(f"   ⚠️  Status: {dataset['status']}")
            if 'note' in dataset:
                print(f"   💡 Note: {dataset['note']}")
        
        print(f"\n❌ WRONG DATASET IDENTIFICATION:")
        print("-" * 40)
        
        for dataset_id, info in self.wrong_datasets.items():
            print(f"\n🚫 {dataset_id}")
            print(f"   Actual Name: {info['actual_name']}")
            print(f"   Actual Description: {info['actual_description']}")
            print(f"   Why Wrong: {info['why_wrong']}")
        
        print(f"\n🎯 SEARCH STRATEGY RECOMMENDATIONS:")  
        print("-" * 40)
        print("1. For current FDNY violations: Use avgm-ztsb or ktas-47y7")
        print("   - Search by borough + block + lot")
        print("   - Search by address components (house number + street name)")
        print("   - NO BIN support available")
        print("")
        print("2. For fire prevention inspections: Use ssq6-fkht, bi53-yph3, nvgj-hbht")
        print("   - These are HISTORICAL datasets (no longer updated)")
        print("   - Support BIN-based searches")
        print("   - Good for historical compliance research")
        print("")
        print("3. Current fire prevention data: Contact FDNY directly")
        print("   - Use FDNY Business portal: fires.fdnycloud.org/CitizenAccess")
        print("   - Call 311 for current inspection information")

def main():
    """Test the corrected FDNY dataset implementation"""
    
    # Initialize the researcher
    try:
        from config import API_KEY_ID, API_KEY_SECRET
        researcher = FDNYDatasetResearcher(API_KEY_ID, API_KEY_SECRET)
        print("✅ Initialized with API credentials")
    except:
        researcher = FDNYDatasetResearcher()
        print("✅ Initialized without API credentials (anonymous access)")
    
    # Print comprehensive dataset information
    researcher.print_dataset_summary()
    
    # Test searches with example property: 140 West 28th Street, Manhattan
    print(f"\n" + "="*80)
    print("🧪 TESTING CORRECTED SEARCH METHODS")
    print("="*80)
    
    test_address = "140 West 28th Street"
    test_borough = "MANHATTAN"
    test_block = "1073"
    test_lot = "1"
    test_bin = "4433339"
    
    print(f"\n🏢 Test Property: {test_address}, {test_borough}")
    print(f"   Block/Lot: {test_block}/{test_lot}, BIN: {test_bin}")
    
    # Test 1: Search FDNY violations by block/lot
    print(f"\n" + "="*60)
    print("TEST 1: FDNY Violations by Block/Lot")
    print("="*60)
    violations_df = researcher.search_fdny_violations_by_block_lot(test_borough, test_block, test_lot)
    if not violations_df.empty:
        print(f"📋 Sample violations:")
        print(violations_df.head())
    
    # Test 2: Search by address
    print(f"\n" + "="*60)
    print("TEST 2: FDNY Violations by Address")
    print("="*60)
    address_violations = researcher.search_fdny_violations_by_address(test_address, test_borough)
    if not address_violations.empty:
        print(f"📋 Sample violations:")
        print(address_violations.head())
    
    # Test 3: Search fire prevention by BIN
    print(f"\n" + "="*60)
    print("TEST 3: Fire Prevention Data by BIN")
    print("="*60)
    fire_prev_results = researcher.search_fire_prevention_by_bin(test_bin)
    
    total_records = sum(len(df) for df in fire_prev_results.values())
    print(f"\n📊 Total fire prevention records found: {total_records}")
    
    for dataset_name, df in fire_prev_results.items():
        if not df.empty:
            print(f"\n📋 {dataset_name} sample:")
            print(df.head())
    
    print(f"\n" + "="*80)
    print("✅ TESTING COMPLETE - FDNY Dataset Research Results")
    print("="*80)

if __name__ == "__main__":
    main()