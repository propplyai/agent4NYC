#!/usr/bin/env python3
"""
Generate a comprehensive compliance report for a NYC property
using both BIN and BBL identifiers.

This script creates a detailed report of property compliance data
from multiple NYC Open Data sources including:
- DOB violations
- HPD violations
- Boiler inspections
- Elevator inspections
- 311 complaints
- FDNY violations (if available)
"""

import pandas as pd
import json
from datetime import datetime
from nyc_opendata_client import NYCOpenDataClient

# --- Property Identifiers ---
# Property found in our search for 810 Whitestone Expressway
# Address: 13-22 147 STREET, QUEENS, NY 11357
BOROUGH = 'QUEENS'  # Equivalent to '4' in some datasets
BLOCK = '4465'
LOT = '175'
BIN_NUMBER = '4433339'

def get_property_address(client, bin_number=None, boro=None, block=None, lot=None):
    """Get the property address using BIN or BBL"""
    print("Finding property address...")
    
    # Try using BIN first if available
    if bin_number:
        try:
            query = f"bin = '{bin_number}'"
            data = client.get_data('hpd_violations', where=query, limit=1)
            
            if not data.empty:
                if 'housenumber' in data.columns and 'streetname' in data.columns:
                    house_number = data['housenumber'].iloc[0]
                    street_name = data['streetname'].iloc[0]
                    address = f"{house_number} {street_name}"
                    return address
        except Exception as e:
            print(f"Error getting address by BIN: {e}")
    
    # Try using BBL if BIN didn't work
    if boro and block and lot:
        try:
            query = f"boro='{boro}' AND block='{block}' AND lot='{lot}'"
            data = client.get_data('hpd_violations', where=query, limit=1)
            
            if not data.empty:
                if 'housenumber' in data.columns and 'streetname' in data.columns:
                    house_number = data['housenumber'].iloc[0]
                    street_name = data['streetname'].iloc[0]
                    address = f"{house_number} {street_name}"
                    return address
        except Exception as e:
            print(f"Error getting address by BBL: {e}")
    
    return None

def get_owner_info(client, bin_number=None, boro=None, block=None, lot=None):
    """Get property owner information"""
    print("Finding owner information...")
    
    # Try HPD registrations
    try:
        if boro and block and lot:
            query = f"boroid='{boro}' AND block='{block}' AND lot='{lot}'"
            data = client.get_data('hpd_registrations', where=query, limit=1)
            
            if not data.empty:
                owner_info = {}
                
                # Check for owner name columns
                if 'ownername' in data.columns:
                    owner_info['name'] = data['ownername'].iloc[0]
                elif 'ownerfirstname' in data.columns and 'ownerlastname' in data.columns:
                    owner_info['name'] = f"{data['ownerfirstname'].iloc[0]} {data['ownerlastname'].iloc[0]}"
                
                # Check for owner address columns
                address_parts = []
                for col in ['ownerhousenumber', 'ownerstreetname', 'ownercity', 'ownerstate', 'ownerzip']:
                    if col in data.columns and not pd.isna(data[col].iloc[0]):
                        address_parts.append(str(data[col].iloc[0]))
                
                if address_parts:
                    owner_info['address'] = " ".join(address_parts)
                
                # Check for owner phone
                if 'ownerphone' in data.columns:
                    owner_info['phone'] = data['ownerphone'].iloc[0]
                
                return owner_info
    except Exception as e:
        print(f"Error getting owner info: {e}")
    
    # Try boiler inspections as fallback
    try:
        if bin_number:
            query = f"bin_number='{bin_number}'"
            data = client.get_data('boiler_inspections', where=query, limit=1)
            
            if not data.empty:
                owner_info = {}
                
                # Check for owner name columns
                if 'owner_first_name' in data.columns and 'owner_last_name' in data.columns:
                    owner_info['name'] = f"{data['owner_first_name'].iloc[0]} {data['owner_last_name'].iloc[0]}"
                
                # Check for owner business name
                if 'owner_business_name' in data.columns:
                    owner_info['business'] = data['owner_business_name'].iloc[0]
                
                return owner_info
    except Exception as e:
        print(f"Error getting owner info from boiler inspections: {e}")
    
    return None

