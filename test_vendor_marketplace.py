"""
Test script for Enhanced Vendor Marketplace
Demonstrates vendor verification capabilities without requiring Apify token
"""

import asyncio
import json
from enhanced_vendor_marketplace import EnhancedVendorMarketplace, CertifiedInspector

async def test_vendor_marketplace():
    """Test the enhanced vendor marketplace functionality"""
    print("🏢 Testing Enhanced Vendor Marketplace for Propply AI")
    print("=" * 60)
    
    # Initialize marketplace (without Apify token for testing)
    marketplace = EnhancedVendorMarketplace()
    
    # Test 1: Get certified inspectors for different service types
    print("\n📋 Test 1: Getting Certified Inspectors")
    print("-" * 40)
    
    service_types = ['elevator', 'fire_safety', 'hvac', 'plumbing', 'electrical']
    
    for service_type in service_types:
        print(f"\n🔍 Searching for {service_type} inspectors...")
        try:
            inspectors = await marketplace._get_certified_inspectors(service_type)
            print(f"   Found {len(inspectors)} certified inspectors")
            
            if inspectors:
                for i, inspector in enumerate(inspectors[:2]):  # Show first 2
                    print(f"   {i+1}. {inspector.name}")
                    print(f"      License: {inspector.license_number} ({inspector.license_type})")
                    print(f"      Status: {inspector.license_status}")
                    if inspector.specializations:
                        print(f"      Specializations: {', '.join(inspector.specializations)}")
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    # Test 2: Test compliance category mapping
    print("\n\n📊 Test 2: Compliance Category Mapping")
    print("-" * 40)
    
    compliance_categories = [
        'elevator_inspections',
        'fire_safety_inspections', 
        'boiler_inspections',
        'backflow_prevention',
        'electrical_inspections'
    ]
    
    for category in compliance_categories:
        service_type = marketplace._map_compliance_to_service(category)
        print(f"   {category} → {service_type}")
    
    # Test 3: Service type mappings
    print("\n\n🔧 Test 3: Service Type Mappings")
    print("-" * 40)
    
    for service_type, mapping in marketplace.service_mappings.items():
        print(f"\n   {service_type.upper()}:")
        print(f"     Keywords: {', '.join(mapping['keywords'])}")
        print(f"     Required Licenses: {', '.join(mapping['required_licenses'])}")
        print(f"     Compliance Categories: {', '.join(mapping['compliance_categories'])}")
    
    # Test 4: Mock vendor verification
    print("\n\n✅ Test 4: Mock Vendor Verification")
    print("-" * 40)
    
    # Create a mock vendor for testing
    from apify_integration import VendorInfo
    
    mock_vendor = VendorInfo(
        name="NYC Elevator Services Inc",
        address="123 Main St, Brooklyn, NY",
        phone="(718) 555-0123",
        website="www.nycelevator.com",
        categories=["Elevator Repair", "Elevator Inspection"],
        overall_rating=4.5,
        total_reviews=87,
        platform="yelp",
        platform_url="https://yelp.com/biz/nyc-elevator-services"
    )
    
    # Create mock certified inspectors
    mock_inspectors = [
        CertifiedInspector(
            name="NYC Elevator Services Inc",
            license_number="ELV-2024-001",
            license_type="DOB_ELEVATOR_AGENCY",
            license_status="ACTIVE",
            company_name="NYC Elevator Services Inc",
            address="123 Main St, Brooklyn, NY",
            specializations=["elevator_inspection", "escalator_inspection"]
        )
    ]
    
    verification = await marketplace._verify_vendor_comprehensive(
        mock_vendor, "elevator", mock_inspectors
    )
    
    print(f"   Vendor: {verification.vendor_name}")
    print(f"   Overall Score: {verification.overall_score}/100")
    print(f"   License Status: {verification.license_status}")
    print(f"   Certifications Found: {len(verification.certifications)}")
    print(f"   Risk Factors: {', '.join(verification.risk_factors) if verification.risk_factors else 'None'}")
    print(f"   Recommendations: {', '.join(verification.recommendations) if verification.recommendations else 'None'}")
    
    # Test 5: Database connectivity test
    print("\n\n🌐 Test 5: Database Connectivity")
    print("-" * 40)
    
    print("   Testing NYC Open Data API connectivity...")
    try:
        import requests
        response = requests.get(
            "https://data.cityofnewyork.us/resource/t8hj-ruu2.json",
            params={'$limit': 1},
            timeout=10
        )
        if response.status_code == 200:
            print("   ✅ NYC DOB License Database: Connected")
            data = response.json()
            if data:
                print(f"   Sample record: {data[0].get('licensee_name', 'N/A')}")
        else:
            print(f"   ❌ NYC DOB License Database: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ NYC DOB License Database: Connection failed - {str(e)}")
    
    # Test NYC Open Data Client
    print("   Testing NYC Open Data Client...")
    try:
        from nyc_opendata_client import NYCOpenDataClient
        client = NYCOpenDataClient()
        print("   ✅ NYC Open Data Client: Initialized")
    except Exception as e:
        print(f"   ❌ NYC Open Data Client: Error - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Vendor Marketplace Test Complete!")
    print("\nNext Steps:")
    print("1. Set APIFY_TOKEN environment variable for review scraping")
    print("2. Test with real property addresses")
    print("3. Integrate with property addition form")
    print("4. Add more certification databases")

if __name__ == "__main__":
    asyncio.run(test_vendor_marketplace())
