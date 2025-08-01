#!/usr/bin/env python3
"""
NYC Open Data API Client
A comprehensive script to access NYC Open Data via Socrata API (SODA)
"""

import requests
import pandas as pd
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
            'fire_safety_inspections': {
                'id': 'tsak-vtv3',
                'name': 'FDNY Fire Safety Inspections',
                'description': 'FDNY inspection data, including dates, violations, and compliance status.'
            },
            'fdny_violations': {
                'id': 'avgm-ztsb',
                'name': 'FDNY Violations',
                'description': 'Violation tickets issued by the FDNY.'
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
                 format_type: str = 'json', **kwargs) -> Union[pd.DataFrame, List[Dict]]:
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
        
        # Build parameters
        params = self._build_params(
            **{f'${k}': v for k, v in {
                'limit': limit,
                'offset': offset,
                'where': where,
                'select': select,
                'order': order
            }.items() if v is not None},
            **kwargs
        )
        
        try:
            # Use auth parameter for HTTP Basic Authentication if credentials are provided
            response = self.session.get(url, params=params, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            if format_type == 'json':
                data = response.json()
                return pd.DataFrame(data) if data else pd.DataFrame()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def get_all_data(self, dataset_key: str, batch_size: int = 50000, 
                     max_records: int = None, **kwargs) -> pd.DataFrame:
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
        
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    
    def search_by_date_range(self, dataset_key: str, date_column: str, 
                           start_date: str, end_date: str, **kwargs) -> pd.DataFrame:
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
                       date_column: str = 'created_date', **kwargs) -> pd.DataFrame:
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
