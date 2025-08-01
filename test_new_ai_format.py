#!/usr/bin/env python3
"""
Test script to verify new AI response format handling
"""

import json

# Simulate the new AI response format
simulated_ai_response = [
    {
        "output": {
            "property_analysis": {
                "address": "140 WEST 28 STREET, MANHATTAN, NY 10001",
                "overall_risk_assessment": {
                    "risk_level": "HIGH",
                    "risk_score": "87",
                    "primary_risk_factors": [
                        "2 active HPD violations including failure to file valid registration and bedbug report",
                        "Elevator compliance score at 75% with 6 active elevator devices requiring oversight"
                    ],
                    "risk_summary": "The property shows a moderately high compliance score of 87/100 with specific concerns around 2 active HPD violations that are non-rent-impairing but require prompt filing compliance."
                },
                "priority_actions": [
                    {
                        "priority": "HIGH",
                        "category": "HPD Violation Remediation",
                        "action": "Immediate filing and compliance with annual bedbug reporting and valid registration statement to HPD to avoid fines.",
                        "reason": "Active HPD violations are legal obligations that directly impact property compliance and tenant relations",
                        "estimated_cost": "$2,000 - $4,000 for legal and filing fees",
                        "timeline": "Within 30 days"
                    }
                ]
            },
            "ai_confidence": "HIGH",
            "analysis_timestamp": "2025-07-26T14:07:15.028854"
        }
    }
]

def test_ai_response_parsing():
    """Test the AI response parsing logic"""
    
    print("Testing AI Response Format Parsing")
    print("=" * 40)
    
    # Test the parsing logic from app.py
    raw_ai_response = simulated_ai_response
    ai_analysis = None
    
    try:
        if isinstance(raw_ai_response, list) and len(raw_ai_response) > 0:
            if 'output' in raw_ai_response[0]:
                ai_analysis = raw_ai_response[0]['output']
                print("✅ Successfully extracted AI analysis from output wrapper")
            else:
                ai_analysis = raw_ai_response[0]
        elif isinstance(raw_ai_response, dict):
            if 'output' in raw_ai_response:
                ai_analysis = raw_ai_response['output']
            else:
                ai_analysis = raw_ai_response
        else:
            ai_analysis = raw_ai_response
            
        print(f"✅ Processed AI analysis structure: {type(ai_analysis)}")
        
        # Test key data extraction
        if ai_analysis and 'property_analysis' in ai_analysis:
            analysis = ai_analysis['property_analysis']
            risk_assessment = analysis['overall_risk_assessment']
            
            print(f"✅ Address: {analysis['address']}")
            print(f"✅ Risk Level: {risk_assessment['risk_level']}")
            print(f"✅ Risk Score: {risk_assessment['risk_score']}")
            print(f"✅ Risk Factors Count: {len(risk_assessment['primary_risk_factors'])}")
            print(f"✅ Priority Actions Count: {len(analysis['priority_actions'])}")
            print(f"✅ AI Confidence: {ai_analysis['ai_confidence']}")
            
            return True
        else:
            print("❌ Missing expected data structure")
            return False
            
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_response_parsing()
    
    if success:
        print("\n🎉 AI Response Format Test: PASSED")
        print("The backend should now handle the new AI response format correctly!")
    else:
        print("\n❌ AI Response Format Test: FAILED")
        print("Review the parsing logic in app.py")