def get_dataset_records(client, dataset_name, bin_number=None, boro=None, block=None, lot=None, address=None):
    """Get records from a dataset using BIN, BBL, or address"""
    print(f"Checking dataset: {dataset_name}")
    results = {'found': False, 'count': 0, 'records': None, 'error': None}
    
    # Define dataset-specific configurations
    dataset_config = {
        'hpd_violations': {
            'bin_column': 'bin',
            'bbl_columns': {'boro': 'boro', 'block': 'block', 'lot': 'lot'},
            'address_columns': {'house': 'housenumber', 'street': 'streetname'},
            'display_cols': ['violationid', 'inspectiondate', 'novdescription', 'currentstatus']
        },
        'dob_violations': {
            'bin_column': 'bin',
            'bbl_columns': {'boro': 'boro', 'block': 'block', 'lot': 'lot'},
            'address_columns': {'house': 'house_number', 'street': 'street'},
            'display_cols': ['violation_number', 'issue_date', 'violation_type', 'status']
        },
        'elevator_inspections': {
            'bin_column': 'bin',
            'bbl_columns': None,
            'address_columns': {'house': 'house_number', 'street': 'street_name'},
            'display_cols': ['device_number', 'device_type', 'device_status', 'status_date']
        },
        'boiler_inspections': {
            'bin_column': 'bin_number',
            'bbl_columns': None,
            'address_columns': None,
            'display_cols': ['tracking_number', 'inspection_type', 'inspection_date', 'report_status']
        },
        'complaints_311': {
            'bin_column': None,
            'bbl_columns': None,
            'address_columns': {'address': 'incident_address'},
            'display_cols': ['complaint_type', 'descriptor', 'created_date', 'status']
        },
        'fdny_violations': {
            'bin_column': None,
            'bbl_columns': {'boro': 'borough', 'block': 'block', 'lot': 'lot'},
            'address_columns': {'address': 'address'},
            'display_cols': ['violation_number', 'violation_date', 'violation_description', 'violation_status']
        }
    }
    
    # Check if dataset is supported
    if dataset_name not in dataset_config:
        results['error'] = f"Dataset {dataset_name} not supported"
        return results
    
    config = dataset_config[dataset_name]
    
    # Try BIN first if available
    if bin_number and config['bin_column']:
        try:
            query = f"{config['bin_column']} = '{bin_number}'"
            data = client.get_data(dataset_name, where=query, limit=100)
            
            if not data.empty:
                results['found'] = True
                results['count'] = len(data)
                
                # Get display columns
                display_cols = [col for col in config['display_cols'] if col in data.columns]
                if display_cols:
                    results['records'] = data[display_cols].head(5).to_dict('records')
                else:
                    # Fallback to first few columns
                    results['records'] = data.iloc[:, :5].head(5).to_dict('records')
                
                return results
        except Exception as e:
            results['error'] = f"Error searching by BIN: {e}"
    
    # Try BBL if BIN didn't work
    if boro and block and lot and config['bbl_columns']:
        try:
            boro_col = config['bbl_columns']['boro']
            block_col = config['bbl_columns']['block']
            lot_col = config['bbl_columns']['lot']
            
            query = f"{boro_col}='{boro}' AND {block_col}='{block}' AND {lot_col}='{lot}'"
            data = client.get_data(dataset_name, where=query, limit=100)
            
            if not data.empty:
                results['found'] = True
                results['count'] = len(data)
                
                # Get display columns
                display_cols = [col for col in config['display_cols'] if col in data.columns]
                if display_cols:
                    results['records'] = data[display_cols].head(5).to_dict('records')
                else:
                    # Fallback to first few columns
                    results['records'] = data.iloc[:, :5].head(5).to_dict('records')
                
                return results
        except Exception as e:
            results['error'] = f"Error searching by BBL: {e}"
    
    # Try address as last resort
    if address and config['address_columns']:
        try:
            if 'address' in config['address_columns']:
                # Full address search
                address_col = config['address_columns']['address']
                query = f"{address_col} LIKE '%{address}%'"
            elif 'house' in config['address_columns'] and 'street' in config['address_columns']:
                # Split address into house number and street
                house_parts = address.split(' ', 1)
                if len(house_parts) == 2:
                    house_num = house_parts[0]
                    street = house_parts[1]
                    
                    house_col = config['address_columns']['house']
                    street_col = config['address_columns']['street']
                    query = f"{house_col} = '{house_num}' AND {street_col} LIKE '%{street}%'"
                else:
                    return results
            else:
                return results
            
            data = client.get_data(dataset_name, where=query, limit=100)
            
            if not data.empty:
                results['found'] = True
                results['count'] = len(data)
                
                # Get display columns
                display_cols = [col for col in config['display_cols'] if col in data.columns]
                if display_cols:
                    results['records'] = data[display_cols].head(5).to_dict('records')
                else:
                    # Fallback to first few columns
                    results['records'] = data.iloc[:, :5].head(5).to_dict('records')
        except Exception as e:
            results['error'] = f"Error searching by address: {e}"
    
    return results

