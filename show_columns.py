# /usr/bin/env python3
"""
This script fetches a single record from a specified dataset 
and lists all of its available data columns.
"""

import sys
from nyc_opendata_client import NYCOpenDataClient

# --- Configuration ---
# Change this to any dataset key from the client to see its columns
DEFAULT_DATASET = 'boiler_inspections'
# -------------------

def show_dataset_columns(dataset_key: str):
    """Fetches one record and prints its columns."""
    print(f"Fetching column list for dataset: '{dataset_key}'...")
    
    api_key_id = None
    api_key_secret = None

    # Try to load credentials from config file
    try:
        from config import API_KEY_ID, API_KEY_SECRET
        api_key_id = API_KEY_ID
        api_key_secret = API_KEY_SECRET
    except (ImportError, AttributeError):
        print("Running in anonymous mode.")

    # Initialize client
    client = NYCOpenDataClient(api_key_id=api_key_id, api_key_secret=api_key_secret)

    # Fetch one record
    data = client.get_data(dataset_key, limit=1)

    if data is not None and not data.empty:
        print("\n--- Available Data Columns ---")
        for column in data.columns:
            print(f"- {column}")
        print("----------------------------")
    else:
        print("\nCould not retrieve data. Please check the dataset key and your connection.")

if __name__ == "__main__":
    # Use the dataset key from the command line argument if provided, otherwise use the default
    dataset_to_show = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATASET
    show_dataset_columns(dataset_to_show)
