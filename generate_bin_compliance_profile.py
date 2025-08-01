#!/usr/bin/env python3
"""
Generate a comprehensive compliance profile for a property using its BIN
"""

import pandas as pd
from nyc_opendata_client import NYCOpenDataClient

def generate_bin_compliance_profile(bin_number):
    """
    Generate a comprehensive compliance profile for a property using its BIN
    
    Args:
        bin_number (str): Building Identification Number
    """
    print(f"Generating Compliance Profile for BIN: {bin_number}")
    print("=" * 60)
    
    client = NYCOpenDataClient.from_config()
    print("Client created with credentials from config.py.")
    
    # List of datasets to check
    datasets = [
        'hpd_violations',
        'dob_violations',
        'elevator_inspections',
        'boiler_inspections',
        'complaints_311',
        'dob_complaints',
        'dob_now_public_portal_filings',
        'dob_job_application_filings',
        'dob_permit_issuance'
    ]
    
    # Get BBL from BIN if possible
    bbl = None
    try:
        # Try elevator inspections first
        query = f"bin = '{bin_number}'"
        data = client.get_data('elevator_inspections', where=query, limit=1)
        
        if not data.empty:
            if 'bbl' in data.columns:
                bbl = data['bbl'].iloc[0]
                print(f"Found BBL: {bbl} from elevator inspections")
            elif 'block' in data.columns and 'lot' in data.columns:
                block = data['block'].iloc[0]
                lot = data['lot'].iloc[0]
                if 'borough' in data.columns:
                    borough = data['borough'].iloc[0]
                    print(f"Found Borough: {borough}, Block: {block}, Lot: {lot}")
    except Exception as e:
        print(f"Error getting BBL from elevator inspections: {e}")
    
    # Get property address
    property_address = None
    try:
        # Try HPD violations
        query = f"bin = '{bin_number}'"
        data = client.get_data('hpd_violations', where=query, limit=1)
        
        if not data.empty:
            if 'housenumber' in data.columns and 'streetname' in data.columns:
                house_number = data['housenumber'].iloc[0]
                street_name = data['streetname'].iloc[0]
                property_address = f"{house_number} {street_name}"
                print(f"Property Address: {property_address}")
    except Exception as e:
        print(f"Error getting property address: {e}")
        
    if not property_address:
        try:
            # Try DOB violations
            query = f"bin = '{bin_number}'"
            data = client.get_data('dob_violations', where=query, limit=1)
            
            if not data.empty:
                if 'house_number' in data.columns and 'street' in data.columns:
                    house_number = data['house_number'].iloc[0]
                    street_name = data['street'].iloc[0]
                    property_address = f"{house_number} {street_name}"
                    print(f"Property Address: {property_address}")
        except Exception as e:
            print(f"Error getting property address from DOB violations: {e}")
    
    # Check each dataset for records
    print("\n--- COMPLIANCE PROFILE ---")
    
    for dataset in datasets:
        print(f"\nChecking dataset: {dataset}")
        
        try:
            # Query by BIN
            query = f"bin = '{bin_number}' OR bin_number = '{bin_number}'"
            data = client.get_data(dataset, where=query, limit=100)
            
            if not data.empty:
                print(f"✓ Found {len(data)} records")
                
                # Display a subset of columns for readability
                if len(data) > 0:
                    # Select the most informative columns
                    if dataset == 'hpd_violations':
                        display_cols = ['violationid', 'housenumber', 'streetname', 'novdescription', 
                                       'inspectiondate', 'currentstatus', 'novtype']
                    elif dataset == 'dob_violations':
                        display_cols = ['violation_number', 'violation_type', 'violation_category', 
                                       'issue_date', 'violation_date', 'status']
                    elif dataset == 'elevator_inspections':
                        display_cols = ['device_number', 'device_type', 'device_status', 'status_date']
                    elif dataset == 'boiler_inspections':
                        display_cols = ['tracking_number', 'report_type', 'inspection_type', 
                                       'inspection_date', 'report_status']
                    elif dataset == 'complaints_311':
                        display_cols = ['complaint_type', 'descriptor', 'created_date', 'status']
                    elif dataset == 'dob_complaints':
                        display_cols = ['complaint_number', 'complaint_category', 'date_entered', 'status']
                    elif dataset == 'dob_now_public_portal_filings':
                        display_cols = ['filing_number', 'filing_status', 'filing_type', 'filing_date']
                    elif dataset == 'dob_job_application_filings':
                        display_cols = ['job', 'job_type', 'job_status', 'filing_date', 'approved']
                    elif dataset == 'dob_permit_issuance':
                        display_cols = ['permit_si_no', 'permit_type', 'permit_status', 'filing_date', 'issuance_date']
                    else:
                        # Default to first 5 columns
                        display_cols = list(data.columns)[:5]
                    
                    # Filter to only include columns that exist in the dataset
                    display_cols = [col for col in display_cols if col in data.columns]
                    
                    if display_cols:
                        print("\nSample data (up to 5 records):")
                        print(data[display_cols].head().to_string(index=False))
                    else:
                        print("\nSample data (first 5 columns):")
                        print(data.iloc[:, :5].head().to_string(index=False))
            else:
                print("No records found")
        except Exception as e:
            print(f"Error accessing dataset: {e}")
    
    print("\n" + "=" * 60)
    print("COMPLIANCE PROFILE SUMMARY")
    print("=" * 60)
    
    print(f"\nProperty Information:")
    print(f"BIN: {bin_number}")
    if property_address:
        print(f"Address: {property_address}")
    if bbl:
        print(f"BBL: {bbl}")
    
    print("\nRecommendation for test_whitestone_property.py:")
    print("BIN_NUMBER = '" + bin_number + "'")

if __name__ == "__main__":
    # BIN for the property found in our search
    BIN_NUMBER = "4433339"
    generate_bin_compliance_profile(BIN_NUMBER)
