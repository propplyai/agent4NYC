#!/usr/bin/env python3
"""
Propply AI - Intelligent Property Compliance Platform
====================================================

AI-powered compliance management platform for NYC commercial and multifamily properties.
Transforms reactive compliance management into proactive, automated workflows with
integrated vendor marketplace for seamless service provider connections.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import uuid
import asyncio
from datetime import datetime

# Add project directory to path
sys.path.append('/Users/art3a/agent4NYC')

from comprehensive_property_compliance import ComprehensivePropertyComplianceSystem
from webhook_service import ComplianceWebhookService
from vendor_marketplace import VendorMarketplace

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Initialize compliance system, webhook service, and vendor marketplace
compliance_system = ComprehensivePropertyComplianceSystem()
webhook_service = ComplianceWebhookService()
vendor_marketplace = VendorMarketplace()

@app.route('/')
def index():
    """Propply AI - Detailed compliance report interface"""
    return render_template('propply_report.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Propply AI',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test')
def test_api():
    """Simple test endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is working',
        'timestamp': datetime.now().isoformat()
    })

# Additional API endpoints can be added here for Supabase integration
# - Vendor marketplace data
# - Compliance regulations data
# - User management

@app.route('/api/ai-analysis/<analysis_id>', methods=['GET'])
def get_ai_analysis(analysis_id):
    """Fetch AI analysis results by analysis_id for polling"""
    try:
        if not hasattr(app, 'ai_analysis_results'):
            app.ai_analysis_results = {}
            
        if analysis_id not in app.ai_analysis_results:
            return jsonify({
                'success': False,
                'status': 'not_found',
                'message': f'No analysis found with ID: {analysis_id}'
            }), 404
            
        analysis_data = app.ai_analysis_results[analysis_id]
        
        return jsonify({
            'success': True,
            'status': analysis_data['status'],
            'analysis': analysis_data.get('result'),
            'error': analysis_data.get('error'),
            'completed_at': analysis_data.get('completed_at')
        })
        
    except Exception as e:
        print(f"Error fetching AI analysis: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Error fetching analysis: {str(e)}'
        }), 500

