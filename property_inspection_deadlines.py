#!/usr/bin/env python3
"""
Property Inspection Deadline Tracker
Track upcoming inspection deadlines for property management
"""

import pandas as pd
from datetime import datetime, timedelta
from nyc_opendata_client import NYCOpenDataClient

def get_upcoming_inspections(bbl=None, days_ahead=90, property_address=None):
    """
    Get upcoming inspection deadlines for a property
    
    Args:
        bbl: Borough-Block-Lot identifier (tuple or dict with boro/borough, block, lot)
        days_ahead: Number of days to look ahead for deadlines
        property_address: Alternative search by address if BBL not available
        
    Returns:
        DataFrame with upcoming inspection deadlines
    """
    client = NYCOpenDataClient.from_config()
    today = datetime.now()
    deadline_date = today + timedelta(days=days_ahead)
    deadline_str = deadline_date.strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')
    
    # Store all upcoming deadlines
    all_deadlines = []
    
    # Build the where clause based on input
    where_clause = None
    if bbl:
        if isinstance(bbl, tuple) and len(bbl) == 3:
            boro, block, lot = bbl
            where_clause = f"boro = '{boro}' AND block = '{block}' AND lot = '{lot}'"
        elif isinstance(bbl, dict):
            boro = bbl.get('boro') or bbl.get('borough') or bbl.get('borough_id')
            block = bbl.get('block')
            lot = bbl.get('lot')
            if boro and block and lot:
                where_clause = f"boro = '{boro}' AND block = '{block}' AND lot = '{lot}'"
    elif property_address:
        # Try to find the property by address
        address_parts = property_address.split(' ')
        if len(address_parts) >= 2:
            house_number = address_parts[0]
            street_name = ' '.join(address_parts[1:])
            where_clause = f"housenumber = '{house_number}' AND upper(streetname) LIKE '%{street_name.upper()}%'"
    
    if not where_clause:
        raise ValueError("Must provide either BBL or property address")
    
    # Check boiler inspections
    try:
        print("Checking boiler inspection deadlines...")
        # First, let's check what columns are available in this dataset
        sample_data = client.get_data('boiler_inspections', limit=1)
        
        # Check if the dataset exists and has data
        if sample_data is not None and not sample_data.empty:
            print(f"Available columns in boiler_inspections: {list(sample_data.columns)}")
            
            # Check if next_inspection_date column exists
            date_column = None
            for col in sample_data.columns:
                if 'next' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
                elif 'inspection' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
            
            if date_column:
                # Now use the correct column name in the query
                boiler_data = client.get_data(
                    'boiler_inspections',
                    where=f"{where_clause} AND {date_column} >= '{today_str}' AND {date_column} <= '{deadline_str}'",
                    limit=100
                )
                
                if boiler_data is not None and not boiler_data.empty:
                    boiler_data['inspection_type'] = 'Boiler'
                    boiler_data['deadline_date'] = boiler_data[date_column]
                    
                    # Select relevant columns that exist
                    cols = ['inspection_type', 'deadline_date']
                    for col_name in ['device_id', 'device_type', 'device_status']:
                        if col_name in boiler_data.columns:
                            cols.append(col_name)
                            
                    all_deadlines.append(boiler_data[cols])
                    print(f"Found {len(boiler_data)} upcoming boiler inspections")
                else:
                    print("No boiler inspection deadlines found")
            else:
                print("Could not find inspection date column in boiler_inspections dataset")
        else:
            print("Could not access boiler_inspections dataset or it's empty")
    except Exception as e:
        print(f"Error checking boiler inspections: {e}")
    
    # Check elevator inspections
    try:
        print("Checking elevator inspection deadlines...")
        # First, let's check what columns are available in this dataset
        sample_data = client.get_data('elevator_inspections', limit=1)
        
        # Check if the dataset exists and has data
        if sample_data is not None and not sample_data.empty:
            print(f"Available columns in elevator_inspections: {list(sample_data.columns)}")
            
            # Check if next_inspection_date column exists
            date_column = None
            for col in sample_data.columns:
                if 'next' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
                elif 'inspection' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
            
            if date_column:
                # Now use the correct column name in the query
                elevator_data = client.get_data(
                    'elevator_inspections',
                    where=f"{where_clause} AND {date_column} >= '{today_str}' AND {date_column} <= '{deadline_str}'",
                    limit=100
                )
                
                if elevator_data is not None and not elevator_data.empty:
                    elevator_data['inspection_type'] = 'Elevator'
                    elevator_data['deadline_date'] = elevator_data[date_column]
                    
                    # Select relevant columns that exist
                    cols = ['inspection_type', 'deadline_date']
                    for col_name in ['device_id', 'device_type', 'device_status']:
                        if col_name in elevator_data.columns:
                            cols.append(col_name)
                            
                    all_deadlines.append(elevator_data[cols])
                    print(f"Found {len(elevator_data)} upcoming elevator inspections")
                else:
                    print("No elevator inspection deadlines found")
            else:
                print("Could not find inspection date column in elevator_inspections dataset")
        else:
            print("Could not access elevator_inspections dataset or it's empty")
    except Exception as e:
        print(f"Error checking elevator inspections: {e}")
    
    # Check fire safety inspections
    try:
        print("Checking fire safety inspection deadlines...")
        # First, let's check what columns are available in this dataset
        sample_data = client.get_data('fire_safety_inspections', limit=1)
        
        # Check if the dataset exists and has data
        if sample_data is not None and not sample_data.empty:
            print(f"Available columns in fire_safety_inspections: {list(sample_data.columns)}")
            
            # Check if next_inspection_date column exists
            date_column = None
            for col in sample_data.columns:
                if 'next' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
                elif 'inspection' in col.lower() and 'date' in col.lower():
                    date_column = col
                    break
            
            if date_column:
                # Now use the correct column name in the query
                fire_data = client.get_data(
                    'fire_safety_inspections',
                    where=f"{where_clause} AND {date_column} >= '{today_str}' AND {date_column} <= '{deadline_str}'",
                    limit=100
                )
                
                if fire_data is not None and not fire_data.empty:
                    fire_data['inspection_type'] = 'Fire Safety'
                    fire_data['deadline_date'] = fire_data[date_column]
                    
                    # Select relevant columns that exist
                    cols = ['inspection_type', 'deadline_date']
                    for col_name in ['device_id', 'inspection_type']:
                        if col_name in fire_data.columns:
                            cols.append(col_name)
                            
                    all_deadlines.append(fire_data[cols])
                    print(f"Found {len(fire_data)} upcoming fire safety inspections")
                else:
                    print("No fire safety inspection deadlines found")
            else:
                print("Could not find inspection date column in fire_safety_inspections dataset")
        else:
            print("Could not access fire_safety_inspections dataset or it's empty")
    except Exception as e:
        print(f"Error checking fire safety inspections: {e}")
    
    # Check cooling tower inspections
    try:
        print("Checking cooling tower inspection deadlines...")
        # First check if this dataset exists
        try:
            # First, let's check what columns are available in this dataset
            sample_data = client.get_data('cooling_tower_inspections', limit=1)
            
            # Check if the dataset exists and has data
            if sample_data is not None and not sample_data.empty:
                print(f"Available columns in cooling_tower_inspections: {list(sample_data.columns)}")
                
                # Check if next_inspection_date column exists
                date_column = None
                for col in sample_data.columns:
                    if 'next' in col.lower() and 'date' in col.lower():
                        date_column = col
                        break
                    elif 'inspection' in col.lower() and 'date' in col.lower():
                        date_column = col
                        break
                
                if date_column:
                    # Now use the correct column name in the query
                    cooling_data = client.get_data(
                        'cooling_tower_inspections',
                        where=f"{where_clause} AND {date_column} >= '{today_str}' AND {date_column} <= '{deadline_str}'",
                        limit=100
                    )
                    
                    if cooling_data is not None and not cooling_data.empty:
                        cooling_data['inspection_type'] = 'Cooling Tower'
                        cooling_data['deadline_date'] = cooling_data[date_column]
                        
                        # Select relevant columns that exist
                        cols = ['inspection_type', 'deadline_date']
                        for col_name in ['tower_id', 'status']:
                            if col_name in cooling_data.columns:
                                cols.append(col_name)
                                
                        all_deadlines.append(cooling_data[cols])
                        print(f"Found {len(cooling_data)} upcoming cooling tower inspections")
                    else:
                        print("No cooling tower inspection deadlines found")
                else:
                    print("Could not find inspection date column in cooling_tower_inspections dataset")
            else:
                print("Could not access cooling_tower_inspections dataset or it's empty")
        except Exception as e:
            print(f"Could not access cooling tower inspections dataset: {e}")
    except Exception as e:
        print(f"Error checking cooling tower inspections: {e}")
    
    # Combine all deadlines
    if all_deadlines:
        combined_df = pd.concat(all_deadlines, ignore_index=True)
        # Sort by deadline date
        combined_df = combined_df.sort_values('deadline_date')
        return combined_df
    else:
        print("No upcoming inspection deadlines found")
        return pd.DataFrame()

