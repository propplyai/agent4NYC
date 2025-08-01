#!/usr/bin/env python3
"""
Propply AI - Intelligent Compliance Management Platform
Modern Flask web application for property compliance management
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import uuid
import asyncio
from datetime import datetime, timedelta
from nyc_opendata_client import NYCOpenDataClient
from nyc_property_finder import search_property_by_address, get_property_compliance
from ai_compliance_analyzer import AIComplianceAnalyzer
from simple_vendor_marketplace import SimpleVendorMarketplace

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize AI analyzer
ai_analyzer = AIComplianceAnalyzer()

# Initialize simple vendor marketplace
vendor_marketplace = SimpleVendorMarketplace(
    apify_token=os.getenv('APIFY_TOKEN')
)

def get_client():
    """Get NYC Open Data client with config"""
    try:
        return NYCOpenDataClient.from_config()
    except Exception as e:
        print(f"Error initializing client: {e}")
        return None

@app.route('/')
def dashboard():
    """Main dashboard - centralized overview"""
    return render_template('propply/dashboard.html')

@app.route('/portfolio')
def portfolio():
    """Property portfolio visualization"""
    return render_template('propply/portfolio.html')

@app.route('/compliance')
def compliance():
    """Compliance management interface"""
    return render_template('propply/compliance.html')

@app.route('/marketplace')
def marketplace():
    """Service marketplace"""
    return render_template('propply/marketplace.html')

@app.route('/analytics')
def analytics():
    """Analytics and insights"""
    return render_template('propply/analytics.html')

@app.route('/settings')
def settings():
    """User settings and preferences"""
    return render_template('propply/settings.html')

@app.route('/add-property')
def add_property():
    """Render the enhanced 4-step property addition form"""
    return render_template('propply/add_property_4step.html')

@app.route('/add_property', methods=['POST'])
def add_property_post():
    """Handle property addition form submission"""
    try:
        data = request.get_json()
        
        # Extract form data
        address = data.get('address', '').strip()
        property_type = data.get('property_type')
        units = data.get('units')
        contact_name = data.get('contact_name')
        contact_email = data.get('contact_email')
        contact_phone = data.get('contact_phone')
        
        # Optional fields
        year_built = data.get('year_built')
        square_footage = data.get('square_footage')
        management_company = data.get('management_company')
        owner_name = data.get('owner_name')
        owner_email = data.get('owner_email')
        compliance_systems = data.get('compliance_systems', [])
        
        if not address:
            return jsonify({'error': 'Property address is required'}), 400
        
        # Try to auto-discover property data via NYC Open Data
        client = get_client()
        property_data = {'user_input': data}
        
        if client:
            try:
                matches = search_property_by_address(client, address)
                if matches and len(matches) > 0:
                    best_match = matches[0]
                    property_data['nyc_data'] = {
                        'bin': best_match.get('bin'),
                        'borough': best_match.get('borough'),
                        'block': best_match.get('block'),
                        'lot': best_match.get('lot'),
                        'address': best_match.get('address')
                    }
            except Exception as e:
                print(f"Auto-discovery failed: {e}")
        
        # Generate a property ID (in real app, this would be saved to database)
        property_id = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'message': 'Property added successfully!',
            'property_id': property_id,
            'data': property_data
        })
        
    except Exception as e:
        print(f"Add property error: {e}")
        return jsonify({'error': f'Failed to add property: {str(e)}'}), 500

# API Endpoints
@app.route('/api/search', methods=['POST'])
def api_search_property():
    """Search for property by address"""
    try:
        data = request.get_json()
        address = data.get('address', '').strip()
        zip_code = data.get('zip_code', '').strip() or None
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        client = get_client()
        if not client:
            return jsonify({'error': 'Unable to connect to NYC Open Data'}), 500
        
        # Search for properties
        matches = search_property_by_address(client, address, zip_code)
        
        if not matches:
            return jsonify({'matches': [], 'message': 'No properties found'})
        
        # Format matches for frontend
        formatted_matches = []
        for match in matches:
            if match and hasattr(match, 'get'):
                formatted_match = {
                    'address': match.get('address', 'Unknown Address'),
                    'borough': match.get('borough', 'Unknown'),
                    'bin': match.get('bin'),
                    'block': match.get('block'),
                    'lot': match.get('lot'),
                    'dataset': match.get('dataset'),
                    'strategy': match.get('strategy')
                }
                formatted_matches.append(formatted_match)
        
        return jsonify({'matches': formatted_matches})
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/compliance', methods=['POST'])
def api_generate_compliance():
    """Generate compliance report for selected property"""
    try:
        data = request.get_json()
        bin_number = data.get('bin')
        borough = data.get('borough')
        block = data.get('block')
        lot = data.get('lot')
        
        if not bin_number and not (borough and block and lot):
            return jsonify({'error': 'Either BIN or Borough/Block/Lot is required'}), 400
        
        client = get_client()
        if not client:
            return jsonify({'error': 'Unable to connect to NYC Open Data'}), 500
        
        # Generate compliance report
        report = get_property_compliance(client, bin_number, borough, block, lot)
        
        if not report:
            return jsonify({'error': 'Unable to generate compliance report'}), 500
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"compliance_report_{timestamp}.json"
        filepath = os.path.join('static', filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return jsonify({
            'report': report,
            'download_url': f'/static/{filename}',
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Compliance report generation failed: {str(e)}'}), 500

@app.route('/api/ai-analysis', methods=['POST'])
def api_generate_ai_analysis():
    """Generate AI-powered compliance analysis"""
    try:
        data = request.get_json()
        compliance_data = data.get('compliance_data')
        property_info = data.get('property_info')
        
        if not compliance_data or not property_info:
            return jsonify({'error': 'Compliance data and property info are required'}), 400
        
        # Generate AI analysis
        ai_analysis = ai_analyzer.analyze_compliance_data(compliance_data, property_info)
        
        if not ai_analysis:
            return jsonify({'error': 'Unable to generate AI analysis'}), 500
        
        # Save analysis to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ai_analysis_{timestamp}.json"
        filepath = os.path.join('static', filename)
        
        with open(filepath, 'w') as f:
            json.dump(ai_analysis, f, indent=2)
        
        return jsonify({
            'analysis': ai_analysis,
            'download_url': f'/static/{filename}',
            'generated_at': ai_analysis.get('generated_at'),
            'ai_version': '2.0'
        })
        
    except Exception as e:
        print(f"AI Analysis error: {e}")
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """Get dashboard overview data"""
    try:
        # Mock data for demonstration - replace with real data
        dashboard_data = {
            'overview': {
                'total_properties': 12,
                'compliance_rate': 87.5,
                'pending_inspections': 3,
                'overdue_items': 1
            },
            'upcoming_deadlines': [
                {
                    'property': '123 Main St, Brooklyn',
                    'inspection_type': 'Boiler Inspection',
                    'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
                    'priority': 'high'
                },
                {
                    'property': '456 Oak Ave, Manhattan',
                    'inspection_type': 'Elevator Inspection',
                    'due_date': (datetime.now() + timedelta(days=14)).isoformat(),
                    'priority': 'medium'
                },
                {
                    'property': '789 Pine St, Queens',
                    'inspection_type': 'Fire Safety',
                    'due_date': (datetime.now() + timedelta(days=21)).isoformat(),
                    'priority': 'low'
                }
            ],
            'recent_activity': [
                {
                    'type': 'inspection_completed',
                    'property': '123 Main St, Brooklyn',
                    'description': 'Boiler inspection completed successfully',
                    'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    'type': 'violation_resolved',
                    'property': '456 Oak Ave, Manhattan',
                    'description': 'DOB violation resolved',
                    'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
                }
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to load dashboard data: {str(e)}'}), 500

@app.route('/api/vendors/search', methods=['POST'])
def api_search_vendors():
    """Search for verified vendors"""
    try:
        data = request.get_json()
        property_address = data.get('property_address', '').strip()
        service_type = data.get('service_type', '').strip()
        compliance_requirements = data.get('compliance_requirements', [])
        
        if not property_address or not service_type:
            return jsonify({'error': 'Property address and service type are required'}), 400
        
        # Run async vendor search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                vendor_marketplace.find_verified_vendors(
                    property_address=property_address,
                    service_type=service_type,
                    compliance_requirements=compliance_requirements
                )
            )
        finally:
            loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Vendor search error: {e}")
        return jsonify({'error': f'Vendor search failed: {str(e)}'}), 500

@app.route('/api/vendors/compliance', methods=['POST'])
def api_get_compliance_vendors():
    """Get vendors for specific compliance categories"""
    try:
        data = request.get_json()
        compliance_categories = data.get('compliance_categories', [])
        
        if not compliance_categories:
            return jsonify({'error': 'Compliance categories are required'}), 400
        
        # Run async compliance vendor search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                vendor_marketplace.get_compliance_vendors(compliance_categories)
            )
        finally:
            loop.close()
        
        return jsonify({
            'compliance_categories': compliance_categories,
            'vendors_by_category': result,
            'search_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Compliance vendor search error: {e}")
        return jsonify({'error': f'Compliance vendor search failed: {str(e)}'}), 500

@app.route('/vendor-marketplace')
def vendor_marketplace_page():
    """Render vendor marketplace page"""
    return render_template('propply/vendor_marketplace.html')

@app.route('/api/health')
def api_health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('propply/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('propply/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
