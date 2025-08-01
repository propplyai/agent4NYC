// Modern NYC Property Compliance Dashboard JavaScript

class PropertyComplianceDashboard {
    constructor() {
        this.selectedProperty = null;
        this.currentReport = null;
        this.dataTables = {};
        this.charts = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.hideAllSections();
    }

    bindEvents() {
        // Search form submission
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchProperties();
        });

        // Export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportReport();
            });
        }

        // Enter key in address input
        document.getElementById('address').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.searchProperties();
            }
        });
    }

    hideAllSections() {
        document.getElementById('searchResults').classList.add('d-none');
        document.getElementById('complianceDashboard').classList.add('d-none');
        document.getElementById('errorSection').classList.add('d-none');
    }

    showError(message) {
        this.hideAllSections();
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').classList.remove('d-none');
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('d-none');
        }
        
        const searchBtn = document.querySelector('#searchForm button[type="submit"]');
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('d-none');
        }
        
        const searchBtn = document.querySelector('#searchForm button[type="submit"]');
        if (searchBtn) {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Search Property';
        }
    }

    async searchProperties() {
        const address = document.getElementById('address').value.trim();
        
        if (!address) {
            this.showError('Please enter a property address.');
            return;
        }

        this.showLoading();
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ address })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Search failed');
            }

            this.displaySearchResults(data.matches || []);
        } catch (error) {
            console.error('Search error:', error);
            this.showError(`Search failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(matches) {
        this.hideAllSections();
        
        const container = document.getElementById('propertyMatches');
        container.innerHTML = '';

        if (matches.length === 0) {
            container.innerHTML = '<div class="alert alert-info"><i class="fas fa-info-circle me-2"></i>No properties found for the given address.</div>';
        } else {
            matches.forEach((match, index) => {
                const matchElement = this.createPropertyMatchElement(match, index);
                container.appendChild(matchElement);
            });
            
            // Auto-generate report for first match
            if (matches.length > 0) {
                setTimeout(() => {
                    this.generateCompliance(matches[0]);
                }, 100);
            }
        }

        document.getElementById('searchResults').classList.remove('d-none');
    }

    createPropertyMatchElement(match, index) {
        const div = document.createElement('div');
        div.className = 'property-match';
        div.setAttribute('data-property', JSON.stringify(match));
        
        div.innerHTML = `
            <div class="property-match-content">
                <div class="property-address">
                    <i class="fas fa-map-marker-alt me-2"></i>
                    ${match.address}
                </div>
                <div class="property-details">
                    <span class="detail-item"><strong>BIN:</strong> ${match.bin || 'N/A'}</span>
                    <span class="detail-item"><strong>Borough:</strong> ${match.borough || 'N/A'}</span>
                    <span class="detail-item"><strong>Block:</strong> ${match.block || 'N/A'}</span>
                    <span class="detail-item"><strong>Lot:</strong> ${match.lot || 'N/A'}</span>
                    <span class="detail-item"><strong>Source:</strong> ${match.source || 'N/A'}</span>
                </div>
                <button class="btn btn-primary generate-btn" data-index="${index}">
                    <i class="fas fa-chart-line me-2"></i>Generate Compliance Report
                </button>
            </div>
        `;
        
        // Add click event for selection
        div.addEventListener('click', (e) => {
            if (!e.target.closest('.generate-btn')) {
                this.selectProperty(div, match);
            }
        });
        
        // Add click event for generate button
        const generateBtn = div.querySelector('.generate-btn');
        generateBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectProperty(div, match);
            this.generateCompliance(match);
        });
        
        // Auto-select first match
        if (index === 0) {
            div.classList.add('selected');
        }
        
        return div;
    }

    selectProperty(element, property) {
        // Remove selection from all matches
        document.querySelectorAll('.property-match').forEach(match => {
            match.classList.remove('selected');
        });
        
        // Select current match
        element.classList.add('selected');
        this.selectedProperty = property;
    }

    async generateCompliance(property) {
        this.selectedProperty = property;
        
        // Update UI to show selected property
        document.querySelectorAll('.property-match').forEach(match => {
            const matchData = JSON.parse(match.getAttribute('data-property'));
            if (matchData.bin === property.bin) {
                match.classList.add('selected');
            } else {
                match.classList.remove('selected');
            }
        });
        
        this.showLoading();
        
        try {
            const response = await fetch('/compliance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(property)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate compliance report');
            }

            this.currentReport = data;
            this.displayComplianceReport(data);
        } catch (error) {
            console.error('Compliance generation error:', error);
            this.showError(`Failed to generate compliance report: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    displayComplianceReport(data) {
        // Handle the data structure returned by Flask backend
        const report = data.report || data;
        const property_info = report.property_info;
        const compliance_data = report.compliance_data;
        const report_url = data.download_url || data.report_url;
        
        if (!property_info || !compliance_data) {
            this.showError('Invalid compliance report data received');
            return;
        }
        
        // Show compliance dashboard
        document.getElementById('complianceDashboard').classList.remove('d-none');
        
        // Update sections
        this.updatePropertyInfo(property_info);
        this.updateSummaryStats(compliance_data);
        this.updateDatasetCards(compliance_data);
        
        // Set export URL
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn && report_url) {
            exportBtn.setAttribute('data-url', report_url);
        }
        
        // Scroll to dashboard
        this.scrollToElement('complianceDashboard');
    }

    updatePropertyInfo(propertyInfo) {
        const container = document.getElementById('propertyInfo');
        if (!container) return;
        
        const infoItems = [
            { label: 'Address', value: propertyInfo.address },
            { label: 'BIN', value: propertyInfo.bin },
            { label: 'Borough', value: propertyInfo.borough },
            { label: 'Block', value: propertyInfo.block },
            { label: 'Lot', value: propertyInfo.lot },
            { label: 'ZIP Code', value: propertyInfo.zipcode },
            { label: 'Building Class', value: propertyInfo.bldgclass },
            { label: 'Owner Name', value: propertyInfo.ownername },
            { label: 'Year Built', value: propertyInfo.yearbuilt },
            { label: 'Units (Res)', value: propertyInfo.unitsres },
            { label: 'Units (Total)', value: propertyInfo.unitstotal }
        ];
        
        const validItems = infoItems.filter(item => 
            item.value && item.value !== 'N/A' && item.value !== '' && item.value !== '0'
        );
        
        container.innerHTML = validItems.map(item => `
            <div class="info-item">
                <div class="info-label">${item.label}</div>
                <div class="info-value">${item.value}</div>
            </div>
        `).join('');
    }

    updateSummaryStats(complianceData) {
        const stats = {
            totalViolations: 0,
            totalInspections: 0,
            totalComplaints: 0,
            activeIssues: 0
        };
        
        Object.entries(complianceData).forEach(([datasetName, data]) => {
            if (data && (data.count || (data.sample_records && data.sample_records.length > 0))) {
                const count = data.count || data.sample_records.length;
                const records = data.sample_records || data.records || [];
                
                if (datasetName.includes('violation')) {
                    stats.totalViolations += count;
                    const activeCount = records.filter(record => {
                        const status = (record.currentstatus || record.status || '').toLowerCase();
                        return !status.includes('closed') && !status.includes('resolved') && !status.includes('dismissed');
                    }).length;
                    stats.activeIssues += activeCount;
                } else if (datasetName.includes('inspection')) {
                    stats.totalInspections += count;
                } else if (datasetName.includes('complaint')) {
                    stats.totalComplaints += count;
                }
            }
        });
        
        // Update stat cards
        const statElements = {
            'violationsCount': stats.totalViolations,
            'inspectionsCount': stats.totalInspections,
            'complaintsCount': stats.totalComplaints,
            'activeIssuesCount': stats.activeIssues
        };
        
        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateDatasetCards(complianceData) {
        const container = document.getElementById('datasetCards');
        if (!container) return;
        
        container.innerHTML = '';
        
        const datasetInfo = {
            'hpd_violations': { name: 'HPD Violations', icon: 'fas fa-exclamation-triangle', color: 'danger' },
            'dob_violations': { name: 'DOB Violations', icon: 'fas fa-tools', color: 'warning' },
            'boiler_inspections': { name: 'Boiler Inspections', icon: 'fas fa-fire', color: 'info' },
            'elevator_inspections': { name: 'Elevator Inspections', icon: 'fas fa-elevator', color: 'primary' },
            'complaints_311': { name: '311 Complaints', icon: 'fas fa-phone', color: 'secondary' },
            'fdny_violations': { name: 'FDNY Violations', icon: 'fas fa-fire-extinguisher', color: 'danger' }
        };
        
        Object.entries(complianceData).forEach(([datasetName, data]) => {
            const info = datasetInfo[datasetName] || { name: datasetName, icon: 'fas fa-file', color: 'secondary' };
            const recordCount = data ? (data.count || (data.sample_records ? data.sample_records.length : 0)) : 0;
            const hasError = data && data.error;
            
            const card = document.createElement('div');
            card.className = 'dataset-card';
            card.innerHTML = `
                <div class="dataset-header">
                    <div class="dataset-icon">
                        <i class="${info.icon}"></i>
                    </div>
                    <div class="dataset-title">${info.name}</div>
                    <div class="dataset-count ${hasError ? 'error' : ''}">
                        ${hasError ? 'Error' : recordCount}
                    </div>
                </div>
                <div class="dataset-body">
                    ${hasError ? 
                        `<div class="error-message"><i class="fas fa-exclamation-circle me-2"></i>${data.error}</div>` :
                        recordCount > 0 ? 
                            `<div class="dataset-summary">${this.createDatasetSummary(data.sample_records || data.records || [], datasetName)}</div>` :
                            '<div class="no-data">No records found</div>'
                    }
                    ${recordCount > 0 && !hasError ? 
                        `<button class="btn btn-sm btn-outline-primary mt-2 view-details-btn" 
                                onclick="app.showRecordDetails('${datasetName}', '${info.name}')">
                            <i class="fas fa-eye me-1"></i>View Details
                        </button>` : ''
                    }
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    createDatasetSummary(records, datasetName) {
        if (!records || records.length === 0) return 'No data available';
        
        const sample = records.slice(0, 3);
        const summaryFields = {
            'hpd_violations': ['novdescription', 'currentstatus'],
            'dob_violations': ['violation_type', 'status'],
            'boiler_inspections': ['report_status', 'defects_exist'],
            'elevator_inspections': ['device_status', 'status_date'],
            'complaints_311': ['complaint_type', 'status'],
            'fdny_violations': ['violation_description', 'violation_status']
        };
        
        const fields = summaryFields[datasetName] || Object.keys(sample[0]).slice(0, 2);
        
        return sample.map(record => {
            const values = fields.map(field => {
                const value = record[field];
                if (!value) return null;
                return typeof value === 'string' && value.length > 30 ? 
                    value.substring(0, 30) + '...' : value;
            }).filter(v => v);
            
            return values.length > 0 ? `• ${values.join(' - ')}` : '• Record available';
        }).join('<br>');
    }

    showRecordDetails(datasetName, datasetTitle) {
        if (!this.currentReport || !this.currentReport.compliance_data[datasetName]) {
            return;
        }
        
        const data = this.currentReport.compliance_data[datasetName];
        const records = data.sample_records || data.records || [];
        
        if (records.length === 0) {
            return;
        }
        
        // Update modal title
        document.getElementById('modalTitle').textContent = `${datasetTitle} Details`;
        
        // Create table
        const container = document.getElementById('recordDetails');
        const tableHtml = this.createRecordsTable(records, datasetName);
        container.innerHTML = tableHtml;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('recordModal'));
        modal.show();
    }

    createRecordsTable(records, datasetName) {
        if (!records || records.length === 0) {
            return '<div class="alert alert-info">No records available</div>';
        }
        
        // Get relevant fields for each dataset type
        const fieldMappings = {
            'hpd_violations': {
                'Violation ID': 'violationid',
                'Description': 'novdescription',
                'Status': 'currentstatus',
                'Date': 'approveddate',
                'Class': 'class'
            },
            'dob_violations': {
                'ISN DOB BIS Extract': 'isn_dob_bis_extract',
                'Violation Type': 'violation_type',
                'Status': 'status',
                'Issue Date': 'issue_date',
                'Description': 'violation_description'
            },
            'boiler_inspections': {
                'Report Status': 'report_status',
                'Defects Exist': 'defects_exist',
                'Inspection Date': 'inspection_date',
                'Device Number': 'device_number'
            },
            'elevator_inspections': {
                'Device Status': 'device_status',
                'Status Date': 'status_date',
                'Device Number': 'device_number',
                'Device Type': 'device_type'
            },
            'complaints_311': {
                'Complaint Type': 'complaint_type',
                'Status': 'status',
                'Created Date': 'created_date',
                'Closed Date': 'closed_date'
            },
            'fdny_violations': {
                'Violation Description': 'violation_description',
                'Status': 'violation_status',
                'Date': 'violation_date',
                'Unit': 'unit'
            }
        };
        
        const fields = fieldMappings[datasetName] || {};
        const fieldKeys = Object.keys(fields);
        
        if (fieldKeys.length === 0) {
            // Fallback: use first few fields from the record
            const sampleRecord = records[0];
            const availableFields = Object.keys(sampleRecord).slice(0, 5);
            availableFields.forEach(field => {
                fields[field.charAt(0).toUpperCase() + field.slice(1)] = field;
            });
        }
        
        let tableHtml = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            ${Object.keys(fields).map(label => `<th>${label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        records.slice(0, 50).forEach(record => { // Limit to 50 records for performance
            tableHtml += '<tr>';
            Object.values(fields).forEach(fieldKey => {
                const value = record[fieldKey] || 'N/A';
                const displayValue = typeof value === 'string' && value.length > 50 ? 
                    value.substring(0, 50) + '...' : value;
                tableHtml += `<td>${displayValue}</td>`;
            });
            tableHtml += '</tr>';
        });
        
        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
        
        if (records.length > 50) {
            tableHtml += `<div class="alert alert-info mt-3">
                <i class="fas fa-info-circle me-2"></i>
                Showing first 50 of ${records.length} records
            </div>`;
        }
        
        return tableHtml;
    }

    exportReport() {
        const exportBtn = document.getElementById('exportBtn');
        const url = exportBtn?.getAttribute('data-url');
        
        if (url) {
            const link = document.createElement('a');
            link.href = url;
            link.download = url.split('/').pop();
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else if (this.currentReport) {
            // Fallback: download as JSON
            const dataStr = JSON.stringify(this.currentReport, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `compliance-report-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    }

    scrollToElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    }

    formatCurrency(amount) {
        if (!amount || isNaN(amount)) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
}

// Initialize the dashboard when the page loads
let app;
document.addEventListener('DOMContentLoaded', function() {
    app = new PropertyComplianceDashboard();
});