def get_overdue_inspections(bbl=None, property_address=None):
    """
    Get overdue inspections for a property
    
    Args:
        bbl: Borough-Block-Lot identifier (tuple or dict with boro/borough, block, lot)
        property_address: Alternative search by address if BBL not available
        
    Returns:
        DataFrame with overdue inspections
    """
    client = NYCOpenDataClient.from_config()
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    # Build the where clause based on input
    where_clause = None
    if bbl:
        if isinstance(bbl, tuple) and len(bbl) == 3:
            boro, block, lot = bbl
            where_clause = f"boro = '{boro}' AND block = '{block}' AND lot = '{lot}'"
        elif isinstance(bbl, dict):
            boro = bbl.get('boro') or bbl.get('borough') or bbl.get('borough_id')
            block = bbl.get('block')
            lot = bbl.get('lot')
            if boro and block and lot:
                where_clause = f"boro = '{boro}' AND block = '{block}' AND lot = '{lot}'"
    elif property_address:
        # Try to find the property by address
        address_parts = property_address.split(' ')
        if len(address_parts) >= 2:
            house_number = address_parts[0]
            street_name = ' '.join(address_parts[1:])
            where_clause = f"housenumber = '{house_number}' AND upper(streetname) LIKE '%{street_name.upper()}%'"
    
    if not where_clause:
        raise ValueError("Must provide either BBL or property address")
    
    # Store all overdue inspections
    all_overdue = []
    
    # Check for overdue inspections in each dataset
    datasets = [
        ('boiler_inspections', 'Boiler'),
        ('elevator_inspections', 'Elevator'),
        ('fire_safety_inspections', 'Fire Safety'),
        ('cooling_tower_inspections', 'Cooling Tower')
    ]
    
    for dataset_key, inspection_type in datasets:
        try:
            print(f"Checking {inspection_type} overdue inspections...")
            
            # First, check if the dataset exists and get column names
            try:
                sample_data = client.get_data(dataset_key, limit=1)
                
                if sample_data is not None and not sample_data.empty:
                    print(f"Available columns in {dataset_key}: {list(sample_data.columns)}")
                    
                    # Find the date column
                    date_column = None
                    for col in sample_data.columns:
                        if 'next' in col.lower() and 'date' in col.lower():
                            date_column = col
                            break
                        elif 'inspection' in col.lower() and 'date' in col.lower():
                            date_column = col
                            break
                    
                    if date_column:
                        # Now use the correct column name in the query
                        data = client.get_data(
                            dataset_key,
                            where=f"{where_clause} AND {date_column} < '{today_str}'",
                            limit=100
                        )
                        
                        if data is not None and not data.empty:
                            data['inspection_type'] = inspection_type
                            data['deadline_date'] = data[date_column]
                            try:
                                data['days_overdue'] = (today - pd.to_datetime(data[date_column])).dt.days
                            except:
                                # If date conversion fails, just set a placeholder
                                data['days_overdue'] = 0
                            
                            # Select relevant columns that exist
                            cols = ['inspection_type', 'deadline_date', 'days_overdue']
                            for col_name in ['device_id', 'device_type', 'device_status', 'tower_id']:
                                if col_name in data.columns:
                                    cols.append(col_name)
                                    
                            all_overdue.append(data[cols])
                            print(f"Found {len(data)} overdue {inspection_type} inspections")
                        else:
                            print(f"No overdue {inspection_type} inspections found")
                    else:
                        print(f"Could not find inspection date column in {dataset_key} dataset")
                else:
                    print(f"Could not access {dataset_key} dataset or it's empty")
            except Exception as e:
                print(f"Could not access {dataset_key} dataset: {e}")
        except Exception as e:
            print(f"Error checking {inspection_type} inspections: {e}")
    
    # Combine all overdue inspections
    if all_overdue:
        combined_df = pd.concat(all_overdue, ignore_index=True)
        # Sort by most overdue first
        combined_df = combined_df.sort_values('days_overdue', ascending=False)
        return combined_df
    else:
        print("No overdue inspections found")
        return pd.DataFrame()

