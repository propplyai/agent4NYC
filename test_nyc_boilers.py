#!/usr/bin/env python3
"""
Specific test for New York City Boilers - demonstrating complete vendor verification
Shows both official certification data and potential review integration
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

def search_nyc_boilers_in_fdny():
    """Search for New York City Boilers in FDNY data"""
    print("🔍 SEARCHING FDNY DATA FOR 'NEW YORK CITY BOILERS'...")
    print("=" * 60)
    
    try:
        fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
        
        with open(fdny_file, 'r', encoding='utf-8') as f:
            fdny_data = json.load(f)
        
        all_vendors = fdny_data.get('all_vendors_flat', [])
        
        # Search for various combinations
        search_terms = [
            'new york city boilers',
            'nyc boilers',
            'new york boilers',
            'city boilers'
        ]
        
        found_vendors = []
        
        for term in search_terms:
            matches = [
                v for v in all_vendors 
                if term in v.get('name', '').lower()
            ]
            found_vendors.extend(matches)
        
        # Remove duplicates
        unique_vendors = []
        seen_licenses = set()
        for vendor in found_vendors:
            license_num = vendor.get('license_number', '')
            if license_num not in seen_licenses:
                unique_vendors.append(vendor)
                seen_licenses.add(license_num)
        
        if unique_vendors:
            print(f"✅ FOUND {len(unique_vendors)} MATCHING COMPANIES:")
            
            for i, vendor in enumerate(unique_vendors, 1):
                print(f"\n{i}. {vendor['name']}")
                print(f"   📋 License Number: {vendor.get('license_number', 'N/A')}")
                print(f"   🏢 License Type: {vendor.get('license_type', 'N/A')}")
                print(f"   ✅ License Status: {vendor.get('license_status', 'N/A')}")
                print(f"   📅 License Expiry: {vendor.get('license_expiry', 'N/A')}")
                print(f"   📍 Address: {vendor.get('address', 'N/A')}")
                print(f"   📞 Phone: {vendor.get('phone', 'N/A')}")
                print(f"   👤 Principal: {vendor.get('principal', 'N/A')}")
                print(f"   🔧 Services: {', '.join(vendor.get('specializations', []))}")
                
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
                
            return unique_vendors
        else:
            print("❌ 'NEW YORK CITY BOILERS' not found in FDNY fire safety data")
            
            # Show boiler-related companies for reference
            boiler_related = [
                v for v in all_vendors 
                if any(term in v.get('name', '').lower() for term in ['boiler', 'heating', 'hvac'])
            ][:10]
            
            if boiler_related:
                print(f"\n🔍 Found {len(boiler_related)} boiler/heating related companies:")
                for vendor in boiler_related:
                    print(f"   - {vendor['name']}")
            
            return []
            
    except Exception as e:
        print(f"❌ Error searching FDNY data: {str(e)}")
        return []

async def search_dob_for_boiler_contractors():
    """Search DOB database for boiler-related contractors"""
    print("\n🏛️  SEARCHING NYC DOB DATABASE FOR BOILER CONTRACTORS...")
    print("=" * 60)
    
    try:
        marketplace = SimpleVendorMarketplace()
        
        # Get DOB licensed contractors
        dob_inspectors = await marketplace._get_dob_licensed_inspectors()
        
        # Search for boiler-related contractors
        boiler_contractors = [
            inspector for inspector in dob_inspectors
            if any(term in inspector.name.lower() for term in [
                'boiler', 'heating', 'hvac', 'mechanical', 'steam'
            ])
        ]
        
        if boiler_contractors:
            print(f"✅ FOUND {len(boiler_contractors)} BOILER-RELATED DOB CONTRACTORS:")
            
            for i, contractor in enumerate(boiler_contractors[:5], 1):
                print(f"\n{i}. {contractor.name}")
                print(f"   📋 License Number: {contractor.license_number}")
                print(f"   🏢 License Type: {contractor.license_type}")
                print(f"   ✅ Status: {contractor.license_status}")
                print(f"   🔧 Specializations: {', '.join(contractor.specializations)}")
                
                if hasattr(contractor, 'address') and contractor.address:
                    print(f"   📍 Address: {contractor.address}")
                if hasattr(contractor, 'phone') and contractor.phone:
                    print(f"   📞 Phone: {contractor.phone}")
            
            if len(boiler_contractors) > 5:
                print(f"\n   ... and {len(boiler_contractors) - 5} more contractors")
                
            return boiler_contractors
        else:
            print("❌ No boiler-related contractors found in DOB database")
            return []
            
    except Exception as e:
        print(f"❌ Error searching DOB database: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def search_general_boiler_vendors():
    """Search for general boiler service vendors"""
    print("\n🔍 SEARCHING ALL DATABASES FOR BOILER SERVICE VENDORS...")
    print("=" * 60)
    
    try:
        # Search the FDNY data more broadly
        fdny_file = '/Users/art3a/agent4NYC/fdny_comprehensive/fdny_comprehensive_20250720_222117.json'
        
        with open(fdny_file, 'r', encoding='utf-8') as f:
            fdny_data = json.load(f)
        
        all_vendors = fdny_data.get('all_vendors_flat', [])
        
        # Broader search for any company that might do boiler work
        boiler_keywords = [
            'boiler', 'heating', 'hvac', 'mechanical', 'steam', 
            'thermal', 'energy', 'climate', 'temperature'
        ]
        
        potential_vendors = []
        for vendor in all_vendors:
            name_lower = vendor.get('name', '').lower()
            address_lower = vendor.get('address', '').lower()
            
            if any(keyword in name_lower or keyword in address_lower for keyword in boiler_keywords):
                potential_vendors.append(vendor)
        
        if potential_vendors:
            print(f"✅ FOUND {len(potential_vendors)} POTENTIAL BOILER SERVICE VENDORS:")
            
            for i, vendor in enumerate(potential_vendors[:10], 1):
                print(f"\n{i}. {vendor['name']}")
                print(f"   📋 License: {vendor.get('license_number', 'N/A')}")
                print(f"   📞 Phone: {vendor.get('phone', 'N/A')}")
                print(f"   📍 Address: {vendor.get('address', 'N/A')}")
                print(f"   🔧 FDNY Services: {', '.join(vendor.get('specializations', []))}")
            
            if len(potential_vendors) > 10:
                print(f"\n   ... and {len(potential_vendors) - 10} more vendors")
                
            return potential_vendors
        else:
            print("❌ No boiler-related vendors found")
            return []
            
    except Exception as e:
        print(f"❌ Error in general search: {str(e)}")
        return []

def main():
    """Complete search for New York City Boilers and related vendors"""
    print("🚀 COMPLETE VENDOR SEARCH: NEW YORK CITY BOILERS")
    print("=" * 70)
    
    # Step 1: Search FDNY data specifically
    fdny_results = search_nyc_boilers_in_fdny()
    
    # Step 2: Search DOB for boiler contractors
    dob_results = asyncio.run(search_dob_for_boiler_contractors())
    
    # Step 3: General boiler vendor search
    general_results = search_general_boiler_vendors()
    
    # Summary
    print("\n📊 SEARCH RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"🔥 FDNY Fire Safety (exact match): {len(fdny_results)} companies")
    print(f"🏛️  DOB Licensed Contractors: {len(dob_results)} companies")
    print(f"🔍 General Boiler Services: {len(general_results)} companies")
    
    total_found = len(fdny_results) + len(dob_results) + len(general_results)
    
    if total_found > 0:
        print(f"\n🎯 RECOMMENDATION FOR BOILER SERVICES:")
        
        if fdny_results:
            print("   ✅ Found exact matches in FDNY database - these are certified for fire safety")
        
        if dob_results:
            print("   ✅ Found DOB licensed contractors - these are licensed for construction/mechanical work")
        
        if general_results:
            print("   ✅ Found related service providers - may offer complementary services")
        
        print(f"\n📞 NEXT STEPS:")
        print("   1. Contact companies directly to verify boiler inspection/service capabilities")
        print("   2. Check if they have specific boiler certifications (not just fire safety)")
        print("   3. Verify insurance coverage for boiler work")
        print("   4. Request references from similar properties")
        
    else:
        print(f"\n❌ NO DIRECT MATCHES FOUND")
        print(f"   This suggests 'New York City Boilers' may:")
        print(f"   - Not be FDNY certified (fire safety focus)")
        print(f"   - Operate under a different business name")
        print(f"   - Be a newer company not in our July 2025 data")
        print(f"   - Focus on mechanical/HVAC rather than fire safety")

if __name__ == "__main__":
    main()
