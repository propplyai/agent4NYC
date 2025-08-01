#!/usr/bin/env python3
"""
Complete vendor verification for CITYWIDE PLUMBING HEATING & SPRINKLER
Demonstrates integration of official FDNY certification + Google/Yelp reviews via Apify
"""

import json
import os
import sys
import asyncio
import requests
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/Users/art3a/agent4NYC')

from simple_vendor_marketplace import SimpleVendorMarketplace
from apify_integration import ApifyVendorScraper

def get_citywide_fdny_data():
    """Get official FDNY certification data for CITYWIDE PLUMBING"""
    print("🏛️  OFFICIAL FDNY CERTIFICATION DATA")
    print("=" * 50)
    
    try:
        fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
        
        with open(fdny_file, 'r', encoding='utf-8') as f:
            fdny_data = json.load(f)
        
        all_vendors = fdny_data.get('all_vendors_flat', [])
        
        # Find CITYWIDE PLUMBING
        citywide = None
        for vendor in all_vendors:
            if 'citywide plumbing' in vendor.get('name', '').lower():
                citywide = vendor
                break
        
        if citywide:
            print(f"✅ FOUND: {citywide['name']}")
            print(f"   📋 FDNY License: {citywide.get('license_number', 'N/A')}")
            print(f"   🏢 License Type: {citywide.get('license_type', 'N/A')}")
            print(f"   ✅ Status: {citywide.get('license_status', 'N/A')}")
            print(f"   📅 Expiry: {citywide.get('license_expiry', 'N/A')}")
            print(f"   📍 Address: {citywide.get('address', 'N/A')}")
            print(f"   📞 Phone: {citywide.get('phone', 'N/A')}")
            print(f"   🔧 FDNY Services: {', '.join(citywide.get('specializations', []))}")
            print(f"   📊 Insurance Expiry: {citywide.get('insurance_expiry', 'N/A')}")
            
            # License status check
            if citywide.get('license_expiry') and citywide.get('license_expiry') != 'N/A':
                try:
                    expiry_date = datetime.strptime(citywide['license_expiry'], '%m/%d/%Y')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    if days_until_expiry < 0:
                        print(f"   ⚠️  LICENSE: EXPIRED ({abs(days_until_expiry)} days ago)")
                    elif days_until_expiry < 90:
                        print(f"   ⚠️  LICENSE: EXPIRING SOON ({days_until_expiry} days)")
                    else:
                        print(f"   ✅ LICENSE: ACTIVE ({days_until_expiry} days remaining)")
                except:
                    print(f"   ❓ LICENSE: Cannot parse expiry date")
            
            return citywide
        else:
            print("❌ CITYWIDE PLUMBING not found in FDNY data")
            return None
            
    except Exception as e:
        print(f"❌ Error loading FDNY data: {str(e)}")
        return None

