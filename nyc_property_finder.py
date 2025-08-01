#!/usr/bin/env python3
"""
NYC Property Finder and Compliance Reporter
------------------------------------------
This script allows searching for NYC properties by address and 
generating comprehensive compliance reports using NYC Open Data.

Usage:
    python nyc_property_finder.py --address "810 Whitestone Expressway" --zip "11357"
    
    or run without arguments for interactive mode:
    python nyc_property_finder.py
"""

import argparse
import json
import pandas as pd
from datetime import datetime
from nyc_opendata_client import NYCOpenDataClient

def search_property_by_address(client, address, zip_code=None):
    """
    Search for a property by address across multiple datasets
    
    Args:
        client: NYCOpenDataClient instance
        address: Address to search for
        zip_code: Optional ZIP code to narrow search
    
    Returns:
        List of potential property matches with their identifiers
    """
    print(f"Searching for property: {address}")
    if zip_code:
        print(f"ZIP Code: {zip_code}")
    print("-" * 60)
    
    # Normalize address for search
    address = address.upper().strip()
    
    # Prepare search components
    address_parts = address.split(' ')
    street_number = address_parts[0] if address_parts else ""
    street_name = ' '.join(address_parts[1:]) if len(address_parts) > 1 else ""
    
    # Datasets to search in priority order
    datasets = [
        'hpd_violations',
        'dob_violations',
        'boiler_inspections',
        'elevator_inspections',
        'hpd_registrations'
    ]
    
    # Dataset-specific search configurations
    dataset_config = {
        'hpd_violations': {
            'address_columns': {'house': 'housenumber', 'street': 'streetname', 'zip': 'zip'},
            'id_columns': ['bin', 'boro', 'block', 'lot']
        },
        'dob_violations': {
            'address_columns': {'house': 'house_number', 'street': 'street', 'zip': 'zip_code'},
            'id_columns': ['bin', 'boro', 'block', 'lot']
        },
        'boiler_inspections': {
            'address_columns': {'house': 'house_number', 'street': 'street_name', 'zip': 'zip_code'},
            'id_columns': ['bin_number', 'boiler_id']
        },
        'elevator_inspections': {
            'address_columns': {'house': 'house_number', 'street': 'street_name', 'zip': 'zip_code'},
            'id_columns': ['bin', 'block', 'lot', 'borough']
        },
        'hpd_registrations': {
            'address_columns': {'house': 'housenumber', 'street': 'streetname', 'zip': 'zip'},
            'id_columns': ['bin', 'boroid', 'block', 'lot']
        }
    }
    
    # Store potential matches
    potential_matches = []
    
    # Search each dataset
    for dataset in datasets:
        print(f"\nSearching in {dataset}...")
        
        if dataset not in dataset_config:
            print(f"No search configuration for {dataset}, skipping.")
            continue
        
        config = dataset_config[dataset]
        
        # Try different search strategies
        search_strategies = []
        
        # Strategy 1: Full address search
        if 'house' in config['address_columns'] and 'street' in config['address_columns']:
            house_col = config['address_columns']['house']
            street_col = config['address_columns']['street']
            
            # Exact match on house number and street name
            if street_number and street_name:
                query = f"{house_col} = '{street_number}' AND {street_col} LIKE '%{street_name}%'"
                if zip_code and 'zip' in config['address_columns']:
                    zip_col = config['address_columns']['zip']
                    query += f" AND {zip_col} = '{zip_code}'"
                search_strategies.append(('exact_match', query))
            
            # Partial match on street name only
            if street_name:
                query = f"{street_col} LIKE '%{street_name}%'"
                if zip_code and 'zip' in config['address_columns']:
                    zip_col = config['address_columns']['zip']
                    query += f" AND {zip_col} = '{zip_code}'"
                search_strategies.append(('street_match', query))
        
        # Try each search strategy
        for strategy_name, query in search_strategies:
            try:
                print(f"  Trying {strategy_name} strategy...")
                data = client.get_data(dataset, where=query, limit=10)
                
                if not data.empty:
                    print(f"  ✓ Found {len(data)} potential matches")
                    
                    # Extract property identifiers
                    for _, row in data.iterrows():
                        match = {'dataset': dataset, 'strategy': strategy_name}
                        
                        # Get address
                        if 'house' in config['address_columns'] and 'street' in config['address_columns']:
                            house_col = config['address_columns']['house']
                            street_col = config['address_columns']['street']
                            if house_col in row and street_col in row:
                                match['address'] = f"{row[house_col]} {row[street_col]}"
                        
                        # Get identifiers
                        for id_col in config['id_columns']:
                            if id_col in row:
                                match[id_col] = row[id_col]
                        
                        # Add to potential matches if it has minimum required identifiers
                        if ('bin' in match or 'bin_number' in match) or ('boro' in match and 'block' in match and 'lot' in match):
                            # Check if this match is already in our list (avoid duplicates)
                            is_duplicate = False
                            for existing in potential_matches:
                                if (('bin' in match and 'bin' in existing and match['bin'] == existing['bin']) or
                                    ('bin_number' in match and 'bin_number' in existing and match['bin_number'] == existing['bin_number']) or
                                    ('boro' in match and 'block' in match and 'lot' in match and
                                     'boro' in existing and 'block' in existing and 'lot' in existing and
                                     match['boro'] == existing['boro'] and 
                                     match['block'] == existing['block'] and
                                     match['lot'] == existing['lot'])):
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                potential_matches.append(match)
                    
                    # If we found matches, no need to try other strategies for this dataset
                    if potential_matches:
                        break
                else:
                    print("  No matches found with this strategy")
            except Exception as e:
                print(f"  Error with {strategy_name} strategy: {e}")
    
    # Print summary of potential matches
    if potential_matches:
        print("\n" + "=" * 60)
        print(f"Found {len(potential_matches)} potential property matches:")
        
        for i, match in enumerate(potential_matches, 1):
            print(f"\nMatch #{i}:")
            if 'address' in match:
                print(f"  Address: {match['address']}")
            
            print("  Identifiers:")
            for key, value in match.items():
                if key not in ['dataset', 'strategy', 'address']:
                    print(f"    {key}: {value}")
            
            print(f"  Found in: {match['dataset']} using {match['strategy']} strategy")
    else:
        print("\nNo property matches found.")
    
    return potential_matches

