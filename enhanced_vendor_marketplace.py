"""
Enhanced Vendor Marketplace for Propply AI
Integrates multiple data sources for comprehensive vendor verification:
- Google Maps & Yelp reviews (via Apify)
- NYC DOB licensed contractors database
- FDNY certified fire safety companies
- Elevator inspection agencies
- Official certification databases
"""

import os
import asyncio
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re

# Import existing components
from apify_integration import ApifyVendorScraper, VendorInfo, VendorReview
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

class EnhancedVendorMarketplace:
    """
    Enhanced vendor marketplace with comprehensive verification
    """
    
    def __init__(self, apify_token: str = None):
        """Initialize with API tokens and clients"""
        self.apify_token = apify_token or os.getenv('APIFY_TOKEN')
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        if self.apify_token:
            self.apify_scraper = ApifyVendorScraper(self.apify_token)
        else:
            self.logger.warning("No Apify token provided - review scraping will be disabled")
            self.apify_scraper = None
            
        self.nyc_client = NYCOpenDataClient()
        
        # Official databases and APIs
        self.official_databases = {
            'dob_licenses': 'https://data.cityofnewyork.us/resource/t8hj-ruu2.json',
            'dob_contractors': 'https://data.cityofnewyork.us/resource/ckqw-hc7u.json',
            'fdny_companies': 'https://www.nyc.gov/assets/fdny/downloads/pdf/business/approved-companies-fire-alarm-system-inspection-testing-service.pdf'
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
        
        Args:
            property_address: Property address
            service_type: Type of service needed
            compliance_requirements: Specific compliance requirements
            
        Returns:
            Dictionary with verified vendor recommendations
        """
        try:
            self.logger.info(f"Finding verified vendors for {service_type} at {property_address}")
            
            # Step 1: Get basic vendor info from review platforms
            review_vendors = []
            if self.apify_scraper:
                location = self._extract_location(property_address)
                
                # Search Yelp for vendors
                yelp_vendors = await self.apify_scraper.scrape_yelp_business_info(
                    search_term=service_type,
                    location=location,
                    max_results=20
                )
                review_vendors.extend(yelp_vendors)
            
            # Step 2: Get certified inspectors from official databases
            certified_inspectors = await self._get_certified_inspectors(service_type)
            
            # Step 3: Cross-reference and verify
            verified_vendors = []
            for vendor in review_vendors:
                verification = await self._verify_vendor_comprehensive(
                    vendor, service_type, certified_inspectors
                )
                if verification.overall_score >= 60:  # Minimum threshold
                    verified_vendors.append(verification)
            
            # Step 4: Add certified inspectors not found in reviews
            for inspector in certified_inspectors:
                if not any(v.vendor_name.lower() in inspector.name.lower() or 
                          inspector.name.lower() in v.vendor_name.lower() 
                          for v in verified_vendors):
                    # Create verification result for certified inspector
                    verification = VendorVerificationResult(
                        vendor_name=inspector.name,
                        overall_score=75,  # Base score for certified inspectors
                        review_data={'source': 'official_database', 'reviews': []},
                        certifications=[inspector],
                        license_status=inspector.license_status,
                        risk_factors=[],
                        recommendations=['Officially certified but no online reviews found'],
                        last_verified=datetime.now().isoformat()
                    )
                    verified_vendors.append(verification)
            
            # Sort by overall score
            verified_vendors.sort(key=lambda x: x.overall_score, reverse=True)
            
            return {
                'property_address': property_address,
                'service_type': service_type,
                'total_vendors_found': len(verified_vendors),
                'verified_vendors': verified_vendors[:10],  # Top 10
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
            if service_type in ['elevator', 'structural', 'electrical', 'plumbing']:
                dob_inspectors = await self._get_dob_licensed_contractors(service_type)
                inspectors.extend(dob_inspectors)
            
            # FDNY Certified Companies
            if service_type in ['fire_safety', 'sprinkler']:
                fdny_inspectors = await self._get_fdny_certified_companies()
                inspectors.extend(fdny_inspectors)
            
            # Elevator Agencies (special case)
            if service_type == 'elevator':
                elevator_agencies = await self._get_elevator_agencies()
                inspectors.extend(elevator_agencies)
                
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
                '$limit': 1000,
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
                        name=item.get('licensee_name', ''),
                        license_number=item.get('license_nbr', ''),
                        license_type=f"DOB_{item.get('license_type', '').upper()}",
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
        """Get FDNY certified fire safety companies"""
        inspectors = []
        
        try:
            # This would typically involve parsing the FDNY PDF or accessing their API
            # For now, we'll use a placeholder implementation
            # In production, you'd want to implement PDF parsing or find an API endpoint
            
            # Placeholder data - in real implementation, parse FDNY approved companies list
            fdny_companies = [
                {
                    'name': 'NYC Fire Safety Services',
                    'license_number': 'FDNY-001',
                    'specializations': ['fire_alarm_inspection', 'sprinkler_testing']
                },
                # Add more companies from actual FDNY database
            ]
            
            for company in fdny_companies:
                inspector = CertifiedInspector(
                    name=company['name'],
                    license_number=company['license_number'],
                    license_type='FDNY_FIRE_SAFETY',
                    license_status='ACTIVE',
                    specializations=company.get('specializations', [])
                )
                inspectors.append(inspector)
                
        except Exception as e:
            self.logger.error(f"Error getting FDNY companies: {str(e)}")
        
        return inspectors

    async def _get_elevator_agencies(self) -> List[CertifiedInspector]:
        """Get DOB approved elevator inspection agencies"""
        inspectors = []
        
        try:
            # Query DOB for elevator agencies
            # This would use the DOB BIS Web system or API
            
            # Placeholder implementation
            elevator_agencies = [
                {
                    'name': 'Metropolitan Elevator Inspections',
                    'license_number': 'ELV-001',
                    'address': 'Brooklyn, NY'
                },
                # Add more from actual DOB database
            ]
            
            for agency in elevator_agencies:
                inspector = CertifiedInspector(
                    name=agency['name'],
                    license_number=agency['license_number'],
                    license_type='DOB_ELEVATOR_AGENCY',
                    license_status='ACTIVE',
                    address=agency.get('address'),
                    specializations=['elevator_inspection', 'escalator_inspection']
                )
                inspectors.append(inspector)
                
        except Exception as e:
            self.logger.error(f"Error getting elevator agencies: {str(e)}")
        
        return inspectors

    async def _verify_vendor_comprehensive(self, 
                                         vendor: VendorInfo, 
                                         service_type: str,
                                         certified_inspectors: List[CertifiedInspector]) -> VendorVerificationResult:
        """Comprehensive vendor verification"""
        
        # Find matching certifications
        matching_certs = []
        for inspector in certified_inspectors:
            if (vendor.name.lower() in inspector.name.lower() or 
                inspector.name.lower() in vendor.name.lower() or
                (inspector.company_name and vendor.name.lower() in inspector.company_name.lower())):
                matching_certs.append(inspector)
        
        # Calculate verification score
        score = 0
        risk_factors = []
        recommendations = []
        
        # Base score from reviews
        if vendor.overall_rating >= 4.5:
            score += 30
        elif vendor.overall_rating >= 4.0:
            score += 25
        elif vendor.overall_rating >= 3.5:
            score += 20
        else:
            score += 10
            risk_factors.append("Low review rating")
        
        # Review count factor
        if vendor.total_reviews >= 50:
            score += 20
        elif vendor.total_reviews >= 20:
            score += 15
        elif vendor.total_reviews >= 10:
            score += 10
        else:
            risk_factors.append("Limited review history")
        
        # Certification bonus
        if matching_certs:
            score += 30
            active_certs = [c for c in matching_certs if c.license_status == 'ACTIVE']
            if not active_certs:
                risk_factors.append("Expired or inactive licenses")
                score -= 15
        else:
            risk_factors.append("No official certifications found")
            recommendations.append("Verify licensing status before hiring")
        
        # Service type alignment
        service_keywords = self.service_mappings.get(service_type, {}).get('keywords', [])
        if any(keyword in ' '.join(vendor.categories).lower() for keyword in service_keywords):
            score += 10
        
        # License status
        license_status = 'UNKNOWN'
        if matching_certs:
            active_certs = [c for c in matching_certs if c.license_status == 'ACTIVE']
            if active_certs:
                license_status = 'ACTIVE'
            else:
                license_status = 'EXPIRED/INACTIVE'
        
        # Get detailed reviews if available
        review_data = {
            'platform': vendor.platform,
            'rating': vendor.overall_rating,
            'total_reviews': vendor.total_reviews,
            'categories': vendor.categories
        }
        
        if self.apify_scraper and hasattr(vendor, 'platform_url'):
            try:
                if vendor.platform == 'yelp':
                    reviews = await self.apify_scraper.scrape_yelp_reviews(
                        vendor.platform_url, max_reviews=10
                    )
                    review_data['recent_reviews'] = [
                        {
                            'rating': r.rating,
                            'text': r.review_text[:200] + '...' if len(r.review_text) > 200 else r.review_text,
                            'date': r.review_date
                        } for r in reviews[:5]
                    ]
            except Exception as e:
                self.logger.warning(f"Could not fetch detailed reviews: {str(e)}")
        
        return VendorVerificationResult(
            vendor_name=vendor.name,
            overall_score=min(100, max(0, score)),
            review_data=review_data,
            certifications=matching_certs,
            license_status=license_status,
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
    """Example usage of enhanced vendor marketplace"""
    apify_token = os.getenv('APIFY_TOKEN')
    
    marketplace = EnhancedVendorMarketplace(apify_token)
    
    # Find verified elevator inspectors
    result = await marketplace.find_verified_vendors(
        property_address="123 Main St, Brooklyn, NY 11201",
        service_type="elevator",
        compliance_requirements=["elevator_inspections"]
    )
    
    print(f"Found {result.get('total_vendors_found', 0)} verified vendors")
    for vendor in result.get('verified_vendors', [])[:3]:
        print(f"- {vendor.vendor_name}: Score {vendor.overall_score}/100")
        print(f"  License Status: {vendor.license_status}")
        print(f"  Certifications: {len(vendor.certifications)}")
        if vendor.risk_factors:
            print(f"  Risk Factors: {', '.join(vendor.risk_factors)}")

if __name__ == "__main__":
    asyncio.run(main())
