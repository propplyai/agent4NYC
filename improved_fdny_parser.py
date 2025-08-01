"""
Improved FDNY PDF Parser
Extracts structured company data from FDNY approved companies PDF
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any

def parse_fdny_text_file(filepath: str) -> List[Dict[str, Any]]:
    """Parse the extracted FDNY text file to get structured company data"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    companies = []
    
    # Split by the separator lines
    sections = content.split('____________________________________________________')
    
    for section in sections:
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        if len(lines) < 3:  # Skip sections with insufficient data
            continue
            
        company_data = {
            'app_number': None,
            'approval_expiry': None,
            'company_name': None,
            'address': None,
            'city_state_zip': None,
            'phone': None,
            'principal_name': None,
            'insurance_expiry': None,
            'services': ['fire_alarm_inspection', 'fire_alarm_testing'],
            'license_status': 'ACTIVE',
            'license_type': 'FDNY_FIRE_ALARM'
        }
        
        for line in lines:
            # Extract App Number and Approval Expiry
            app_match = re.search(r'App No\.\s*(\d+S?)\s*Approval Exp:\s*(\d{1,2}/\d{1,2}/\d{4})', line)
            if app_match:
                company_data['app_number'] = app_match.group(1)
                company_data['approval_expiry'] = app_match.group(2)
                
                # Check if approval is expired
                try:
                    exp_date = datetime.strptime(app_match.group(2), '%m/%d/%Y')
                    if exp_date < datetime.now():
                        company_data['license_status'] = 'EXPIRED'
                except:
                    pass
            
            # Extract Company Name
            company_match = re.search(r'Company\s*:\s*(.+)', line)
            if company_match:
                company_data['company_name'] = company_match.group(1).strip()
            
            # Extract Address
            if line.startswith('Address:'):
                company_data['address'] = line.replace('Address:', '').strip()
            elif re.match(r'^[A-Za-z\s,]+,\s*[A-Z]{2}\s*\d{5}', line):
                company_data['city_state_zip'] = line.strip()
            
            # Extract Phone
            phone_match = re.search(r'Telephone #:\s*([0-9\-\(\)\s]+)', line)
            if phone_match:
                company_data['phone'] = phone_match.group(1).strip()
            
            # Extract Principal Name
            principal_match = re.search(r'Principal\'s Name:\s*([A-Z\s\.]+)', line)
            if principal_match:
                company_data['principal_name'] = principal_match.group(1).strip()
            
            # Extract Insurance Expiry
            insurance_match = re.search(r'Insurance Exp Date:\s*(\d{1,2}/\d{1,2}/\d{4})', line)
            if insurance_match:
                company_data['insurance_expiry'] = insurance_match.group(1)
        
        # Only add if we have essential data
        if company_data['company_name'] and company_data['app_number']:
            # Check for smoke detector maintenance approval
            if 'S' in company_data['app_number']:
                company_data['services'].append('smoke_detector_maintenance')
            
            companies.append(company_data)
    
    return companies

def integrate_with_vendor_marketplace():
    """Create integration file for vendor marketplace"""
    
    # Parse the FDNY text file
    fdny_text_file = '/Users/art3a/agent4NYC/fdny_pdfs/fire_alarm_companies_text.txt'
    companies = parse_fdny_text_file(fdny_text_file)
    
    print(f"Parsed {len(companies)} FDNY approved fire alarm companies")
    
    # Convert to vendor marketplace format
    fdny_vendors = []
    
    for company in companies:
        vendor = {
            'name': company['company_name'],
            'license_number': company['app_number'],
            'license_type': 'FDNY_FIRE_ALARM',
            'license_status': company['license_status'],
            'license_expiry': company['approval_expiry'],
            'company_name': company['company_name'],
            'address': f"{company['address']}, {company['city_state_zip']}" if company['address'] and company['city_state_zip'] else company['address'],
            'phone': company['phone'],
            'specializations': company['services'],
            'certification_date': None,
            'violations': [],
            'principal_name': company['principal_name'],
            'insurance_expiry': company['insurance_expiry']
        }
        fdny_vendors.append(vendor)
    
    # Save to JSON file for integration
    output_data = {
        'metadata': {
            'source': 'FDNY Official Approved Companies List',
            'parsed_at': datetime.now().isoformat(),
            'total_companies': len(fdny_vendors),
            'categories': ['fire_alarm_inspection', 'fire_alarm_testing', 'smoke_detector_maintenance']
        },
        'fdny_approved_companies': fdny_vendors
    }
    
    output_file = '/Users/art3a/agent4NYC/fdny_approved_companies.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"FDNY vendor data saved to: {output_file}")
    
    # Print sample data
    print("\n📋 Sample FDNY Approved Companies:")
    print("=" * 50)
    
    for i, vendor in enumerate(fdny_vendors[:5]):
        print(f"{i+1}. {vendor['name']}")
        print(f"   License: {vendor['license_number']} (Expires: {vendor['license_expiry']})")
        print(f"   Status: {vendor['license_status']}")
        print(f"   Phone: {vendor['phone'] or 'N/A'}")
        print(f"   Services: {', '.join(vendor['specializations'])}")
        if vendor['address']:
            print(f"   Address: {vendor['address']}")
        print()
    
    return fdny_vendors, output_file

if __name__ == "__main__":
    print("🔥 Improved FDNY Parser - Extracting Real Fire Inspector Data")
    print("=" * 70)
    
    vendors, output_file = integrate_with_vendor_marketplace()
    
    print(f"\n✅ Successfully parsed {len(vendors)} FDNY approved companies")
    print(f"📁 Data saved to: {output_file}")
    print("\nThis data can now be integrated into the vendor marketplace!")