async def get_citywide_reviews():
    """Get Google Maps and Yelp reviews for CITYWIDE PLUMBING via Apify"""
    print("\n⭐ CUSTOMER REVIEWS VIA APIFY INTEGRATION")
    print("=" * 50)
    
    try:
        # Initialize Apify scraper
        scraper = ApifyVendorScraper()
        
        # Search for CITYWIDE PLUMBING HEATING & SPRINKLER
        search_query = "CITYWIDE PLUMBING HEATING & SPRINKLER Queens NY"
        
        print(f"🔍 Searching for: {search_query}")
        
        # Get Google Maps reviews
        print("\n📍 GOOGLE MAPS REVIEWS:")
        google_results = await scraper.scrape_google_maps_reviews(search_query)
        
        if google_results and len(google_results) > 0:
            business = google_results[0]  # Take first result
            
            print(f"   ✅ Found: {business.get('title', 'N/A')}")
            print(f"   ⭐ Rating: {business.get('totalScore', 'N/A')}")
            print(f"   📊 Review Count: {business.get('reviewsCount', 'N/A')}")
            print(f"   📍 Address: {business.get('address', 'N/A')}")
            print(f"   📞 Phone: {business.get('phone', 'N/A')}")
            print(f"   🌐 Website: {business.get('website', 'N/A')}")
            
            # Show recent reviews
            reviews = business.get('reviews', [])
            if reviews:
                print(f"\n   📝 RECENT REVIEWS:")
                for i, review in enumerate(reviews[:3], 1):
                    print(f"      {i}. ⭐ {review.get('stars', 'N/A')} stars - {review.get('text', 'No text')[:100]}...")
                    print(f"         👤 {review.get('name', 'Anonymous')} ({review.get('publishedAtDate', 'No date')})")
                    print()
        else:
            print("   ❌ No Google Maps results found")
        
        # Get Yelp reviews
        print("\n🍽️ YELP REVIEWS:")
        yelp_results = await scraper.scrape_yelp_reviews(search_query)
        
        if yelp_results and len(yelp_results) > 0:
            business = yelp_results[0]  # Take first result
            
            print(f"   ✅ Found: {business.get('name', 'N/A')}")
            print(f"   ⭐ Rating: {business.get('rating', 'N/A')}")
            print(f"   📊 Review Count: {business.get('reviewCount', 'N/A')}")
            print(f"   📍 Address: {business.get('address', 'N/A')}")
            print(f"   📞 Phone: {business.get('phone', 'N/A')}")
            
            # Show recent reviews
            reviews = business.get('reviews', [])
            if reviews:
                print(f"\n   📝 RECENT REVIEWS:")
                for i, review in enumerate(reviews[:3], 1):
                    print(f"      {i}. ⭐ {review.get('rating', 'N/A')} stars - {review.get('text', 'No text')[:100]}...")
                    print(f"         👤 {review.get('userName', 'Anonymous')} ({review.get('publishedAt', 'No date')})")
                    print()
        else:
            print("   ❌ No Yelp results found")
        
        return {
            'google': google_results[0] if google_results else None,
            'yelp': yelp_results[0] if yelp_results else None
        }
        
    except Exception as e:
        print(f"❌ Error getting reviews: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def calculate_verification_score(fdny_data, review_data):
    """Calculate comprehensive verification score"""
    print("\n🎯 COMPREHENSIVE VERIFICATION SCORE")
    print("=" * 50)
    
    score = 0
    max_score = 100
    factors = []
    
    # FDNY Certification (40 points max)
    if fdny_data:
        score += 30  # Base certification points
        factors.append("✅ FDNY Certified (+30 pts)")
        
        # License status bonus
        if fdny_data.get('license_status') == 'ACTIVE':
            score += 10
            factors.append("✅ Active License (+10 pts)")
        
        # Check expiry
        if fdny_data.get('license_expiry') and fdny_data.get('license_expiry') != 'N/A':
            try:
                expiry_date = datetime.strptime(fdny_data['license_expiry'], '%m/%d/%Y')
                days_until_expiry = (expiry_date - datetime.now()).days
                
                if days_until_expiry > 90:
                    # No deduction for good expiry
                    pass
                elif days_until_expiry > 0:
                    score -= 5
                    factors.append("⚠️ Expiring Soon (-5 pts)")
                else:
                    score -= 15
                    factors.append("❌ Expired License (-15 pts)")
            except:
                pass
    else:
        factors.append("❌ No FDNY Certification (-30 pts)")
    
    # Google Reviews (35 points max)
    if review_data and review_data.get('google'):
        google = review_data['google']
        rating = google.get('totalScore', 0)
        review_count = google.get('reviewsCount', 0)
        
        if rating >= 4.5:
            score += 25
            factors.append(f"⭐ Excellent Google Rating {rating} (+25 pts)")
        elif rating >= 4.0:
            score += 20
            factors.append(f"⭐ Good Google Rating {rating} (+20 pts)")
        elif rating >= 3.5:
            score += 15
            factors.append(f"⭐ Average Google Rating {rating} (+15 pts)")
        elif rating > 0:
            score += 5
            factors.append(f"⭐ Low Google Rating {rating} (+5 pts)")
        
        if review_count >= 50:
            score += 10
            factors.append(f"📊 Many Reviews {review_count} (+10 pts)")
        elif review_count >= 20:
            score += 5
            factors.append(f"📊 Some Reviews {review_count} (+5 pts)")
    else:
        factors.append("❌ No Google Reviews Found (-25 pts)")
    
    # Yelp Reviews (25 points max)
    if review_data and review_data.get('yelp'):
        yelp = review_data['yelp']
        rating = yelp.get('rating', 0)
        
        if rating >= 4.5:
            score += 20
            factors.append(f"🍽️ Excellent Yelp Rating {rating} (+20 pts)")
        elif rating >= 4.0:
            score += 15
            factors.append(f"🍽️ Good Yelp Rating {rating} (+15 pts)")
        elif rating >= 3.5:
            score += 10
            factors.append(f"🍽️ Average Yelp Rating {rating} (+10 pts)")
        elif rating > 0:
            score += 5
            factors.append(f"🍽️ Low Yelp Rating {rating} (+5 pts)")
    else:
        factors.append("❌ No Yelp Reviews Found (-15 pts)")
    
    # Risk assessment
    risk_level = "LOW"
    if score >= 80:
        risk_level = "LOW"
    elif score >= 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    print(f"📊 FINAL SCORE: {score}/{max_score} ({score}%)")
    print(f"⚠️  RISK LEVEL: {risk_level}")
    print(f"\n🔍 SCORING FACTORS:")
    for factor in factors:
        print(f"   {factor}")
    
    return score, risk_level

def main():
    """Complete vendor verification for CITYWIDE PLUMBING"""
    print("🚀 COMPLETE VENDOR VERIFICATION: CITYWIDE PLUMBING HEATING & SPRINKLER")
    print("=" * 80)
    
    # Step 1: Get FDNY certification data
    fdny_data = get_citywide_fdny_data()
    
    # Step 2: Get customer reviews
    review_data = asyncio.run(get_citywide_reviews())
    
    # Step 3: Calculate verification score
    score, risk_level = calculate_verification_score(fdny_data, review_data)
    
    # Final recommendation
    print(f"\n🏆 FINAL RECOMMENDATION")
    print("=" * 80)
    
    if fdny_data and review_data:
        print("✅ VERIFIED VENDOR - Has both official certification AND customer reviews")
        print("   Recommended for fire safety services with customer validation")
    elif fdny_data:
        print("⚠️  CERTIFIED BUT LIMITED ONLINE PRESENCE")
        print("   Has official FDNY certification but minimal customer reviews")
        print("   Safe for compliance but consider requesting references")
    elif review_data:
        print("⚠️  REVIEWS BUT NO FDNY CERTIFICATION")
        print("   Has customer reviews but no official fire safety certification")
        print("   May not be qualified for FDNY-required services")
    else:
        print("❌ INSUFFICIENT VERIFICATION DATA")
        print("   Neither certification nor reviews found - high risk vendor")
    
    print(f"\n📞 CONTACT INFORMATION:")
    if fdny_data:
        print(f"   Phone: {fdny_data.get('phone', 'N/A')}")
        print(f"   Address: {fdny_data.get('address', 'N/A')}")
    
    print(f"\n🎯 VERIFICATION SCORE: {score}/100 ({risk_level} RISK)")

if __name__ == "__main__":
    main()
