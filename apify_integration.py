"""
Apify Integration Module for Propply AI
Handles vendor review scraping from Google Maps and Yelp using Apify platform
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib

try:
    from apify_client import ApifyClient
    ApifyClientAsync = None  # Not available in this version
except ImportError:
    print("Please install apify-client: pip install apify-client")
    ApifyClient = None
    ApifyClientAsync = None

@dataclass
class VendorReview:
    """Data class for vendor reviews"""
    vendor_name: str
    platform: str  # 'google_maps' or 'yelp'
    rating: float
    review_text: str
    reviewer_name: str
    review_date: str
    helpful_count: Optional[int] = None
    response_from_owner: Optional[str] = None

@dataclass
class VendorInfo:
    """Data class for vendor information"""
    name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    categories: List[str]
    overall_rating: float
    total_reviews: int
    platform: str
    platform_url: str
    hours: Optional[Dict] = None
    price_range: Optional[str] = None

class ApifyVendorScraper:
    """
    Apify integration for scraping vendor reviews and information
    """
    
    def __init__(self, api_token: str = None):
        """
        Initialize Apify client
        
        Args:
            api_token: Apify API token (can also be set via APIFY_TOKEN env var)
        """
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("Apify API token is required. Set APIFY_TOKEN env var or pass as parameter.")
        
        if ApifyClient is None:
            raise ImportError("apify-client package not installed. Run: pip install apify-client")
        
        self.client = ApifyClient(self.api_token)
        self.async_client = self.client  # Use same client for both sync and async operations
        # Note: Using synchronous client only in this version
        
        # Actor IDs for different scrapers
        self.ACTORS = {
            'google_maps_reviews': 'compass/google-maps-reviews-scraper',
            'google_maps_scraper': 'compass/crawler-google-places',
            'yelp_scraper': 'tri_angle/yelp-scraper',
            'yelp_reviews': 'delicious_zebu/yelp-reviews-scraper'
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cache for reducing API calls
        self._cache = {}
        self._cache_ttl = timedelta(hours=24)  # Cache for 24 hours

    def _get_cache_key(self, actor_id: str, input_data: Dict) -> str:
        """Generate cache key for input data"""
        input_str = json.dumps(input_data, sort_keys=True)
        return hashlib.md5(f"{actor_id}:{input_str}".encode()).hexdigest()

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid"""
        return datetime.now() - timestamp < self._cache_ttl

    async def scrape_google_maps_reviews(self, place_url: str, max_reviews: int = 50) -> List[VendorReview]:
        """
        Scrape reviews from Google Maps for a specific place
        
        Args:
            place_url: Google Maps URL of the place
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of VendorReview objects
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(self.ACTORS['google_maps_reviews'], {'url': place_url})
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]['timestamp']):
                self.logger.info(f"Using cached data for Google Maps reviews: {place_url}")
                return self._cache[cache_key]['data']

            # Prepare input for the actor
            run_input = {
                "url": place_url,
                "maxReviews": max_reviews,
                "reviewsSort": "newest",  # or "most_relevant", "oldest"
                "language": "en"
            }
            
            self.logger.info(f"Starting Google Maps reviews scraping for: {place_url}")
            
            # Run the actor
            run = await self.async_client.actor(self.ACTORS['google_maps_reviews']).call(run_input=run_input)
            
            if run is None:
                self.logger.error("Google Maps reviews scraping failed")
                return []
            
            # Get the results
            dataset_client = self.async_client.dataset(run['defaultDatasetId'])
            items = await dataset_client.list_items()
            
            reviews = []
            for item in items.get('items', []):
                review = VendorReview(
                    vendor_name=item.get('name', 'Unknown'),
                    platform='google_maps',
                    rating=float(item.get('stars', 0)),
                    review_text=item.get('text', ''),
                    reviewer_name=item.get('reviewerName', 'Anonymous'),
                    review_date=item.get('publishedAtDate', ''),
                    helpful_count=item.get('likesCount'),
                    response_from_owner=item.get('responseFromOwnerText')
                )
                reviews.append(review)
            
            # Cache the results
            self._cache[cache_key] = {
                'data': reviews,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Successfully scraped {len(reviews)} Google Maps reviews")
            return reviews
            
        except Exception as e:
            self.logger.error(f"Error scraping Google Maps reviews: {str(e)}")
            return []

    async def scrape_yelp_business_info(self, search_term: str, location: str, max_results: int = 20) -> List[VendorInfo]:
        """
        Scrape business information from Yelp
        
        Args:
            search_term: What to search for (e.g., "plumbers", "HVAC contractors")
            location: Location to search in (e.g., "New York, NY")
            max_results: Maximum number of businesses to return
            
        Returns:
            List of VendorInfo objects
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(self.ACTORS['yelp_scraper'], {
                'searchTerm': search_term, 
                'location': location
            })
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]['timestamp']):
                self.logger.info(f"Using cached data for Yelp search: {search_term} in {location}")
                return self._cache[cache_key]['data']

            # Prepare input for the actor
            run_input = {
                "searchTerm": search_term,
                "location": location,
                "maxResults": max_results,
                "includeReviews": True
            }
            
            self.logger.info(f"Starting Yelp scraping for: {search_term} in {location}")
            
            # Run the actor
            run = await self.async_client.actor(self.ACTORS['yelp_scraper']).call(run_input=run_input)
            
            if run is None:
                self.logger.error("Yelp scraping failed")
                return []
            
            # Get the results
            dataset_client = self.async_client.dataset(run['defaultDatasetId'])
            items = await dataset_client.list_items()
            
            vendors = []
            for item in items.get('items', []):
                vendor = VendorInfo(
                    name=item.get('businessName', 'Unknown'),
                    address=item.get('address', ''),
                    phone=item.get('phoneNumber'),
                    website=item.get('website'),
                    categories=item.get('categories', []),
                    overall_rating=float(item.get('rating', 0)),
                    total_reviews=int(item.get('reviewCount', 0)),
                    platform='yelp',
                    platform_url=item.get('url', ''),
                    hours=item.get('hours'),
                    price_range=item.get('priceRange')
                )
                vendors.append(vendor)
            
            # Cache the results
            self._cache[cache_key] = {
                'data': vendors,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Successfully scraped {len(vendors)} Yelp businesses")
            return vendors
            
        except Exception as e:
            self.logger.error(f"Error scraping Yelp businesses: {str(e)}")
            return []

    async def scrape_yelp_reviews(self, business_url: str, max_reviews: int = 50) -> List[VendorReview]:
        """
        Scrape reviews for a specific Yelp business
        
        Args:
            business_url: Yelp URL of the business
            max_reviews: Maximum number of reviews to scrape
            
        Returns:
            List of VendorReview objects
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(self.ACTORS['yelp_reviews'], {'url': business_url})
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]['timestamp']):
                self.logger.info(f"Using cached data for Yelp reviews: {business_url}")
                return self._cache[cache_key]['data']

            # Prepare input for the actor
            run_input = {
                "url": business_url,
                "maxReviews": max_reviews
            }
            
            self.logger.info(f"Starting Yelp reviews scraping for: {business_url}")
            
            # Run the actor
            run = await self.async_client.actor(self.ACTORS['yelp_reviews']).call(run_input=run_input)
            
            if run is None:
                self.logger.error("Yelp reviews scraping failed")
                return []
            
            # Get the results
            dataset_client = self.async_client.dataset(run['defaultDatasetId'])
            items = await dataset_client.list_items()
            
            reviews = []
            for item in items.get('items', []):
                review = VendorReview(
                    vendor_name=item.get('businessName', 'Unknown'),
                    platform='yelp',
                    rating=float(item.get('rating', 0)),
                    review_text=item.get('reviewText', ''),
                    reviewer_name=item.get('reviewerName', 'Anonymous'),
                    review_date=item.get('reviewDate', ''),
                    helpful_count=item.get('useful')
                )
                reviews.append(review)
            
            # Cache the results
            self._cache[cache_key] = {
                'data': reviews,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Successfully scraped {len(reviews)} Yelp reviews")
            return reviews
            
        except Exception as e:
            self.logger.error(f"Error scraping Yelp reviews: {str(e)}")
            return []

    def get_vendor_analysis(self, reviews: List[VendorReview]) -> Dict[str, Any]:
        """
        Analyze vendor reviews to provide insights
        
        Args:
            reviews: List of VendorReview objects
            
        Returns:
            Dictionary with analysis results
        """
        if not reviews:
            return {}
        
        total_reviews = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / total_reviews
        
        # Rating distribution
        rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating = int(round(review.rating))
            if rating in rating_dist:
                rating_dist[rating] += 1
        
        # Recent reviews (last 30 days)
        recent_reviews = []
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for review in reviews:
            try:
                review_date = datetime.strptime(review.review_date, '%Y-%m-%d')
                if review_date >= thirty_days_ago:
                    recent_reviews.append(review)
            except:
                continue  # Skip if date parsing fails
        
        # Common keywords in reviews
        all_text = ' '.join([r.review_text.lower() for r in reviews if r.review_text])
        common_words = self._extract_keywords(all_text)
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist,
            'recent_reviews_count': len(recent_reviews),
            'recent_average_rating': round(sum(r.rating for r in recent_reviews) / len(recent_reviews), 2) if recent_reviews else 0,
            'common_keywords': common_words[:10],  # Top 10 keywords
            'platforms': list(set(r.platform for r in reviews))
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract common keywords from review text"""
        # Simple keyword extraction (you might want to use more sophisticated NLP)
        import re
        from collections import Counter
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        # Extract words (3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        
        # Count frequency
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common()]