def main():
    """Example usage of the inspection deadline tracker"""
    
    print("NYC Property Inspection Deadline Tracker")
    print("=" * 50)
    
    # First, let's check what datasets are available
    client = NYCOpenDataClient.from_config()
    print("\nAvailable datasets:")
    for key, info in client.datasets.items():
        print(f"- {key}: {info['name']}")
    
    # Example 1: Using the BBL from the Whitestone property
    bbl = {
        'boro': 'QUEENS',
        'block': '3969',
        'lot': '24'
    }
    
    print("\nExample 1: Check upcoming inspections for 810 Whitestone Expressway")
    print("-" * 60)
    try:
        upcoming = get_upcoming_inspections(bbl=bbl, days_ahead=180)
        if upcoming is not None and not upcoming.empty:
            print("\nUpcoming Inspections (next 180 days):")
            print(upcoming.to_string(index=False))
        else:
            print("No upcoming inspections found for this property")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Check by address
    print("\nExample 2: Check by address")
    print("-" * 60)
    try:
        address = "810 Whitestone Expressway"
        overdue = get_overdue_inspections(property_address=address)
        if overdue is not None and not overdue.empty:
            print("\nOverdue Inspections:")
            print(overdue.to_string(index=False))
        else:
            print("No overdue inspections found for this address")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Check multiple properties (portfolio)
    print("\nExample 3: Portfolio Overview")
    print("-" * 60)
    properties = [
        {"address": "810 Whitestone Expressway", "name": "Whitestone Property"},
        {"bbl": {"boro": "MANHATTAN", "block": "1234", "lot": "56"}, "name": "Manhattan Office"}
    ]
    
    print("Portfolio Inspection Summary:")
    for prop in properties:
        print(f"\nProperty: {prop['name']}")
        try:
            if "address" in prop:
                upcoming = get_upcoming_inspections(property_address=prop["address"], days_ahead=90)
            else:
                upcoming = get_upcoming_inspections(bbl=prop["bbl"], days_ahead=90)
                
            if upcoming is not None and not upcoming.empty:
                print(f"  {len(upcoming)} upcoming inspections in next 90 days")
                # Show the next 3 inspections
                print(upcoming.head(3).to_string(index=False))
            else:
                print("  No upcoming inspections in next 90 days")
        except Exception as e:
            print(f"  Error checking property: {e}")

if __name__ == "__main__":
    main()
