#!/usr/bin/env python3
"""
NYC Open Data API Client - Utility Functions
Helper functions for robust data fetching, caching, and error handling
"""

import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from requests.exceptions import RequestException
from typing import Dict, List, Optional, Union, Callable

def robust_data_fetch(client, dataset_key: str, retries: int = 3, 
                     delay: int = 1, **kwargs) -> pd.DataFrame:
    """
    Fetch data with error handling and retries
    
    Args:
        client: NYCOpenDataClient instance
        dataset_key: Dataset key to fetch
        retries: Number of retry attempts
        delay: Initial delay between retries (will use exponential backoff)
        **kwargs: Additional parameters to pass to get_data
        
    Returns:
        DataFrame with the requested data or empty DataFrame on failure
    """
    for attempt in range(retries):
        try:
            data = client.get_data(dataset_key, **kwargs)
            if data is not None and not data.empty:
                return data
            else:
                print(f"Empty response on attempt {attempt + 1}")
                
        except RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                sleep_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return pd.DataFrame()

def cache_data(client, dataset_key: str, cache_dir: str = '.cache', 
              cache_ttl: int = 24, **kwargs) -> pd.DataFrame:
    """
    Fetch data with caching to avoid redundant API calls
    
    Args:
        client: NYCOpenDataClient instance
        dataset_key: Dataset key to fetch
        cache_dir: Directory to store cache files
        cache_ttl: Cache time-to-live in hours
        **kwargs: Additional parameters to pass to get_data
        
    Returns:
        DataFrame with the requested data
    """
    # Create cache directory if it doesn't exist
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    # Create a unique cache key based on the request parameters
    params_str = json.dumps({**kwargs, 'dataset_key': dataset_key}, sort_keys=True)
    cache_key = hashlib.md5(params_str.encode()).hexdigest()
    cache_file = cache_path / f"{dataset_key}_{cache_key}.parquet"
    
    # Check if we have a valid cache file
    if cache_file.exists():
        # Check if the cache is still valid
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - file_time < timedelta(hours=cache_ttl):
            try:
                # Try to use parquet if available
                try:
                    return pd.read_parquet(cache_file)
                except ImportError:
                    # Fall back to pickle if parquet is not available
                    cache_pickle = cache_path / f"{dataset_key}_{cache_key}.pkl"
                    if cache_pickle.exists():
                        return pd.read_pickle(cache_pickle)
                    else:
                        print("Cache file format not supported")
                        # Continue to fetch fresh data
            except Exception as e:
                print(f"Error reading cache file: {e}")
                # If there's an error reading the cache, continue to fetch fresh data
    
    # Fetch fresh data
    data = robust_data_fetch(client, dataset_key, **kwargs)
    
    # Save to cache if we got data
    if not data.empty:
        try:
            # Try to use parquet if available
            try:
                data.to_parquet(cache_file)
            except ImportError:
                # Fall back to pickle if parquet is not available
                cache_pickle = cache_path / f"{dataset_key}_{cache_key}.pkl"
                data.to_pickle(cache_pickle)
        except Exception as e:
            print(f"Error writing cache file: {e}")
    
    return data

