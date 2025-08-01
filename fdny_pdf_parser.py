"""
FDNY PDF Parser for Fire Inspector Certification Data
Downloads and parses official FDNY approved companies PDF
"""

import requests
import os
import json
from typing import List, Dict, Any
from datetime import datetime
import re

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Installing...")
    os.system("pip install PyPDF2")
    import PyPDF2

try:
    import pdfplumber
except ImportError:
    print("pdfplumber not installed. Installing...")
    os.system("pip install pdfplumber")
    import pdfplumber

class FDNYPDFParser:
    """Parser for FDNY approved companies PDF files"""
    
    def __init__(self):
        self.fdny_urls = {
            'fire_alarm_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-fire-alarm-system-inspection-testing-service.pdf',
            'sprinkler_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-sprinkler-system-inspection-testing-service.pdf',
            'extinguisher_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-portable-fire-extinguisher-service.pdf'
        }
        
        self.download_dir = 'fdny_pdfs'
        os.makedirs(self.download_dir, exist_ok=True)

    def download_pdf(self, url: str, filename: str) -> str:
        """Download PDF from URL"""
        try:
            print(f"Downloading PDF from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filepath} ({len(response.content)} bytes)")
            return filepath
            
        except Exception as e:
            print(f"Error downloading PDF: {str(e)}")
            return None

    def parse_pdf_with_pdfplumber(self, filepath: str) -> List[str]:
        """Parse PDF using pdfplumber for better text extraction"""
        text_content = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                print(f"PDF has {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages):
                    print(f"Processing page {page_num + 1}...")
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    # Try to extract tables
                    tables = page.extract_tables()
                    if tables:
                        print(f"Found {len(tables)} tables on page {page_num + 1}")
                        for table in tables:
                            # Convert table to text
                            for row in table:
                                if row:
                                    text_content.append(" | ".join([cell or "" for cell in row]))
                                    
        except Exception as e:
            print(f"Error parsing PDF with pdfplumber: {str(e)}")
            
        return text_content

    def parse_pdf_with_pypdf2(self, filepath: str) -> List[str]:
        """Parse PDF using PyPDF2 as fallback"""
        text_content = []
        
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"PDF has {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    print(f"Processing page {page_num + 1}...")
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                        
        except Exception as e:
            print(f"Error parsing PDF with PyPDF2: {str(e)}")
            
        return text_content

    def extract_company_data(self, text_content: List[str]) -> List[Dict[str, Any]]:
        """Extract company information from parsed text"""
        companies = []
        
        # Common patterns for company information
        patterns = {
            'company_name': r'^([A-Z][A-Z\s&,.\-\']+(?:INC|LLC|CORP|CO|COMPANY|SERVICES|SYSTEMS|FIRE|SAFETY|PROTECTION)\.?)',
            'phone': r'(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            'address': r'(\d+\s+[A-Za-z\s,]+(?:ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|PL|PLACE|WAY|LN|LANE))',
            'license_number': r'([A-Z]{2,4}[-]?\d{3,6})',
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        }
        
        for text_block in text_content:
            lines = text_block.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Look for company names (usually in all caps or title case)
                company_match = re.search(patterns['company_name'], line, re.IGNORECASE)
                if company_match:
                    company_name = company_match.group(1).strip()
                    
                    # Skip common headers/footers
                    skip_terms = ['FDNY', 'FIRE DEPARTMENT', 'NEW YORK CITY', 'PAGE', 'APPROVED COMPANIES']
                    if any(term in company_name.upper() for term in skip_terms):
                        continue
                    
                    company_data = {
                        'name': company_name,
                        'phone': None,
                        'address': None,
                        'license_number': None,
                        'email': None,
                        'services': [],
                        'source_line': line
                    }
                    
                    # Look for additional info in surrounding lines
                    context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                    context_text = ' '.join(context_lines)
                    
                    # Extract phone
                    phone_match = re.search(patterns['phone'], context_text)
                    if phone_match:
                        company_data['phone'] = phone_match.group(1)
                    
                    # Extract address
                    address_match = re.search(patterns['address'], context_text)
                    if address_match:
                        company_data['address'] = address_match.group(1)
                    
                    # Extract license number
                    license_match = re.search(patterns['license_number'], context_text)
                    if license_match:
                        company_data['license_number'] = license_match.group(1)
                    
                    # Extract email
                    email_match = re.search(patterns['email'], context_text)
                    if email_match:
                        company_data['email'] = email_match.group(1)
                    
                    # Determine services based on context
                    services_keywords = {
                        'fire_alarm': ['FIRE ALARM', 'ALARM SYSTEM', 'FIRE DETECTION'],
                        'sprinkler': ['SPRINKLER', 'SUPPRESSION', 'WATER SYSTEM'],
                        'extinguisher': ['EXTINGUISHER', 'PORTABLE FIRE'],
                        'emergency_lighting': ['EMERGENCY LIGHT', 'EXIT SIGN'],
                        'inspection': ['INSPECTION', 'TESTING', 'SERVICE'],
                        'installation': ['INSTALLATION', 'INSTALL']
                    }
                    
                    for service, keywords in services_keywords.items():
                        if any(keyword in context_text.upper() for keyword in keywords):
                            company_data['services'].append(service)
                    
                    companies.append(company_data)
        
        # Remove duplicates based on company name
        unique_companies = []
        seen_names = set()
        
        for company in companies:
            name_key = company['name'].upper().strip()
            if name_key not in seen_names and len(name_key) > 3:
                seen_names.add(name_key)
                unique_companies.append(company)
        
        return unique_companies

    def download_and_parse_all(self) -> Dict[str, List[Dict]]:
        """Download and parse all FDNY PDF files"""
        all_data = {}
        
        for category, url in self.fdny_urls.items():
            print(f"\n{'='*60}")
            print(f"Processing {category}")
            print(f"{'='*60}")
            
            filename = f"{category}.pdf"
            filepath = self.download_pdf(url, filename)
            
            if not filepath:
                print(f"Failed to download {category}")
                continue
            
            # Try pdfplumber first, then PyPDF2 as fallback
            text_content = self.parse_pdf_with_pdfplumber(filepath)
            
            if not text_content:
                print("pdfplumber failed, trying PyPDF2...")
                text_content = self.parse_pdf_with_pypdf2(filepath)
            
            if text_content:
                companies = self.extract_company_data(text_content)
                print(f"Extracted {len(companies)} companies from {category}")
                
                # Save raw text for debugging
                with open(f"{self.download_dir}/{category}_text.txt", 'w', encoding='utf-8') as f:
                    f.write('\n\n---PAGE BREAK---\n\n'.join(text_content))
                
                all_data[category] = companies
            else:
                print(f"No text extracted from {category}")
                all_data[category] = []
        
        return all_data

    def save_parsed_data(self, data: Dict[str, List[Dict]], filename: str = None):
        """Save parsed data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fdny_companies_{timestamp}.json"
        
        filepath = os.path.join(self.download_dir, filename)
        
        # Add metadata
        output_data = {
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'source': 'FDNY Official PDF Documents',
                'categories': list(data.keys()),
                'total_companies': sum(len(companies) for companies in data.values())
            },
            'companies_by_category': data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nParsed data saved to: {filepath}")
        return filepath

def main():
    """Main function to download and parse FDNY PDFs"""
    print("🔥 FDNY PDF Parser for Fire Inspector Certification Data")
    print("="*70)
    
    parser = FDNYPDFParser()
    
    # Download and parse all PDFs
    parsed_data = parser.download_and_parse_all()
    
    # Save results
    output_file = parser.save_parsed_data(parsed_data)
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 PARSING SUMMARY")
    print(f"{'='*70}")
    
    total_companies = 0
    for category, companies in parsed_data.items():
        print(f"{category.replace('_', ' ').title()}: {len(companies)} companies")
        total_companies += len(companies)
        
        # Show sample companies
        if companies:
            print("  Sample companies:")
            for company in companies[:3]:
                print(f"    - {company['name']}")
                if company['phone']:
                    print(f"      Phone: {company['phone']}")
                if company['services']:
                    print(f"      Services: {', '.join(company['services'])}")
    
    print(f"\nTotal Companies Extracted: {total_companies}")
    print(f"Output File: {output_file}")
    
    return parsed_data, output_file

if __name__ == "__main__":
    main()
