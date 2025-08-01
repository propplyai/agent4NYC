#!/usr/bin/env python3
"""
Debug version of NYC Property Compliance Web App
Simplified for troubleshooting 404 issues
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime
from nyc_opendata_client import NYCOpenDataClient
from nyc_property_finder import search_property_by_address, get_property_compliance

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Simple HTML template with inline styles
SIMPLE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NYC Property Search - Debug</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin: 10px 0; }
        input, button { padding: 8px; margin: 5px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        .results { margin-top: 20px; padding: 20px; background: #f8f9fa; }
        .match { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
        .error { color: red; }
        .loading { color: blue; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NYC Property Compliance Tracker (Debug)</h1>
        
        <div class="form-group">
            <input type="text" id="address" placeholder="Enter address (e.g., 1662 Park Avenue)" style="width: 300px;">
            <input type="text" id="zipcode" placeholder="ZIP code" style="width: 100px;">
            <button onclick="searchProperty()">Search</button>
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        async function searchProperty() {
            const address = document.getElementById('address').value;
            const zipcode = document.getElementById('zipcode').value;
            const resultsDiv = document.getElementById('results');
            
            if (!address) {
                resultsDiv.innerHTML = '<div class="error">Please enter an address</div>';
                return;
            }
            
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address: address, zip_code: zipcode })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    if (data.matches && data.matches.length > 0) {
                        let html = '<h3>Found ' + data.matches.length + ' matches:</h3>';
                        data.matches.forEach((match, i) => {
                            html += '<div class="match">';
                            html += '<strong>' + (match && match.address ? match.address : 'Address not available') + '</strong><br>';
                            html += 'BIN: ' + (match && match.bin ? match.bin : 'N/A') + '<br>';
                            html += 'Borough: ' + (match && match.borough ? match.borough : 'N/A') + '<br>';
                            html += 'Block: ' + (match && match.block ? match.block : 'N/A') + ', Lot: ' + (match && match.lot ? match.lot : 'N/A') + '<br>';
                            html += '<button onclick="getCompliance(' + i + ')">Get Compliance Report</button>';
                            html += '</div>';
                        });
                        resultsDiv.innerHTML = html;
                        window.currentMatches = data.matches;
                    } else {
                        resultsDiv.innerHTML = '<div class="error">No matches found</div>';
                    }
                } else {
                    resultsDiv.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
                }
            } catch (error) {
                resultsDiv.innerHTML = '<div class="error">Request failed: ' + error.message + '</div>';
            }
        }
        
        async function getCompliance(index) {
            const match = window.currentMatches && window.currentMatches[index];
            const resultsDiv = document.getElementById('results');
            
            if (!match) {
                resultsDiv.innerHTML += '<div class="error">Error: No property data available</div>';
                return;
            }
            
            resultsDiv.innerHTML += '<div class="loading">Generating compliance report...</div>';
            
            try {
                const response = await fetch('/compliance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bin: match.bin,
                        borough: match.borough,
                        block: match.block,
                        lot: match.lot
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const report = data.report;
                    const propertyAddress = (match && match.address) || (report && report.property_info && report.property_info.address) || 'Unknown Address';
                    let html = '<h3>Compliance Report for ' + propertyAddress + '</h3>';
                    html += '<p><strong>BIN:</strong> ' + report.property_info.bin + '</p>';
                    html += '<h4>Compliance Data:</h4>';
                    
                    Object.entries(report.compliance_data).forEach(([dataset, info]) => {
                        html += '<p><strong>' + dataset + ':</strong> ' + info.count + ' records</p>';
                    });
                    
                    if (data.download_url) {
                        html += '<p><a href="' + data.download_url + '" target="_blank">Download JSON Report</a></p>';
                    }
                    
                    resultsDiv.innerHTML += '<div class="results">' + html + '</div>';
                } else {
                    resultsDiv.innerHTML += '<div class="error">Compliance error: ' + data.error + '</div>';
                }
            } catch (error) {
                resultsDiv.innerHTML += '<div class="error">Compliance request failed: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with simple inline template"""
    return render_template_string(SIMPLE_TEMPLATE)