def batch_process(client, dataset_key: str, process_func: Callable, 
                 batch_size: int = 10000, max_records: int = None, **kwargs) -> pd.DataFrame:
    """
    Process large datasets in batches with a custom processing function
    
    Args:
        client: NYCOpenDataClient instance
        dataset_key: Dataset key to fetch
        process_func: Function to process each batch (takes DataFrame as input)
        batch_size: Number of records per batch
        max_records: Maximum total records to process
        **kwargs: Additional parameters to pass to get_data
        
    Returns:
        Combined results from all batches
    """
    results = []
    offset = 0
    total_processed = 0
    
    print(f"Batch processing data from {dataset_key}...")
    
    while True:
        # Calculate current batch limit
        current_limit = min(batch_size, max_records - total_processed) if max_records else batch_size
        
        # Fetch batch
        batch = robust_data_fetch(client, dataset_key, limit=current_limit, offset=offset, **kwargs)
        
        if batch.empty:
            break
            
        # Process batch
        result = process_func(batch)
        if result is not None:
            results.append(result)
            
        # Update counters
        batch_size = len(batch)
        total_processed += batch_size
        print(f"Processed batch: {batch_size} records (total: {total_processed})")
        
        # Check if we're done
        if batch_size < current_limit:  # Last batch
            break
            
        if max_records and total_processed >= max_records:
            break
            
        # Move to next batch
        offset += current_limit
        time.sleep(0.1)  # Be respectful to the API
    
    # Combine results if they're DataFrames
    if results and isinstance(results[0], pd.DataFrame):
        return pd.concat(results, ignore_index=True)
    
    return results

def export_data(data: pd.DataFrame, filename: str, format: str = 'csv') -> str:
    """
    Export data to various formats
    
    Args:
        data: DataFrame to export
        filename: Base filename (without extension)
        format: Export format ('csv', 'json', 'excel', 'parquet')
        
    Returns:
        Path to the exported file
    """
    if data.empty:
        print("No data to export")
        return None
        
    # Ensure filename has no extension
    filename = os.path.splitext(filename)[0]
    
    if format.lower() == 'csv':
        output_file = f"{filename}.csv"
        data.to_csv(output_file, index=False)
    elif format.lower() == 'json':
        output_file = f"{filename}.json"
        data.to_json(output_file, orient='records', date_format='iso')
    elif format.lower() == 'excel':
        output_file = f"{filename}.xlsx"
        data.to_excel(output_file, index=False)
    elif format.lower() == 'parquet':
        output_file = f"{filename}.parquet"
        data.to_parquet(output_file, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
        
    print(f"Data exported to {output_file}")
    return output_file

def clean_dataset(df: pd.DataFrame, date_columns: List[str] = None) -> pd.DataFrame:
    """
    Clean and standardize a dataset
    
    Args:
        df: DataFrame to clean
        date_columns: List of column names that should be parsed as dates
        
    Returns:
        Cleaned DataFrame
    """
    # Make a copy to avoid modifying the original
    cleaned = df.copy()
    
    # Convert date columns
    if date_columns:
        for col in date_columns:
            if col in cleaned.columns:
                cleaned[col] = pd.to_datetime(cleaned[col], errors='coerce')
    
    # Handle common issues
    
    # 1. Strip whitespace from string columns
    for col in cleaned.select_dtypes(include=['object']).columns:
        cleaned[col] = cleaned[col].str.strip() if cleaned[col].dtype == 'object' else cleaned[col]
    
    # 2. Standardize missing values
    cleaned = cleaned.replace(['', 'N/A', 'NA', 'NULL', 'None', 'NONE'], pd.NA)
    
    # 3. Drop completely empty rows
    cleaned = cleaned.dropna(how='all')
    
    return cleaned

# Example usage
if __name__ == "__main__":
    from nyc_opendata_client import NYCOpenDataClient
    
    # Initialize client
    app_token = os.environ.get("NYC_OPENDATA_TOKEN", "YOUR_APP_TOKEN_HERE")
    client = NYCOpenDataClient(app_token=app_token)
    
    # Example: Fetch data with caching
    print("Fetching data with caching...")
    data = cache_data(
        client, 
        'complaints_311',
        where="created_date >= '2024-01-01T00:00:00'",
        limit=100
    )
    
    if not data.empty:
        print(f"Retrieved {len(data)} records")
        
        # Clean the data
        date_columns = ['created_date', 'closed_date', 'resolution_action_updated_date']
        cleaned_data = clean_dataset(data, date_columns)
        
        # Export to CSV
        export_data(cleaned_data, "recent_311_complaints", "csv")