def get_property_compliance(client, bin_number=None, boro=None, block=None, lot=None):
    """
    Generate a compliance report for a property using BIN or BBL
    
    Args:
        client: NYCOpenDataClient instance
        bin_number: Building Identification Number
        boro: Borough name or code
        block: Block number
        lot: Lot number
    
    Returns:
        Dictionary with compliance data
    """
    if not bin_number and not (boro and block and lot):
        print("Error: Either BIN or BBL (Borough, Block, Lot) must be provided")
        return None
    
    print("\nGenerating compliance report...")
    print("-" * 60)
    
    # Get property address
    address = None
    if bin_number:
        try:
            query = f"bin = '{bin_number}'"
            data = client.get_data('hpd_violations', where=query, limit=1)
            
            if not data.empty:
                if 'housenumber' in data.columns and 'streetname' in data.columns:
                    house_number = data['housenumber'].iloc[0]
                    street_name = data['streetname'].iloc[0]
                    address = f"{house_number} {street_name}"
                    print(f"Property Address: {address}")
        except Exception as e:
            print(f"Error getting address by BIN: {e}")
    
    if not address and boro and block and lot:
        try:
            query = f"boro='{boro}' AND block='{block}' AND lot='{lot}'"
            data = client.get_data('hpd_violations', where=query, limit=1)
            
            if not data.empty:
                if 'housenumber' in data.columns and 'streetname' in data.columns:
                    house_number = data['housenumber'].iloc[0]
                    street_name = data['streetname'].iloc[0]
                    address = f"{house_number} {street_name}"
                    print(f"Property Address: {address}")
        except Exception as e:
            print(f"Error getting address by BBL: {e}")
    
    # Initialize report
    report = {
        'property_info': {
            'bin': bin_number,
            'borough': boro,
            'block': block,
            'lot': lot,
            'address': address
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
    
    # Dataset-specific configurations
    dataset_config = {
        'hpd_violations': {
            'bin_column': 'bin',
            'bbl_columns': {'boro': 'boro', 'block': 'block', 'lot': 'lot'},
            'display_cols': ['violationid', 'inspectiondate', 'novdescription', 'currentstatus']
        },
        'dob_violations': {
            'bin_column': 'bin',
            'bbl_columns': {'boro': 'boro', 'block': 'block', 'lot': 'lot'},
            'display_cols': ['violation_number', 'issue_date', 'violation_type', 'status']
        },
        'elevator_inspections': {
            'bin_column': 'bin',
            'bbl_columns': None,
            'display_cols': ['device_number', 'device_type', 'device_status', 'status_date']
        },
        'boiler_inspections': {
            'bin_column': 'bin_number',
            'bbl_columns': None,
            'display_cols': ['tracking_number', 'inspection_type', 'inspection_date', 'report_status']
        },
        'complaints_311': {
            'bin_column': None,
            'bbl_columns': None,
            'address_search': True,
            'display_cols': ['complaint_type', 'descriptor', 'created_date', 'status']
        },
        'fdny_violations': {
            'bin_column': None,
            'bbl_columns': {'boro': 'borough', 'block': 'block', 'lot': 'lot'},
            'address_search': True,
            'display_cols': ['violation_number', 'violation_date', 'violation_description', 'violation_status']
        }
    }
    
    # Check each dataset
    print("\n--- COMPLIANCE DATA ---")
    
    for dataset in datasets:
        print(f"\nChecking dataset: {dataset}")
        
        if dataset not in dataset_config:
            print(f"No configuration for {dataset}, skipping.")
            continue
        
        config = dataset_config[dataset]
        found_data = False
        
        # Try BIN first if available
        if bin_number and config['bin_column']:
            try:
                query = f"{config['bin_column']} = '{bin_number}'"
                data = client.get_data(dataset, where=query, limit=100)
                
                if not data.empty:
                    found_data = True
                    count = len(data)
                    print(f"✓ Found {count} records using BIN")
                    
                    # Get display columns
                    display_cols = [col for col in config['display_cols'] if col in data.columns]
                    if display_cols:
                        sample_data = data[display_cols].head(5).to_dict('records')
                    else:
                        sample_data = data.iloc[:, :5].head(5).to_dict('records')
                    
                    report['compliance_data'][dataset] = {
                        'count': count,
                        'sample_records': sample_data
                    }
            except Exception as e:
                print(f"Error searching by BIN: {e}")
        
        # Try BBL if BIN didn't work
        if not found_data and boro and block and lot and config['bbl_columns']:
            try:
                boro_col = config['bbl_columns']['boro']
                block_col = config['bbl_columns']['block']
                lot_col = config['bbl_columns']['lot']
                
                query = f"{boro_col}='{boro}' AND {block_col}='{block}' AND {lot_col}='{lot}'"
                data = client.get_data(dataset, where=query, limit=100)
                
                if not data.empty:
                    found_data = True
                    count = len(data)
                    print(f"✓ Found {count} records using BBL")
                    
                    # Get display columns
                    display_cols = [col for col in config['display_cols'] if col in data.columns]
                    if display_cols:
                        sample_data = data[display_cols].head(5).to_dict('records')
                    else:
                        sample_data = data.iloc[:, :5].head(5).to_dict('records')
                    
                    report['compliance_data'][dataset] = {
                        'count': count,
                        'sample_records': sample_data
                    }
            except Exception as e:
                print(f"Error searching by BBL: {e}")
        
        # Try address as last resort
        if not found_data and address and config.get('address_search', False):
            try:
                query = f"address LIKE '%{address}%' OR incident_address LIKE '%{address}%'"
                data = client.get_data(dataset, where=query, limit=100)
                
                if not data.empty:
                    found_data = True
                    count = len(data)
                    print(f"✓ Found {count} records using address")
                    
                    # Get display columns
                    display_cols = [col for col in config['display_cols'] if col in data.columns]
                    if display_cols:
                        sample_data = data[display_cols].head(5).to_dict('records')
                    else:
                        sample_data = data.iloc[:, :5].head(5).to_dict('records')
                    
                    report['compliance_data'][dataset] = {
                        'count': count,
                        'sample_records': sample_data
                    }
            except Exception as e:
                print(f"Error searching by address: {e}")
        
        if not found_data:
            print("No records found")
            report['compliance_data'][dataset] = {
                'count': 0
            }
    
    # Print summary
    print("\n" + "=" * 60)
    print("COMPLIANCE REPORT SUMMARY")
    print("=" * 60)
    
    print(f"\nProperty Information:")
    if bin_number:
        print(f"BIN: {bin_number}")
    if boro and block and lot:
        print(f"Borough: {boro}, Block: {block}, Lot: {lot}")
    if address:
        print(f"Address: {address}")
    
    print("\nCompliance Summary:")
    for dataset, data in report['compliance_data'].items():
        if data.get('count', 0) > 0:
            print(f"- {dataset}: {data['count']} records")
        else:
            print(f"- {dataset}: No records")
    
    return report

def main():
    """Main function to run the property finder"""
    parser = argparse.ArgumentParser(description='NYC Property Finder and Compliance Reporter')
    parser.add_argument('--address', help='Property address to search for')
    parser.add_argument('--zip', help='ZIP code to narrow search')
    parser.add_argument('--bin', help='Building Identification Number (if known)')
    parser.add_argument('--borough', help='Borough name or code')
    parser.add_argument('--block', help='Block number')
    parser.add_argument('--lot', help='Lot number')
    parser.add_argument('--output', help='Output file for compliance report (JSON)')
    
    args = parser.parse_args()
    
    # Initialize client
    client = NYCOpenDataClient.from_config()
    print("NYC Property Finder initialized with credentials from config.py")
    
    # Interactive mode if no arguments provided
    if not (args.address or args.bin or (args.borough and args.block and args.lot)):
        print("\n" + "=" * 60)
        print("NYC PROPERTY FINDER - INTERACTIVE MODE")
        print("=" * 60)
        
        search_type = input("\nSearch by (1) Address or (2) Property ID? [1/2]: ")
        
        if search_type == "1":
            address = input("Enter property address: ")
            zip_code = input("Enter ZIP code (optional): ")
            
            # Search for property
            matches = search_property_by_address(client, address, zip_code)
            
            if matches:
                # Ask which match to use for compliance report
                print("\nWhich property would you like to generate a compliance report for?")
                for i, match in enumerate(matches, 1):
                    addr = match.get('address', 'Unknown address')
                    print(f"{i}. {addr}")
                
                choice = input("\nEnter number (or 0 to exit): ")
                try:
                    choice = int(choice)
                    if 1 <= choice <= len(matches):
                        match = matches[choice - 1]
                        
                        # Generate compliance report
                        bin_number = match.get('bin') or match.get('bin_number')
                        boro = match.get('boro') or match.get('boroid') or match.get('borough')
                        block = match.get('block')
                        lot = match.get('lot')
                        
                        report = get_property_compliance(client, bin_number, boro, block, lot)
                        
                        # Save report
                        if report:
                            output_file = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(output_file, 'w') as f:
                                json.dump(report, f, indent=2)
                            print(f"\nFull report saved to {output_file}")
                except ValueError:
                    print("Invalid choice.")
        
        elif search_type == "2":
            id_type = input("\nEnter ID type (1) BIN or (2) BBL? [1/2]: ")
            
            if id_type == "1":
                bin_number = input("Enter BIN: ")
                report = get_property_compliance(client, bin_number=bin_number)
            elif id_type == "2":
                boro = input("Enter Borough name or code: ")
                block = input("Enter Block number: ")
                lot = input("Enter Lot number: ")
                report = get_property_compliance(client, boro=boro, block=block, lot=lot)
            else:
                print("Invalid choice.")
                return
            
            # Save report
            if report:
                output_file = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\nFull report saved to {output_file}")
        
        else:
            print("Invalid choice.")
    
    # Command line mode
    else:
        # If address provided, search for property
        if args.address:
            matches = search_property_by_address(client, args.address, args.zip)
            
            if matches:
                # Use first match for compliance report
                match = matches[0]
                bin_number = match.get('bin') or match.get('bin_number')
                boro = match.get('boro') or match.get('boroid') or match.get('borough')
                block = match.get('block')
                lot = match.get('lot')
                
                report = get_property_compliance(client, bin_number, boro, block, lot)
            else:
                print("No property matches found. Cannot generate compliance report.")
                return
        
        # If BIN or BBL provided directly, generate compliance report
        elif args.bin or (args.borough and args.block and args.lot):
            report = get_property_compliance(client, args.bin, args.borough, args.block, args.lot)
        
        # Save report
        if report:
            output_file = args.output or f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nFull report saved to {output_file}")

if __name__ == "__main__":
    main()