def generate_compliance_report():
    """Generate a comprehensive compliance report for the property"""
    print(f"Generating Compliance Report")
    print(f"BIN: {BIN_NUMBER}")
    print(f"Borough: {BOROUGH}, Block: {BLOCK}, Lot: {LOT}")
    print("=" * 60)
    
    # Initialize client
    client = NYCOpenDataClient.from_config()
    print("Client created with credentials from config.py.")
    
    # Get property address
    address = get_property_address(client, BIN_NUMBER, BOROUGH, BLOCK, LOT)
    if address:
        print(f"Property Address: {address}")
    
    # Get owner information
    owner_info = get_owner_info(client, BIN_NUMBER, BOROUGH, BLOCK, LOT)
    
    # Initialize report
    report = {
        'property_info': {
            'bin': BIN_NUMBER,
            'borough': BOROUGH,
            'block': BLOCK,
            'lot': LOT,
            'address': address,
            'owner': owner_info
        },
        'compliance_data': {},
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Datasets to check
    datasets = [
        'hpd_violations',
        'dob_violations',
        'boiler_inspections',
        'elevator_inspections',
        'complaints_311',
        'fdny_violations'
    ]
    
    # Check each dataset
    print("\n--- COMPLIANCE DATA ---")
    
    for dataset in datasets:
        results = get_dataset_records(client, dataset, BIN_NUMBER, BOROUGH, BLOCK, LOT, address)
        
        if results['found']:
            print(f"✓ {dataset}: Found {results['count']} records")
            report['compliance_data'][dataset] = {
                'count': results['count'],
                'sample_records': results['records']
            }
        elif results['error']:
            print(f"✗ {dataset}: Error - {results['error']}")
            report['compliance_data'][dataset] = {
                'count': 0,
                'error': results['error']
            }
        else:
            print(f"✗ {dataset}: No records found")
            report['compliance_data'][dataset] = {
                'count': 0
            }
    
    # Generate summary
    print("\n" + "=" * 60)
    print("COMPLIANCE REPORT SUMMARY")
    print("=" * 60)
    
    print(f"\nProperty Information:")
    print(f"BIN: {BIN_NUMBER}")
    print(f"Borough: {BOROUGH}, Block: {BLOCK}, Lot: {LOT}")
    if address:
        print(f"Address: {address}")
    
    if owner_info:
        print("\nOwner Information:")
        for key, value in owner_info.items():
            print(f"{key.title()}: {value}")
    
    print("\nCompliance Summary:")
    for dataset, data in report['compliance_data'].items():
        if data.get('count', 0) > 0:
            print(f"- {dataset}: {data['count']} records")
        else:
            print(f"- {dataset}: No records")
    
    # Save report to file
    report_file = f"compliance_report_BIN{BIN_NUMBER}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull report saved to {report_file}")

if __name__ == "__main__":
    generate_compliance_report()
