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
        Send filtered compliance analysis data to external AI agent webhook
        
        Args:
            compliance_data: Complete compliance analysis data from our system
            
        Returns:
            Response from external AI agent or None if failed
        """
        try:
            # Filter and clean data for external AI agent
            filtered_data = self._prepare_filtered_data(compliance_data)
            
            # Prepare webhook payload with only filtered NYC data
            webhook_payload = {
                "timestamp": datetime.now().isoformat(),
                "source": "propply_ai_compliance_system",
                "data_type": "filtered_property_data", 
                "property_data": filtered_data,
                "request_metadata": {
                    "version": "2.0",
                    "analysis_type": "external_ai_compliance_analysis",
                    "data_filter": "last_2_years_only",
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
            logger.info(f"Starting AI analysis request at {datetime.now().isoformat()}")
            
            # Send POST request to webhook
            response = self.session.post(
                self.webhook_url,
                json=webhook_payload,
                timeout=240  # Give AI 4 minutes for comprehensive analysis
            )
            
            logger.info(f"AI analysis request completed at {datetime.now().isoformat()}")
            
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
    
    def _prepare_filtered_data(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter compliance data to only include last 2 years and remove pre-calculated scores
        
        Args:
            compliance_data: Raw compliance data from our system
            
        Returns:
            Filtered data with only recent records and no pre-calculated scores
        """
        from datetime import datetime, timedelta
        import json
        
        # Calculate cutoff date (2 years ago)
        cutoff_date = datetime.now() - timedelta(days=730)
        
        # Prepare filtered data structure
        filtered_data = {
            # Property identification (keep as-is)
            "address": compliance_data.get("address"),
            "bin": compliance_data.get("bin"),
            "bbl": compliance_data.get("bbl"),
            "borough": compliance_data.get("borough"),
            "block": compliance_data.get("block"),
            "lot": compliance_data.get("lot"),
            "zip_code": compliance_data.get("zip_code"),
            
            # Raw NYC data (filtered to last 2 years)
            "nyc_data": {
                "hpd_violations": self._parse_and_filter_json_data(
                    compliance_data.get("hpd_violations_data", "[]"), 
                    "approveddate", cutoff_date
                ),
                "dob_violations": self._parse_and_filter_json_data(
                    compliance_data.get("dob_violations_data", "[]"), 
                    "issue_date", cutoff_date
                ),
                "elevator_inspections": self._parse_and_filter_json_data(
                    compliance_data.get("elevator_data", "[]"), 
                    "status_date", cutoff_date
                ),
                "boiler_inspections": self._parse_and_filter_json_data(
                    compliance_data.get("boiler_data", "[]"), 
                    "inspection_date", cutoff_date
                ),
                "electrical_permits": self._parse_and_filter_json_data(
                    compliance_data.get("electrical_data", "[]"), 
                    "filing_date", cutoff_date
                )
            },
            
            # Metadata
            "data_collection_date": compliance_data.get("processed_at"),
            "data_sources": compliance_data.get("data_sources")
        }
        
        return filtered_data
    
    def _parse_and_filter_json_data(self, json_data: str, date_field: str, cutoff_date: datetime) -> list:
        """
        Parse JSON string data and filter to only include records after cutoff date
        
        Args:
            json_data: JSON string containing the data
            date_field: Field name containing the date to filter on
            cutoff_date: Only include records after this date
            
        Returns:
            Filtered list of records
        """
        import json
        from datetime import datetime
        
        try:
            data = json.loads(json_data) if json_data else []
            if not isinstance(data, list):
                return []
            
            filtered_records = []
            
            for record in data:
                date_str = record.get(date_field)
                if not date_str:
                    continue
                
                try:
                    # Handle different date formats
                    if isinstance(date_str, str):
                        # Handle MM/DD/YYYY HH:MM:SS format (boiler inspections)
                        if '/' in date_str and ' ' in date_str:
                            date_part = date_str.split(' ')[0]
                            record_date = datetime.strptime(date_part, '%m/%d/%Y')
                        # Handle ISO format (YYYY-MM-DDTHH:MM:SS.fff)
                        elif 'T' in date_str:
                            record_date = datetime.fromisoformat(date_str.replace('T', ' ').split('.')[0])
                        # Handle YYYY-MM-DD format
                        elif '-' in date_str:
                            record_date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                        else:
                            # Skip records with unparseable dates
                            continue
                    else:
                        continue
                    
                    # Only include records from last 2 years
                    if record_date >= cutoff_date:
                        filtered_records.append(record)
                        
                except (ValueError, AttributeError):
                    # Skip records with invalid dates
                    continue
            
            return filtered_records
            
        except (json.JSONDecodeError, TypeError):
            return []
    
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