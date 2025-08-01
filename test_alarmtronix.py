#!/usr/bin/env python3
"""
Specific test for ALARMTRONIX INC - demonstrating complete vendor verification
Shows both official FDNY license info and Google reviews integration
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

def find_alarmtronix_in_fdny_data():
    """Find ALARMTRONIX INC in the FDNY data"""
    print("🔍 SEARCHING FDNY DATA FOR ALARMTRONIX INC...")
    print("=" * 50)
    
    try:
        fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
        
        with open(fdny_file, 'r', encoding='utf-8') as f:
            fdny_data = json.load(f)
        
        all_vendors = fdny_data.get('all_vendors_flat', [])
        
        # Search for ALARMTRONIX (case insensitive)
        alarmtronix_vendors = [
            v for v in all_vendors 
            if 'alarmtronix' in v.get('name', '').lower()
        ]
        
        if alarmtronix_vendors:
            for vendor in alarmtronix_vendors:
                print(f"✅ FOUND: {vendor['name']}")
                print(f"   📋 License Number: {vendor.get('license_number', 'N/A')}")
                print(f"   🏢 License Type: {vendor.get('license_type', 'N/A')}")
                print(f"   ✅ License Status: {vendor.get('license_status', 'N/A')}")
                print(f"   📅 License Expiry: {vendor.get('license_expiry', 'N/A')}")
                print(f"   📍 Address: {vendor.get('address', 'N/A')}")
                print(f"   📞 Phone: {vendor.get('phone', 'N/A')}")
                print(f"   👤 Principal: {vendor.get('principal', 'N/A')}")
                print(f"   🔧 Services: {', '.join(vendor.get('specializations', []))}")
                print(f"   📊 Insurance Expiry: {vendor.get('insurance_expiry', 'N/A')}")
                
                # Check license status
                if vendor.get('license_expiry') and vendor.get('license_expiry') != 'N/A':
                    try:
                        expiry_date = datetime.strptime(vendor['license_expiry'], '%m/%d/%Y')
                        days_until_expiry = (expiry_date - datetime.now()).days
                        
                        if days_until_expiry < 0:
                            print(f"   ⚠️  LICENSE STATUS: EXPIRED ({abs(days_until_expiry)} days ago)")
                        elif days_until_expiry < 90:
                            print(f"   ⚠️  LICENSE STATUS: EXPIRING SOON ({days_until_expiry} days)")
                        else:
                            print(f"   ✅ LICENSE STATUS: ACTIVE ({days_until_expiry} days remaining)")
                    except:
                        print(f"   ❓ LICENSE STATUS: Cannot parse expiry date")
                
                print()
                
            return alarmtronix_vendors
        else:
            print("❌ ALARMTRONIX INC not found in FDNY data")
            
            # Show similar companies for reference
            similar = [v for v in all_vendors if 'alarm' in v.get('name', '').lower()][:5]
            if similar:
                print("\n🔍 Similar companies found:")
                for vendor in similar:
                    print(f"   - {vendor['name']}")
            
            return []
            
    except Exception as e:
        print(f"❌ Error searching FDNY data: {str(e)}")
        return []

async def get_alarmtronix_reviews():
    """Get Google reviews for ALARMTRONIX INC via Apify integration"""
    print("\n⭐ GETTING GOOGLE REVIEWS FOR ALARMTRONIX INC...")
    print("=" * 50)
    
    try:
        marketplace = SimpleVendorMarketplace()
        
        # Search for ALARMTRONIX using the vendor search
        result = await marketplace.find_verified_vendors(
            property_address="New York, NY",
            service_type="fire_safety",
            search_query="ALARMTRONIX"
        )
        
        vendors = result.get('vendors', [])
        alarmtronix_vendors = [
            v for v in vendors 
            if 'alarmtronix' in v.get('name', '').lower()
        ]
        
        if alarmtronix_vendors:
            vendor = alarmtronix_vendors[0]
            print(f"✅ FOUND REVIEW DATA FOR: {vendor.get('name', 'N/A')}")
            print(f"   ⭐ Google Rating: {vendor.get('review_rating', 'N/A')}")
            print(f"   📊 Review Count: {vendor.get('review_count', 'N/A')}")
            print(f"   🎯 Verification Score: {vendor.get('verification_score', 'N/A')}")
            print(f"   ⚠️  Risk Level: {vendor.get('risk_level', 'N/A')}")
            
            # Show review summary if available
            if vendor.get('review_summary'):
                print(f"   📝 Review Summary: {vendor.get('review_summary')}")
            
            return vendor
        else:
            print("❌ No review data found for ALARMTRONIX INC")
            print("   This could mean:")
            print("   - Company not found on Google Maps")
            print("   - Limited online presence")
            print("   - Name variation in online listings")
            return None
            
    except Exception as e:
        print(f"❌ Error getting reviews: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_api_search():
    """Test the API search for ALARMTRONIX"""
    print("\n🌐 TESTING API SEARCH FOR ALARMTRONIX...")
    print("=" * 50)
    
    try:
        response = requests.post("http://127.0.0.1:5002/api/vendors/search", 
                               json={
                                   "property_address": "New York, NY",
                                   "service_type": "fire_safety"
                               })
        
        if response.status_code == 200:
            data = response.json()
            vendors = data.get('vendors', [])
            
            # Look for ALARMTRONIX in results
            alarmtronix_vendors = [
                v for v in vendors 
                if 'alarmtronix' in v.get('name', '').lower()
            ]
            
            if alarmtronix_vendors:
                vendor = alarmtronix_vendors[0]
                print(f"✅ FOUND VIA API: {vendor.get('name', 'N/A')}")
                print(f"   📋 License: {vendor.get('license_number', 'N/A')}")
                print(f"   ⭐ Rating: {vendor.get('review_rating', 'N/A')}")
                print(f"   🎯 Score: {vendor.get('verification_score', 'N/A')}")
                return vendor
            else:
                print(f"❌ ALARMTRONIX not found in API results ({len(vendors)} total vendors)")
                return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return None

def main():
    """Complete ALARMTRONIX INC verification"""
    print("🚀 COMPLETE VENDOR VERIFICATION: ALARMTRONIX INC")
    print("=" * 70)
    
    # Step 1: Find in FDNY official data
    fdny_data = find_alarmtronix_in_fdny_data()
    
    # Step 2: Get Google reviews
    review_data = asyncio.run(get_alarmtronix_reviews())
    
    # Step 3: Test API search
    api_data = test_api_search()
    
    # Summary
    print("\n📊 COMPLETE VENDOR PROFILE: ALARMTRONIX INC")
    print("=" * 70)
    
    if fdny_data:
        vendor = fdny_data[0]
        print("🏛️  OFFICIAL FDNY CERTIFICATION:")
        print(f"   Company: {vendor['name']}")
        print(f"   License: {vendor.get('license_number', 'N/A')}")
        print(f"   Status: {vendor.get('license_status', 'N/A')}")
        print(f"   Expiry: {vendor.get('license_expiry', 'N/A')}")
        print(f"   Phone: {vendor.get('phone', 'N/A')}")
        print(f"   Address: {vendor.get('address', 'N/A')}")
    else:
        print("🏛️  OFFICIAL FDNY CERTIFICATION: Not found")
    
    if review_data:
        print(f"\n⭐ GOOGLE REVIEWS:")
        print(f"   Rating: {review_data.get('review_rating', 'N/A')}")
        print(f"   Count: {review_data.get('review_count', 'N/A')}")
        print(f"   Verification Score: {review_data.get('verification_score', 'N/A')}")
    else:
        print(f"\n⭐ GOOGLE REVIEWS: Not available")
    
    print(f"\n🎯 RECOMMENDATION:")
    if fdny_data and review_data:
        print("   ✅ VERIFIED VENDOR - Has both official certification and customer reviews")
    elif fdny_data:
        print("   ⚠️  CERTIFIED BUT LIMITED REVIEWS - Official license but minimal online presence")
    elif review_data:
        print("   ⚠️  REVIEWS BUT NO CERTIFICATION - Has reviews but no official FDNY license found")
    else:
        print("   ❌ INSUFFICIENT DATA - Neither certification nor reviews found")

if __name__ == "__main__":
    main()
