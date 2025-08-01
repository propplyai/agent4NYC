# NYC Open Data API Client

A comprehensive Python client for accessing NYC Open Data via the Socrata Open Data API (SODA).

## Overview

This client provides easy access to various NYC datasets including:
- Building violations (DOB, HPD)
- Inspections (boilers, elevators, fire safety)
- 311 Complaints
- Property registrations
- Cooling tower data

## Installation

```bash
# Install required dependencies
pip install requests pandas
```

## Getting Started

### Basic Usage

```python
from nyc_opendata_client import NYCOpenDataClient

# Initialize client (recommended to use an app token)
client = NYCOpenDataClient(app_token="YOUR_APP_TOKEN")

# Get recent 311 complaints
complaints = client.get_recent_data('complaints_311', days_back=7, limit=100)
print(f"Found {len(complaints)} recent complaints")
print(complaints[['created_date', 'complaint_type', 'borough']].head())
```

### API Credentials

To avoid throttling and access the API with higher rate limits, you should obtain API credentials from NYC Open Data.

1. Go to the [NYC Open Data](https://opendata.cityofnewyork.us/) website.
2. Create an account or sign in.
3. Navigate to your profile and find the API Keys section.
4. Generate a new API Key. This will give you an **API Key ID** and an **API Key Secret**.

Once you have your credentials, you should store them securely. This client uses a `config.py` file (which is ignored by Git) to manage them.

**Configuration File**

Create a `config.py` file in the project root and add your credentials like this:

```python
# config.py

# Your API Key ID (serves as the username for Basic Auth)
API_KEY_ID = "your_api_key_id_here"

# Your API Key Secret (serves as the password for Basic Auth)
API_KEY_SECRET = "your_api_key_secret_here"
```

The client will automatically load these credentials to authenticate your requests.

## Features

- **Simple API**: Easy-to-use methods for common data retrieval patterns
- **Pagination**: Automatically handle large datasets
- **Date Filtering**: Search by date ranges or recent data
- **Flexible Querying**: Support for SoQL (Socrata Query Language)
- **Multiple Formats**: Get data as DataFrame, JSON, CSV, etc.

## Available Datasets

| Key | Name | Description |
|-----|------|-------------|
| boiler_inspections | Boiler Inspections | Inspection type, dates, boiler type, property types |
| elevator_inspections | Elevator Inspections | DOB NOW Elevator Compliance data |
| dob_violations | DOB Violations | Building code compliance data |
| hpd_violations | HPD Violations | Housing Preservation & Development violations |
| hpd_registrations | HPD Registrations | Property registration information |
| cooling_tower_registrations | Cooling Tower Registrations | Registration data for cooling towers |
| cooling_tower_inspections | Cooling Tower Inspections | Inspection dates, status, compliance information |
| complaints_311 | 311 Complaints | Citizen complaints about properties |
| building_complaints | Building Complaints | DOB Complaints specific to building issues |
| fire_safety_inspections | Fire Safety Inspections | FDNY Inspections data |

## Advanced Usage Examples

### Complex Query with Multiple Filters

```python
# Get 311 complaints for noise issues in Brooklyn from last month
noise_complaints = client.get_data(
    'complaints_311',
    where="complaint_type like '%Noise%' AND borough = 'BROOKLYN'",
    select="unique_key, created_date, complaint_type, descriptor, incident_address",
    order="created_date DESC",
    limit=500
)
```

### Data Export to Different Formats

```python
# Get data as CSV
csv_data = client.get_data('dob_violations', format_type='csv', limit=1000)

# Save to file
with open('dob_violations.csv', 'w') as f:
    f.write(csv_data)

# Get data as JSON and save
json_data = client.get_data('fire_safety_inspections', limit=100)
json_data.to_json('fire_inspections.json', orient='records')
```

### Geospatial Queries

```python
# Get violations within a specific lat/lon bounding box
spatial_query = """
latitude > 40.7 AND latitude < 40.8 AND 
longitude > -74.0 AND longitude < -73.9
"""

manhattan_violations = client.get_data(
    'hpd_violations',
    where=spatial_query,
    select="latitude, longitude, violationstatus, violationtype",
    limit=1000
)
```

### Time Series Analysis

```python
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Get daily complaint counts for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

daily_complaints = client.get_data(
    'complaints_311',
    select="date_trunc_ymd(created_date) as date, count(*) as count",
    where=f"created_date >= '{start_date.strftime('%Y-%m-%d')}'",
    group="date_trunc_ymd(created_date)",
    order="date"
)

# Plot the data
plt.figure(figsize=(12, 6))
plt.plot(pd.to_datetime(daily_complaints['date']), daily_complaints['count'])
plt.title('Daily 311 Complaints - Last 30 Days')
plt.xlabel('Date')
plt.ylabel('Number of Complaints')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## Common SoQL Query Patterns

### Date Filtering
```python
# Last 30 days
where="created_date >= '2024-06-15T00:00:00'"

# Specific date range
where="created_date between '2024-01-01T00:00:00' and '2024-12-31T23:59:59'"

# This year
where="date_extract_y(created_date) = 2024"
```

### Text Searching
```python
# Contains text
where="complaint_type like '%Noise%'"

# Starts with
where="address like '123 MAIN%'"

# Multiple conditions
where="complaint_type like '%Noise%' AND borough = 'MANHATTAN'"
```

### Numeric Filtering
```python
# Greater than
where="amount > 1000"

# Range
where="amount between 100 and 5000"

# In list
where="borough in ('MANHATTAN', 'BROOKLYN')"
```

### Aggregation
```python
# Count by group
select="borough, count(*) as count"
group="borough"

# Sum by group
select="violation_type, sum(amount) as total_amount"
group="violation_type"

# Average
select="borough, avg(amount) as avg_amount"
group="borough"
```

## Error Handling Best Practices

```python
import time
from requests.exceptions import RequestException

def robust_data_fetch(client, dataset_key, retries=3, delay=1):
    """Fetch data with error handling and retries"""
    
    for attempt in range(retries):
        try:
            data = client.get_data(dataset_key, limit=1000)
            if data is not None and not data.empty:
                return data
            else:
                print(f"Empty response on attempt {attempt + 1}")
                
        except RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return None
```

## Performance Tips

1. **Use pagination** for large datasets instead of requesting all at once
2. **Add specific SELECT clauses** to only get columns you need
3. **Use WHERE clauses** to filter data server-side
4. **Implement caching** for frequently accessed data
5. **Respect rate limits** - add delays between requests if needed

## Dataset-Specific Tips

### 311 Complaints (`erm2-nwe9`)
- Very large dataset - always use date filters
- Common columns: `created_date`, `complaint_type`, `borough`, `incident_address`
- Updated frequently - good for real-time analysis

### DOB Violations (`3h2n-5cm9`)
- Contains building code violations
- Key columns: `violation_type`, `issue_date`, `current_status`
- Good for building compliance tracking

### HPD Violations (`wvxf-dwi5`)
- Housing violations and conditions
- Key columns: `violationid`, `boroid`, `violationstatus`
- Links to property registration data

## Troubleshooting Common Issues

### Authentication Errors
- Verify your app token is correct
- Check if token has expired
- Ensure token is included in requests

### Rate Limiting
- Implement delays between requests
- Use batch processing for large datasets
- Monitor your usage

### Data Quality Issues
- Check for null values in date columns
- Validate coordinate data for geospatial queries
- Handle different date formats across datasets

### Query Errors
- Verify column names exist in dataset
- Check SoQL syntax
- Test queries with small limits first

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
