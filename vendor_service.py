#!/usr/bin/env python3
"""
Google Places API Service for Contractor Search
==============================================

Service to find contractors and service providers using Google Places API
for the Propply AI vendor marketplace.
"""

import googlemaps
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VendorService:
    """Service for finding contractors using Google Places API"""
    
    def __init__(self, api_key: str = "AIzaSyA4gSJ9LDVqQ9AVxw3zVoHSQQVr_9W2V54"):
        """Initialize Google Maps client"""
        self.gmaps = googlemaps.Client(key=api_key)
        self.api_key = api_key
        
        # Mapping violation categories to contractor search terms
        self.contractor_categories = {
            'hpd': [
                'general contractor NYC',
                'handyman services NYC', 
                'plumbing contractor NYC',
                'heating repair NYC',
                'apartment maintenance NYC'
            ],
            'dob': [
                'structural engineer NYC',
                'general contractor NYC',
                'building code compliance NYC',
                'architect NYC',
                'construction contractor NYC'
            ],
            'elevator': [
                'elevator repair NYC',
                'elevator inspection NYC',
                'elevator maintenance NYC',
                'elevator contractor NYC',
                'conveyor repair NYC'
            ],
            'boiler': [
                'boiler repair NYC',
                'HVAC contractor NYC',
                'boiler inspection NYC',
                'heating system repair NYC',
                'boiler maintenance NYC'
            ],
            'electrical': [
                'electrician NYC',
                'electrical contractor NYC',
                'electrical inspection NYC',
                'electrical permits NYC',
                'commercial electrician NYC'
            ],
            'fire_safety': [
                'fire safety inspection NYC',
                'fire alarm installation NYC',
                'fire suppression systems NYC',
                'fire alarm testing NYC',
                'FDNY approved companies NYC'
            ]
        }
    
    def find_contractors_by_category(self, 
                                   category: str, 
                                   property_address: str,
                                   radius_miles: float = 10.0,
                                   max_results: int = 10) -> List[Dict]:
        """
        Find contractors for a specific violation category near a property
        
        Args:
            category: Violation category (hpd, dob, elevator, boiler, electrical, fire_safety)
            property_address: Property address for proximity search
            radius_miles: Search radius in miles
            max_results: Maximum number of results to return
            
        Returns:
            List of contractor dictionaries with business info
        """
        try:
            logger.info(f"Searching for {category} contractors near {property_address}")
            
            # Get coordinates for property address
            property_coords = self._geocode_address(property_address)
            if not property_coords:
                logger.error(f"Could not geocode address: {property_address}")
                return []
            
            # Get search terms for this category
            search_terms = self.contractor_categories.get(category, [f'{category} contractor NYC'])
            
            all_contractors = []
            seen_place_ids = set()
            
            # Search for contractors using each search term
            for search_term in search_terms:
                contractors = self._search_places(
                    query=search_term,
                    location=property_coords,
                    radius_meters=int(radius_miles * 1609.34),  # Convert miles to meters
                    max_results=max_results // len(search_terms) + 1
                )
                
                # Filter duplicates and add to results
                for contractor in contractors:
                    if contractor['place_id'] not in seen_place_ids:
                        seen_place_ids.add(contractor['place_id'])
                        contractor['search_category'] = category
                        contractor['search_term'] = search_term
                        all_contractors.append(contractor)
            
            # Sort by rating and distance, limit results
            all_contractors.sort(key=lambda x: (-(x.get('rating') or 0), x.get('distance_miles', float('inf'))))
            
            logger.info(f"Found {len(all_contractors)} contractors for {category}")
            return all_contractors[:max_results]
            
        except Exception as e:
            logger.error(f"Error finding contractors for {category}: {e}")
            return []
    
    def find_contractors_for_violations(self, 
                                      property_address: str,
                                      violation_categories: List[str],
                                      max_per_category: int = 5) -> Dict[str, List[Dict]]:
        """
        Find contractors for multiple violation categories
        
        Args:
            property_address: Property address
            violation_categories: List of violation categories
            max_per_category: Max contractors per category
            
        Returns:
            Dictionary mapping categories to contractor lists
        """
        results = {}
        
        for category in violation_categories:
            contractors = self.find_contractors_by_category(
                category=category,
                property_address=property_address,
                max_results=max_per_category
            )
            if contractors:
                results[category] = contractors
        
        return results
    
    def get_contractor_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific contractor
        
        Args:
            place_id: Google Places ID for the business
            
        Returns:
            Detailed contractor information
        """
        try:
            # Request detailed place information (using valid fields only)
            fields = [
                'place_id', 'name', 'formatted_address', 'geometry',
                'formatted_phone_number', 'international_phone_number',
                'website', 'rating', 'user_ratings_total', 'reviews',
                'opening_hours', 'business_status', 'price_level', 'url'
            ]
            
            result = self.gmaps.place(place_id=place_id, fields=fields)
            
            if result['status'] == 'OK':
                place = result['result']
                
                # Format the response
                contractor = {
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'address': place.get('formatted_address'),
                    'phone': place.get('formatted_phone_number'),
                    'website': place.get('website'),
                    'rating': place.get('rating'),
                    'rating_count': place.get('user_ratings_total'),
                    'google_maps_url': place.get('url'),
                    'business_status': place.get('business_status'),
                    'price_level': place.get('price_level'),
                    'opening_hours': self._format_opening_hours(place.get('opening_hours')),
                    'reviews': self._format_reviews(place.get('reviews', []))
                }
                
                return contractor
            else:
                logger.error(f"Places API error: {result['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting contractor details for {place_id}: {e}")
            return None
    
    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address to get coordinates"""
        try:
            geocode_result = self.gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return (location['lat'], location['lng'])
            return None
        except Exception as e:
            logger.error(f"Geocoding error for {address}: {e}")
            return None
    
    def _search_places(self, 
                      query: str, 
                      location: Tuple[float, float],
                      radius_meters: int,
                      max_results: int = 10) -> List[Dict]:
        """Search for places using text search"""
        try:
            # Use text search for better results with complex queries
            places_result = self.gmaps.places(
                query=query,
                location=location,
                radius=radius_meters,
                type='establishment'
            )
            
            contractors = []
            
            if places_result['status'] == 'OK':
                for place in places_result.get('results', []):
                    # Calculate distance
                    place_location = place['geometry']['location']
                    distance_miles = self._calculate_distance(
                        location, 
                        (place_location['lat'], place_location['lng'])
                    )
                    
                    contractor = {
                        'place_id': place['place_id'],
                        'name': place['name'],
                        'address': place.get('formatted_address', place.get('vicinity', '')),
                        'rating': place.get('rating'),
                        'rating_count': place.get('user_ratings_total'),
                        'price_level': place.get('price_level'),
                        'types': place.get('types', []),
                        'business_status': place.get('business_status'),
                        'distance_miles': round(distance_miles, 2),
                        'latitude': place_location['lat'],
                        'longitude': place_location['lng']
                    }
                    
                    contractors.append(contractor)
            
            return contractors[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching places for '{query}': {e}")
            return []
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in miles"""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = radians(coord1[0]), radians(coord1[1])
        lat2, lon2 = radians(coord2[0]), radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in miles
        return 3959 * c
    
    def _format_opening_hours(self, opening_hours: Optional[Dict]) -> Optional[Dict]:
        """Format opening hours data"""
        if not opening_hours:
            return None
            
        return {
            'open_now': opening_hours.get('open_now'),
            'weekday_text': opening_hours.get('weekday_text', [])
        }
    
    def _format_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """Format reviews data (first 3 reviews)"""
        formatted_reviews = []
        
        for review in reviews[:3]:  # Limit to 3 reviews
            formatted_review = {
                'author_name': review.get('author_name'),
                'rating': review.get('rating'),
                'text': review.get('text'),
                'time': review.get('time'),
                'relative_time_description': review.get('relative_time_description')
            }
            formatted_reviews.append(formatted_review)
        
        return formatted_reviews
    
    def _get_photo_urls(self, photos: List[Dict]) -> List[str]:
        """Get photo URLs from photo references"""
        photo_urls = []
        
        for photo in photos[:3]:  # Limit to 3 photos
            photo_reference = photo.get('photo_reference')
            if photo_reference:
                # Construct photo URL
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={self.api_key}"
                photo_urls.append(photo_url)
        
        return photo_urls

def test_vendor_service():
    """Test the vendor service"""
    service = VendorService()
    
    # Test address
    test_address = "140 West 28 Street, Manhattan, NY 10001"
    
    print("Testing Vendor Service...")
    print("=" * 50)
    
    # Test single category search
    print(f"\n1. Testing elevator contractors near {test_address}")
    elevator_contractors = service.find_contractors_by_category(
        category='elevator',
        property_address=test_address,
        max_results=5
    )
    
    print(f"Found {len(elevator_contractors)} elevator contractors:")
    for contractor in elevator_contractors:
        print(f"  - {contractor['name']} ({contractor.get('rating', 'No rating')}/5) - {contractor['distance_miles']} miles")
    
    # Test multiple categories
    print(f"\n2. Testing multiple categories")
    all_contractors = service.find_contractors_for_violations(
        property_address=test_address,
        violation_categories=['hpd', 'electrical'],
        max_per_category=3
    )
    
    for category, contractors in all_contractors.items():
        print(f"\n{category.upper()} Contractors:")
        for contractor in contractors:
            print(f"  - {contractor['name']} ({contractor.get('rating', 'No rating')}/5)")
    
    # Test detailed contractor info
    if elevator_contractors:
        print(f"\n3. Testing detailed info for: {elevator_contractors[0]['name']}")
        details = service.get_contractor_details(elevator_contractors[0]['place_id'])
        if details:
            print(f"  Phone: {details.get('phone', 'N/A')}")
            print(f"  Website: {details.get('website', 'N/A')}")
            print(f"  Business Status: {details.get('business_status', 'N/A')}")

if __name__ == "__main__":
    test_vendor_service()