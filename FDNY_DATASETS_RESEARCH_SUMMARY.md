# NYC Open Data FDNY Datasets - Research Summary

## Research Findings

Based on comprehensive investigation of NYC Open Data FDNY datasets, here are the corrected dataset information and solutions for the 400 Client Error issues:

## ❌ **Problem Identified**

1. **Dataset `avgm-ztsb` (FDNY Violations)**: Does **NOT** support BIN searches - only block/lot and address
2. **Dataset `tsak-vtv3`**: This is **NOT** fire safety inspections! It's actually "Upcoming contracts to be awarded (CIP)" - school construction projects
3. **400 Client Errors**: Caused by using wrong column names and unsupported search parameters

## ✅ **Corrected Dataset Information**

### 1. FDNY Violations (Current Data)

#### Dataset: `avgm-ztsb` - FDNY Violations (OATH ECB Hearings)
- **Columns**: 78 total
- **Description**: Complete FDNY violations with hearing results and payments
- **Supports**: ✅ Block/Lot, ✅ Address, ❌ BIN
- **Status**: Active, current data

**Correct Column Names:**
```python
{
    'borough': 'violation_location_borough',
    'block': 'violation_location_block_no',
    'lot': 'violation_location_lot_no', 
    'house_number': 'violation_location_house',
    'street_name': 'violation_location_street_name',
    'zip_code': 'violation_location_zip_code',
    'ticket_number': 'ticket_number',
    'violation_date': 'violation_date',
    'amount': 'total_violation_amount',
    'status': 'hearing_status'
}
```

**Correct Search Examples:**
```python
# Search by block/lot (WORKING)
where = "violation_location_borough = 'MANHATTAN' AND violation_location_block_no = '01073' AND violation_location_lot_no = '0001'"

# Search by address (WORKING) 
where = "violation_location_house = '140' AND violation_location_street_name LIKE '%28TH STREET%'"
```

#### Dataset: `ktas-47y7` - FDNY Violations (Simplified)
- **Columns**: 15 total
- **Description**: Simplified version with key fields only
- **Supports**: ✅ Block/Lot, ✅ Address, ❌ BIN
- **Status**: Active, current data

### 2. Bureau of Fire Prevention (Historical Data)

#### Dataset: `ssq6-fkht` - Bureau of Fire Prevention Inspections (Historical)
- **Columns**: 20 total
- **Supports**: ✅ BIN, ✅ Address, ❌ Block/Lot
- **Status**: ⚠️ HISTORICAL ONLY - No new data since decommissioning

**Correct Column Names:**
```python
{
    'bin': 'BIN',
    'address': 'PREM_ADDR',
    'borough': 'BOROUGH',
    'owner_name': 'OWNER_NAME',
    'last_visit': 'LAST_VISIT_DT',
    'last_inspection': 'LAST_FULL_INSP_DT',
    'inspection_status': 'LAST_INSP_STAT'
}
```

**Correct Search Examples:**
```python
# Search by BIN (WORKING)
where = "BIN = '4433339'"

# Search by address (WORKING)
where = "PREM_ADDR LIKE '%140 WEST 28TH%'"
```

#### Dataset: `bi53-yph3` - Bureau of Fire Prevention Violation Orders (Historical)
- **Supports**: ✅ BIN, ✅ Address, ❌ Block/Lot
- **Status**: ⚠️ HISTORICAL ONLY

#### Dataset: `nvgj-hbht` - Bureau of Fire Prevention Building Summary (Historical)
- **Supports**: ✅ BIN, ✅ Block/Lot, ❌ Address
- **Status**: ⚠️ HISTORICAL ONLY

### 3. ❌ Wrong Dataset
- **`tsak-vtv3`**: This is **"Upcoming contracts to be awarded (CIP)"** - school construction projects, NOT fire safety inspections!

## 🔧 **Working Code Examples**