@app.route('/search', methods=['POST'])
def search_property():
    """Search for property by address"""
    try:
        data = request.get_json()
        address = data.get('address', '').strip()
        zip_code = data.get('zip_code', '').strip() or None
        
        # Clean address - remove common suffixes that interfere with search
        import re
        # Remove city, state patterns like ", New York, NY" or ", NYC" or ", Manhattan"
        address = re.sub(r',\s*(New York|NYC|Manhattan|Brooklyn|Queens|Bronx|Staten Island),?\s*(NY|New York)?$', '', address, flags=re.IGNORECASE)
        address = address.strip()
        
        print(f"DEBUG: Cleaned address: '{address}'")
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        # Get client
        try:
            client = NYCOpenDataClient.from_config()
        except Exception as e:
            return jsonify({'error': f'Client initialization failed: {str(e)}'}), 500
        
        print(f"DEBUG: Searching for: {address}, ZIP: {zip_code}")
        
        # Search with output capture
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        matches = []
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                matches = search_property_by_address(client, address, zip_code)
        except Exception as search_error:
            print(f"DEBUG: Search error: {search_error}")
            return jsonify({'error': f'Search failed: {str(search_error)}'}), 500
        
        print(f"DEBUG: Found {len(matches) if matches else 0} matches")
        
        if not matches:
            return jsonify({'matches': [], 'message': 'No properties found matching your search'})
        
        # Format matches
        formatted_matches = []
        for match in matches:
            formatted_match = {
                'address': match.get('address', 'Unknown address'),
                'bin': match.get('bin') or match.get('bin_number'),
                'borough': match.get('boro') or match.get('boroid') or match.get('borough'),
                'block': match.get('block'),
                'lot': match.get('lot'),
                'dataset': match.get('dataset'),
                'strategy': match.get('strategy')
            }
            formatted_matches.append(formatted_match)
        
        print(f"DEBUG: Returning {len(formatted_matches)} formatted matches")
        return jsonify({'matches': formatted_matches})
        
    except Exception as e:
        print(f"DEBUG: Endpoint error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/compliance', methods=['POST'])
def generate_compliance():
    """Generate compliance report for selected property"""
    try:
        data = request.get_json()
        bin_number = data.get('bin')
        borough = data.get('borough')
        block = data.get('block')
        lot = data.get('lot')
        
        if not bin_number and not (borough and block and lot):
            return jsonify({'error': 'Either BIN or Borough/Block/Lot is required'}), 400
        
        # Get client
        try:
            client = NYCOpenDataClient.from_config()
        except Exception as e:
            return jsonify({'error': f'Client initialization failed: {str(e)}'}), 500
        
        print(f"DEBUG: Generating compliance for BIN: {bin_number}")
        
        # Generate compliance report with output capture
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        report = None
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                report = get_property_compliance(client, bin_number, borough, block, lot)
        except Exception as compliance_error:
            print(f"DEBUG: Compliance error: {compliance_error}")
            return jsonify({'error': f'Compliance generation failed: {str(compliance_error)}'}), 500
        
        if not report:
            return jsonify({'error': 'Unable to generate compliance report'}), 500
        
        # Save report to file for download
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"compliance_report_{timestamp}.json"
        filepath = os.path.join('static', filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"DEBUG: Compliance report saved to {filepath}")
        
        return jsonify({
            'report': report,
            'download_url': f'/static/{filename}'
        })
        
    except Exception as e:
        print(f"DEBUG: Compliance endpoint error: {e}")
        return jsonify({'error': f'Compliance report generation failed: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("Starting debug version on port 5002")
    print("Open browser to: http://localhost:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)