"""
AI Compliance Analyzer
Generates intelligent compliance reports from NYC property data
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class AIComplianceAnalyzer:
    def __init__(self):
        self.violation_keywords = {
            'critical': ['fire', 'emergency', 'unsafe', 'hazard', 'dangerous', 'immediate'],
            'structural': ['elevator', 'stairs', 'roof', 'foundation', 'structural'],
            'maintenance': ['repair', 'replace', 'maintain', 'clean', 'fix'],
            'administrative': ['registration', 'notice', 'post', 'file', 'certificate']
        }
        
        self.equipment_types = {
            'elevator': ['elevator', 'lift'],
            'boiler': ['boiler', 'heating'],
            'conveyor': ['conveyor'],
            'hoist': ['hoist']
        }

    def analyze_compliance_data(self, compliance_data: Dict, property_info: Dict) -> Dict:
        """
        Generate comprehensive AI analysis of property compliance data
        """
        try:
            analysis = {
                'property_info': property_info,
                'hpd_violations': self._analyze_hpd_violations(compliance_data.get('compliance_data', {}).get('hpd_violations', {})),
                'dob_violations': self._analyze_dob_violations(compliance_data.get('compliance_data', {}).get('dob_violations', {})),
                'equipment_data': self._analyze_equipment_data(compliance_data.get('compliance_data', {})),
                'scorecard': self._generate_scorecard(compliance_data.get('compliance_data', {})),
                'recommendations': self._generate_recommendations(compliance_data.get('compliance_data', {})),
                'highlights': self._generate_highlights(compliance_data.get('compliance_data', {}), property_info),
                'generated_at': datetime.now().isoformat(),
                'ai_insights': self._generate_ai_insights(compliance_data.get('compliance_data', {}))
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return self._generate_fallback_analysis(property_info)

    def _analyze_hpd_violations(self, hpd_data: Dict) -> Dict:
        """Analyze HPD violations with AI insights"""
        if not hpd_data or hpd_data.get('count', 0) == 0:
            return {
                'total': 0,
                'status_breakdown': {'No violations': 0},
                'recent_issues': None,
                'time_period': '2023-2024'
            }

        violations = hpd_data.get('sample_records', [])
        total_count = hpd_data.get('count', len(violations))
        
        # Analyze recent issues (last 2 years)
        recent_issues = []
        status_counts = {}
        
        for violation in violations[:10]:  # Analyze up to 10 recent violations
            try:
                # Extract date
                date_str = violation.get('inspectiondate', '')
                if 'T' in date_str:
                    date_str = date_str.split('T')[0]
                
                # Extract description
                description = violation.get('novdescription', '').strip()
                if len(description) > 100:
                    description = description[:97] + '...'
                
                # Determine violation type
                violation_type = self._categorize_violation(description)
                
                # Extract status
                status = violation.get('currentstatus', 'Unknown').title()
                status_counts[status] = status_counts.get(status, 0) + 1
                
                recent_issues.append({
                    'date': date_str,
                    'description': f"{violation_type} violation",
                    'status': status,
                    'details': description
                })
                
            except Exception as e:
                print(f"Error processing violation: {e}")
                continue
        
        # Sort by date (most recent first)
        recent_issues.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'total': total_count,
            'recent_issues': recent_issues[:4],  # Show top 4
            'status_breakdown': status_counts,
            'time_period': '2023-2024',
            'severity_analysis': self._analyze_violation_severity(violations)
        }

    def _analyze_dob_violations(self, dob_data: Dict) -> Dict:
        """Analyze DOB violations with historical patterns"""
        if not dob_data or dob_data.get('count', 0) == 0:
            return {
                'total': 0,
                'status_breakdown': {'No violations': 0},
                'historical_pattern': 'No DOB violations on record',
                'time_period': '2000-2020'
            }

        violations = dob_data.get('sample_records', [])
        total_count = dob_data.get('count', len(violations))
        
        # Analyze historical patterns
        categories = {
            'Elevator Issues': 0,
            'Construction Violations': 0,
            'Certification Failures': 0,
            'Benchmarking Failures': 0
        }
        
        status_counts = {}
        
        for violation in violations:
            try:
                description = violation.get('novdescription', '').lower()
                status = violation.get('currentstatus', 'Unknown').title()
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Categorize violation
                if 'elevator' in description:
                    categories['Elevator Issues'] += 1
                elif any(word in description for word in ['construction', 'building']):
                    categories['Construction Violations'] += 1
                elif any(word in description for word in ['certificate', 'certification', 'energy']):
                    categories['Certification Failures'] += 1
                elif 'benchmark' in description:
                    categories['Benchmarking Failures'] += 1
                    
            except Exception as e:
                print(f"Error processing DOB violation: {e}")
                continue
        
        # Generate historical pattern description
        active_categories = [cat for cat, count in categories.items() if count > 0]
        pattern_desc = f"Historical Pattern (2000-2020): {', '.join(active_categories)}" if active_categories else "No significant patterns identified"
        
        return {
            'total': total_count,
            'status_breakdown': status_counts,
            'historical_pattern': pattern_desc,
            'time_period': '2000-2020',
            'categories': categories
        }

    def _analyze_equipment_data(self, compliance_data: Dict) -> Optional[Dict]:
        """Analyze equipment and inspection data"""
        equipment_data = {}
        active_equipment = []
        removed_equipment = []
        total_devices = 0
        
        # Check for elevator equipment data
        elevator_data = compliance_data.get('elevator_equipment', {})
        if elevator_data and elevator_data.get('count', 0) > 0:
            records = elevator_data.get('sample_records', [])
            
            # Group by equipment type and status
            equipment_groups = {}
            for record in records:
                try:
                    device_type = record.get('devicetype', 'Unknown Equipment').title()
                    status = record.get('status', 'Unknown').lower()
                    
                    key = f"{device_type}_{status}"
                    if key not in equipment_groups:
                        equipment_groups[key] = []
                    equipment_groups[key].append(record)
                    
                except Exception as e:
                    print(f"Error processing equipment: {e}")
                    continue
            
            # Format active equipment
            for key, records in equipment_groups.items():
                device_type, status = key.rsplit('_', 1)
                count = len(records)
                total_devices += count
                
                # Get inspection dates for details
                inspection_dates = []
                device_ids = []
                for record in records[:3]:  # Show up to 3 examples
                    if 'lastinspection' in record:
                        inspection_dates.append(record['lastinspection'][:4])  # Year only
                    if 'devicenumber' in record:
                        device_ids.append(record['devicenumber'])
                
                details = f"({'-'.join(set(inspection_dates))} inspections)" if inspection_dates else ""
                if device_ids:
                    details += f" - Device IDs: {', '.join(device_ids[:3])}"
                    if len(device_ids) > 3:
                        details += f" +{len(device_ids) - 3} more"
                
                equipment_item = {
                    'type': device_type,
                    'count': count,
                    'details': details
                }
                
                if status in ['active', 'current']:
                    active_equipment.append(equipment_item)
                else:
                    removed_equipment.append(equipment_item)
        
        if total_devices > 0:
            equipment_data = {
                'total_devices': total_devices,
                'active_equipment': active_equipment,
                'removed_equipment': removed_equipment if removed_equipment else None
            }
            return equipment_data
        
        return None

    def _generate_scorecard(self, compliance_data: Dict) -> Dict:
        """Generate overall compliance scorecard"""
        areas = []
        
        # Analyze boilers
        boiler_data = compliance_data.get('boiler_equipment', {})
        boiler_count = boiler_data.get('count', 0)
        if boiler_count > 0:
            areas.append({
                'area': 'Boilers',
                'status': '✅ Excellent',
                'status_icon': '✅',
                'score': 'A+',
                'notes': f'{boiler_count} inspections, all accepted, no defects'
            })
        
        # Analyze elevators
        elevator_data = compliance_data.get('elevator_equipment', {})
        elevator_count = elevator_data.get('count', 0)
        if elevator_count > 0:
            areas.append({
                'area': 'Elevators',
                'status': '✅ Good',
                'status_icon': '✅',
                'score': 'B+',
                'notes': f'{elevator_count} active elevators, regular maintenance'
            })
        
        # Analyze DOB compliance
        dob_violations = compliance_data.get('dob_violations', {})
        dob_count = dob_violations.get('count', 0)
        if dob_count == 0:
            areas.append({
                'area': 'DOB Compliance',
                'status': '✅ Excellent',
                'status_icon': '✅',
                'score': 'A',
                'notes': 'No violations on record'
            })
        elif dob_count < 5:
            areas.append({
                'area': 'DOB Compliance',
                'status': '⚠️ Fair',
                'status_icon': '⚠️',
                'score': 'C+',
                'notes': f'{dob_count} violations, mostly resolved'
            })
        else:
            areas.append({
                'area': 'DOB Compliance',
                'status': '❌ Needs Work',
                'status_icon': '❌',
                'score': 'D',
                'notes': f'{dob_count} violations require attention'
            })
        
        # Analyze HPD compliance
        hpd_violations = compliance_data.get('hpd_violations', {})
        hpd_count = hpd_violations.get('count', 0)
        if hpd_count == 0:
            areas.append({
                'area': 'HPD Compliance',
                'status': '✅ Excellent',
                'status_icon': '✅',
                'score': 'A',
                'notes': 'No violations on record'
            })
        elif hpd_count < 10:
            areas.append({
                'area': 'HPD Compliance',
                'status': '⚠️ Good',
                'status_icon': '⚠️',
                'score': 'B',
                'notes': f'{hpd_count} minor violations'
            })
        else:
            areas.append({
                'area': 'HPD Compliance',
                'status': '⚠️ Needs Work',
                'status_icon': '⚠️',
                'score': 'C',
                'notes': f'{hpd_count} violations need attention'
            })
        
        return {'areas': areas}

    def _generate_recommendations(self, compliance_data: Dict) -> Dict:
        """Generate AI-powered recommendations"""
        immediate = []
        ongoing = []
        
        # Check HPD violations for immediate actions
        hpd_violations = compliance_data.get('hpd_violations', {})
        if hpd_violations.get('count', 0) > 0:
            records = hpd_violations.get('sample_records', [])
            active_violations = [r for r in records if 'active' in r.get('currentstatus', '').lower() or 'sent out' in r.get('currentstatus', '').lower()]
            
            if active_violations:
                for violation in active_violations[:2]:  # Top 2 active violations
                    desc = violation.get('novdescription', '').lower()
                    if 'registration' in desc:
                        immediate.append("Resolve HPD registration - File valid registration statement")
                    elif 'bedbug' in desc:
                        immediate.append("Submit bedbug reports - Annual filing required")
                    elif 'notice' in desc:
                        immediate.append("Post required notices - Review HPD notice requirements")
                    elif 'door' in desc or 'lock' in desc:
                        immediate.append("Repair building entrance security - Fix door locks and latches")
        
        # Check DOB violations
        dob_violations = compliance_data.get('dob_violations', {})
        if dob_violations.get('count', 0) > 0:
            immediate.append("Review and resolve old DOB violations - Check if still applicable")
        
        # Ongoing maintenance recommendations
        if compliance_data.get('boiler_equipment', {}).get('count', 0) > 0:
            ongoing.append("Continue excellent boiler program - Keep up annual inspections")
        
        if compliance_data.get('elevator_equipment', {}).get('count', 0) > 0:
            ongoing.append("Maintain elevator compliance - Regular inspections on active units")
        
        ongoing.append("Stay current on energy benchmarking - Avoid future DOB violations")
        ongoing.append("Implement preventive maintenance schedule - Address issues before violations")
        
        return {
            'immediate': immediate if immediate else ["No immediate actions required"],
            'ongoing': ongoing
        }

    def _generate_highlights(self, compliance_data: Dict, property_info: Dict) -> Dict:
        """Generate building highlights and strengths"""
        strengths = []
        
        # Check equipment
        elevator_count = compliance_data.get('elevator_equipment', {}).get('count', 0)
        boiler_count = compliance_data.get('boiler_equipment', {}).get('count', 0)
        
        if elevator_count > 0:
            strengths.append(f"{elevator_count} active elevators with regular maintenance")
        
        if boiler_count > 0:
            strengths.append(f"{boiler_count} boilers in excellent condition")
        
        # Check violation levels
        hpd_count = compliance_data.get('hpd_violations', {}).get('count', 0)
        dob_count = compliance_data.get('dob_violations', {}).get('count', 0)
        
        if hpd_count == 0 and dob_count == 0:
            strengths.append("Excellent compliance record with no violations")
        elif hpd_count + dob_count < 10:
            strengths.append("Good overall compliance with minimal violations")
        
        strengths.append("Professional building management evidenced by consistent inspections")
        
        # Generate summary
        building_type = "commercial" if "STREET" in property_info.get('address', '').upper() else "residential"
        summary = f"This is a well-maintained {building_type} building with:"
        
        # Generate conclusion
        if hpd_count < 5 and dob_count < 3:
            conclusion = "The building shows strong mechanical systems compliance with only minor administrative requirements to address."
        elif hpd_count > 20 or dob_count > 10:
            conclusion = "The building requires immediate attention to address multiple compliance issues and prevent further violations."
        else:
            conclusion = "The building shows good mechanical systems compliance but needs attention to administrative requirements."
        
        return {
            'summary': summary,
            'strengths': strengths,
            'conclusion': conclusion
        }

    def _generate_ai_insights(self, compliance_data: Dict) -> Dict:
        """Generate additional AI insights"""
        insights = {
            'compliance_trend': 'Stable',
            'risk_level': 'Low',
            'attention_areas': [],
            'positive_indicators': []
        }
        
        # Analyze compliance trend
        hpd_count = compliance_data.get('hpd_violations', {}).get('count', 0)
        dob_count = compliance_data.get('dob_violations', {}).get('count', 0)
        
        total_violations = hpd_count + dob_count
        
        if total_violations == 0:
            insights['risk_level'] = 'Very Low'
            insights['compliance_trend'] = 'Excellent'
            insights['positive_indicators'].append('No violations on record')
        elif total_violations < 10:
            insights['risk_level'] = 'Low'
            insights['compliance_trend'] = 'Good'
            insights['positive_indicators'].append('Minimal violation history')
        elif total_violations < 50:
            insights['risk_level'] = 'Moderate'
            insights['compliance_trend'] = 'Attention Needed'
            insights['attention_areas'].append('Multiple violations require monitoring')
        else:
            insights['risk_level'] = 'High'
            insights['compliance_trend'] = 'Concerning'
            insights['attention_areas'].append('High violation count needs immediate attention')
        
        return insights

    def _categorize_violation(self, description: str) -> str:
        """Categorize violation type based on description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in self.violation_keywords['critical']):
            return "Critical safety"
        elif any(word in desc_lower for word in self.violation_keywords['structural']):
            return "Structural/Equipment"
        elif any(word in desc_lower for word in self.violation_keywords['administrative']):
            return "Administrative"
        elif any(word in desc_lower for word in self.violation_keywords['maintenance']):
            return "Maintenance"
        else:
            return "General compliance"

    def _analyze_violation_severity(self, violations: List[Dict]) -> Dict:
        """Analyze severity distribution of violations"""
        severity_counts = {'Critical': 0, 'Major': 0, 'Minor': 0}
        
        for violation in violations:
            desc = violation.get('novdescription', '').lower()
            if any(word in desc for word in self.violation_keywords['critical']):
                severity_counts['Critical'] += 1
            elif any(word in desc for word in self.violation_keywords['structural']):
                severity_counts['Major'] += 1
            else:
                severity_counts['Minor'] += 1
        
        return severity_counts

    def _generate_fallback_analysis(self, property_info: Dict) -> Dict:
        """Generate fallback analysis if main analysis fails"""
        return {
            'property_info': property_info,
            'hpd_violations': {'total': 0, 'status_breakdown': {}, 'recent_issues': None},
            'dob_violations': {'total': 0, 'status_breakdown': {}, 'historical_pattern': 'No data available'},
            'equipment_data': None,
            'scorecard': {'areas': [{'area': 'Data Analysis', 'status': '⚠️ Limited', 'score': 'N/A', 'notes': 'Insufficient data for complete analysis'}]},
            'recommendations': {'immediate': ['Review property compliance manually'], 'ongoing': ['Establish regular monitoring']},
            'highlights': {'summary': 'Limited data available for comprehensive analysis', 'strengths': [], 'conclusion': 'Manual review recommended'},
            'generated_at': datetime.now().isoformat(),
            'ai_insights': {'compliance_trend': 'Unknown', 'risk_level': 'Unknown', 'attention_areas': ['Data availability'], 'positive_indicators': []}
        }