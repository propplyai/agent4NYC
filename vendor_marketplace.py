#!/usr/bin/env python3
"""
Vendor Marketplace Integration
=============================

Main coordination service that uses Google Places API to provide 
comprehensive vendor recommendations for compliance violations.
"""

import logging
from typing import Dict, List, Optional, Tuple
import asyncio
from datetime import datetime
import json

from vendor_service import VendorService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VendorMarketplace:
    """Main vendor marketplace service"""
    
    def __init__(self):
        """Initialize vendor services"""
        self.vendor_service = VendorService()
        
        # Map violation categories to contractor types
        self.violation_to_category_map = {
            'hpd_violations': 'hpd',
            'dob_violations': 'dob', 
            'elevator_devices': 'elevator',
            'boiler_devices': 'boiler',
            'electrical_permits': 'electrical'
        }
    
    def get_vendors_for_property(self, 
                               property_address: str,
                               violation_data: Dict,
                               max_vendors_per_category: int = 5) -> Dict[str, List[Dict]]:
        """
        Get vendor recommendations based on property violations
        
        Args:
            property_address: Property address for proximity search
            violation_data: Dictionary with violation counts by category
            max_vendors_per_category: Maximum vendors per category
            
        Returns:
            Dictionary mapping categories to vendor lists with reviews
        """
        try:
            logger.info(f"Getting vendors for property: {property_address}")
            
            # Determine which categories need vendors based on violations
            categories_needed = self._identify_needed_categories(violation_data)
            
            if not categories_needed:
                logger.info("No violations found, providing general contractors")
                categories_needed = ['hpd']  # Default to general contractors
            
            logger.info(f"Categories needed: {categories_needed}")
            
            # Get contractors for each category
            vendor_results = self.vendor_service.find_contractors_for_violations(
                property_address=property_address,
                violation_categories=categories_needed,
                max_per_category=max_vendors_per_category
            )
            
            # Enhanced results using only Google Places data (no Apify)
            enhanced_results = {}
            
            for category, vendors in vendor_results.items():
                enhanced_vendors = []
                
                for vendor in vendors:
                    # Get enhanced details from Google Places API only
                    enhanced_vendor = self._enhance_vendor_with_places_data(vendor)
                    enhanced_vendors.append(enhanced_vendor)
                
                enhanced_results[category] = enhanced_vendors
            
            logger.info(f"Successfully retrieved vendors for {len(enhanced_results)} categories")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error getting vendors for property: {e}")
            return {}
    
    def get_vendor_details_with_reviews(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed vendor information using Google Places API only
        
        Args:
            place_id: Google Places ID
            
        Returns:
            Enhanced vendor details from Google Places
        """
        try:
            # Get detailed contractor info from Google Places
            contractor_details = self.vendor_service.get_contractor_details(place_id)
            
            if not contractor_details:
                return None
            
            # Mark as enhanced with Google Places data
            contractor_details['reviews_enhanced'] = True
            contractor_details['data_source'] = 'Google Places'
            
            return contractor_details
            
        except Exception as e:
            logger.error(f"Error getting vendor details for {place_id}: {e}")
            return None
    
    def _identify_needed_categories(self, violation_data: Dict) -> List[str]:
        """Identify which contractor categories are needed based on violations"""
        categories = []
        
        # Check HPD violations
        if violation_data.get('hpd_violations_active', 0) > 0:
            categories.append('hpd')
        
        # Check DOB violations
        if violation_data.get('dob_violations_active', 0) > 0:
            categories.append('dob')
        
        # Check elevator issues
        if violation_data.get('elevator_devices_active', 0) > 0:
            categories.append('elevator')
        
        # Check boiler issues (assume need maintenance if devices exist)
        if violation_data.get('boiler_devices_total', 0) > 0:
            categories.append('boiler')
        
        # Check electrical permits
        if violation_data.get('electrical_permits_active', 0) > 0:
            categories.append('electrical')
        
        # Always include fire safety if there are any violations
        if any(violation_data.get(key, 0) > 0 for key in ['hpd_violations_active', 'dob_violations_active']):
            categories.append('fire_safety')
        
        return categories
    
    def _enhance_vendor_with_places_data(self, vendor: Dict) -> Dict:
        """Enhance a vendor with Google Places data only"""
        try:
            # Get detailed vendor info from Google Places
            place_id = vendor.get('place_id')
            if not place_id:
                vendor['reviews_enhanced'] = False
                vendor['data_source'] = 'Basic'
                return vendor
            
            detailed_info = self.vendor_service.get_contractor_details(place_id)
            if not detailed_info:
                vendor['reviews_enhanced'] = False
                vendor['data_source'] = 'Basic'
                return vendor
            
            # Update vendor with detailed Google Places info
            vendor.update(detailed_info)
            
            # Mark as enhanced with Google Places data (no Apify needed)
            vendor['reviews_enhanced'] = True
            vendor['data_source'] = 'Google Places'
            vendor['enhanced_rating'] = detailed_info.get('rating')
            vendor['enhanced_review_count'] = detailed_info.get('rating_count')
            
            return vendor
            
        except Exception as e:
            logger.error(f"Error enhancing vendor with Places data: {e}")
            vendor['reviews_enhanced'] = False
            vendor['data_source'] = 'Basic'
            return vendor
    
    def format_vendor_for_ui(self, vendor: Dict, category: str) -> Dict:
        """Format vendor data for UI display"""
        return {
            'place_id': vendor.get('place_id'),
            'name': vendor.get('name'),
            'address': vendor.get('address'),
            'phone': vendor.get('phone'),
            'website': vendor.get('website'),
            'rating': vendor.get('enhanced_rating') or vendor.get('rating'),
            'rating_count': vendor.get('enhanced_review_count') or vendor.get('rating_count'),
            'distance_miles': vendor.get('distance_miles'),
            'business_status': vendor.get('business_status'),
            'opening_hours': vendor.get('opening_hours'),
            'price_level': vendor.get('price_level'),
            'category': category,
            'search_term': vendor.get('search_term'),
            'reviews_enhanced': vendor.get('reviews_enhanced', False),
            'google_maps_url': vendor.get('google_maps_url'),
            'photos': vendor.get('photos', []),
            'google_reviews': vendor.get('reviews', [])
        }

def test_vendor_marketplace():
    """Test the vendor marketplace integration"""
    marketplace = VendorMarketplace()
    
    # Test data based on a property with violations
    test_address = "140 West 28 Street, Manhattan, NY 10001"
    test_violations = {
        'hpd_violations_active': 2,
        'dob_violations_active': 1,
        'elevator_devices_active': 6,
        'boiler_devices_total': 1,
        'electrical_permits_active': 0
    }
    
    print("Testing Vendor Marketplace Integration...")
    print("=" * 50)
    
    print(f"\nProperty: {test_address}")
    print(f"Violations: {test_violations}")
    
    print("\nGetting vendor recommendations...")
    vendors = marketplace.get_vendors_for_property(
        property_address=test_address,
        violation_data=test_violations,
        max_vendors_per_category=3
    )
    
    print(f"\nFound vendors for {len(vendors)} categories:")
    
    for category, vendor_list in vendors.items():
        print(f"\n{category.upper()} Vendors:")
        for i, vendor in enumerate(vendor_list, 1):
            formatted = marketplace.format_vendor_for_ui(vendor, category)
            reviews_status = "✅ Enhanced" if formatted['reviews_enhanced'] else "📋 Basic"
            
            print(f"  {i}. {formatted['name']}")
            print(f"     Rating: {formatted['rating'] or 'N/A'}/5 ({formatted['rating_count'] or 0} reviews)")
            print(f"     Distance: {formatted['distance_miles']} miles")
            print(f"     Reviews: {reviews_status}")
            if formatted['common_keywords']:
                print(f"     Keywords: {', '.join(formatted['common_keywords'][:3])}")
    
    print("\n✅ Vendor marketplace test completed")

if __name__ == "__main__":
    test_vendor_marketplace()