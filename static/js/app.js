// NYC Property Compliance Tracker JavaScript

class PropertyApp {
    constructor() {
        this.selectedProperty = null;
        this.currentReport = null;
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

        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadReport();
        });
    }

    hideAllSections() {
        document.getElementById('searchResults').classList.add('d-none');
        document.getElementById('complianceSection').classList.add('d-none');
        document.getElementById('errorSection').classList.add('d-none');
        document.getElementById('loadingSpinner').classList.add('d-none');
    }

    showError(message) {
        this.hideAllSections();
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').classList.remove('d-none');
        document.getElementById('errorSection').scrollIntoView({ behavior: 'smooth' });
    }

    showLoading(show = true) {
        if (show) {
            document.getElementById('loadingSpinner').classList.remove('d-none');
            document.getElementById('searchBtn').disabled = true;
            document.getElementById('searchBtn').innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
        } else {
            document.getElementById('loadingSpinner').classList.add('d-none');
            document.getElementById('searchBtn').disabled = false;
            document.getElementById('searchBtn').innerHTML = '<i class="fas fa-search me-2"></i>Search Property';
        }
    }

    async searchProperties() {
        const address = document.getElementById('address').value.trim();
        const zipCode = document.getElementById('zipCode').value.trim();

        if (!address) {
            this.showError('Please enter a property address');
            return;
        }

        this.hideAllSections();
        this.showLoading(true);

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    address: address,
                    zip_code: zipCode
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Search failed');
            }

            this.displaySearchResults(data);

        } catch (error) {
            this.showError(`Search failed: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    displaySearchResults(data) {
        const { matches, message } = data;
        
        if (!matches || matches.length === 0) {
            this.showError(message || 'No properties found matching your search');
            return;
        }

        // Show results section
        document.getElementById('searchResults').classList.remove('d-none');
        document.getElementById('matchCount').textContent = matches.length;

        const container = document.getElementById('propertyMatches');
        container.innerHTML = '';

        matches.forEach((match, index) => {
            const matchElement = this.createPropertyMatchElement(match, index);
            container.appendChild(matchElement);
        });

        // Scroll to results
        document.getElementById('searchResults').scrollIntoView({ behavior: 'smooth' });
    }

    createPropertyMatchElement(match, index) {
        const div = document.createElement('div');
        div.className = 'property-match fade-in';
        div.style.animationDelay = `${index * 0.1}s`;
        
        div.innerHTML = `
            <div class="property-address">${match.address}</div>
            <div class="property-details">
                ${match.bin ? `<span class="property-detail"><strong>BIN:</strong> ${match.bin}</span>` : ''}
                ${match.borough ? `<span class="property-detail"><strong>Borough:</strong> ${match.borough}</span>` : ''}
                ${match.block ? `<span class="property-detail"><strong>Block:</strong> ${match.block}</span>` : ''}
                ${match.lot ? `<span class="property-detail"><strong>Lot:</strong> ${match.lot}</span>` : ''}
            </div>
            <div class="property-source">Found in ${match.dataset} using ${match.strategy} strategy</div>
            <div class="mt-2">
                <button class="btn btn-primary btn-sm" onclick="app.generateCompliance(${JSON.stringify(match).replace(/"/g, '&quot;')})">
                    <i class="fas fa-clipboard-check me-1"></i>Generate Compliance Report
                </button>
            </div>
        `;

        return div;
    }

    async generateCompliance(property) {
        this.selectedProperty = property;
        
        // Show loading for compliance
        document.getElementById('complianceSection').classList.remove('d-none');
        document.getElementById('complianceReport').innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Generating compliance report...</p>
            </div>
        `;

        // Scroll to compliance section
        document.getElementById('complianceSection').scrollIntoView({ behavior: 'smooth' });

        try {
            const response = await fetch('/compliance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    bin: property.bin,
                    borough: property.borough,
                    block: property.block,
                    lot: property.lot
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate compliance report');
            }

            this.displayComplianceReport(data);

        } catch (error) {
            document.getElementById('complianceReport').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to generate compliance report: ${error.message}
                </div>
            `;
        }
    }

    displayComplianceReport(data) {
        this.currentReport = data;
        const { report, download_url } = data;

        // Enable download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.disabled = false;
        downloadBtn.setAttribute('data-url', download_url);

        const container = document.getElementById('complianceReport');
        container.innerHTML = '';

        // Property information section
        const propertyInfo = this.createPropertyInfoSection(report.property_info);
        container.appendChild(propertyInfo);

        // Compliance data section
        const complianceData = this.createComplianceDataSection(report.compliance_data);
        container.appendChild(complianceData);

        // Generation timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'text-muted mt-3';
        timestamp.innerHTML = `<small><i class="fas fa-clock me-1"></i>Generated: ${report.generated_at}</small>`;
        container.appendChild(timestamp);
    }

    createPropertyInfoSection(propertyInfo) {
        const section = document.createElement('div');
        section.className = 'property-info fade-in';
        
        let ownerHtml = '';
        if (propertyInfo.owner) {
            ownerHtml = `
                <div class="info-item">
                    <div class="info-label">Owner Information</div>
                    <div class="info-value">
                        ${propertyInfo.owner.name || 'N/A'}<br>
                        ${propertyInfo.owner.address || ''}<br>
                        ${propertyInfo.owner.phone || ''}
                    </div>
                </div>
            `;
        }

        section.innerHTML = `
            <h6><i class="fas fa-building me-2"></i>Property Information</h6>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Address</div>
                    <div class="info-value">${propertyInfo.address || 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">BIN</div>
                    <div class="info-value">${propertyInfo.bin || 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Borough</div>
                    <div class="info-value">${propertyInfo.borough || 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Block</div>
                    <div class="info-value">${propertyInfo.block || 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Lot</div>
                    <div class="info-value">${propertyInfo.lot || 'N/A'}</div>
                </div>
                ${ownerHtml}
            </div>
        `;

        return section;
    }

    createComplianceDataSection(complianceData) {
        const section = document.createElement('div');
        section.className = 'mt-4';
        
        const header = document.createElement('h6');
        header.innerHTML = '<i class="fas fa-clipboard-list me-2"></i>Compliance Data by Dataset';
        section.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'compliance-summary';

        Object.entries(complianceData).forEach(([dataset, data]) => {
            const datasetElement = this.createDatasetElement(dataset, data);
            grid.appendChild(datasetElement);
        });

        section.appendChild(grid);
        return section;
    }

    createDatasetElement(datasetName, data) {
        const div = document.createElement('div');
        div.className = 'compliance-dataset fade-in';

        const count = data.count || 0;
        let countClass = 'record-count';
        if (count === 0) countClass += ' zero';
        else if (count > 10) countClass += ' high';
        else if (count > 50) countClass += ' critical';

        let recordsHtml = '';
        if (data.sample_records && data.sample_records.length > 0) {
            recordsHtml = `
                <div class="sample-records">
                    <h6 class="mb-2">Sample Records:</h6>
                    ${data.sample_records.map(record => this.createSampleRecordHtml(record)).join('')}
                </div>
            `;
        } else if (count === 0) {
            recordsHtml = '<div class="text-muted">No records found</div>';
        }

        let errorHtml = '';
        if (data.error) {
            errorHtml = `<div class="alert alert-warning mt-2"><small>${data.error}</small></div>`;
        }

        div.innerHTML = `
            <div class="dataset-header">
                <div class="dataset-name">${datasetName.replace(/_/g, ' ')}</div>
                <div class="${countClass}">${count}</div>
            </div>
            ${recordsHtml}
            ${errorHtml}
        `;

        return div;
    }

    createSampleRecordHtml(record) {
        const fields = Object.entries(record)
            .filter(([key, value]) => value !== null && value !== undefined && value !== '')
            .map(([key, value]) => `
                <div class="record-field">
                    <span class="field-name">${key.replace(/_/g, ' ')}:</span>
                    <span class="field-value">${this.formatFieldValue(value)}</span>
                </div>
            `).join('');

        return `<div class="sample-record">${fields}</div>`;
    }

    formatFieldValue(value) {
        if (typeof value === 'string' && value.length > 50) {
            return value.substring(0, 47) + '...';
        }
        return value;
    }

    downloadReport() {
        const downloadBtn = document.getElementById('downloadBtn');
        const url = downloadBtn.getAttribute('data-url');
        
        if (url) {
            const link = document.createElement('a');
            link.href = url;
            link.download = url.split('/').pop();
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PropertyApp();
});