# Example usage and integration functions for Propply AI
class PropplyVendorService:
    """
    Service class to integrate Apify vendor scraping with Propply AI
    """
    
    def __init__(self, apify_token: str):
        self.scraper = ApifyVendorScraper(apify_token)
        self.logger = logging.getLogger(__name__)

    async def find_contractors_for_property(self, property_address: str, service_type: str) -> Dict[str, Any]:
        """
        Find contractors/vendors for a specific property and service type
        
        Args:
            property_address: Address of the property
            service_type: Type of service needed (e.g., "plumber", "HVAC", "electrician")
            
        Returns:
            Dictionary with vendor recommendations
        """
        try:
            # Extract location from property address (you might want to use a geocoding service)
            location = self._extract_location(property_address)
            
            # Search for vendors on Yelp
            vendors = await self.scraper.scrape_yelp_business_info(
                search_term=service_type,
                location=location,
                max_results=10
            )
            
            # Get detailed reviews for top-rated vendors
            vendor_details = []
            for vendor in vendors[:5]:  # Top 5 vendors
                if vendor.platform_url:
                    reviews = await self.scraper.scrape_yelp_reviews(
                        business_url=vendor.platform_url,
                        max_reviews=20
                    )
                    analysis = self.scraper.get_vendor_analysis(reviews)
                    
                    vendor_details.append({
                        'vendor_info': vendor,
                        'reviews': reviews,
                        'analysis': analysis
                    })
            
            return {
                'property_address': property_address,
                'service_type': service_type,
                'total_vendors_found': len(vendors),
                'vendor_details': vendor_details,
                'search_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error finding contractors: {str(e)}")
            return {}

    def _extract_location(self, address: str) -> str:
        """Extract city/state from full address for search purposes"""
        # Simple extraction - you might want to use a proper address parser
        parts = address.split(',')
        if len(parts) >= 2:
            return f"{parts[-2].strip()}, {parts[-1].strip()}"
        return "New York, NY"  # Default fallback

    async def verify_vendor_credentials(self, vendor_name: str, location: str) -> Dict[str, Any]:
        """
        Verify vendor credentials by checking multiple platforms
        
        Args:
            vendor_name: Name of the vendor to verify
            location: Location to search in
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Search on both Yelp and Google Maps
            yelp_vendors = await self.scraper.scrape_yelp_business_info(
                search_term=vendor_name,
                location=location,
                max_results=5
            )
            
            verification_results = {
                'vendor_name': vendor_name,
                'location': location,
                'found_on_yelp': len(yelp_vendors) > 0,
                'yelp_results': yelp_vendors,
                'verification_score': 0,
                'verification_timestamp': datetime.now().isoformat()
            }
            
            # Calculate verification score based on presence and ratings
            if yelp_vendors:
                avg_rating = sum(v.overall_rating for v in yelp_vendors) / len(yelp_vendors)
                total_reviews = sum(v.total_reviews for v in yelp_vendors)
                
                verification_results['verification_score'] = min(100, 
                    (avg_rating / 5.0) * 50 +  # 50% based on rating
                    min(total_reviews / 100, 1) * 30 +  # 30% based on review count
                    20  # 20% for being found online
                )
            
            return verification_results
            
        except Exception as e:
            self.logger.error(f"Error verifying vendor credentials: {str(e)}")
            return {}

# Example usage
async def main():
    """Example usage of the Apify integration"""
    # Initialize with your Apify token
    apify_token = os.getenv('APIFY_TOKEN')
    if not apify_token:
        print("Please set APIFY_TOKEN environment variable")
        return
    
    # Create service instance
    vendor_service = PropplyVendorService(apify_token)
    
    # Example: Find plumbers for a property
    property_address = "123 Main St, Brooklyn, NY 11201"
    contractors = await vendor_service.find_contractors_for_property(
        property_address=property_address,
        service_type="plumber"
    )
    
    print(f"Found {contractors.get('total_vendors_found', 0)} contractors")
    for detail in contractors.get('vendor_details', []):
        vendor = detail['vendor_info']
        analysis = detail['analysis']
        print(f"- {vendor.name}: {vendor.overall_rating}★ ({analysis.get('total_reviews', 0)} reviews)")

if __name__ == "__main__":
    asyncio.run(main())
