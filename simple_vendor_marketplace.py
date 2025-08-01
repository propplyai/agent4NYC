"""
Simplified Vendor Marketplace for Propply AI
Focuses on official certification databases with basic review integration
"""

import os
import asyncio
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

# Import existing components
from nyc_opendata_client import NYCOpenDataClient

@dataclass
class CertifiedInspector:
    """Data class for certified inspectors from official databases"""
    name: str
    license_number: str
    license_type: str  # 'DOB_ELEVATOR', 'FDNY_FIRE_SAFETY', 'DOB_CONTRACTOR', etc.
    license_status: str  # 'ACTIVE', 'EXPIRED', 'SUSPENDED'
    license_expiry: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    certification_date: Optional[str] = None
    violations: List[Dict] = field(default_factory=list)

@dataclass
class VendorVerificationResult:
    """Comprehensive vendor verification result"""
    vendor_name: str
    overall_score: float  # 0-100
    review_data: Dict[str, Any]
    certifications: List[CertifiedInspector]
    license_status: str
    risk_factors: List[str]
    recommendations: List[str]
    last_verified: str

class SimpleVendorMarketplace:
    """
    Simplified vendor marketplace focusing on official certifications
    """
    
    def __init__(self, apify_token: str = None):
        """Initialize with API tokens and clients"""
        self.apify_token = apify_token or os.getenv('APIFY_TOKEN')
        self.logger = logging.getLogger(__name__)
        
        self.nyc_client = NYCOpenDataClient()
        
        # Official databases and APIs
        self.official_databases = {
            'dob_licenses': 'https://data.cityofnewyork.us/resource/t8hj-ruu2.json',
            'dob_contractors': 'https://data.cityofnewyork.us/resource/ckqw-hc7u.json'
        }
        
        # Service type mappings to compliance categories
        self.service_mappings = {
            'elevator': {
                'keywords': ['elevator', 'lift', 'escalator', 'conveying'],
                'required_licenses': ['DOB_ELEVATOR_INSPECTOR', 'DOB_ELEVATOR_AGENCY'],
                'compliance_categories': ['elevator_inspections', 'accessibility_compliance']
            },
            'fire_safety': {
                'keywords': ['fire', 'alarm', 'sprinkler', 'extinguisher', 'safety'],
                'required_licenses': ['FDNY_FIRE_SAFETY', 'FDNY_SPRINKLER'],
                'compliance_categories': ['fire_safety_inspections', 'emergency_systems']
            },
            'hvac': {
                'keywords': ['hvac', 'heating', 'cooling', 'ventilation', 'boiler'],
                'required_licenses': ['DOB_BOILER', 'EPA_REFRIGERANT'],
                'compliance_categories': ['boiler_inspections', 'cooling_tower_inspections']
            },
            'plumbing': {
                'keywords': ['plumbing', 'water', 'backflow', 'pipe'],
                'required_licenses': ['DOB_PLUMBER', 'BACKFLOW_TESTER'],
                'compliance_categories': ['backflow_prevention', 'water_tank_inspections']
            },
            'electrical': {
                'keywords': ['electrical', 'electric', 'wiring', 'panel'],
                'required_licenses': ['DOB_ELECTRICIAN'],
                'compliance_categories': ['electrical_inspections']
            },
            'structural': {
                'keywords': ['structural', 'facade', 'roof', 'building'],
                'required_licenses': ['DOB_STRUCTURAL_ENGINEER', 'DOB_ARCHITECT'],
                'compliance_categories': ['facade_inspections', 'structural_inspections']
            }
        }

    async def find_verified_vendors(self, 
                                  property_address: str, 
                                  service_type: str,
                                  compliance_requirements: List[str] = None) -> Dict[str, Any]:
        """
        Find and verify vendors for specific property and service type
        """
        try:
            self.logger.info(f"Finding verified vendors for {service_type} at {property_address}")
            
            # Get certified inspectors from official databases
            certified_inspectors = await self._get_certified_inspectors(service_type)
            
            # Create verification results for certified inspectors
            verified_vendors = []
            for inspector in certified_inspectors[:10]:  # Limit to top 10
                verification = self._create_verification_result(inspector)
                verified_vendors.append(verification)
            
            # Sort by overall score
            verified_vendors.sort(key=lambda x: x.overall_score, reverse=True)
            
            return {
                'property_address': property_address,
                'service_type': service_type,
                'total_vendors_found': len(verified_vendors),
                'verified_vendors': verified_vendors,
                'certification_summary': self._generate_certification_summary(certified_inspectors),
                'compliance_requirements': compliance_requirements or [],
                'search_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error finding verified vendors: {str(e)}")
            return {'error': str(e)}

    async def _get_certified_inspectors(self, service_type: str) -> List[CertifiedInspector]:
        """Get certified inspectors from official databases"""
        inspectors = []
        
        try:
            # DOB Licensed Contractors
            if service_type in ['elevator', 'structural', 'electrical', 'plumbing', 'hvac']:
                dob_inspectors = await self._get_dob_licensed_contractors(service_type)
                inspectors.extend(dob_inspectors)
            
            # FDNY Certified Companies (mock data for now)
            if service_type in ['fire_safety']:
                fdny_inspectors = await self._get_fdny_certified_companies()
                inspectors.extend(fdny_inspectors)
                
        except Exception as e:
            self.logger.error(f"Error getting certified inspectors: {str(e)}")
        
        return inspectors

    async def _get_dob_licensed_contractors(self, service_type: str) -> List[CertifiedInspector]:
        """Get DOB licensed contractors from NYC Open Data"""
        inspectors = []
        
        try:
            # Use NYC Open Data API for DOB licenses
            url = self.official_databases['dob_licenses']
            params = {
                '$limit': 200,
                '$where': f"license_status='ACTIVE'"
            }
            
            # Add service-specific filters
            service_mapping = self.service_mappings.get(service_type, {})
            keywords = service_mapping.get('keywords', [])
            
            if keywords:
                keyword_filter = " OR ".join([f"upper(license_type) like upper('%{kw}%')" for kw in keywords])
                params['$where'] += f" AND ({keyword_filter})"
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                for item in data:
                    inspector = CertifiedInspector(
                        name=item.get('licensee_name', 'Unknown'),
                        license_number=item.get('license_nbr', ''),
                        license_type=f"DOB_{item.get('license_type', '').upper().replace(' ', '_')}",
                        license_status=item.get('license_status', ''),
                        license_expiry=item.get('license_expiration_date'),
                        company_name=item.get('business_name'),
                        address=item.get('business_address'),
                        phone=item.get('business_phone'),
                        certification_date=item.get('license_creation_date')
                    )
                    inspectors.append(inspector)
                    
        except Exception as e:
            self.logger.error(f"Error getting DOB contractors: {str(e)}")
        
        return inspectors

    async def _get_fdny_certified_companies(self) -> List[CertifiedInspector]:
        """Get FDNY certified fire safety companies from real parsed data"""
        inspectors = []
        
        try:
            # Load real FDNY data from parsed JSON file
            fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
            
            if os.path.exists(fdny_file):
                with open(fdny_file, 'r', encoding='utf-8') as f:
                    fdny_data = json.load(f)
                
                # Extract all vendors from the flat list
                all_vendors = fdny_data.get('all_vendors_flat', [])
                
                for vendor in all_vendors:
                    inspector = CertifiedInspector(
                        name=vendor['name'],
                        license_number=vendor['license_number'],
                        license_type=vendor['license_type'],
                        license_status=vendor['license_status'],
                        license_expiry=vendor.get('license_expiry'),
                        company_name=vendor.get('company_name'),
                        address=vendor.get('address'),
                        phone=vendor.get('phone'),
                        specializations=vendor.get('specializations', []),
                        certification_date=vendor.get('certification_date')
                    )
                    inspectors.append(inspector)
                
                self.logger.info(f"Loaded {len(inspectors)} real FDNY companies from parsed data")
            else:
                self.logger.warning(f"FDNY data file not found: {fdny_file}")
                # Fallback to basic mock data
                mock_company = CertifiedInspector(
                    name='FDNY Data Not Available',
                    license_number='FDNY-MOCK',
                    license_type='FDNY_FIRE_SAFETY',
                    license_status='ACTIVE',
                    specializations=['fire_safety_inspection']
                )
                inspectors.append(mock_company)
                
        except Exception as e:
            self.logger.error(f"Error loading FDNY companies: {str(e)}")
        
        return inspectors

    def _create_verification_result(self, inspector: CertifiedInspector) -> VendorVerificationResult:
        """Create verification result for certified inspector"""
        
        # Calculate score based on certification
        score = 70  # Base score for certified inspectors
        risk_factors = []
        recommendations = []
        
        # Active license bonus
        if inspector.license_status == 'ACTIVE':
            score += 20
        else:
            risk_factors.append("License not active")
            score -= 20
        
        # License expiry check
        if inspector.license_expiry:
            try:
                expiry_date = datetime.strptime(inspector.license_expiry, '%Y-%m-%dT%H:%M:%S.%f')
                days_until_expiry = (expiry_date - datetime.now()).days
                if days_until_expiry < 30:
                    risk_factors.append("License expires soon")
                    score -= 10
                elif days_until_expiry < 0:
                    risk_factors.append("License expired")
                    score -= 30
            except:
                pass
        
        # Specializations bonus
        if inspector.specializations:
            score += 10
        
        # Contact info bonus
        if inspector.phone or inspector.address:
            score += 5
        else:
            recommendations.append("Verify contact information")
        
        return VendorVerificationResult(
            vendor_name=inspector.name,
            overall_score=min(100, max(0, score)),
            review_data={'source': 'official_database', 'reviews': []},
            certifications=[inspector],
            license_status=inspector.license_status,
            risk_factors=risk_factors,
            recommendations=recommendations,
            last_verified=datetime.now().isoformat()
        )

    def _generate_certification_summary(self, inspectors: List[CertifiedInspector]) -> Dict[str, Any]:
        """Generate summary of available certifications"""
        summary = {
            'total_certified_inspectors': len(inspectors),
            'active_licenses': len([i for i in inspectors if i.license_status == 'ACTIVE']),
            'license_types': {},
            'specializations': {}
        }
        
        for inspector in inspectors:
            # Count license types
            if inspector.license_type not in summary['license_types']:
                summary['license_types'][inspector.license_type] = 0
            summary['license_types'][inspector.license_type] += 1
            
            # Count specializations
            for spec in inspector.specializations:
                if spec not in summary['specializations']:
                    summary['specializations'][spec] = 0
                summary['specializations'][spec] += 1
        
        return summary

    def _extract_location(self, address: str) -> str:
        """Extract city/state from full address"""
        parts = address.split(',')
        if len(parts) >= 2:
            return f"{parts[-2].strip()}, {parts[-1].strip()}"
        return "New York, NY"

    async def get_compliance_vendors(self, compliance_categories: List[str]) -> Dict[str, List[VendorVerificationResult]]:
        """Get verified vendors for specific compliance categories"""
        vendors_by_category = {}
        
        for category in compliance_categories:
            # Map compliance category to service type
            service_type = self._map_compliance_to_service(category)
            if service_type:
                vendors = await self.find_verified_vendors(
                    property_address="New York, NY",  # Generic search
                    service_type=service_type,
                    compliance_requirements=[category]
                )
                vendors_by_category[category] = vendors.get('verified_vendors', [])
        
        return vendors_by_category

    def _map_compliance_to_service(self, compliance_category: str) -> Optional[str]:
        """Map compliance category to service type"""
        mapping = {
            'elevator_inspections': 'elevator',
            'fire_safety_inspections': 'fire_safety',
            'boiler_inspections': 'hvac',
            'cooling_tower_inspections': 'hvac',
            'backflow_prevention': 'plumbing',
            'water_tank_inspections': 'plumbing',
            'electrical_inspections': 'electrical',
            'facade_inspections': 'structural',
            'structural_inspections': 'structural'
        }
        return mapping.get(compliance_category)

# Example usage
async def main():
    """Example usage of simplified vendor marketplace"""
    marketplace = SimpleVendorMarketplace()
    
    # Find elevator inspectors
    result = await marketplace.find_verified_vendors(
        property_address="123 Main St, Brooklyn, NY 11201",
        service_type="elevator",
        compliance_requirements=["elevator_inspections"]
    )
    
    print(f"Found {result.get('total_vendors_found', 0)} verified vendors")
    for vendor in result.get('verified_vendors', [])[:3]:
        print(f"- {vendor.vendor_name}: Score {vendor.overall_score}/100")

if __name__ == "__main__":
    asyncio.run(main())
