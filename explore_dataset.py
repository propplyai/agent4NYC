# /usr/bin/env python3
"""
This script fetches a single record from any NYC Open Data dataset ID
and lists all of its available data columns.
"""

import sys
import requests
import pandas as pd

# --- Configuration ---
BASE_URL = "https://data.cityofnewyork.us/resource/"
# -------------------

def explore_dataset(dataset_id: str):
    """Fetches one record from a given dataset ID and prints its columns."""
    print(f"Fetching column list for dataset ID: '{dataset_id}'...")
    
    api_key_id = None
    api_key_secret = None
    auth = None

    # Try to load credentials from config file for authenticated access
    try:
        from config import API_KEY_ID, API_KEY_SECRET
        api_key_id = API_KEY_ID
        api_key_secret = API_KEY_SECRET
        auth = (api_key_id, api_key_secret)
        print("Using credentials from config.py.")
    except (ImportError, AttributeError):
        print("Running in anonymous mode.")

    # Construct the request URL
    url = f"{BASE_URL}{dataset_id}.json"
    params = {'$limit': 1}

    try:
        response = requests.get(url, auth=auth, params=params, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        if data:
            df = pd.DataFrame(data)
            print("\n--- Available Data Columns ---")
            for column in df.columns:
                print(f"- {column}")
            print("----------------------------")
        else:
            print("\nDataset is empty or does not exist.")

    except requests.exceptions.RequestException as e:
        print(f"\nError fetching data: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python explore_dataset.py <dataset_id>")
        print("Example: python explore_dataset.py avgm-ztsb")
        sys.exit(1)
    
    dataset_to_explore = sys.argv[1]
    explore_dataset(dataset_to_explore)
