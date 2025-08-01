#!/usr/bin/env python3
"""
NYC Open Data API Client
A comprehensive script to access NYC Open Data via Socrata API (SODA)
"""

import requests
# import pandas as pd  # Removed for deployment compatibility
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

class NYCOpenDataClient:
    """Client for accessing NYC Open Data via Socrata API"""
    
    def __init__(self, api_key_id: str = None, api_key_secret: str = None):
        """
        Initialize the NYC Open Data client
        
        Args:
            api_key_id: Your Socrata API Key ID (used for HTTP Basic Auth username).
            api_key_secret: Your Socrata API Key Secret (used for HTTP Basic Auth password).
        """
        self.base_url = "https://data.cityofnewyork.us/resource"
        self.auth = (api_key_id, api_key_secret) if api_key_id and api_key_secret else None
        self.session = requests.Session()
        
        # Dataset configurations
        self.datasets = {
            'boiler_inspections': {
                'id': '52dp-yji6',  # Corrected ID
                'name': 'DOB NOW: Safety Boiler',
                'description': 'DOB NOW safety data for boilers.'
            },
            'elevator_inspections': {
                'id': 'e5aq-a4j2',
                'name': 'Elevator Inspections',
                'description': 'DOB NOW Elevator Compliance data - inspection dates, device types, status, violations'
            },
            'dob_violations': {
                'id': '3h2n-5cm9',
                'name': 'DOB Violations',
                'description': 'Building code compliance data - violation types, dates, status, resolution'
            },
            'hpd_violations': {
                'id': 'wvxf-dwi5',
                'name': 'HPD Violations',
                'description': 'Housing Preservation & Development violations - class, description, status, dates'
            },
            'hpd_registrations': {
                'id': 'hv8p-yzbx',
                'name': 'HPD Registrations',
                'description': 'Property registration information'
            },
            'cooling_tower_registrations': {
                'id': 'y4fw-iqfr',
                'name': 'Cooling Tower Registrations',
                'description': 'Registration data for cooling towers'
            },
            'cooling_tower_inspections': {
                'id': 'n4c4-3e4h',
                'name': 'Cooling Tower Inspections',
                'description': 'Inspection dates, status, compliance information'
            },
            'complaints_311': {
                'id': 'erm2-nwe9',
                'name': '311 Complaints',
                'description': 'Citizen complaints about properties'
            },
            'building_complaints': {
                'id': 'eabe-havv',
                'name': 'Building Complaints',
                'description': 'DOB Complaints specific to building issues'
            },
            'fdny_violations': {
                'id': 'avgm-ztsb',
                'name': 'FDNY Violations (OATH ECB)',
                'description': 'FDNY violations from OATH hearings. Search by borough+block+lot or address. NO BIN support.',
                'search_fields': {
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no', 
                    'lot': 'violation_location_lot_no',
                    'house_number': 'violation_location_house',
                    'street_name': 'violation_location_street_name'
                }
            },
            'fdny_violations_simple': {
                'id': 'ktas-47y7',
                'name': 'FDNY Violations (Simplified)',
                'description': 'Simplified FDNY violations dataset. Search by borough+block+lot or address. NO BIN support.',
                'search_fields': {
                    'borough': 'violation_location_borough',
                    'block': 'violation_location_block_no',
                    'lot': 'violation_location_lot_no',
                    'house_number': 'violation_location_house'
                }
            },
            'fire_prevention_inspections': {
                'id': 'ssq6-fkht',
                'name': 'Bureau of Fire Prevention - Inspections (Historical)',
                'description': 'Historical fire prevention inspections. Search by BIN or address. HISTORICAL DATA ONLY.',
                'search_fields': {
                    'bin': 'BIN',
                    'address': 'PREM_ADDR',
                    'borough': 'BOROUGH'
                }
            },
            'fire_prevention_violations': {
                'id': 'bi53-yph3',
                'name': 'Bureau of Fire Prevention - Violation Orders (Historical)',
                'description': 'Historical fire prevention violation orders. Search by BIN or address. HISTORICAL DATA ONLY.',
                'search_fields': {
                    'bin': 'BIN',
                    'address': 'PREM_ADDR',
                    'borough': 'BOROUGH'
                }
            },
            'fire_prevention_summary': {
                'id': 'nvgj-hbht',
                'name': 'Bureau of Fire Prevention - Building Summary (Historical)',
                'description': 'Historical building summary with violation counts. Search by BIN or block+lot. HISTORICAL DATA ONLY.',
                'search_fields': {
                    'bin': 'BIN',
                    'block': 'BLOCK',
                    'lot': 'LOT',
                    'borough': 'BOROUGH'
                }
            },
            'certificate_of_occupancy': {
                'id': 'pkdm-hqz6',
                'name': 'DOB NOW: Certificate of Occupancy',
                'description': 'Certificate of Occupancy data - legal occupancy status, classifications, dates'
            },
            'electrical_permits': {
                'id': 'dm9a-ab7w',
                'name': 'DOB NOW: Electrical Permit Applications',
                'description': 'Electrical permit applications - electrical safety compliance, permits, inspections'
            }
        }
    
    @classmethod
    def from_config(cls):
        """
        Creates a client instance by loading credentials from config.py.
        Falls back to anonymous access if config is not found.
        """
        api_key_id = None
        api_key_secret = None
        try:
            from config import API_KEY_ID, API_KEY_SECRET
            api_key_id = API_KEY_ID
            api_key_secret = API_KEY_SECRET
            print("Client created with credentials from config.py.")
        except (ImportError, AttributeError):
            print("Client created for anonymous access. To increase rate limits, provide API credentials in config.py.")
        
        return cls(api_key_id=api_key_id, api_key_secret=api_key_secret)

    def _build_url(self, dataset_id: str, format_type: str = 'json') -> str:
        """Build the API endpoint URL"""
        return f"{self.base_url}/{dataset_id}.{format_type}"
    
    def _build_params(self, **kwargs) -> Dict:
        """Build query parameters"""
        params = {}
        
        # Add other parameters
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
        
        return params
    
    def get_data(self, dataset_key: str, limit: int = 1000, offset: int = 0, 
                 where: str = None, select: str = None, order: str = None,
                 format_type: str = 'json', **kwargs) -> List[Dict]:
        """
        Retrieve data from a specific dataset
        
        Args:
            dataset_key: Key from self.datasets (e.g., 'boiler_inspections')
            limit: Maximum number of records to return (default: 1000, max: 50000)
            offset: Number of records to skip (for pagination)
            where: SoQL WHERE clause for filtering
            select: SoQL SELECT clause for specific columns
            order: SoQL ORDER BY clause for sorting
            format_type: Response format ('json', 'csv', 'xml')
            **kwargs: Additional SoQL parameters
        
        Returns:
            DataFrame (if format_type='json') or raw data
        """
        if dataset_key not in self.datasets:
            raise ValueError(f"Unknown dataset: {dataset_key}. Available: {list(self.datasets.keys())}")
        
        dataset_id = self.datasets[dataset_key]['id']
        url = self._build_url(dataset_id, format_type)
        
        # Adjust timeout and limit for problematic datasets
        timeout = 30
        adjusted_limit = limit
        
        # Special handling for FDNY datasets (performance issues)
        if dataset_key.startswith('fdny_'):
            timeout = 60
            adjusted_limit = min(limit, 100)  # Reduce limit for FDNY datasets
        
        # Special handling for electrical permits (API errors)
        if dataset_key == 'electrical_permits':
            timeout = 45
        
        # Build parameters
        params = self._build_params(
            **{f'${k}': v for k, v in {
                'limit': adjusted_limit,
                'offset': offset,
                'where': where,
                'select': select,
                'order': order
            }.items() if v is not None},
            **kwargs
        )
        
        # Retry logic for problematic datasets
        max_retries = 3 if dataset_key in ['electrical_permits'] or dataset_key.startswith('fdny_') else 1
        
        for attempt in range(max_retries):
            try:
                # Use auth parameter for HTTP Basic Authentication if credentials are provided
                response = self.session.get(url, params=params, auth=self.auth, timeout=timeout)
                response.raise_for_status()
                
                if format_type == 'json':
                    data = response.json()
                    return data if data else []
                else:
                    return response.text
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    print(f"Timeout on attempt {attempt + 1} for {dataset_key}, retrying...")
                    time.sleep(2)
                    continue
                else:
                    print(f"Final timeout error for {dataset_key}: {e}")
                    return []
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400 and dataset_key == 'electrical_permits':
                    if attempt < max_retries - 1:
                        print(f"400 error on attempt {attempt + 1} for electrical permits, simplifying query...")
                        # Try with simpler select clause
                        if 'select' in params:
                            params['$select'] = 'filing_number, filing_date, filing_status, bin'
                        time.sleep(1)
                        continue
                    else:
                        print(f"Electrical permits API consistently returning 400 errors - may need column name updates")
                        return []
                else:
                    print(f"HTTP error for {dataset_key}: {e}")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data from {dataset_key}: {e}")
                return []
        
        return []
    
    def get_all_data(self, dataset_key: str, batch_size: int = 50000, 
                     max_records: int = None, **kwargs) -> List[Dict]:
        """
        Retrieve all data from a dataset using pagination
        
        Args:
            dataset_key: Key from self.datasets
            batch_size: Number of records per batch (max 50000)
            max_records: Maximum total records to retrieve
            **kwargs: Additional SoQL parameters
        
        Returns:
            Complete DataFrame with all records
        """
        all_data = []
        offset = 0
        
        print(f"Fetching data from {self.datasets[dataset_key]['name']}...")
        
        while True:
            current_limit = min(batch_size, max_records - len(all_data)) if max_records else batch_size
            
            df = self.get_data(dataset_key, limit=current_limit, offset=offset, **kwargs)
            
            if df is None or df.empty:
                break
                
            all_data.append(df)
            print(f"Fetched {len(df)} records (total: {sum(len(d) for d in all_data)})")
            
            if len(df) < current_limit:  # Last batch
                break
                
            if max_records and sum(len(d) for d in all_data) >= max_records:
                break
                
            offset += current_limit
            time.sleep(0.1)  # Be respectful to the API
        
        # Flatten list of lists into single list
        result = []
        for data_chunk in all_data:
            if isinstance(data_chunk, list):
                result.extend(data_chunk)
        return result if result else []
    
    def search_by_date_range(self, dataset_key: str, date_column: str, 
                           start_date: str, end_date: str, **kwargs) -> List[Dict]:
        """
        Search data within a specific date range
        
        Args:
            dataset_key: Key from self.datasets
            date_column: Name of the date column to filter on
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            **kwargs: Additional parameters
        
        Returns:
            Filtered DataFrame
        """
        where_clause = f"{date_column} between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        return self.get_data(dataset_key, where=where_clause, **kwargs)
    
    def get_recent_data(self, dataset_key: str, days_back: int = 30, 
                       date_column: str = 'created_date', **kwargs) -> List[Dict]:
        """
        Get recent data from the last N days
        
        Args:
            dataset_key: Key from self.datasets
            days_back: Number of days to look back
            date_column: Name of the date column
            **kwargs: Additional parameters
        
        Returns:
            Recent data DataFrame
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return self.search_by_date_range(
            dataset_key, date_column, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d'),
            **kwargs
        )
    
    def get_dataset_info(self, dataset_key: str = None) -> Dict:
        """
        Get information about available datasets
        
        Args:
            dataset_key: Specific dataset key, or None for all datasets
        
        Returns:
            Dataset information dictionary
        """
        if dataset_key:
            if dataset_key not in self.datasets:
                raise ValueError(f"Unknown dataset: {dataset_key}")
            return self.datasets[dataset_key]
        
        return self.datasets
    
    def count_records(self, dataset_key: str, where: str = None) -> int:
        """
        Count total records in a dataset
        
        Args:
            dataset_key: Key from self.datasets
            where: Optional WHERE clause for filtering
        
        Returns:
            Total number of records
        """
        df = self.get_data(dataset_key, select='count(*)', where=where, limit=1)
        return int(df.iloc[0, 0]) if not df.empty else 0
    
    def search_fdny_violations_by_location(self, borough: str, block: str = None, lot: str = None, 
                                         address: str = None, dataset_type: str = 'full') -> List[Dict]:
        """
        Search FDNY violations using correct column names and search strategies
        
        Args:
            borough: Borough name (MANHATTAN, BROOKLYN, QUEENS, BRONX, STATEN ISLAND)
            block: Block number (optional)
            lot: Lot number (optional, requires block)
            address: Street address like "140 West 28th Street" (optional)
            dataset_type: 'full' (avgm-ztsb) or 'simple' (ktas-47y7)
        
        Returns:
            DataFrame with FDNY violations or empty DataFrame if none found
        """
        
        dataset_key = 'fdny_violations' if dataset_type == 'full' else 'fdny_violations_simple'
        
        # Normalize borough name
        borough = borough.upper()
        borough_map = {
            'MN': 'MANHATTAN', 'MANHATTAN': 'MANHATTAN',
            'BK': 'BROOKLYN', 'BROOKLYN': 'BROOKLYN', 
            'QN': 'QUEENS', 'QUEENS': 'QUEENS',
            'BX': 'BRONX', 'BRONX': 'BRONX',
            'SI': 'STATEN ISLAND', 'STATEN ISLAND': 'STATEN ISLAND'
        }
        borough_normalized = borough_map.get(borough, borough)
        
        where_parts = [f"violation_location_borough = '{borough_normalized}'"]
        
        # Add block/lot if provided
        if block and lot:
            block_padded = block.zfill(5)  # Pad with leading zeros
            lot_padded = lot.zfill(4)
            where_parts.extend([
                f"violation_location_block_no = '{block_padded}'",
                f"violation_location_lot_no = '{lot_padded}'"
            ])
        
        # Add address search if provided
        if address:
            address_parts = address.strip().split(' ')
            if address_parts:
                house_number = address_parts[0]
                where_parts.append(f"violation_location_house = '{house_number}'")
                
                if len(address_parts) > 1:
                    street_name = ' '.join(address_parts[1:]).upper()
                    where_parts.append(f"UPPER(violation_location_street_name) LIKE '%{street_name}%'")
        
        where_clause = ' AND '.join(where_parts)
        
        try:
            return self.get_data(
                dataset_key,
                where=where_clause,
                select="ticket_number, violation_date, violation_location_borough, " +
                       "violation_location_block_no, violation_location_lot_no, " +
                       "violation_location_house, violation_location_street_name, " +
                       "total_violation_amount, hearing_status, violation_description",
                order="violation_date DESC",
                limit=100
            )
        except Exception as e:
            print(f"Error searching FDNY violations: {e}")
            return []
    
    def search_fire_prevention_by_bin(self, bin_number: str) -> Dict[str, List[Dict]]:
        """
        Search Bureau of Fire Prevention datasets by BIN (historical data only)
        
        Args:
            bin_number: Building Identification Number
            
        Returns:
            Dictionary with results from different fire prevention datasets
        """
        
        results = {}
        fire_prev_datasets = ['fire_prevention_inspections', 'fire_prevention_violations', 'fire_prevention_summary']
        
        print(f"Searching historical fire prevention data for BIN {bin_number}...")
        print("Note: These datasets contain historical data only (no longer updated)")
        
        for dataset_key in fire_prev_datasets:
            try:
                data = self.get_data(
                    dataset_key,
                    where=f"BIN = '{bin_number}'",
                    limit=100
                )
                
                if data is not None and not data.empty:
                    results[dataset_key] = data
                    print(f"  Found {len(data)} records in {self.datasets[dataset_key]['name']}")
                else:
                    results[dataset_key] = []
                    
            except Exception as e:
                print(f"  Error searching {dataset_key}: {e}")
                results[dataset_key] = []
        
        return results
    
    def test_electrical_permits_columns(self, bin_number: str = None) -> Dict:
        """
        Test electrical permits dataset to identify correct column names
        
        Args:
            bin_number: Optional BIN to test with specific search
            
        Returns:
            Dictionary with column information and sample data
        """
        print("Testing electrical permits dataset for correct column names...")
        
        try:
            # First, get a small sample without filters to see available columns
            sample_data = self.get_data(
                'electrical_permits',
                limit=5,
                select=None  # Get all columns
            )
            
            result = {
                'available_columns': list(sample_data.columns) if not sample_data.empty else [],
                'sample_data': sample_data.head(2).to_dict('records') if not sample_data.empty else [],
                'total_records': len(sample_data) if not sample_data.empty else 0
            }
            
            if bin_number and not sample_data.empty:
                # Test search by BIN if provided
                bin_search = self.get_data(
                    'electrical_permits',
                    where=f"bin = '{bin_number}'",
                    limit=10
                )
                result['bin_search_results'] = len(bin_search) if bin_search is not None else 0
                result['bin_search_sample'] = bin_search.head(2).to_dict('records') if not bin_search.empty else []
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'available_columns': [],
                'sample_data': [],
                'total_records': 0
            }


# Example usage and utility functions
def main():
    """Example usage of the NYC Open Data client"""
    
    # Initialize client (add your app token here)
    APP_TOKEN = "YOUR_APP_TOKEN_HERE"  # Replace with your actual token
    client = NYCOpenDataClient(app_token=APP_TOKEN)
    
    print("NYC Open Data Client - Available Datasets:")
    print("=" * 50)
    
    # Display available datasets
    for key, info in client.get_dataset_info().items():
        print(f"{key}: {info['name']}")
        print(f"  Description: {info['description']}")
        print(f"  Dataset ID: {info['id']}")
        print()
    
    # Example 1: Get recent 311 complaints
    print("Example 1: Recent 311 Complaints")
    print("-" * 30)
    complaints = client.get_recent_data('complaints_311', days_back=7, limit=100)
    if not complaints.empty:
        print(f"Found {len(complaints)} recent complaints")
        print(complaints[['created_date', 'complaint_type', 'borough']].head())
    
    # Example 2: Search boiler inspections by date range
    print("\nExample 2: Boiler Inspections in Date Range")
    print("-" * 45)
    boiler_data = client.search_by_date_range(
        'boiler_inspections',
        'inspection_date',
        '2024-01-01',
        '2024-12-31',
        limit=50
    )
    if not boiler_data.empty:
        print(f"Found {len(boiler_data)} boiler inspections")
        print(boiler_data.head())
    
    # Example 3: Get violations in Manhattan
    print("\nExample 3: HPD Violations in Manhattan")
    print("-" * 35)
    manhattan_violations = client.get_data(
        'hpd_violations',
        where="boroid = '1'",  # Manhattan
        limit=100
    )
    if not manhattan_violations.empty:
        print(f"Found {len(manhattan_violations)} violations in Manhattan")
        print(manhattan_violations.head())
    
    # Example 4: Count total records
    print("\nExample 4: Dataset Record Counts")
    print("-" * 30)
    for dataset_key in ['complaints_311', 'dob_violations', 'hpd_violations']:
        try:
            count = client.count_records(dataset_key)
            print(f"{dataset_key}: {count:,} records")
        except Exception as e:
            print(f"{dataset_key}: Error counting records - {e}")


if __name__ == "__main__":
    main()