@app.route('/api/analyze-property', methods=['POST'])
def analyze_property():
    """Comprehensive property compliance analysis using our advanced system"""
    try:
        print(f"[DEBUG] Received request: {request.method} {request.url}")
        
        data = request.get_json()
        if not data:
            print("[ERROR] No JSON data received")
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        address = data.get('address', '').strip()
        print(f"[DEBUG] Analyzing address: '{address}'")
        
        if not address:
            return jsonify({'success': False, 'error': 'Address is required'}), 400
        
        # Run comprehensive property analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print(f"Analyzing property: {address}")
            record = loop.run_until_complete(
                compliance_system.process_property(address)
            )
            
            # Convert dataclass to dict for JSON response
            compliance_data = {
                'address': record.address,
                'bin': record.bin,
                'bbl': record.bbl,
                'borough': record.borough,
                'block': record.block,
                'lot': record.lot,
                'zip_code': record.zip_code,
                'hpd_violations_total': record.hpd_violations_total,
                'hpd_violations_active': record.hpd_violations_active,
                'dob_violations_total': record.dob_violations_total,
                'dob_violations_active': record.dob_violations_active,
                'elevator_devices_total': record.elevator_devices_total,
                'elevator_devices_active': record.elevator_devices_active,
                'boiler_devices_total': record.boiler_devices_total,
                'electrical_permits_total': record.electrical_permits_total,
                'electrical_permits_active': record.electrical_permits_active,
                'hpd_compliance_score': round(record.hpd_compliance_score, 1),
                'dob_compliance_score': round(record.dob_compliance_score, 1),
                'elevator_compliance_score': round(record.elevator_compliance_score, 1),
                'electrical_compliance_score': round(record.electrical_compliance_score, 1),
                'overall_compliance_score': round(record.overall_compliance_score, 1),
                'hpd_violations_data': record.hpd_violations_data,
                'dob_violations_data': record.dob_violations_data,
                'elevator_data': record.elevator_data,
                'boiler_data': record.boiler_data,
                'electrical_data': record.electrical_data,
                'processed_at': record.processed_at,
                'data_sources': record.data_sources
            }
            
            # Generate analysis ID for async AI processing
            analysis_id = str(uuid.uuid4())
            
            # Start AI analysis in background (non-blocking)
            import threading
            def background_ai_analysis():
                try:
                    print(f"🤖 [Background] Starting AI analysis for {analysis_id}...")
                    raw_ai_response = webhook_service.send_compliance_data(compliance_data)
                    
                    # Process the AI response
                    processed_ai_analysis = None
                    if raw_ai_response:
                        if isinstance(raw_ai_response, list) and len(raw_ai_response) > 0:
                            first_item = raw_ai_response[0]
                            if isinstance(first_item, dict) and 'output' in first_item:
                                processed_ai_analysis = first_item['output']
                            else:
                                processed_ai_analysis = first_item
                        elif isinstance(raw_ai_response, dict):
                            if 'output' in raw_ai_response:
                                processed_ai_analysis = raw_ai_response['output']
                            else:
                                processed_ai_analysis = raw_ai_response
                    
                    # Store result in memory (in production, use Redis/database)
                    if not hasattr(app, 'ai_analysis_results'):
                        app.ai_analysis_results = {}
                    
                    app.ai_analysis_results[analysis_id] = {
                        'status': 'completed',
                        'result': processed_ai_analysis,
                        'completed_at': datetime.now().isoformat()
                    }
                    print(f"✅ [Background] AI analysis completed for {analysis_id}")
                except Exception as e:
                    print(f"❌ [Background] AI analysis failed for {analysis_id}: {e}")
                    if not hasattr(app, 'ai_analysis_results'):
                        app.ai_analysis_results = {}
                    app.ai_analysis_results[analysis_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'completed_at': datetime.now().isoformat()
                    }
            
            # Initialize analysis status
            if not hasattr(app, 'ai_analysis_results'):
                app.ai_analysis_results = {}
            
            app.ai_analysis_results[analysis_id] = {
                'status': 'processing',
                'started_at': datetime.now().isoformat()
            }
            
            # Start background thread
            thread = threading.Thread(target=background_ai_analysis)
            thread.daemon = True
            thread.start()
            
            print(f"🚀 AI analysis started in background with ID: {analysis_id}")
            ai_analysis = None  # Will be fetched via polling
            
            # Get vendor recommendations based on violations
            vendor_recommendations = None
            try:
                print("Getting vendor recommendations...")
                violation_data = {
                    'hpd_violations_active': record.hpd_violations_active,
                    'dob_violations_active': record.dob_violations_active,
                    'elevator_devices_active': record.elevator_devices_active,
                    'boiler_devices_total': record.boiler_devices_total,
                    'electrical_permits_active': record.electrical_permits_active
                }
                
                vendor_recommendations = vendor_marketplace.get_vendors_for_property(
                    property_address=record.address,
                    violation_data=violation_data,
                    max_vendors_per_category=3
                )
                
                # Format vendors for UI
                formatted_vendors = {}
                for category, vendors in vendor_recommendations.items():
                    formatted_vendors[category] = [
                        vendor_marketplace.format_vendor_for_ui(vendor, category) 
                        for vendor in vendors
                    ]
                
                vendor_recommendations = formatted_vendors
                print(f"✅ Found vendors for {len(vendor_recommendations)} categories")
                
            except Exception as e:
                print(f"❌ Vendor recommendations failed: {e}")
                vendor_recommendations = {}
            
            result = {
                'success': True,
                'property': {
                    'address': record.address,
                    'bin': record.bin,
                    'bbl': record.bbl,
                    'borough': record.borough,
                    'block': record.block,
                    'lot': record.lot,
                    'zip_code': record.zip_code
                },
                'compliance_scores': {
                    'overall': round(record.overall_compliance_score, 1),
                    'hpd': round(record.hpd_compliance_score, 1),
                    'dob': round(record.dob_compliance_score, 1),
                    'elevator': round(record.elevator_compliance_score, 1),
                    'electrical': round(record.electrical_compliance_score, 1)
                },
                'violations': {
                    'hpd_total': record.hpd_violations_total,
                    'hpd_active': record.hpd_violations_active,
                    'dob_total': record.dob_violations_total,
                    'dob_active': record.dob_violations_active
                },
                'equipment': {
                    'elevator_total': record.elevator_devices_total,
                    'elevator_active': record.elevator_devices_active,
                    'boiler_total': record.boiler_devices_total,
                    'electrical_permits_total': record.electrical_permits_total,
                    'electrical_permits_active': record.electrical_permits_active
                },
                'inspections': {
                    'hpd_violations': json.loads(record.hpd_violations_data) if record.hpd_violations_data else [],
                    'dob_violations': json.loads(record.dob_violations_data) if record.dob_violations_data else [],
                    'elevator_data': json.loads(record.elevator_data) if record.elevator_data else [],
                    'boiler_data': json.loads(record.boiler_data) if record.boiler_data else [],
                    'electrical_data': json.loads(record.electrical_data) if record.electrical_data else []
                },
                'analysis_metadata': {
                    'processed_at': record.processed_at,
                    'data_sources': record.data_sources,
                    'analysis_id': analysis_id,  # Add analysis_id for polling
                    'ai_analysis_status': 'pending' if ai_analysis is None else 'completed'
                },
                'ai_analysis': ai_analysis,  # Add AI analysis to response
                'vendor_recommendations': vendor_recommendations  # Add vendor recommendations
            }
            
            print(f"Final result being sent to frontend:")
            print(f"- success: {result['success']}")
            print(f"- ai_analysis present: {'ai_analysis' in result}")
            print(f"- ai_analysis type: {type(result.get('ai_analysis'))}")
            if result.get('ai_analysis'):
                print(f"- ai_analysis keys: {result['ai_analysis'].keys() if isinstance(result['ai_analysis'], dict) else 'Not a dict'}")
            print(f"- vendor_recommendations present: {'vendor_recommendations' in result}")
            print(f"- vendor categories: {list(result.get('vendor_recommendations', {}).keys())}")
            
            return jsonify(result)
            
        finally:
            loop.close()
            
    except Exception as e:
        print(f"Property analysis error: {e}")
        return jsonify({
            'success': False,
            'error': f'Property analysis failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)