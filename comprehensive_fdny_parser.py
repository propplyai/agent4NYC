"""
Comprehensive FDNY Parser for All Fire Safety Services
Downloads and parses multiple FDNY approved company PDFs:
- Fire Alarm Systems
- Fire Extinguisher Services  
- Fire Sprinkler Systems
- General Fire Safety Inspections
"""

import requests
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any

try:
    import pdfplumber
except ImportError:
    os.system("pip install pdfplumber")
    import pdfplumber

class ComprehensiveFDNYParser:
    """Parser for all FDNY fire safety service PDFs"""
    
    def __init__(self):
        self.fdny_urls = {
            'fire_alarm_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-fire-alarm-system-inspection-testing-service.pdf',
            'fire_extinguisher_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-full-service-portable-fire-extinguisher.pdf',
            'sprinkler_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-sprinkler-system-inspection-testing-service.pdf',
            'emergency_lighting_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-emergency-lighting-exit-signs.pdf'
        }
        
        self.download_dir = 'fdny_comprehensive'
        os.makedirs(self.download_dir, exist_ok=True)

    def download_pdf(self, url: str, filename: str) -> str:
        """Download PDF from URL"""
        try:
            print(f"📥 Downloading: {filename}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded: {len(response.content)} bytes")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Download failed: {str(e)}")
            return None

    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text_content = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                print(f"📄 Processing {len(pdf.pages)} pages...")
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                        
        except Exception as e:
            print(f"❌ Error extracting text: {str(e)}")
            return ""
            
        return '\n\n---PAGE BREAK---\n\n'.join(text_content)

    def parse_fdny_companies(self, text_content: str, service_category: str) -> List[Dict[str, Any]]:
        """Parse FDNY company data from text content"""
        companies = []
        
        # Split by separator lines
        sections = text_content.split('____________________________________________________')
        
        # Determine service types based on category
        service_mappings = {
            'fire_alarm_companies': ['fire_alarm_inspection', 'fire_alarm_testing', 'smoke_detector_maintenance'],
            'fire_extinguisher_companies': ['fire_extinguisher_service', 'fire_extinguisher_inspection', 'fire_extinguisher_maintenance'],
            'sprinkler_companies': ['sprinkler_inspection', 'sprinkler_testing', 'sprinkler_maintenance'],
            'emergency_lighting_companies': ['emergency_lighting_inspection', 'exit_sign_inspection', 'emergency_lighting_maintenance']
        }
        
        default_services = service_mappings.get(service_category, ['fire_safety_inspection'])
        
        for section in sections:
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            
            if len(lines) < 3:
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
                'services': default_services.copy(),
                'license_status': 'ACTIVE',
                'license_type': f'FDNY_{service_category.upper().replace("_COMPANIES", "")}',
                'service_category': service_category
            }
            
            for line in lines:
                # Extract App Number and Approval Expiry
                app_match = re.search(r'App No\.\s*(\d+[A-Z]?)\s*Approval Exp:\s*(\d{1,2}/\d{1,2}/\d{4})', line)
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
                companies.append(company_data)
        
        return companies

    def download_and_parse_all(self) -> Dict[str, List[Dict]]:
        """Download and parse all FDNY PDF files"""
        all_companies = {}
        
        for category, url in self.fdny_urls.items():
            print(f"\n{'='*60}")
            print(f"🔥 Processing {category.replace('_', ' ').title()}")
            print(f"{'='*60}")
            
            filename = f"{category}.pdf"
            filepath = self.download_pdf(url, filename)
            
            if not filepath:
                print(f"❌ Skipping {category} - download failed")
                all_companies[category] = []
                continue
            
            # Extract text from PDF
            text_content = self.extract_text_from_pdf(filepath)
            
            if not text_content:
                print(f"❌ No text extracted from {category}")
                all_companies[category] = []
                continue
            
            # Save raw text for debugging
            text_file = os.path.join(self.download_dir, f"{category}_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Parse companies from text
            companies = self.parse_fdny_companies(text_content, category)
            all_companies[category] = companies
            
            print(f"✅ Extracted {len(companies)} companies from {category}")
            
            # Show sample companies
            if companies:
                print("📋 Sample companies:")
                for company in companies[:3]:
                    print(f"   • {company['company_name']}")
                    if company['phone']:
                        print(f"     📞 {company['phone']}")
                    print(f"     🏷️ {company['app_number']} (Expires: {company['approval_expiry']})")
        
        return all_companies

    def save_comprehensive_data(self, all_companies: Dict[str, List[Dict]]) -> str:
        """Save all parsed data to comprehensive JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"fdny_comprehensive_{timestamp}.json"
        filepath = os.path.join(self.download_dir, filename)
        
        # Calculate totals
        total_companies = sum(len(companies) for companies in all_companies.values())
        
        # Flatten all companies with category tags
        all_vendors = []
        for category, companies in all_companies.items():
            for company in companies:
                vendor = {
                    'name': company['company_name'],
                    'license_number': company['app_number'],
                    'license_type': company['license_type'],
                    'license_status': company['license_status'],
                    'license_expiry': company['approval_expiry'],
                    'company_name': company['company_name'],
                    'address': f"{company['address']}, {company['city_state_zip']}" if company['address'] and company['city_state_zip'] else company['address'],
                    'phone': company['phone'],
                    'specializations': company['services'],
                    'service_category': category,
                    'principal_name': company['principal_name'],
                    'insurance_expiry': company['insurance_expiry'],
                    'certification_date': None,
                    'violations': []
                }
                all_vendors.append(vendor)
        
        # Create comprehensive output
        output_data = {
            'metadata': {
                'source': 'FDNY Official Approved Companies Lists',
                'parsed_at': datetime.now().isoformat(),
                'total_companies': total_companies,
                'categories': list(all_companies.keys()),
                'service_types': [
                    'fire_alarm_inspection', 'fire_alarm_testing', 'smoke_detector_maintenance',
                    'fire_extinguisher_service', 'fire_extinguisher_inspection', 'fire_extinguisher_maintenance',
                    'sprinkler_inspection', 'sprinkler_testing', 'sprinkler_maintenance',
                    'emergency_lighting_inspection', 'exit_sign_inspection', 'emergency_lighting_maintenance'
                ]
            },
            'companies_by_category': all_companies,
            'all_vendors_flat': all_vendors
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive data saved to: {filepath}")
        return filepath

def main():
    """Main function to download and parse all FDNY fire safety PDFs"""
    print("🔥 Comprehensive FDNY Fire Safety Services Parser")
    print("="*70)
    print("Downloading and parsing all FDNY approved company lists:")
    print("• Fire Alarm Systems")
    print("• Fire Extinguisher Services") 
    print("• Fire Sprinkler Systems")
    print("• Emergency Lighting & Exit Signs")
    print("="*70)
    
    parser = ComprehensiveFDNYParser()
    
    # Download and parse all PDFs
    all_companies = parser.download_and_parse_all()
    
    # Save comprehensive results
    output_file = parser.save_comprehensive_data(all_companies)
    
    # Print final summary
    print(f"\n{'='*70}")
    print("📊 COMPREHENSIVE PARSING SUMMARY")
    print(f"{'='*70}")
    
    total_companies = 0
    for category, companies in all_companies.items():
        count = len(companies)
        total_companies += count
        status = "✅" if count > 0 else "❌"
        print(f"{status} {category.replace('_', ' ').title()}: {count} companies")
    
    print(f"\n🎯 Total Fire Safety Companies: {total_companies}")
    print(f"📁 Output File: {output_file}")
    
    if total_companies > 0:
        print(f"\n🚀 Ready to integrate {total_companies} certified fire safety companies into vendor marketplace!")
    
    return all_companies, output_file

if __name__ == "__main__":
    main()
