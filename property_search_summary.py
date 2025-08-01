#!/usr/bin/env python3
"""
NYC Property Search Summary
--------------------------
This script summarizes the findings from our search for 810 Whitestone Expressway
and provides a comparison with the property we found at 13-22 147 STREET.
"""

import json
import os
from datetime import datetime

# Original search target
SEARCH_TARGET = {
    "address": "810 Whitestone Expressway",
    "neighborhood": "Whitestone",
    "zip_code": "11357"
}

# Property we found
FOUND_PROPERTY = {
    "address": "13-22 147 STREET",
    "borough": "QUEENS",
    "block": "4465",
    "lot": "175",
    "bin": "4433339"
}

def load_compliance_report():
    """Load the compliance report if it exists"""
    report_file = f"compliance_report_BIN{FOUND_PROPERTY['bin']}.json"
    
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading compliance report: {e}")
            return None
    else:
        print(f"Compliance report file not found: {report_file}")
        return None

def summarize_search_process():
    """Summarize the search process and findings"""
    print("=" * 80)
    print("NYC PROPERTY SEARCH SUMMARY")
    print("=" * 80)
    
    print("\nORIGINAL SEARCH TARGET:")
    print(f"Address: {SEARCH_TARGET['address']}")
    print(f"Neighborhood: {SEARCH_TARGET['neighborhood']}")
    print(f"ZIP Code: {SEARCH_TARGET['zip_code']}")
    
    print("\nSEARCH PROCESS:")
    print("1. Initial search for exact address '810 Whitestone Expressway' in multiple datasets")
    print("2. Expanded search to include partial address matches in the 11357 ZIP code")
    print("3. Found multiple properties on Whitestone Expressway but none at exact #810")
    print("4. Identified property at 13-22 147 STREET with BBL: QUEENS/4465/175 and BIN: 4433339")
    print("5. Generated comprehensive compliance profile for this property")
    
    print("\nFOUND PROPERTY:")
    print(f"Address: {FOUND_PROPERTY['address']}")
    print(f"Borough: {FOUND_PROPERTY['borough']}")
    print(f"Block: {FOUND_PROPERTY['block']}")
    print(f"Lot: {FOUND_PROPERTY['lot']}")
    print(f"BIN: {FOUND_PROPERTY['bin']}")
    
    # Load and display compliance summary
    report = load_compliance_report()
    if report:
        print("\nCOMPLIANCE SUMMARY:")
        for dataset, data in report['compliance_data'].items():
            count = data.get('count', 0)
            if count > 0:
                print(f"- {dataset}: {count} records")
                
                # Show sample record for datasets with violations
                if dataset in ['hpd_violations', 'dob_violations'] and 'sample_records' in data:
                    if data['sample_records']:
                        sample = data['sample_records'][0]
                        print(f"  Sample: {sample}")
            else:
                print(f"- {dataset}: No records")
    
    print("\nCONCLUSION:")
    print("We could not find an exact match for '810 Whitestone Expressway' in the NYC Open Data")
    print("datasets. The property at 13-22 147 STREET (BIN: 4433339) was identified as a")
    print("potential match based on our search criteria. This property has multiple HPD")
    print("violations, DOB violations, and boiler inspection records.")
    
    print("\nRECOMMENDATIONS:")
    print("1. Verify if 13-22 147 STREET is the correct property or related to the target address")
    print("2. Consider using external geocoding services to confirm the exact BIN/BBL for")
    print("   810 Whitestone Expressway")
    print("3. Contact NYC Department of Buildings directly with the address to confirm the BIN")
    print("4. For future searches, use the BIN as the primary identifier once confirmed")
    
    print("\n" + "=" * 80)
    print(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    summarize_search_process()
