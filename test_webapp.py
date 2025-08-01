#!/usr/bin/env python3
"""
Test script for the NYC Property Compliance Web App
"""

import requests
import json

def test_webapp():
    """Test the web app endpoints"""
    base_url = "http://localhost:5001"
    
    print("Testing NYC Property Compliance Web App")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test search endpoint
    search_data = {
        "address": "810 Whitestone Expressway",
        "zip_code": "11357"
    }
    
    try:
        response = requests.post(
            f"{base_url}/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nSearch test: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            matches = result.get('matches', [])
            print(f"Found {len(matches)} matches")
            
            if matches:
                print("\nSample match:")
                print(json.dumps(matches[0], indent=2))
                
                # Test compliance endpoint with first match
                match = matches[0]
                compliance_data = {
                    "bin": match.get('bin'),
                    "borough": match.get('borough'),
                    "block": match.get('block'),
                    "lot": match.get('lot')
                }
                
                print(f"\nTesting compliance report for: {match.get('address')}")
                compliance_response = requests.post(
                    f"{base_url}/compliance",
                    json=compliance_data,
                    headers={"Content-Type": "application/json"}
                )
                print(f"Compliance test: {compliance_response.status_code}")
                
                if compliance_response.status_code == 200:
                    compliance_result = compliance_response.json()
                    report = compliance_result.get('report', {})
                    compliance_data = report.get('compliance_data', {})
                    
                    print("Compliance data summary:")
                    for dataset, data in compliance_data.items():
                        count = data.get('count', 0)
                        print(f"  {dataset}: {count} records")
                else:
                    print(f"Compliance error: {compliance_response.text}")
            else:
                print("No matches found!")
        else:
            print(f"Search error: {response.text}")
            
    except Exception as e:
        print(f"Search test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Make sure the web app is running on port 5001")
    print("Run: python app.py")
    print()
    
    test_webapp()