# NYC Boiler Data Search - Investigation Results

## Problem Identified
The original error "400 Client Error: Bad Request" occurred because the boiler data retrieval was using incorrect column names that don't exist in the dataset.

## Root Cause
The boiler inspections dataset (52dp-yji6) has a limited column structure and does NOT contain address components:

### Available Columns in Boiler Dataset:
1. tracking_number
2. boiler_id  
3. report_type
4. boiler_make
5. pressure_type
6. inspection_date
7. defects_exist
8. lff_45_days
9. lff_180_days
10. filing_fee
11. total_amount_paid
12. report_status
13. bin_number

### Missing Columns (That Don't Exist):
- ❌ house_number
- ❌ street_name  
- ❌ address
- ❌ block
- ❌ lot

## Solution Implemented

### Before (Incorrect):
```python
# This would fail with 400 error
data = client.get_data(
    'boiler_inspections',
    where="house_number = '140' AND street_name LIKE '%WEST 28%'",
    select="tracking_number, boiler_id, inspection_date, defects_exist, report_status, bin_number"
)
```

### After (Correct):
```python
# This works - BIN-only search
data = client.get_data(
    'boiler_inspections',
    where=f"bin_number = '{bin_number}'",
    select="tracking_number, boiler_id, inspection_date, defects_exist, " +
           "report_status, bin_number, boiler_make, pressure_type, report_type"
)
```

## Search Strategy

### Only Supported Method:
1. **BIN-based search** - Search using `bin_number` field
2. This requires first obtaining the BIN from other datasets (like HPD violations)

### Workflow:
1. Use address to find BIN via HPD violations or other address-containing datasets
2. Use the BIN to search boiler inspections
3. If no BIN is available, boiler data cannot be retrieved

## Key Insights

1. **Dataset Limitation**: The boiler dataset is BIN-centric and doesn't store address information
2. **Cross-Dataset Dependency**: Requires integration with other datasets to resolve addresses to BINs
3. **Error Handling**: 400 errors typically indicate invalid column names in the query

## Files Updated

1. **comprehensive_property_compliance.py** - Fixed `gather_boiler_data()` method
2. **test_boiler_search.py** - Created test script demonstrating correct usage
3. **BOILER_SEARCH_FINDINGS.md** - This documentation

## Test Results
- ✅ BIN-based search works correctly
- ✅ Returns proper boiler inspection data
- ✅ No more 400 Client Error
- ✅ Proper error messages when BIN is unavailable