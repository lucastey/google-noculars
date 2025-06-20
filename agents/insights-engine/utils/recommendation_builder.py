#!/usr/bin/env python3
"""
Recommendation Builder Utilities for Insights Engine
Handles creation of page-centric recommendations from aggregated data
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timezone

from .statistical import (
    calculate_statistical_power, calculate_cross_agent_correlation,
    calculate_data_consistency_score, identify_outlier_sessions,
    calculate_evidence_strength_score, calculate_data_quality_score,
    calculate_business_priority_rank, calculate_sample_size_adequacy
)
from .data_processing import generate_recommendation_id


def build_recommendation_details(category: str, aggregated_data: Dict) -> Dict[str, str]:
    """Build recommendation title, description, and complexity based on category"""
    page_url = aggregated_data['page_url']
    session_count = aggregated_data['session_count']
    avg_engagement = aggregated_data.get('average_engagement_score', 0)
    avg_frustration = aggregated_data.get('average_frustration_level', 0)
    avg_conversion = aggregated_data.get('average_conversion_probability', 0)
    
    if category == 'ui_design':
        return {
            'title': f"Improve UI Design for {page_url}",
            'description': f"Based on {session_count} sessions, users show frustration indicators ({avg_frustration:.1f}) and low engagement ({avg_engagement:.1f}). UI improvements needed.",
            'complexity': 'complex' if avg_frustration >= 4 else 'moderate'
        }
    elif category == 'performance':
        return {
            'title': f"Optimize Performance for {page_url}",
            'description': f"High frustration levels ({avg_frustration:.1f}) across {session_count} sessions indicate performance bottlenecks.",
            'complexity': 'complex'
        }
    elif category == 'conversion_optimization':
        return {
            'title': f"Optimize Conversion Funnel for {page_url}",
            'description': f"Low conversion probability ({avg_conversion:.2f}) across {session_count} sessions. Funnel optimization needed.",
            'complexity': 'moderate'
        }
    elif category == 'content':
        return {
            'title': f"Improve Content Strategy for {page_url}",
            'description': f"Low engagement ({avg_engagement:.1f}) across {session_count} sessions suggests content improvements needed.",
            'complexity': 'moderate'
        }
    else:  # user_experience
        return {
            'title': f"Enhance User Experience for {page_url}",
            'description': f"General UX improvements recommended based on analysis of {session_count} user sessions.",
            'complexity': 'moderate'
        }


def determine_severity(avg_frustration: float, avg_engagement: float, total_revenue_impact: float) -> str:
    """Determine insight severity based on aggregated metrics"""
    if avg_frustration >= 4 or avg_engagement < 20 or total_revenue_impact >= 5000:
        return 'critical'
    elif avg_frustration >= 3 or avg_engagement < 30 or total_revenue_impact >= 1000:
        return 'high'
    elif avg_frustration >= 2 or avg_engagement < 50 or total_revenue_impact >= 100:
        return 'medium'
    else:
        return 'low'


def calculate_confidence_score(session_count: int, evidence_strength: float) -> float:
    """Calculate confidence score based on session count and evidence strength"""
    if session_count >= 100:
        base_confidence = 0.95
    elif session_count >= 30:
        base_confidence = 0.85
    elif session_count >= 10:
        base_confidence = 0.70
    else:
        base_confidence = 0.50
    
    # Adjust confidence based on evidence strength
    confidence = min(0.98, base_confidence * (0.7 + 0.3 * evidence_strength))
    return confidence


def build_confidence_evolution(existing_rec: Dict, new_confidence: float, session_count: int) -> List[Dict]:
    """Build confidence evolution tracking"""
    confidence_evolution = [{
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'confidence': new_confidence,
        'sample_size': session_count
    }]
    
    if existing_rec:
        try:
            existing_evolution = json.loads(existing_rec.get('confidence_score_evolution', '[]'))
            confidence_evolution = existing_evolution + confidence_evolution
        except:
            pass  # Use new confidence evolution if parsing fails
    
    return confidence_evolution


def get_required_resources(category: str) -> List[str]:
    """Get required resources based on recommendation category"""
    if category in ['ui_design', 'user_experience']:
        return ['UX Designer', 'Frontend Developer']
    elif category == 'performance':
        return ['Performance Engineer', 'Frontend Developer']
    elif category == 'conversion_optimization':
        return ['Marketing Analyst', 'UX Designer']
    else:  # content
        return ['Content Strategist', 'UX Writer']


def create_page_recommendation(
    aggregated_data: Dict,
    category: str,
    existing_rec: Dict = None,
    ab_data: List[Dict] = None
) -> Dict[str, Any]:
    """Create a page-centric recommendation from aggregated multi-agent data"""
    
    start_time = datetime.now(timezone.utc)
    
    page_url = aggregated_data['page_url']
    session_count = aggregated_data['session_count']
    pattern_sessions = aggregated_data.get('pattern_sessions', [])
    business_sessions = aggregated_data.get('business_sessions', [])
    
    # Get aggregated metrics
    avg_engagement = aggregated_data.get('average_engagement_score', 0)
    avg_frustration = aggregated_data.get('average_frustration_level', 0)
    avg_conversion = aggregated_data.get('average_conversion_probability', 0)
    total_revenue_impact = aggregated_data.get('total_revenue_impact', 0)
    dominant_funnel_stage = aggregated_data.get('dominant_funnel_stage', 'entry')
    
    # Calculate dynamic quality metrics
    cross_agent_correlation = calculate_cross_agent_correlation(pattern_sessions, business_sessions)
    
    # Calculate data consistency across key metrics
    all_sessions = pattern_sessions + business_sessions
    consistency_metrics = ['engagement_score', 'frustration_indicators', 'conversion_probability']
    data_consistency = calculate_data_consistency_score(all_sessions, consistency_metrics)
    
    # Identify outlier sessions
    outlier_count = identify_outlier_sessions(all_sessions.copy(), consistency_metrics)
    
    # Calculate statistical power
    statistical_power = calculate_statistical_power(session_count)
    
    # Calculate evidence strength
    evidence_strength = calculate_evidence_strength_score(
        session_count, cross_agent_correlation, data_consistency, statistical_power
    )
    
    # Calculate data quality score
    missing_data_ratio = max(0, 1 - (len(all_sessions) / max(1, session_count)))
    data_quality = calculate_data_quality_score(
        session_count, data_consistency, outlier_count, missing_data_ratio
    )
    
    # Calculate confidence
    confidence = calculate_confidence_score(session_count, evidence_strength)
    
    # Build recommendation details
    rec_details = build_recommendation_details(category, aggregated_data)
    
    # Calculate priority rank
    priority_rank = calculate_business_priority_rank(
        revenue_impact=total_revenue_impact,
        conversion_impact=avg_conversion * 100,
        ux_impact=avg_engagement,
        implementation_complexity=rec_details['complexity'],
        statistical_confidence=confidence
    )
    
    # Determine severity
    severity = determine_severity(avg_frustration, avg_engagement, total_revenue_impact)
    
    # Build confidence evolution
    confidence_evolution = build_confidence_evolution(existing_rec, confidence, session_count)
    
    # Build page-centric recommendation object
    recommendation = {
        'page_url': page_url,
        'recommendation_category': category,
        'recommendation_id': generate_recommendation_id(page_url, category),
        'coordination_confidence': confidence,
        'analysis_completeness_score': 0.9,
        'confidence_score_evolution': confidence_evolution,
        'primary_insight_category': category,
        'insight_severity': severity,
        'insight_urgency': 'immediate' if severity == 'critical' else 'short_term' if priority_rank <= 20 else 'medium_term',
        'insight_confidence': confidence,
        'estimated_revenue_impact': total_revenue_impact,
        'average_conversion_probability': avg_conversion,
        'conversion_impact_percent': max(0, (0.5 - avg_conversion) * 100),
        'user_experience_impact_score': max(0, 100 - avg_engagement),
        'statistical_significance': 0.0,
        'business_priority_rank': priority_rank,
        'priority_rank_evolution': [{'timestamp': datetime.now(timezone.utc).isoformat(), 'rank': priority_rank}],
        'recommendation_title': rec_details['title'],
        'recommendation_description': rec_details['description'],
        'implementation_complexity': rec_details['complexity'],
        'estimated_implementation_hours': {'simple': 8, 'moderate': 24, 'complex': 80, 'major': 200}[rec_details['complexity']],
        'required_resources': get_required_resources(category),
        'pattern_evidence_aggregated': {
            'average_engagement_score': avg_engagement,
            'average_frustration_level': avg_frustration,
            'session_count': session_count,
            'sample_adequacy': calculate_sample_size_adequacy(session_count)
        },
        'business_evidence_aggregated': {
            'average_conversion_probability': avg_conversion,
            'total_revenue_impact': total_revenue_impact,
            'dominant_funnel_stage': dominant_funnel_stage,
            'funnel_stage_distribution': aggregated_data.get('funnel_stage_distribution', {})
        },
        'ab_test_evidence': {
            'test_data': ab_data if ab_data else [],
            'relevant_tests': [test for test in (ab_data or []) if test.get('page_url') == page_url],
            'test_coverage': len([test for test in (ab_data or []) if test.get('page_url') == page_url]) > 0
        },
        'cross_agent_correlation': cross_agent_correlation,
        'evidence_strength_score': evidence_strength,
        'data_consistency_score': data_consistency,
        'outlier_sessions_count': outlier_count,
        'data_quality_issues': [],
        'immediate_actions': [
            'Analyze current page performance',
            f'Review user flows for {page_url}',
            'Identify specific friction points'
        ],
        'short_term_actions': [
            'Implement targeted improvements',
            'Set up A/B tests for changes',
            'Monitor key metrics'
        ],
        'long_term_actions': [
            'Continuous optimization based on user feedback',
            'Regular performance reviews',
            'Iterate based on results'
        ],
        'success_metrics': [
            'Engagement score improvement',
            'Frustration level reduction',
            'Conversion rate increase',
            'User satisfaction scores'
        ],
        'monitoring_plan': {
            'frequency': 'weekly',
            'metrics': ['engagement', 'conversion', 'satisfaction', 'performance'],
            'alerts': [f'frustration_level > {avg_frustration + 1}', f'engagement_score < {avg_engagement - 10}']
        },
        'implementation_risks': [
            'User experience disruption during implementation',
            'Technical complexity',
            'Resource availability'
        ],
        'risk_mitigation_strategies': [
            'Gradual rollout to minimize disruption',
            'User testing before full implementation',
            'Rollback plan preparation'
        ],
        'rollback_plan': 'Revert to previous version if key metrics decline by >10%',
        'affected_user_segments': ['all_users'],
        'baseline_metrics': {
            'engagement_score': avg_engagement,
            'conversion_probability': avg_conversion,
            'frustration_level': avg_frustration
        },
        'target_metrics': {
            'engagement_score': min(100, avg_engagement + 20),
            'conversion_probability': min(1.0, avg_conversion + 0.2),
            'frustration_level': max(0, avg_frustration - 1)
        },
        'measurement_methodology': 'Compare pre/post implementation metrics over 4-week periods',
        'expected_timeline_to_impact_days': 14 if rec_details['complexity'] == 'simple' else 30 if rec_details['complexity'] == 'moderate' else 60,
        'average_engagement_score': avg_engagement,
        'average_frustration_level': avg_frustration,
        'dominant_funnel_stage': dominant_funnel_stage,
        'funnel_stage_distribution': aggregated_data.get('funnel_stage_distribution', {}),
        'dashboard_priority': priority_rank <= 10 or severity in ['critical', 'high'],
        'alert_threshold_met': avg_frustration >= 4 or avg_engagement < 25 or severity == 'critical',
        'data_quality_score': data_quality,
        'recommendation_accuracy_score': evidence_strength,
        'peer_review_status': 'pending',
        'validation_methodology': f'Statistical analysis of {session_count} user sessions with {confidence:.0%} confidence',
        'processing_duration_seconds': (datetime.now(timezone.utc) - start_time).total_seconds()
    }
    
    return recommendation