### Search FDNY Violations by Block/Lot
```python
import requests

def search_fdny_violations_block_lot(borough, block, lot):
    url = "https://data.cityofnewyork.us/resource/avgm-ztsb.json"
    
    # Format with leading zeros
    block_padded = block.zfill(5)
    lot_padded = lot.zfill(4)
    
    params = {
        '$where': f"violation_location_borough = '{borough}' AND violation_location_block_no = '{block_padded}' AND violation_location_lot_no = '{lot_padded}'",
        '$select': 'ticket_number, violation_date, violation_location_house, violation_location_street_name, total_violation_amount, hearing_status',
        '$limit': 100
    }
    
    response = requests.get(url, params=params)
    return response.json()

# Example usage
violations = search_fdny_violations_block_lot('MANHATTAN', '1073', '1')
```

### Search Fire Prevention by BIN (Historical)
```python
def search_fire_prevention_by_bin(bin_number):
    url = "https://data.cityofnewyork.us/resource/ssq6-fkht.json"
    
    params = {
        '$where': f"BIN = '{bin_number}'",
        '$select': 'ACCT_ID, OWNER_NAME, LAST_VISIT_DT, LAST_FULL_INSP_DT, LAST_INSP_STAT, PREM_ADDR, BIN, BOROUGH',
        '$limit': 100
    }
    
    response = requests.get(url, params=params)
    return response.json()

# Example usage
inspections = search_fire_prevention_by_bin('4433339')
```

## 🎯 **Search Strategy Recommendations**

### For Current FDNY Violations:
1. **Use**: `avgm-ztsb` or `ktas-47y7`
2. **Search by**: Borough + Block + Lot (most reliable)
3. **Alternative**: Address components (house number + street name)
4. **Never use**: BIN (not supported)

### For Fire Prevention Data:
1. **Historical**: Use `ssq6-fkht`, `bi53-yph3`, `nvgj-hbht` (BIN supported)
2. **Current**: Contact FDNY directly
   - FDNY Business Portal: `fires.fdnycloud.org/CitizenAccess`
   - Call 311 for current inspection information

### For Property Searches:
1. **Best approach**: Use multiple search strategies
2. **Fallback chain**: BIN → Block/Lot → Address → Direct FDNY contact

## 📊 **Test Results**

Test property: **140 West 28th Street, Manhattan** (BIN: 4433339, Block: 1073, Lot: 1)

### Results:
- ✅ **Fire Prevention Inspections (Historical)**: Found 1 record 
  - Owner: KAIPIN GROUP LLC
  - Last visit: 2018-03-08
- ❌ **FDNY Violations**: No current violations found
- ❌ **Other datasets**: No records or 400 errors with wrong parameters

## 🔍 **Alternative FDNY Datasets Available**

| Dataset ID | Name | BIN | Block/Lot | Address | Status |
|------------|------|-----|-----------|---------|--------|
| `avgm-ztsb` | FDNY Violations (Full) | ❌ | ✅ | ✅ | Active |
| `ktas-47y7` | FDNY Violations (Simple) | ❌ | ✅ | ✅ | Active |
| `ssq6-fkht` | Fire Prevention Inspections | ✅ | ❌ | ✅ | Historical |
| `bi53-yph3` | Fire Prevention Violations | ✅ | ❌ | ✅ | Historical |
| `nvgj-hbht` | Fire Prevention Summary | ✅ | ✅ | ❌ | Historical |
| `8m42-w767` | Fire Incident Dispatch | ❌ | ❌ | ❌ | Active |

## 💡 **Solutions for 400 Client Errors**

1. **Use correct column names** from the research above
2. **Don't use BIN** for FDNY violations datasets
3. **Pad block/lot numbers** with leading zeros (block: 5 digits, lot: 4 digits)
4. **Use proper borough names** (MANHATTAN, BROOKLYN, QUEENS, BRONX, STATEN ISLAND)
5. **Check dataset status** - many fire prevention datasets are historical only

## 📞 **Current FDNY Data Sources**

Since many datasets are historical, for current fire prevention data:

1. **FDNY Business Portal**: https://fires.fdnycloud.org/CitizenAccess
2. **Call 311**: Request transfer to FDNY Customer Service Center
3. **Email**: FDNY.BusinessSupport@fdny.nyc.gov
4. **In-person**: FDNY Headquarters, 9 MetroTech Center, Brooklyn

---

**Research completed on**: 2025-01-25  
**Files created**: `test_fdny_datasets.py`, `fdny_research_results.py`, `corrected_fdny_search.py`