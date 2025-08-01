#!/usr/bin/env python3
"""
Corrected FDNY Dataset Search Script
===================================

Based on the investigation results, this script implements proper searches
for FDNY violations and fire prevention data using the correct column names
and search strategies.

Key Findings:
1. avgm-ztsb (FDNY Violations) - Uses block/lot and address searches (NO BIN!)
2. tsak-vtv3 - This is NOT fire safety inspections, it's construction contracts
3. Alternative FDNY datasets available with proper BIN support
"""

import sys
import pandas as pd
from nyc_opendata_client import NYCOpenDataClient

class CorrectedFDNYSearcher:
    """Corrected FDNY dataset searcher with proper column names"""
    
    def __init__(self):
        self.client = NYCOpenDataClient.from_config()
        
        # Corrected dataset configurations based on investigation
        self.datasets = {
            'fdny_violations_oath': {
                'id': 'avgm-ztsb',
                'name': 'FDNY Violations (OATH ECB)',
                'search_fields': {
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no', 
                    'lot': 'violation_location_lot_no',
                    'house_number': 'violation_location_house',
                    'street_name': 'violation_location_street_name',
                    'zip_code': 'violation_location_zip_code'
                },
                'select_fields': [
                    'ticket_number', 'violation_date', 'violation_description',
                    'violation_location_borough', 'violation_location_block_no', 
                    'violation_location_lot_no', 'violation_location_house',
                    'violation_location_street_name', 'hearing_status', 
                    'total_violation_amount', 'paid_amount'
                ]
            },
            'fdny_violations_simplified': {
                'id': 'ktas-47y7',
                'name': 'FDNY Violations (Simplified)',
                'search_fields': {
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no',
                    'lot': 'violation_location_lot_no', 
                    'house_number': 'violation_location_house'
                },
                'select_fields': [
                    'ticket_number', 'violation_date', 'violation_location_borough',
                    'violation_location_block_no', 'violation_location_lot_no',
                    'violation_location_house', 'total_violation_amount'
                ]
            },
            'bureau_fire_prevention_inspections': {
                'id': 'ssq6-fkht',
                'name': 'Bureau of Fire Prevention - Inspections (Historical)',
                'search_fields': {
                    'bin': 'BIN',
                    'address': 'PREM_ADDR',
                    'borough': 'BOROUGH'
                },
                'select_fields': [
                    'ACCT_ID', 'OWNER_NAME', 'LAST_VISIT_DT', 'LAST_FULL_INSP_DT',
                    'LAST_INSP_STAT', 'PREM_ADDR', 'BIN', 'BBL', 'BOROUGH'
                ]
            },
            'bureau_fire_prevention_violations': {
                'id': 'bi53-yph3',
                'name': 'Bureau of Fire Prevention - Active Violation Orders (Historical)',
                'search_fields': {
                    'bin': 'BIN',
                    'address': 'PREM_ADDR',
                    'borough': 'BOROUGH'
                },
                'select_fields': [
                    'VIO_ID', 'VIOLATION_NUM', 'VIO_LAW_DESC', 'VIO_DATE',
                    'ACTION', 'PREM_ADDR', 'BIN', 'BBL', 'BOROUGH'
                ]
            },
            'bureau_fire_prevention_summary': {
                'id': 'nvgj-hbht',
                'name': 'Bureau of Fire Prevention - Building Summary (Historical)',
                'search_fields': {
                    'bin': 'BIN',
                    'block': 'BLOCK',
                    'lot': 'LOT',
                    'borough': 'BOROUGH'
                },
                'select_fields': [
                    'BIN', 'BBL', 'BLOCK', 'LOT', 'BOROUGH',
                    'NUM_OF_VIOLATION_NOTICES', 'NUM_OF_VIOLATION_ORDER',
                    'SPRINKLER_TYPE', 'STANDPIPE_TYPE'
                ]
            }
        }
    
    def search_by_bin(self, bin_number: str) -> dict:
        """Search FDNY data by BIN (only works for Bureau of Fire Prevention datasets)"""
        results = {}
        
        print(f"🔍 SEARCHING BY BIN: {bin_number}")
        print("=" * 50)
        
        # Only Bureau of Fire Prevention datasets support BIN searches
        bin_datasets = ['bureau_fire_prevention_inspections', 'bureau_fire_prevention_violations', 'bureau_fire_prevention_summary']
        
        for dataset_key in bin_datasets:
            dataset = self.datasets[dataset_key]
            print(f"\n📊 Searching {dataset['name']}...")
            
            try:
                where_clause = f"{dataset['search_fields']['bin']} = '{bin_number}'"
                select_clause = ', '.join(dataset['select_fields'])
                
                data = self.client.get_data(
                    dataset_key,  # This will need to be handled differently
                    where=where_clause,
                    select=select_clause,
                    limit=100
                )
                
                if data is not None and not data.empty:
                    results[dataset_key] = data.to_dict('records')
                    print(f"   ✅ Found {len(data)} records")
                    
                    # Show sample
                    sample = data.iloc[0]
                    print(f"   📝 Sample: {dict(sample)}")
                else:
                    print(f"   ❌ No records found")
                    results[dataset_key] = []
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[dataset_key] = []
        
        return results
    
    def search_by_block_lot(self, borough: str, block: str, lot: str) -> dict:
        """Search FDNY data by borough/block/lot"""
        results = {}
        
        print(f"🔍 SEARCHING BY BLOCK/LOT: {borough} Block {block}, Lot {lot}")
        print("=" * 60)
        
        # Search FDNY violations (OATH dataset)
        print(f"\n📊 Searching FDNY Violations (OATH)...")
        try:
            # Normalize borough name for FDNY violations dataset
            borough_normalized = borough.upper()
            if borough_normalized in ['MN', 'MANHATTAN']:
                borough_normalized = 'MANHATTAN'
            elif borough_normalized in ['BK', 'BROOKLYN']:
                borough_normalized = 'BROOKLYN'
            elif borough_normalized in ['QN', 'QUEENS']:
                borough_normalized = 'QUEENS'
            elif borough_normalized in ['BX', 'BRONX']:
                borough_normalized = 'BRONX'
            elif borough_normalized in ['SI', 'STATEN ISLAND']:
                borough_normalized = 'STATEN ISLAND'
            
            dataset = self.datasets['fdny_violations_oath']
            where_clause = (f"{dataset['search_fields']['borough']} = '{borough_normalized}' AND "
                          f"{dataset['search_fields']['block']} = '{block.zfill(5)}' AND "
                          f"{dataset['search_fields']['lot']} = '{lot.zfill(4)}'")
            
            data = self._search_dataset('fdny_violations_oath', where_clause)
            results['fdny_violations_oauth'] = data
            
        except Exception as e:
            print(f"   ❌ Error searching FDNY violations: {e}")
            results['fdny_violations_oauth'] = []
        
        # Search Bureau of Fire Prevention datasets that support block/lot
        print(f"\n📊 Searching Bureau of Fire Prevention - Building Summary...")
        try:
            dataset = self.datasets['bureau_fire_prevention_summary']
            where_clause = (f"{dataset['search_fields']['borough']} = '{borough_normalized}' AND "
                          f"{dataset['search_fields']['block']} = '{block}' AND "
                          f"{dataset['search_fields']['lot']} = '{lot}'")
            
            data = self._search_dataset('bureau_fire_prevention_summary', where_clause)
            results['bureau_fire_prevention_summary'] = data
            
        except Exception as e:
            print(f"   ❌ Error searching Fire Prevention summary: {e}")
            results['bureau_fire_prevention_summary'] = []
        
        return results
    
    def search_by_address(self, address: str, borough: str = None) -> dict:
        """Search FDNY data by address"""
        results = {}
        
        print(f"🔍 SEARCHING BY ADDRESS: {address}")
        if borough:
            print(f"   Borough: {borough}")
        print("=" * 50)
        
        # Parse address components
        address_parts = address.split(' ')
        house_number = address_parts[0] if address_parts else ""
        street_name = ' '.join(address_parts[1:]) if len(address_parts) > 1 else ""
        
        # Search FDNY violations by address components
        print(f"\n📊 Searching FDNY Violations by address...")
        try:
            dataset = self.datasets['fdny_violations_oath']
            where_parts = []
            
            if house_number:
                where_parts.append(f"{dataset['search_fields']['house_number']} = '{house_number}'")
            
            if street_name:
                where_parts.append(f"{dataset['search_fields']['street_name']} LIKE '%{street_name.upper()}%'")
            
            if borough:
                borough_normalized = borough.upper()
                where_parts.append(f"{dataset['search_fields']['borough']} = '{borough_normalized}'")
            
            if where_parts:
                where_clause = ' AND '.join(where_parts)
                data = self._search_dataset('fdny_violations_oath', where_clause)
                results['fdny_violations_oauth'] = data
            else:
                print(f"   ❌ No valid address components found")
                results['fdny_violations_oauth'] = []
                
        except Exception as e:
            print(f"   ❌ Error searching by address: {e}")
            results['fdny_violations_oauth'] = []
        
        # Search Bureau of Fire Prevention by premise address
        print(f"\n📊 Searching Bureau of Fire Prevention by premise address...")
        try:
            for dataset_key in ['bureau_fire_prevention_inspections', 'bureau_fire_prevention_violations']:
                dataset = self.datasets[dataset_key]
                where_clause = f"{dataset['search_fields']['address']} LIKE '%{address.upper()}%'"
                
                if borough:
                    where_clause += f" AND {dataset['search_fields']['borough']} = '{borough.upper()}'"
                
                data = self._search_dataset(dataset_key, where_clause)
                results[dataset_key] = data
                
        except Exception as e:
            print(f"   ❌ Error searching Bureau datasets by address: {e}")
        
        return results
    
    def _search_dataset(self, dataset_key: str, where_clause: str) -> list:
        """Helper method to search a specific dataset"""
        try:
            dataset = self.datasets[dataset_key]
            select_clause = ', '.join(dataset['select_fields'])
            
            # We need to directly use the dataset ID since our client expects predefined keys
            dataset_id = dataset['id']
            url = f"https://data.cityofnewyork.us/resource/{dataset_id}.json"
            
            params = {
                '$where': where_clause,
                '$select': select_clause,
                '$limit': 100
            }
            
            response = self.client.session.get(url, params=params, auth=self.client.auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                print(f"   ✅ Found {len(data)} records in {dataset['name']}")
                
                # Show sample
                if len(data) > 0:
                    sample = data[0]
                    print(f"   📝 Sample: {dict(list(sample.items())[:5])}...")
                
                return data
            else:
                print(f"   ❌ No records found in {dataset['name']}")
                return []
                
        except Exception as e:
            print(f"   ❌ Error searching {dataset['name']}: {e}")
            return []
    
    def comprehensive_property_search(self, address: str = None, bin_number: str = None, 
                                    borough: str = None, block: str = None, lot: str = None) -> dict:
        """Comprehensive search using all available methods"""
        
        print(f"\n🚒 COMPREHENSIVE FDNY PROPERTY SEARCH")
        print("=" * 80)
        
        all_results = {}
        
        # Search by BIN if available
        if bin_number:
            bin_results = self.search_by_bin(bin_number)
            all_results.update(bin_results)
        
        # Search by block/lot if available
        if borough and block and lot:
            block_lot_results = self.search_by_block_lot(borough, block, lot)
            all_results.update(block_lot_results)
        
        # Search by address if available
        if address:
            address_results = self.search_by_address(address, borough)
            all_results.update(address_results)
        
        return all_results

def main():
    """Main function to test corrected FDNY searches"""
    
    if len(sys.argv) < 2:
        print("Usage: python corrected_fdny_search.py <search_type> <parameters>")
        print("\nSearch types:")
        print("  bin <bin_number>")
        print("  block_lot <borough> <block> <lot>")
        print("  address '<address>' [borough]")
        print("  comprehensive '<address>' [bin] [borough] [block] [lot]")
        print("\nExamples:")
        print("  python corrected_fdny_search.py bin 4433339")
        print("  python corrected_fdny_search.py block_lot MANHATTAN 1073 1")
        print("  python corrected_fdny_search.py address '140 West 28th Street' MANHATTAN")
        print("  python corrected_fdny_search.py comprehensive '140 West 28th Street' 4433339 MANHATTAN 1073 1")
        sys.exit(1)
    
    search_type = sys.argv[1].lower()
    searcher = CorrectedFDNYSearcher()
    
    if search_type == 'bin' and len(sys.argv) >= 3:
        bin_number = sys.argv[2]
        results = searcher.search_by_bin(bin_number)
        
    elif search_type == 'block_lot' and len(sys.argv) >= 5:
        borough, block, lot = sys.argv[2], sys.argv[3], sys.argv[4]
        results = searcher.search_by_block_lot(borough, block, lot)
        
    elif search_type == 'address' and len(sys.argv) >= 3:
        address = sys.argv[2]
        borough = sys.argv[3] if len(sys.argv) > 3 else None
        results = searcher.search_by_address(address, borough)
        
    elif search_type == 'comprehensive' and len(sys.argv) >= 3:
        address = sys.argv[2]
        bin_number = sys.argv[3] if len(sys.argv) > 3 else None
        borough = sys.argv[4] if len(sys.argv) > 4 else None
        block = sys.argv[5] if len(sys.argv) > 5 else None
        lot = sys.argv[6] if len(sys.argv) > 6 else None
        
        results = searcher.comprehensive_property_search(
            address=address, bin_number=bin_number, borough=borough, 
            block=block, lot=lot
        )
    else:
        print("❌ Invalid search type or insufficient parameters")
        return
    
    # Summary
    print(f"\n" + "="*80)
    print("📊 SEARCH RESULTS SUMMARY")
    print("="*80)
    
    total_records = 0
    for dataset, data in results.items():
        count = len(data) if data else 0
        status = "✅ FOUND" if count > 0 else "❌ NONE"
        print(f"{dataset}: {status} ({count} records)")
        total_records += count
    
    print(f"\n🎯 Total records found across all datasets: {total_records}")
    
    if total_records == 0:
        print("\n💡 SUGGESTIONS:")
        print("1. Try searching with different address formats") 
        print("2. Use block/lot numbers if available")
        print("3. Check that the property has FDNY-related violations or inspections")
        print("4. Note: Bureau of Fire Prevention datasets are historical (no longer updated)")

if __name__ == "__main__":
    main()