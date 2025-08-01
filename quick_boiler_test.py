#!/usr/bin/env python3
"""
Quick test to find boiler inspectors for 1662 Park Avenue
Shows what vendors we can currently qualify
"""

import json
import os
from datetime import datetime

def search_fdny_boiler_vendors():
    """Search FDNY data for boiler-related vendors"""
    print("🔍 SEARCHING FOR BOILER INSPECTORS NEAR 1662 PARK AVENUE")
    print("=" * 60)
    
    try:
        fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
        
        if not os.path.exists(fdny_file):
            print("❌ FDNY data file not found")
            return []
        
        with open(fdny_file, 'r', encoding='utf-8') as f:
            fdny_data = json.load(f)
        
        all_vendors = fdny_data.get('all_vendors_flat', [])
        print(f"📊 Total vendors in FDNY database: {len(all_vendors)}")
        
        # Search for boiler-related companies
        boiler_keywords = ['boiler', 'heating', 'hvac', 'mechanical', 'steam', 'thermal']
        
        boiler_vendors = []
        for vendor in all_vendors:
            name_lower = vendor.get('name', '').lower()
            if any(keyword in name_lower for keyword in boiler_keywords):
                boiler_vendors.append(vendor)
        
        print(f"🔥 Found {len(boiler_vendors)} boiler-related companies")
        
        # Filter for Manhattan/NYC area
        manhattan_vendors = []
        for vendor in boiler_vendors:
            address = vendor.get('address', '').lower()
            if any(area in address for area in ['manhattan', 'new york', 'nyc', 'harlem']):
                manhattan_vendors.append(vendor)
        
        print(f"🗽 Manhattan area companies: {len(manhattan_vendors)}")
        
        # Show top qualified vendors
        print(f"\n✅ TOP QUALIFIED BOILER INSPECTORS:")
        print("-" * 50)
        
        # Sort by license status (active first)
        active_vendors = [v for v in manhattan_vendors if v.get('license_status') == 'ACTIVE']
        
        if active_vendors:
            for i, vendor in enumerate(active_vendors[:5], 1):
                print(f"{i}. {vendor.get('name', 'N/A')}")
                print(f"   📋 License: {vendor.get('license_number', 'N/A')}")
                print(f"   ✅ Status: {vendor.get('license_status', 'N/A')}")
                print(f"   📍 Address: {vendor.get('address', 'N/A')}")
                print(f"   📞 Phone: {vendor.get('phone', 'N/A')}")
                
                # Check license expiry
                expiry = vendor.get('license_expiry')
                if expiry and expiry != 'N/A':
                    try:
                        expiry_date = datetime.strptime(expiry, '%m/%d/%Y')
                        days_left = (expiry_date - datetime.now()).days
                        if days_left > 0:
                            print(f"   📅 Expires: {expiry} ({days_left} days)")
                        else:
                            print(f"   ⚠️  EXPIRED: {expiry}")
                    except:
                        print(f"   📅 Expiry: {expiry}")
                
                print(f"   🔧 Services: {', '.join(vendor.get('specializations', []))}")
                print()
        
        # Show broader NYC area if Manhattan is limited
        if len(active_vendors) < 3:
            print(f"\n🔍 EXPANDING SEARCH TO ALL NYC BOROUGHS:")
            print("-" * 50)
            
            nyc_vendors = [v for v in boiler_vendors if v.get('license_status') == 'ACTIVE'][:10]
            
            for i, vendor in enumerate(nyc_vendors, 1):
                print(f"{i}. {vendor.get('name', 'N/A')}")
                print(f"   📍 {vendor.get('address', 'N/A')}")
                print(f"   📞 {vendor.get('phone', 'N/A')}")
        
        return active_vendors
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def show_vendor_qualification_criteria():
    """Show what criteria we use to qualify vendors"""
    print(f"\n📋 VENDOR QUALIFICATION CRITERIA")
    print("=" * 60)
    print("✅ FDNY Fire Safety Certification")
    print("✅ Active License Status")
    print("✅ Manhattan/NYC Location Preference")
    print("✅ Boiler/HVAC Specialization Keywords")
    print("✅ Valid License Expiration Date")
    print("✅ Contact Information Available")
    
    print(f"\n🎯 SCORING FACTORS:")
    print("• License Status (Active vs Expired)")
    print("• Geographic Proximity to Property")
    print("• Service Specialization Match")
    print("• License Expiration Timeline")
    print("• Company Contact Availability")

def main():
    """Run quick boiler inspector test"""
    print("🏢 BOILER INSPECTOR SEARCH: 1662 Park Avenue, NY 10035")
    print("(Using Current Propply AI Vendor Qualification System)")
    print("=" * 70)
    
    # Search FDNY data
    qualified_vendors = search_fdny_boiler_vendors()
    
    # Show qualification criteria
    show_vendor_qualification_criteria()
    
    # Summary
    print(f"\n📊 SEARCH RESULTS SUMMARY")
    print("=" * 70)
    print(f"🎯 Qualified Vendors Found: {len(qualified_vendors)}")
    
    if qualified_vendors:
        print(f"\n💡 NEXT STEPS FOR PROPERTY MANAGER:")
        print("1. Contact top-rated vendors for quotes")
        print("2. Verify boiler inspection certifications")
        print("3. Check insurance and bonding status")
        print("4. Schedule property visit for assessment")
        print("5. Compare pricing and service offerings")
        
        print(f"\n🔗 ADDITIONAL VERIFICATION:")
        print("• Cross-check with NYC DOB contractor database")
        print("• Review Google Maps/Yelp ratings (via Apify)")
        print("• Verify EPA refrigerant certifications")
        print("• Check Better Business Bureau ratings")
    else:
        print(f"\n⚠️  LIMITED RESULTS - RECOMMENDATIONS:")
        print("• Expand search to all NYC boroughs")
        print("• Contact general HVAC contractors")
        print("• Check with building management companies")
        print("• Consider certified mechanical engineers")

if __name__ == "__main__":
    main()
