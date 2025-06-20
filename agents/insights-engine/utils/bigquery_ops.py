#!/usr/bin/env python3
"""
BigQuery Operations Utilities for Insights Engine
Handles database upsert operations and field mapping
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timezone

from .data_retrieval import get_bigquery_client
from .data_processing import generate_recommendation_id


def create_recommendation_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Create a BigQuery row from recommendation data with proper field mapping"""
    return {
        'page_url': rec.get('page_url', ''),
        'recommendation_category': rec.get('recommendation_category', 'user_experience'),
        'recommendation_id': rec.get('recommendation_id', ''),
        'first_analyzed': datetime.now(timezone.utc).isoformat(),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'data_freshness_hours': rec.get('data_freshness_hours', 24),
        'sessions_analyzed_count': rec.get('sessions_analyzed_count', 0),
        'sessions_analyzed_list': json.dumps(rec.get('sessions_analyzed_list', [])),
        'unique_users_count': rec.get('unique_users_count', 0),
        'sample_size_adequacy': rec.get('sample_size_adequacy', 'insufficient'),
        'statistical_power': rec.get('statistical_power', 0.0),
        'agents_analyzed': json.dumps(rec.get('agents_analyzed', [])),
        'data_sources_used': json.dumps(rec.get('data_sources_used', [])),
        'coordination_confidence': rec.get('coordination_confidence', 0.0),
        'analysis_completeness_score': rec.get('analysis_completeness_score', 0.0),
        'confidence_score_evolution': json.dumps(rec.get('confidence_score_evolution', [])),
        'primary_insight_category': rec.get('primary_insight_category', 'user_experience'),
        'insight_severity': rec.get('insight_severity', 'medium'),
        'insight_urgency': rec.get('insight_urgency', 'medium_term'),
        'insight_confidence': rec.get('insight_confidence', 0.0),
        'estimated_revenue_impact': rec.get('estimated_revenue_impact', 0.0),
        'average_conversion_probability': rec.get('average_conversion_probability', 0.0),
        'conversion_impact_percent': rec.get('conversion_impact_percent', 0.0),
        'user_experience_impact_score': rec.get('user_experience_impact_score', 0.0),
        'statistical_significance': rec.get('statistical_significance', 0.0),
        'business_priority_rank': rec.get('business_priority_rank', 50),
        'priority_rank_evolution': json.dumps(rec.get('priority_rank_evolution', [])),
        'recommendation_title': rec.get('recommendation_title', ''),
        'recommendation_description': rec.get('recommendation_description', ''),
        'implementation_complexity': rec.get('implementation_complexity', 'moderate'),
        'estimated_implementation_hours': rec.get('estimated_implementation_hours', 0.0),
        'required_resources': json.dumps(rec.get('required_resources', [])),
        'pattern_evidence_aggregated': json.dumps(rec.get('pattern_evidence_aggregated', {})),
        'business_evidence_aggregated': json.dumps(rec.get('business_evidence_aggregated', {})),
        'ab_test_evidence': json.dumps(rec.get('ab_test_evidence', {})),
        'cross_agent_correlation': rec.get('cross_agent_correlation', 0.0),
        'evidence_strength_score': rec.get('evidence_strength_score', 0.0),
        'data_consistency_score': rec.get('data_consistency_score', 0.0),
        'outlier_sessions_count': rec.get('outlier_sessions_count', 0),
        'data_quality_issues': json.dumps(rec.get('data_quality_issues', [])),
        'immediate_actions': json.dumps(rec.get('immediate_actions', [])),
        'short_term_actions': json.dumps(rec.get('short_term_actions', [])),
        'long_term_actions': json.dumps(rec.get('long_term_actions', [])),
        'success_metrics': json.dumps(rec.get('success_metrics', [])),
        'monitoring_plan': json.dumps(rec.get('monitoring_plan', {})),
        'implementation_risks': json.dumps(rec.get('implementation_risks', [])),
        'risk_mitigation_strategies': json.dumps(rec.get('risk_mitigation_strategies', [])),
        'rollback_plan': rec.get('rollback_plan', ''),
        'affected_user_segments': json.dumps(rec.get('affected_user_segments', [])),
        'device_specific_considerations': json.dumps(rec.get('device_specific_considerations', {})),
        'geographic_considerations': json.dumps(rec.get('geographic_considerations', {})),
        'baseline_metrics': json.dumps(rec.get('baseline_metrics', {})),
        'target_metrics': json.dumps(rec.get('target_metrics', {})),
        'measurement_methodology': rec.get('measurement_methodology', ''),
        'expected_timeline_to_impact_days': rec.get('expected_timeline_to_impact_days', 30),
        'industry_benchmark_comparison': rec.get('industry_benchmark_comparison', ''),
        'competitive_advantage_potential': rec.get('competitive_advantage_potential', ''),
        'market_differentiation_score': rec.get('market_differentiation_score', 0.0),
        'average_engagement_score': rec.get('average_engagement_score', 0.0),
        'average_frustration_level': rec.get('average_frustration_level', 0),
        'dominant_funnel_stage': rec.get('dominant_funnel_stage', ''),
        'funnel_stage_distribution': json.dumps(rec.get('funnel_stage_distribution', {})),
        'source_ab_test_winner': rec.get('source_ab_test_winner', ''),
        'source_statistical_confidence': rec.get('source_statistical_confidence', 0.0),
        'dashboard_priority': rec.get('dashboard_priority', False),
        'alert_threshold_met': rec.get('alert_threshold_met', False),
        'api_endpoint_data': json.dumps(rec.get('api_endpoint_data', {})),
        'visualization_config': json.dumps(rec.get('visualization_config', {})),
        'data_quality_score': rec.get('data_quality_score', 0.0),
        'recommendation_accuracy_score': rec.get('recommendation_accuracy_score', 0.0),
        'peer_review_status': rec.get('peer_review_status', 'pending'),
        'validation_methodology': rec.get('validation_methodology', ''),
        'assigned_team': rec.get('assigned_team', ''),
        'stakeholder_notifications': json.dumps(rec.get('stakeholder_notifications', [])),
        'approval_workflow_status': rec.get('approval_workflow_status', 'draft'),
        'similar_recommendations_history': json.dumps(rec.get('similar_recommendations_history', [])),
        'implementation_success_rate': rec.get('implementation_success_rate', 0.0),
        'lessons_learned': rec.get('lessons_learned', ''),
        'processing_duration_seconds': rec.get('processing_duration_seconds', 0.0),
        'agent_versions': json.dumps(rec.get('agent_versions', {})),
        'created_at': datetime.now(timezone.utc).isoformat()
    }


