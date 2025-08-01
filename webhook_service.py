#!/usr/bin/env python3
"""
Webhook Service for Propply AI
=============================

Service to send compliance analysis data to external AI agent via webhook
for enhanced analysis and insights generation.
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceWebhookService:
    """Service for sending compliance data to external AI analysis webhook"""
    
    def __init__(self, webhook_url: str = "https://klevaideas.app.n8n.cloud/webhook/compliance_analysis"):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Propply-AI-Webhook-Service/1.0'
        })
    
    def send_compliance_data(self, compliance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send compliance analysis data to external AI agent webhook
        
        Args:
            compliance_data: Complete compliance analysis data from our system
            
        Returns:
            Response from external AI agent or None if failed
        """
        try:
            # Prepare webhook payload
            webhook_payload = {
                "timestamp": datetime.now().isoformat(),
                "source": "propply_ai_compliance_system",
                "data_type": "property_compliance_analysis", 
                "compliance_data": compliance_data,
                "request_metadata": {
                    "version": "1.0",
                    "analysis_type": "comprehensive_property_compliance",
                    "datasets_included": [
                        "hpd_violations",
                        "dob_violations", 
                        "elevator_inspections",
                        "boiler_inspections",
                        "electrical_permits"
                    ]
                }
            }
            
            logger.info(f"Sending compliance data to webhook: {self.webhook_url}")
            logger.info(f"Property: {compliance_data.get('address', 'Unknown')}")
            
            # Send POST request to webhook
            response = self.session.post(
                self.webhook_url,
                json=webhook_payload,
                timeout=45  # 45 seconds to allow for AI processing time
            )
            
            # Check response status
            response.raise_for_status()
            
            logger.info(f"Webhook request successful - Status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                ai_analysis = response.json()
                logger.info("Received AI analysis response")
                return ai_analysis
            except json.JSONDecodeError:
                logger.warning("Webhook response was not valid JSON")
                return {
                    "status": "success",
                    "message": "Data sent successfully but no structured response received",
                    "raw_response": response.text
                }
                
        except requests.exceptions.Timeout:
            logger.error("Webhook request timed out")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request failed: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error sending webhook: {str(e)}")
            return None
    
    def test_webhook_connection(self) -> bool:
        """Test if webhook endpoint is accessible"""
        try:
            test_payload = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Connection test from Propply AI"
            }
            
            response = self.session.post(
                self.webhook_url,
                json=test_payload,
                timeout=10
            )
            
            logger.info(f"Webhook test - Status: {response.status_code}")
            return response.status_code < 400
            
        except Exception as e:
            logger.error(f"Webhook test failed: {str(e)}")
            return False

def send_test_compliance_report():
    """Send a test compliance report to the webhook"""
    
    # Load sample compliance data
    sample_data_file = "/Users/art3a/agent4NYC/comprehensive_compliance_report_20250726_124252.json"
    
    try:
        with open(sample_data_file, 'r') as f:
            sample_compliance_data = json.load(f)
        
        logger.info(f"Loaded sample compliance data for: {sample_compliance_data.get('address')}")
        
        # Initialize webhook service
        webhook_service = ComplianceWebhookService()
        
        # Test connection first (but continue even if test fails - webhook may only accept full payloads)
        webhook_service.test_webhook_connection()
        
        # Send compliance data
        ai_response = webhook_service.send_compliance_data(sample_compliance_data)
        
        if ai_response:
            logger.info("Successfully sent compliance data and received AI analysis")
            return ai_response
        else:
            logger.error("Failed to get AI analysis response")
            return None
            
    except FileNotFoundError:
        logger.error(f"Sample data file not found: {sample_data_file}")
        return None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in sample data file")
        return None
    except Exception as e:
        logger.error(f"Error sending test report: {str(e)}")
        return None

if __name__ == "__main__":
    print("Testing Propply AI Webhook Service...")
    print("=" * 50)
    
    result = send_test_compliance_report()
    
    if result:
        print("\n✅ Webhook test successful!")
        print("AI Analysis Response:")
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ Webhook test failed!")
        print("Check logs for details.")