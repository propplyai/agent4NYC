// AI Compliance Dashboard JavaScript
class ComplianceDashboard {
    constructor() {
        this.currentReport = null;
        this.isGenerating = false;
        this.progressSteps = [
            'Searching property databases...',
            'Collecting violation records...',
            'Analyzing compliance data...',
            'Processing elevator equipment...',
            'Evaluating boiler inspections...',
            'Generating AI insights...',
            'Formatting comprehensive report...'
        ];
        this.currentStep = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRecentReports();
    }

    bindEvents() {
        // Main form submission
        document.getElementById('aiReportForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateAIReport();
        });

        // Export functionality
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportReport();
        });

        // Share functionality
        document.getElementById('shareBtn').addEventListener('click', () => {
            this.shareReport();
        });
    }

    async generateAIReport() {
        if (this.isGenerating) return;
        
        const address = document.getElementById('propertyAddress').value.trim();
        const zipCode = document.getElementById('propertyZip').value.trim();

        if (!address) {
            this.showError('Please enter a property address');
            return;
        }

        this.isGenerating = true;
        this.hideAllSections();
        this.showLoadingAnimation();

        try {
            // Step 1: Search for property
            await this.updateProgress(0, 'Searching property databases...');
            const searchResponse = await this.searchProperty(address, zipCode);
            
            if (!searchResponse.matches || searchResponse.matches.length === 0) {
                throw new Error('No properties found matching your search');
            }

            // Use the first match
            const property = searchResponse.matches[0];
            
            // Step 2: Generate compliance data
            await this.updateProgress(20, 'Collecting violation records...');
            const complianceResponse = await this.getComplianceData(property);
            
            // Step 3: Generate AI analysis
            await this.updateProgress(60, 'Generating AI insights...');
            const aiAnalysis = await this.generateAIAnalysis(complianceResponse.report, property);
            
            // Step 4: Display report
            await this.updateProgress(100, 'Formatting comprehensive report...');
            await this.delay(500);
            
            this.displayAIReport(aiAnalysis, property);
            this.saveRecentReport(aiAnalysis, property);
            
        } catch (error) {
            this.showError(`Failed to generate report: ${error.message}`);
        } finally {
            this.isGenerating = false;
            this.hideLoadingAnimation();
        }
    }

    async searchProperty(address, zipCode) {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, zip_code: zipCode })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Search failed');
        }

        return await response.json();
    }

    async getComplianceData(property) {
        const response = await fetch('/compliance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bin: property.bin,
                borough: property.borough,
                block: property.block,
                lot: property.lot
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get compliance data');
        }

        return await response.json();
    }

    async generateAIAnalysis(complianceData, property) {
        const response = await fetch('/ai-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                compliance_data: complianceData,
                property_info: property
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate AI analysis');
        }

        return await response.json();
    }

    displayAIReport(aiAnalysis, property) {
        this.currentReport = { aiAnalysis, property };
        
        // Update report title
        document.getElementById('reportTitle').textContent = 
            `Comprehensive Compliance Analysis - ${property.address.toUpperCase()}`;

        // Generate and display the report HTML
        const reportHtml = this.generateReportHtml(aiAnalysis, property);
        document.getElementById('aiReportContent').innerHTML = reportHtml;
        
        // Show the report section
        document.getElementById('reportSection').classList.remove('d-none');
        document.getElementById('reportSection').scrollIntoView({ behavior: 'smooth' });
        
        // Add animation effects
        this.animateReportSections();
    }

    generateReportHtml(analysis, property) {
        // Check if we have the new comprehensive structure
        const hasComprehensiveData = analysis.risk_assessment || analysis.priority_actions || analysis.compliance_insights;
        
        if (hasComprehensiveData) {
            return this.generateComprehensiveReportHtml(analysis, property);
        } else {
            // Fallback to legacy structure
            return this.generateLegacyReportHtml(analysis, property);
        }
    }

    generateComprehensiveReportHtml(analysis, property) {
        return `
            <div class="ai-report-container">
                <!-- Enhanced Report Header -->
                ${this.generateEnhancedHeader(analysis, property)}

                <!-- Risk Assessment Dashboard -->
                ${this.generateRiskAssessmentSection(analysis.risk_assessment)}

                <!-- Priority Actions Timeline -->
                ${this.generatePriorityActionsSection(analysis.priority_actions)}

                <!-- Financial Impact Analysis -->
                ${this.generateFinancialImpactSection(analysis.financial_impact)}

                <!-- Equipment Monitoring Dashboard -->
                ${this.generateEquipmentMonitoringSection(analysis.equipment_monitoring)}

                <!-- Compliance Insights -->
                ${this.generateComplianceInsightsSection(analysis.compliance_insights)}

                <!-- Regulatory Intelligence -->
                ${this.generateRegulatoryIntelligenceSection(analysis.regulatory_intelligence)}

                <!-- Data Freshness & Confidence -->
                ${this.generateDataFreshnessSection(analysis.data_freshness, analysis.ai_confidence)}
                
                <!-- Generation Info -->
                <div class="mt-4 text-center">
                    <small class="text-muted">
                        <i class="fas fa-robot me-1"></i>
                        Generated by AI on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}
                    </small>
                </div>
            </div>
        `;
    }

    generateLegacyReportHtml(analysis, property) {
        return `
            <div class="ai-report-container">
                <!-- Report Header -->
                <div class="report-header">
                    <h1 class="report-building-title">🏢 ${property.address.toUpperCase()}</h1>
                    <p class="report-building-subtitle">Building ID: ${property.bin} | ${property.borough}</p>
                </div>

                <!-- HPD Violations Section -->
                ${this.generateViolationsSection(analysis.hpd_violations, '🔥', 'HPD VIOLATIONS', 'hpd')}
                
                <!-- DOB Violations Section -->
                ${this.generateViolationsSection(analysis.dob_violations, '🏗️', 'DOB VIOLATIONS', 'dob')}
                
                <!-- Equipment Section -->
                ${this.generateEquipmentSection(analysis.equipment_data)}
                
                <!-- Compliance Scorecard -->
                ${this.generateScorecardSection(analysis.scorecard)}
                
                <!-- Recommendations -->
                ${this.generateRecommendationsSection(analysis.recommendations)}
                
                <!-- Building Highlights -->
                ${this.generateHighlightsSection(analysis.highlights)}
                
                <!-- Generation Info -->
                <div class="mt-4 text-center">
                    <small class="text-muted">
                        <i class="fas fa-robot me-1"></i>
                        Generated by AI on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}
                    </small>
                </div>
            </div>
        `;
    }

    generateViolationsSection(violations, icon, title, type) {
        if (!violations || violations.total === 0) {
            return `
                <div class="compliance-section">
                    <div class="section-header">
                        <span class="section-icon">${icon}</span>
                        <h2 class="section-title">${title}</h2>
                        <span class="section-count">0 records</span>
                    </div>
                    <div class="text-center text-muted py-3">
                        <i class="fas fa-check-circle fa-3x mb-2 text-success"></i>
                        <p>No violations found - Excellent compliance!</p>
                    </div>
                </div>
            `;
        }

        const recentItems = violations.recent_issues?.slice(0, 4) || [];
        const statusBreakdown = violations.status_breakdown || {};

        return `
            <div class="compliance-section">
                <div class="section-header">
                    <span class="section-icon">${icon}</span>
                    <h2 class="section-title">${title}</h2>
                    <span class="section-count">${violations.total} records</span>
                </div>
                
                ${violations.recent_issues ? `
                    <h4 class="mb-3">Recent Issues (${violations.time_period}):</h4>
                    ${recentItems.map((item, index) => `
                        <div class="violation-item ${this.getViolationClass(item.status)}">
                            <div class="violation-date">${index + 1}. ${item.date} - ${item.description}</div>
                            <span class="violation-status ${this.getStatusClass(item.status)}">${item.status}</span>
                        </div>
                    `).join('')}
                ` : ''}
                
                <h4 class="mt-4 mb-3">Status Breakdown:</h4>
                <div class="status-breakdown">
                    ${Object.entries(statusBreakdown).map(([status, count]) => `
                        <div class="status-item">
                            <div class="status-count ${this.getStatusColorClass(status)}">${count}</div>
                            <div class="status-label">${status} ${status.includes('violations') ? '' : 'violations'} ${this.getStatusIcon(status)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    generateEquipmentSection(equipment) {
        if (!equipment || !equipment.active_equipment) {
            return '';
        }

        return `
            <div class="compliance-section">
                <div class="section-header">
                    <span class="section-icon">🛗</span>
                    <h2 class="section-title">ELEVATOR EQUIPMENT</h2>
                    <span class="section-count">${equipment.total_devices} devices</span>
                </div>
                
                <h4 class="mb-3">Active Equipment:</h4>
                <div class="equipment-list">
                    ${equipment.active_equipment.map(item => `
                        <div class="equipment-item">
                            <div class="equipment-status">Active</div>
                            <div class="equipment-type">${item.count} ${item.type}</div>
                            <div class="equipment-details">${item.details}</div>
                        </div>
                    `).join('')}
                </div>
                
                ${equipment.removed_equipment ? `
                    <h4 class="mt-4 mb-3">Removed Equipment:</h4>
                    <div class="equipment-list">
                        ${equipment.removed_equipment.map(item => `
                            <div class="equipment-item" style="border-left-color: #94a3b8;">
                                <div class="equipment-status" style="color: #64748b;">Removed</div>
                                <div class="equipment-type">${item.count} ${item.type}</div>
                                <div class="equipment-details">${item.details}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateScorecardSection(scorecard) {
        if (!scorecard || !scorecard.areas) {
            return '';
        }

        return `
            <div class="compliance-section">
                <div class="section-header">
                    <span class="section-icon">📊</span>
                    <h2 class="section-title">OVERALL COMPLIANCE SCORECARD</h2>
                </div>
                
                <div class="scorecard-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Area</th>
                                <th>Status</th>
                                <th>Score</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${scorecard.areas.map(area => `
                                <tr>
                                    <td><strong>${area.area}</strong></td>
                                    <td>${area.status_icon} ${area.status}</td>
                                    <td><span class="grade-badge grade-${area.score.toLowerCase().charAt(0)}">${area.score}</span></td>
                                    <td>${area.notes}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    generateRecommendationsSection(recommendations) {
        if (!recommendations) {
            return '';
        }

        return `
            <div class="recommendations-section">
                <div class="recommendations-header">
                    <h2 class="recommendations-title">🎯 KEY RECOMMENDATIONS</h2>
                </div>
                
                ${recommendations.immediate ? `
                    <div class="recommendation-category">
                        <h3 class="category-title">
                            <i class="fas fa-exclamation-triangle category-icon"></i>
                            Immediate Actions:
                        </h3>
                        ${recommendations.immediate.map(item => `
                            <div class="recommendation-item">${item}</div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${recommendations.ongoing ? `
                    <div class="recommendation-category">
                        <h3 class="category-title">
                            <i class="fas fa-tasks category-icon"></i>
                            Ongoing Maintenance:
                        </h3>
                        ${recommendations.ongoing.map(item => `
                            <div class="recommendation-item">${item}</div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateHighlightsSection(highlights) {
        if (!highlights) {
            return '';
        }

        return `
            <div class="highlights-section">
                <div class="highlights-header">
                    <span class="highlights-icon">🏆</span>
                    <h2 class="highlights-title">BUILDING HIGHLIGHTS</h2>
                </div>
                
                <p class="mb-3">${highlights.summary}</p>
                
                ${highlights.strengths ? highlights.strengths.map(strength => `
                    <div class="highlight-item">
                        <i class="fas fa-check highlight-icon"></i>
                        <p class="highlight-text">${strength}</p>
                    </div>
                `).join('') : ''}
                
                ${highlights.conclusion ? `
                    <div class="mt-3 p-3" style="background: rgba(59, 130, 246, 0.1); border-radius: 8px; border-left: 4px solid var(--ai-blue);">
                        <p class="mb-0"><strong>Conclusion:</strong> ${highlights.conclusion}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // Helper methods for styling
    getViolationClass(status) {
        if (status?.toLowerCase().includes('active') || status?.toLowerCase().includes('pending')) return 'active';
        if (status?.toLowerCase().includes('dismiss')) return 'dismissed';
        return 'pending';
    }

    getStatusClass(status) {
        if (status?.toLowerCase().includes('active') || status?.toLowerCase().includes('pending')) return 'status-active';
        if (status?.toLowerCase().includes('dismiss')) return 'status-dismissed';
        return 'status-pending';
    }

    getStatusColorClass(status) {
        if (status?.toLowerCase().includes('dismiss')) return 'text-success';
        if (status?.toLowerCase().includes('active') || status?.toLowerCase().includes('pending')) return 'text-warning';
        return 'text-info';
    }

    getStatusIcon(status) {
        if (status?.toLowerCase().includes('dismiss')) return '✅';
        if (status?.toLowerCase().includes('active') || status?.toLowerCase().includes('pending')) return '⚠️';
        return '📋';
    }

    // Animation and UI methods
    async updateProgress(percentage, message) {
        document.getElementById('progressBar').style.width = `${percentage}%`;
        document.getElementById('loadingStatus').textContent = message;
        await this.delay(800); // Simulate processing time
    }

    showLoadingAnimation() {
        document.getElementById('loadingSection').classList.remove('d-none');
        this.currentStep = 0;
    }

    hideLoadingAnimation() {
        document.getElementById('loadingSection').classList.add('d-none');
    }

    animateReportSections() {
        const sections = document.querySelectorAll('.compliance-section');
        sections.forEach((section, index) => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            setTimeout(() => {
                section.style.transition = 'all 0.6s ease';
                section.style.opacity = '1';
                section.style.transform = 'translateY(0)';
            }, index * 200);
        });
    }

    hideAllSections() {
        document.getElementById('reportSection').classList.add('d-none');
        document.getElementById('errorSection').classList.add('d-none');
    }

    showError(message) {
        this.hideAllSections();
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').classList.remove('d-none');
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Export and sharing functionality
    exportReport() {
        if (!this.currentReport) return;
        
        // Create a printable version
        const printContent = document.getElementById('aiReportContent').innerHTML;
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Compliance Report - ${this.currentReport.property.address}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .compliance-section { margin-bottom: 30px; page-break-inside: avoid; }
                    .section-header { border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-bottom: 15px; }
                    .violation-item { border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
                    .scorecard-table table { width: 100%; border-collapse: collapse; }
                    .scorecard-table th, .scorecard-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    .recommendations-section, .highlights-section { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                </style>
            </head>
            <body>${printContent}</body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    shareReport() {
        if (!this.currentReport || !navigator.share) {
            // Fallback for browsers that don't support Web Share API
            this.copyReportLink();
            return;
        }

        navigator.share({
            title: `Compliance Report - ${this.currentReport.property.address}`,
            text: 'AI-generated property compliance analysis',
            url: window.location.href
        }).catch(err => {
            console.log('Error sharing:', err);
            this.copyReportLink();
        });
    }

    copyReportLink() {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            // Show success message
            const btn = document.getElementById('shareBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            btn.classList.add('btn-success');
            btn.classList.remove('btn-outline-secondary');
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-secondary');
            }, 2000);
        });
    }

    // Recent reports management
    saveRecentReport(analysis, property) {
        const reports = this.getRecentReports();
        const newReport = {
            id: Date.now(),
            property: property,
            analysis: analysis,
            timestamp: new Date().toISOString(),
            address: property.address
        };
        
        reports.unshift(newReport);
        // Keep only last 5 reports
        reports.splice(5);
        
        localStorage.setItem('recentReports', JSON.stringify(reports));
        this.loadRecentReports();
    }

    getRecentReports() {
        try {
            return JSON.parse(localStorage.getItem('recentReports') || '[]');
        } catch {
            return [];
        }
    }

    loadRecentReports() {
        const reports = this.getRecentReports();
        if (reports.length === 0) return;

        document.getElementById('recentReportsSection').classList.remove('d-none');
        const container = document.getElementById('recentReportsList');
        
        container.innerHTML = reports.map(report => `
            <div class="card mb-2">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${report.address}</h6>
                            <small class="text-muted">${new Date(report.timestamp).toLocaleDateString()}</small>
                        </div>
                        <button class="btn btn-outline-primary btn-sm" onclick="dashboard.loadReport('${report.id}')">
                            <i class="fas fa-eye me-1"></i>View
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    loadReport(reportId) {
        const reports = this.getRecentReports();
        const report = reports.find(r => r.id === parseInt(reportId));
        if (report) {
            this.displayAIReport(report.analysis, report.property);
        }
    }

    // NEW COMPREHENSIVE SECTION GENERATORS

    generateEnhancedHeader(analysis, property) {
        const riskAssessment = analysis.risk_assessment || {};
        const score = riskAssessment.risk_score || '0/100';
        const riskLevel = riskAssessment.risk_level || 'Unknown';
        const timestamp = analysis.analysis_timestamp ? new Date(analysis.analysis_timestamp).toLocaleString() : new Date().toLocaleString();
        
        const getRiskColor = (level) => {
            switch(level?.toLowerCase()) {
                case 'low': return 'success';
                case 'medium': return 'warning';
                case 'high': return 'danger';
                default: return 'secondary';
            }
        };

        return `
            <div class="enhanced-report-header">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h1 class="report-building-title">🏢 ${property.address.toUpperCase()}</h1>
                        <p class="report-building-subtitle">Building ID: ${property.bin} | ${property.borough}</p>
                        <div class="analysis-meta">
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>Analysis completed: ${timestamp}
                                ${analysis.ai_confidence ? `| Confidence: ${analysis.ai_confidence}` : ''}
                            </small>
                        </div>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="risk-score-display">
                            <div class="score-circle">
                                <span class="score-number">${score.split('/')[0]}</span>
                                <small class="score-total">/${score.split('/')[1] || '100'}</small>
                            </div>
                            <div class="risk-level">
                                <span class="badge bg-${getRiskColor(riskLevel)} risk-badge">${riskLevel.toUpperCase()} RISK</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generateRiskAssessmentSection(riskAssessment) {
        if (!riskAssessment) return '';
        
        const factors = riskAssessment.primary_risk_factors || [];
        const summary = riskAssessment.risk_summary || '';
        
        return `
            <div class="compliance-section risk-assessment-section">
                <div class="section-header">
                    <div class="section-icon text-warning">⚠️</div>
                    <h2 class="section-title">Risk Assessment</h2>
                </div>
                <div class="risk-summary">
                    <p class="lead">${summary}</p>
                </div>
                ${factors.length > 0 ? `
                    <div class="risk-factors">
                        <h4>Primary Risk Factors</h4>
                        <ul class="risk-factors-list">
                            ${factors.map(factor => `<li><i class="fas fa-exclamation-triangle text-warning me-2"></i>${factor}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generatePriorityActionsSection(priorityActions) {
        if (!priorityActions || priorityActions.length === 0) return '';
        
        return `
            <div class="compliance-section priority-actions-section">
                <div class="section-header">
                    <div class="section-icon text-danger">🎯</div>
                    <h2 class="section-title">Priority Actions</h2>
                    <span class="section-count">${priorityActions.length}</span>
                </div>
                <div class="priority-actions-timeline">
                    ${priorityActions.map(action => this.generatePriorityActionCard(action)).join('')}
                </div>
            </div>
        `;
    }

    generatePriorityActionCard(action) {
        const urgencyClass = this.getPriorityClass(action.priority);
        const deadline = action.timeline?.deadline ? new Date(action.timeline.deadline).toLocaleDateString() : 'No deadline';
        const cost = action.financial_impact?.estimated_cost || 'Cost TBD';
        const penalty = action.financial_impact?.potential_penalty || 'Penalty TBD';
        
        return `
            <div class="priority-action-card ${urgencyClass}">
                <div class="action-header">
                    <div class="action-priority">${action.priority}</div>
                    <div class="action-category">${action.category?.toUpperCase() || 'GENERAL'}</div>
                </div>
                <h4 class="action-title">${action.title}</h4>
                <p class="action-description">${action.action}</p>
                <div class="action-details">
                    <div class="row">
                        <div class="col-md-4">
                            <strong>Deadline:</strong><br>
                            <span class="deadline-date">${deadline}</span>
                        </div>
                        <div class="col-md-4">
                            <strong>Estimated Cost:</strong><br>
                            <span class="cost-amount">${cost}</span>
                        </div>
                        <div class="col-md-4">
                            <strong>Potential Penalty:</strong><br>
                            <span class="penalty-amount text-danger">${penalty}</span>
                        </div>
                    </div>
                </div>
                ${action.reason ? `
                    <div class="action-reason">
                        <strong>Why this matters:</strong> ${action.reason}
                    </div>
                ` : ''}
                ${action.regulatory_context ? `
                    <div class="regulatory-context">
                        <small class="text-muted">
                            <strong>Regulation:</strong> ${action.regulatory_context.regulation_reference || 'N/A'}
                        </small>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateFinancialImpactSection(financialImpact) {
        if (!financialImpact) return '';
        
        return `
            <div class="compliance-section financial-impact-section">
                <div class="section-header">
                    <div class="section-icon text-success">💰</div>
                    <h2 class="section-title">Financial Impact Analysis</h2>
                </div>
                <div class="financial-overview">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="financial-card immediate-exposure">
                                <h4>Immediate Exposure</h4>
                                <div class="amount text-danger">${financialImpact.immediate_exposure || 'TBD'}</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="financial-card annual-costs">
                                <h4>Annual Compliance Costs</h4>
                                <div class="amount text-info">${financialImpact.annual_compliance_costs || 'TBD'}</div>
                            </div>
                        </div>
                    </div>
                </div>
                ${financialImpact.cost_breakdown ? `
                    <div class="cost-breakdown">
                        <h4>Cost Breakdown</h4>
                        <div class="breakdown-grid">
                            ${Object.entries(financialImpact.cost_breakdown).map(([category, cost]) => `
                                <div class="breakdown-item">
                                    <span class="category">${category.replace('_', ' ').toUpperCase()}:</span>
                                    <span class="cost">${cost}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateEquipmentMonitoringSection(equipmentMonitoring) {
        if (!equipmentMonitoring) return '';
        
        return `
            <div class="compliance-section equipment-monitoring-section">
                <div class="section-header">
                    <div class="section-icon text-primary">🔧</div>
                    <h2 class="section-title">Equipment Monitoring</h2>
                </div>
                <div class="equipment-grid">
                    ${equipmentMonitoring.elevators ? this.generateEquipmentCard('Elevators', equipmentMonitoring.elevators, '🛗') : ''}
                    ${equipmentMonitoring.boilers ? this.generateEquipmentCard('Boilers', equipmentMonitoring.boilers, '🔥') : ''}
                    ${equipmentMonitoring.electrical ? this.generateEquipmentCard('Electrical', equipmentMonitoring.electrical, '⚡') : ''}
                </div>
            </div>
        `;
    }

    generateEquipmentCard(type, data, icon) {
        const totalDevices = data.total_devices || data.active_permits || 'N/A';
        const status = data.inspection_status || data.status_summary || 'Unknown';
        const gaps = data.compliance_gaps || data.action_needed || [];
        
        return `
            <div class="equipment-card">
                <div class="equipment-header">
                    <div class="equipment-icon">${icon}</div>
                    <h4>${type}</h4>
                    <span class="device-count">${totalDevices} ${type === 'Electrical' ? 'permits' : 'devices'}</span>
                </div>
                <div class="equipment-status">
                    <p><strong>Status:</strong> ${status}</p>
                </div>
                ${gaps.length > 0 ? `
                    <div class="compliance-gaps">
                        <strong>Action Required:</strong>
                        <ul>
                            ${gaps.map(gap => `<li>${gap}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${data.estimated_annual_costs ? `
                    <div class="equipment-costs">
                        <small class="text-muted">Annual Cost: ${data.estimated_annual_costs}</small>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateComplianceInsightsSection(insights) {
        if (!insights) return '';
        
        return `
            <div class="compliance-section insights-section">
                <div class="section-header">
                    <div class="section-icon text-info">💡</div>
                    <h2 class="section-title">Compliance Insights</h2>
                </div>
                <div class="insights-grid">
                    ${insights.strengths ? `
                        <div class="insight-card strengths">
                            <h4><i class="fas fa-check-circle text-success me-2"></i>Strengths</h4>
                            <ul>
                                ${insights.strengths.map(strength => `<li>${strength}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${insights.immediate_concerns ? `
                        <div class="insight-card concerns">
                            <h4><i class="fas fa-exclamation-triangle text-warning me-2"></i>Immediate Concerns</h4>
                            <ul>
                                ${insights.immediate_concerns.map(concern => `<li>${concern}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
                ${insights.trends_analysis ? `
                    <div class="trends-analysis">
                        <h4>Trends Analysis</h4>
                        <p>${insights.trends_analysis}</p>
                    </div>
                ` : ''}
                ${insights.compliance_trajectory ? `
                    <div class="compliance-trajectory">
                        <h4>Compliance Trajectory</h4>
                        <p>${insights.compliance_trajectory}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateRegulatoryIntelligenceSection(regulatory) {
        if (!regulatory) return '';
        
        return `
            <div class="compliance-section regulatory-section">
                <div class="section-header">
                    <div class="section-icon text-secondary">📋</div>
                    <h2 class="section-title">Regulatory Intelligence</h2>
                </div>
                ${regulatory.upcoming_inspections ? `
                    <div class="upcoming-inspections">
                        <h4>Upcoming Inspections & Deadlines</h4>
                        <p>${regulatory.upcoming_inspections}</p>
                    </div>
                ` : ''}
                ${regulatory.best_practices ? `
                    <div class="best-practices">
                        <h4>Best Practices</h4>
                        <ul>
                            ${regulatory.best_practices.map(practice => `<li>${practice}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${regulatory.monitoring_schedule ? `
                    <div class="monitoring-schedule">
                        <h4>Recommended Monitoring Schedule</h4>
                        <p>${regulatory.monitoring_schedule}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    generateDataFreshnessSection(dataFreshness, confidence) {
        return `
            <div class="compliance-section data-freshness-section">
                <div class="section-header">
                    <div class="section-icon text-muted">📊</div>
                    <h2 class="section-title">Data Quality & Freshness</h2>
                </div>
                <div class="row">
                    <div class="col-md-8">
                        ${dataFreshness ? `
                            <div class="freshness-info">
                                <p><strong>Compliance Data:</strong> ${dataFreshness.compliance_data_date || 'Current'}</p>
                                <p><strong>Regulatory Data:</strong> ${dataFreshness.regulatory_data_date || 'Current'}</p>
                                <p><strong>Analysis Confidence:</strong> ${dataFreshness.analysis_confidence || confidence || 'High'}</p>
                            </div>
                        ` : ''}
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="confidence-meter">
                            <div class="confidence-label">AI Confidence</div>
                            <div class="confidence-value">${confidence || 'High'}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Utility functions for new sections
    getPriorityClass(priority) {
        if (!priority) return 'priority-low';
        const p = priority.toLowerCase();
        if (p.includes('immediate') || p.includes('highest')) return 'priority-critical';
        if (p.includes('high')) return 'priority-high';
        if (p.includes('medium')) return 'priority-medium';
        return 'priority-low';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ComplianceDashboard();
});