def build_update_query(rec: Dict[str, Any], page_url: str, category: str, all_sessions: List[str], total_session_count: int) -> str:
    """Build SQL update query for existing recommendations"""
    return f"""
    UPDATE `ux_insights.final_recommendations`
    SET 
        last_updated = CURRENT_TIMESTAMP(),
        sessions_analyzed_count = {total_session_count},
        sessions_analyzed_list = '{json.dumps(all_sessions)}',
        average_engagement_score = {rec.get('average_engagement_score', 0)},
        average_frustration_level = {rec.get('average_frustration_level', 0)},
        average_conversion_probability = {rec.get('average_conversion_probability', 0)},
        estimated_revenue_impact = {rec.get('estimated_revenue_impact', 0)},
        business_priority_rank = {rec.get('business_priority_rank', 50)},
        insight_confidence = {rec.get('insight_confidence', 0)},
        statistical_power = {rec.get('statistical_power', 0)},
        sample_size_adequacy = '{rec.get('sample_size_adequacy', 'insufficient')}',
        pattern_evidence_aggregated = '{json.dumps(rec.get('pattern_evidence_aggregated', {}))}',
        business_evidence_aggregated = '{json.dumps(rec.get('business_evidence_aggregated', {}))}',
        data_freshness_hours = {rec.get('data_freshness_hours', 24)},
        cross_agent_correlation = {rec.get('cross_agent_correlation', 0.0)},
        evidence_strength_score = {rec.get('evidence_strength_score', 0.0)},
        data_consistency_score = {rec.get('data_consistency_score', 0.0)},
        outlier_sessions_count = {rec.get('outlier_sessions_count', 0)},
        data_quality_score = {rec.get('data_quality_score', 0.0)},
        processing_duration_seconds = {rec.get('processing_duration_seconds', 0.0)}
    WHERE page_url = '{page_url}' AND recommendation_category = '{category}'
    """


def upsert_final_recommendations(recommendations: List[Dict[str, Any]]):
    """Function tool: Upsert (insert or update) page-centric recommendations in BigQuery"""
    client = get_bigquery_client()
    
    results = {'inserted': 0, 'updated': 0, 'errors': []}
    
    for rec in recommendations:
        try:
            page_url = rec.get('page_url', '')
            category = rec.get('recommendation_category', 'user_experience')
            
            if not page_url:
                results['errors'].append(f"Missing page_url in recommendation")
                continue
            
            # Check if recommendation already exists
            existing_query = f"""
            SELECT recommendation_id, sessions_analyzed_count, sessions_analyzed_list, last_updated
            FROM `ux_insights.final_recommendations`
            WHERE page_url = '{page_url}' AND recommendation_category = '{category}'
            LIMIT 1
            """
            
            try:
                existing_results = list(client.query(existing_query).result())
                is_update = len(existing_results) > 0
            except:
                is_update = False
            
            if is_update:
                # Update existing recommendation
                existing = dict(existing_results[0])
                existing_sessions = json.loads(existing.get('sessions_analyzed_list', '[]'))
                new_sessions = rec.get('sessions_analyzed_list', [])
                
                # Merge session lists
                all_sessions = list(set(existing_sessions + new_sessions))
                total_session_count = len(all_sessions)
                
                update_query = build_update_query(rec, page_url, category, all_sessions, total_session_count)
                client.query(update_query).result()
                results['updated'] += 1
                
            else:
                # Insert new recommendation
                row = create_recommendation_row(rec)
                
                # Insert the new recommendation
                dataset = client.dataset('ux_insights')
                table = dataset.table('final_recommendations')
                errors = client.insert_rows_json(table, [row])
                
                if errors:
                    results['errors'].append(f"Insert error for {page_url}: {errors}")
                else:
                    results['inserted'] += 1
                    
        except Exception as e:
            results['errors'].append(f"Error processing recommendation for {rec.get('page_url', 'unknown')}: {str(e)}")
    
    return results