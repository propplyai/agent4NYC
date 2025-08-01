#!/usr/bin/env python3
"""
NYC Open Data API Client - Advanced Examples
This script demonstrates advanced usage patterns for the NYC Open Data client
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from nyc_opendata_client import NYCOpenDataClient

def example_visualization():
    """Example of data visualization with NYC Open Data"""
    # Initialize client
    app_token = os.environ.get("NYC_OPENDATA_TOKEN", "YOUR_APP_TOKEN_HERE")
    client = NYCOpenDataClient(app_token=app_token)
    
    # Get complaint types distribution
    print("Fetching 311 complaint types distribution...")
    complaint_types = client.get_data(
        'complaints_311',
        select="complaint_type, count(*) as count",
        where="created_date >= '2024-01-01T00:00:00'",
        group="complaint_type",
        order="count DESC",
        limit=10
    )
    
    if not complaint_types.empty:
        # Plot the data
        plt.figure(figsize=(12, 8))
        plt.barh(complaint_types['complaint_type'], complaint_types['count'])
        plt.title('Top 10 NYC 311 Complaint Types (2024)')
        plt.xlabel('Number of Complaints')
        plt.tight_layout()
        plt.savefig('complaint_types.png')
        print(f"Visualization saved as 'complaint_types.png'")
        
        # Show the data
        print("\nTop 10 Complaint Types:")
        for _, row in complaint_types.iterrows():
            print(f"  {row['complaint_type']}: {row['count']:,}")
    else:
        print("No data returned for complaint types")

def example_geospatial_analysis():
    """Example of geospatial analysis with NYC Open Data"""
    # Initialize client
    app_token = os.environ.get("NYC_OPENDATA_TOKEN", "YOUR_APP_TOKEN_HERE")
    client = NYCOpenDataClient(app_token=app_token)
    
    # Define neighborhoods by approximate lat/lon boundaries
    neighborhoods = {
        'Lower Manhattan': {'lat_min': 40.7, 'lat_max': 40.73, 'lon_min': -74.02, 'lon_max': -73.98},
        'Midtown': {'lat_min': 40.74, 'lat_max': 40.77, 'lon_min': -74.0, 'lon_max': -73.96},
        'Upper East Side': {'lat_min': 40.76, 'lat_max': 40.79, 'lon_min': -73.97, 'lon_max': -73.94},
        'Upper West Side': {'lat_min': 40.77, 'lat_max': 40.8, 'lon_min': -73.99, 'lon_max': -73.96},
        'Harlem': {'lat_min': 40.8, 'lat_max': 40.83, 'lon_min': -74.0, 'lon_max': -73.93}
    }
    
    print("Analyzing HPD violations by neighborhood...")
    results = {}
    
    for name, bounds in neighborhoods.items():
        query = f"""
        latitude > {bounds['lat_min']} AND latitude < {bounds['lat_max']} AND 
        longitude > {bounds['lon_min']} AND longitude < {bounds['lon_max']}
        """
        
        violations = client.get_data(
            'hpd_violations',
            where=query,
            select="count(*) as count",
            limit=1
        )
        
        count = int(violations.iloc[0]['count']) if not violations.empty else 0
        results[name] = count
        print(f"  {name}: {count:,} violations")
    
    # Create a simple report
    print("\nNeighborhood Violation Density:")
    for name, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count:,} violations")

def example_time_series():
    """Example of time series analysis with NYC Open Data"""
    # Initialize client
    app_token = os.environ.get("NYC_OPENDATA_TOKEN", "YOUR_APP_TOKEN_HERE")
    client = NYCOpenDataClient(app_token=app_token)
    
    # Get elevator inspection trends by month
    print("Analyzing elevator inspection trends...")
    
    # Last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    monthly_inspections = client.get_data(
        'elevator_inspections',
        select="date_trunc_ym(inspection_date) as month, count(*) as count",
        where=f"inspection_date >= '{start_date.strftime('%Y-%m-%d')}'",
        group="date_trunc_ym(inspection_date)",
        order="month"
    )
    
    if not monthly_inspections.empty:
        # Convert to proper datetime
        monthly_inspections['month'] = pd.to_datetime(monthly_inspections['month'])
        monthly_inspections['count'] = monthly_inspections['count'].astype(int)
        
        # Print the data
        print("\nMonthly Elevator Inspections:")
        for _, row in monthly_inspections.iterrows():
            print(f"  {row['month'].strftime('%Y-%m')}: {row['count']:,} inspections")
        
        # Calculate month-over-month change
        monthly_inspections['previous'] = monthly_inspections['count'].shift(1)
        monthly_inspections['change'] = (monthly_inspections['count'] - monthly_inspections['previous']) / monthly_inspections['previous'] * 100
        
        print("\nMonth-over-Month Change:")
        for _, row in monthly_inspections.iterrows():
            if not pd.isna(row['change']):
                direction = "increase" if row['change'] > 0 else "decrease"
                print(f"  {row['month'].strftime('%Y-%m')}: {abs(row['change']):.1f}% {direction}")
    else:
        print("No data returned for elevator inspections")

def example_cross_dataset_analysis():
    """Example of analysis across multiple datasets"""
    # Initialize client
    app_token = os.environ.get("NYC_OPENDATA_TOKEN", "YOUR_APP_TOKEN_HERE")
    client = NYCOpenDataClient(app_token=app_token)
    
    print("Performing cross-dataset analysis...")
    
    # Get building complaints
    building_complaints = client.get_data(
        'building_complaints',
        select="complaint_number, bin, date_entered, status",
        where="date_entered >= '2024-01-01T00:00:00'",
        limit=1000
    )
    
    # Get DOB violations for the same buildings
    if not building_complaints.empty and 'bin' in building_complaints.columns:
        # Extract unique BINs (Building Identification Numbers)
        bins = building_complaints['bin'].dropna().unique()
        
        if len(bins) > 0:
            # Take first 100 BINs to avoid query size limits
            bin_list = bins[:100]
            bin_string = "', '".join(bin_list)
            
            violations = client.get_data(
                'dob_violations',
                where=f"bin in ('{bin_string}')",
                limit=1000
            )
            
            if not violations.empty:
                # Merge datasets
                print(f"\nFound {len(building_complaints)} complaints and {len(violations)} violations")
                print(f"Buildings with both complaints and violations: {len(bin_list)}")
                
                # Count violations per building
                if 'bin' in violations.columns:
                    violation_counts = violations['bin'].value_counts()
                    
                    print("\nTop 5 Buildings by Violation Count:")
                    for bin_num, count in violation_counts.head().items():
                        print(f"  Building #{bin_num}: {count} violations")
            else:
                print("No violations found for the buildings with complaints")
        else:
            print("No valid BINs found in building complaints data")
    else:
        print("No building complaints data available or missing BIN column")

if __name__ == "__main__":
    print("NYC Open Data API Client - Advanced Examples")
    print("=" * 50)
    
    # Run examples
    try:
        example_visualization()
        print("\n" + "=" * 50 + "\n")
        
        example_geospatial_analysis()
        print("\n" + "=" * 50 + "\n")
        
        example_time_series()
        print("\n" + "=" * 50 + "\n")
        
        example_cross_dataset_analysis()
    except Exception as e:
        print(f"Error running examples: {e}")
    
    print("\nExamples completed. Check for any output files in the current directory.")
