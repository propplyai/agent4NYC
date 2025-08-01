"""
Complete FDNY Dataset Finder and Parser
Discovers and parses ALL available FDNY approved company PDFs
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

class CompleteFDNYDatasetFinder:
    """Comprehensive FDNY approved companies dataset finder and parser"""
    
    def __init__(self):
        # All discovered FDNY approved company PDFs
        self.fdny_datasets = {
            'fire_alarm_companies': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-fire-alarm-system-inspection-testing-service.pdf',
                'services': ['fire_alarm_inspection', 'fire_alarm_testing', 'smoke_detector_maintenance'],
                'description': 'Fire Alarm System Inspection, Testing & Service'
            },
            'fire_extinguisher_companies': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-full-service-portable-fire-extinguisher.pdf',
                'services': ['fire_extinguisher_service', 'fire_extinguisher_inspection', 'fire_extinguisher_maintenance'],
                'description': 'Full Service Portable Fire Extinguisher'
            },
            'central_station_companies': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-central-station.pdf',
                'services': ['central_station_monitoring', 'alarm_monitoring', 'fire_alarm_monitoring'],
                'description': 'Central Station Monitoring Services'
            },
            'arc_system_companies': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-arc-system.pdf',
                'services': ['auxiliary_radio_communication', 'emergency_communication', 'radio_system_maintenance'],
                'description': 'Auxiliary Radio Communication System'
            },
            'underground_tank_installers': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-underground-tank-installers.pdf',
                'services': ['underground_tank_installation', 'fuel_tank_installation', 'tank_system_maintenance'],
                'description': 'Underground Tank Installers'
            },
            'motor_fuel_installers': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-motor-fueled-installer.pdf',
                'services': ['motor_fuel_installation', 'fuel_system_installation', 'fuel_equipment_service'],
                'description': 'Motor Fuel Installation'
            },
            'cor_expeditors': {
                'url': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/cor-expeditors-list.pdf',
                'services': ['certificate_of_occupancy_expediting', 'permit_expediting', 'regulatory_compliance'],
                'description': 'Certificate of Occupancy Expeditors'
            }
        }
        
        # Additional potential datasets to try
        self.potential_datasets = {
            'sprinkler_companies': {
                'urls': [
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-sprinkler-system.pdf',
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-sprinkler-inspection.pdf',
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-sprinkler-testing.pdf'
                ],
                'services': ['sprinkler_inspection', 'sprinkler_testing', 'sprinkler_maintenance'],
                'description': 'Sprinkler System Services'
            },
            'emergency_lighting_companies': {
                'urls': [
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-emergency-lighting.pdf',
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-exit-signs.pdf',
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-emergency-lighting-exit-signs.pdf'
                ],
                'services': ['emergency_lighting_inspection', 'exit_sign_inspection', 'emergency_lighting_maintenance'],
                'description': 'Emergency Lighting & Exit Signs'
            },
            'standpipe_companies': {
                'urls': [
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-standpipe-system.pdf',
                    'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-standpipe-inspection.pdf'
                ],
                'services': ['standpipe_inspection', 'standpipe_testing', 'standpipe_maintenance'],
                'description': 'Standpipe System Services'
            }
        }
        
        self.download_dir = 'fdny_complete_datasets'
        os.makedirs(self.download_dir, exist_ok=True)

    def test_url_availability(self, url: str) -> bool:
        """Test if a URL is available"""
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False

    def discover_available_datasets(self) -> Dict[str, Dict]:
        """Discover which FDNY datasets are actually available"""
        available_datasets = {}
        
        print("🔍 Discovering Available FDNY Datasets...")
        print("=" * 60)
        
        # Test confirmed datasets
        for dataset_name, dataset_info in self.fdny_datasets.items():
            url = dataset_info['url']
            print(f"Testing {dataset_name}...")
            
            if self.test_url_availability(url):
                print(f"✅ Available: {dataset_info['description']}")
                available_datasets[dataset_name] = dataset_info
            else:
                print(f"❌ Not available: {url}")
        
        # Test potential datasets
        for dataset_name, dataset_info in self.potential_datasets.items():
            print(f"\nTesting potential {dataset_name}...")
            
            for url in dataset_info['urls']:
                print(f"  Trying: {url}")
                if self.test_url_availability(url):
                    print(f"  ✅ Found: {dataset_info['description']}")
                    available_datasets[dataset_name] = {
                        'url': url,
                        'services': dataset_info['services'],
                        'description': dataset_info['description']
                    }
                    break
            else:
                print(f"  ❌ No available URLs for {dataset_name}")
        
        return available_datasets

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
            
        except Exception as e:
            print(f"❌ Download failed: {str(e)}")
            return None

    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF"""
        try:
            with pdfplumber.open(filepath) as pdf:
                text_content = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                return '\n\n---PAGE BREAK---\n\n'.join(text_content)
        except Exception as e:
            print(f"❌ Text extraction failed: {str(e)}")
            return ""

    def parse_fdny_companies(self, text_content: str, dataset_name: str, services: List[str]) -> List[Dict[str, Any]]:
        """Parse FDNY company data from text content"""
        companies = []
        sections = text_content.split('____________________________________________________')
        
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
                'services': services.copy(),
                'license_status': 'ACTIVE',
                'license_type': f'FDNY_{dataset_name.upper()}',
                'dataset_category': dataset_name
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

    def process_all_datasets(self) -> Dict[str, Any]:
        """Process all available FDNY datasets"""
        print("\n🔥 Processing All Available FDNY Datasets")
        print("=" * 60)
        
        # Discover available datasets
        available_datasets = self.discover_available_datasets()
        
        all_companies = {}
        total_companies = 0
        
        for dataset_name, dataset_info in available_datasets.items():
            print(f"\n{'='*50}")
            print(f"🔥 Processing {dataset_name.replace('_', ' ').title()}")
            print(f"{'='*50}")
            
            filename = f"{dataset_name}.pdf"
            filepath = self.download_pdf(dataset_info['url'], filename)
            
            if not filepath:
                all_companies[dataset_name] = []
                continue
            
            # Extract text
            text_content = self.extract_text_from_pdf(filepath)
            
            if not text_content:
                print(f"❌ No text extracted from {dataset_name}")
                all_companies[dataset_name] = []
                continue
            
            # Save raw text
            text_file = os.path.join(self.download_dir, f"{dataset_name}_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Parse companies
            companies = self.parse_fdny_companies(text_content, dataset_name, dataset_info['services'])
            all_companies[dataset_name] = companies
            total_companies += len(companies)
            
            print(f"✅ Extracted {len(companies)} companies")
            
            # Show samples
            if companies:
                print("📋 Sample companies:")
                for company in companies[:2]:
                    print(f"   • {company['company_name']}")
                    if company['phone']:
                        print(f"     📞 {company['phone']}")
                    print(f"     🏷️ {company['app_number']} (Expires: {company['approval_expiry']})")
        
        return {
            'datasets_processed': available_datasets,
            'companies_by_category': all_companies,
            'total_companies': total_companies
        }

    def save_complete_dataset(self, processed_data: Dict[str, Any]) -> str:
        """Save complete FDNY dataset"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"fdny_complete_dataset_{timestamp}.json"
        filepath = os.path.join(self.download_dir, filename)
        
        # Flatten all companies
        all_vendors = []
        for category, companies in processed_data['companies_by_category'].items():
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
                    'dataset_category': category,
                    'principal_name': company['principal_name'],
                    'insurance_expiry': company['insurance_expiry'],
                    'certification_date': None,
                    'violations': []
                }
                all_vendors.append(vendor)
        
        # Create output
        output_data = {
            'metadata': {
                'source': 'FDNY Official Approved Companies - Complete Dataset',
                'parsed_at': datetime.now().isoformat(),
                'total_companies': processed_data['total_companies'],
                'datasets_found': len(processed_data['datasets_processed']),
                'dataset_categories': list(processed_data['companies_by_category'].keys())
            },
            'datasets_processed': processed_data['datasets_processed'],
            'companies_by_category': processed_data['companies_by_category'],
            'all_vendors_flat': all_vendors
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return filepath

def main():
    """Main function to discover and parse all FDNY datasets"""
    print("🔥 Complete FDNY Dataset Finder & Parser")
    print("=" * 70)
    print("Discovering ALL available FDNY approved company datasets...")
    print("=" * 70)
    
    finder = CompleteFDNYDatasetFinder()
    
    # Process all datasets
    processed_data = finder.process_all_datasets()
    
    # Save results
    output_file = finder.save_complete_dataset(processed_data)
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 COMPLETE FDNY DATASET SUMMARY")
    print(f"{'='*70}")
    
    print(f"🎯 Total Datasets Found: {len(processed_data['datasets_processed'])}")
    print(f"🏢 Total Companies Extracted: {processed_data['total_companies']}")
    
    print(f"\n📋 Datasets Processed:")
    for dataset_name, dataset_info in processed_data['datasets_processed'].items():
        company_count = len(processed_data['companies_by_category'].get(dataset_name, []))
        print(f"  ✅ {dataset_name.replace('_', ' ').title()}: {company_count} companies")
        print(f"     {dataset_info['description']}")
    
    print(f"\n💾 Complete dataset saved to: {output_file}")
    print(f"\n🚀 Ready to integrate {processed_data['total_companies']} certified fire safety companies!")
    
    return processed_data, output_file

if __name__ == "__main__":
    main()
