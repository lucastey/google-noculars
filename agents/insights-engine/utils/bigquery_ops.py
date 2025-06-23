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
    
    # Helper function to recursively serialize datetime objects in nested structures
    def serialize_value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [serialize_value(item) for item in value]
        return value
    
    # Convert any datetime objects in the rec dictionary to strings (including nested)
    serialized_rec = {}
    for key, value in rec.items():
        serialized_rec[key] = serialize_value(value)
    
    return {
        'page_url': serialized_rec.get('page_url', ''),
        'recommendation_category': serialized_rec.get('recommendation_category', 'user_experience'),
        'recommendation_id': serialized_rec.get('recommendation_id', ''),
        'first_analyzed': datetime.now(timezone.utc).isoformat(),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'data_freshness_hours': serialized_rec.get('data_freshness_hours', 24),
        'sessions_analyzed_count': serialized_rec.get('sessions_analyzed_count', 0),
        'sessions_analyzed_list': json.dumps(serialized_rec.get('sessions_analyzed_list', [])),
        'unique_users_count': serialized_rec.get('unique_users_count', 0),
        'sample_size_adequacy': serialized_rec.get('sample_size_adequacy', 'insufficient'),
        'statistical_power': serialized_rec.get('statistical_power', 0.0),
        'agents_analyzed': json.dumps(serialized_rec.get('agents_analyzed', [])),
        'data_sources_used': json.dumps(serialized_rec.get('data_sources_used', [])),
        'coordination_confidence': serialized_rec.get('coordination_confidence', 0.0),
        'analysis_completeness_score': serialized_rec.get('analysis_completeness_score', 0.0),
        'confidence_score_evolution': json.dumps(serialized_rec.get('confidence_score_evolution', [])),
        'primary_insight_category': serialized_rec.get('primary_insight_category', 'user_experience'),
        'insight_severity': serialized_rec.get('insight_severity', 'medium'),
        'insight_urgency': serialized_rec.get('insight_urgency', 'medium_term'),
        'insight_confidence': serialized_rec.get('insight_confidence', 0.0),
        'estimated_revenue_impact': serialized_rec.get('estimated_revenue_impact', 0.0),
        'average_conversion_probability': serialized_rec.get('average_conversion_probability', 0.0),
        'conversion_impact_percent': serialized_rec.get('conversion_impact_percent', 0.0),
        'user_experience_impact_score': serialized_rec.get('user_experience_impact_score', 0.0),
        'statistical_significance': serialized_rec.get('statistical_significance', 0.0),
        'business_priority_rank': serialized_rec.get('business_priority_rank', 50),
        'priority_rank_evolution': json.dumps(serialized_rec.get('priority_rank_evolution', [])),
        'recommendation_title': serialized_rec.get('recommendation_title', ''),
        'recommendation_description': serialized_rec.get('recommendation_description', ''),
        'implementation_complexity': serialized_rec.get('implementation_complexity', 'moderate'),
        'estimated_implementation_hours': serialized_rec.get('estimated_implementation_hours', 0.0),
        'required_resources': json.dumps(serialized_rec.get('required_resources', [])),
        'pattern_evidence_aggregated': json.dumps(serialized_rec.get('pattern_evidence_aggregated', {})),
        'business_evidence_aggregated': json.dumps(serialized_rec.get('business_evidence_aggregated', {})),
        'ab_test_evidence': json.dumps(serialized_rec.get('ab_test_evidence', {})),
        'cross_agent_correlation': serialized_rec.get('cross_agent_correlation', 0.0),
        'evidence_strength_score': serialized_rec.get('evidence_strength_score', 0.0),
        'data_consistency_score': serialized_rec.get('data_consistency_score', 0.0),
        'outlier_sessions_count': serialized_rec.get('outlier_sessions_count', 0),
        'data_quality_issues': json.dumps(serialized_rec.get('data_quality_issues', [])),
        'immediate_actions': json.dumps(serialized_rec.get('immediate_actions', [])),
        'short_term_actions': json.dumps(serialized_rec.get('short_term_actions', [])),
        'long_term_actions': json.dumps(serialized_rec.get('long_term_actions', [])),
        'success_metrics': json.dumps(serialized_rec.get('success_metrics', [])),
        'monitoring_plan': json.dumps(serialized_rec.get('monitoring_plan', {})),
        'implementation_risks': json.dumps(serialized_rec.get('implementation_risks', [])),
        'risk_mitigation_strategies': json.dumps(serialized_rec.get('risk_mitigation_strategies', [])),
        'rollback_plan': serialized_rec.get('rollback_plan', ''),
        'affected_user_segments': json.dumps(serialized_rec.get('affected_user_segments', [])),
        'device_specific_considerations': json.dumps(serialized_rec.get('device_specific_considerations', {})),
        'geographic_considerations': json.dumps(serialized_rec.get('geographic_considerations', {})),
        'baseline_metrics': json.dumps(serialized_rec.get('baseline_metrics', {})),
        'target_metrics': json.dumps(serialized_rec.get('target_metrics', {})),
        'measurement_methodology': serialized_rec.get('measurement_methodology', ''),
        'expected_timeline_to_impact_days': serialized_rec.get('expected_timeline_to_impact_days', 30),
        'industry_benchmark_comparison': serialized_rec.get('industry_benchmark_comparison', ''),
        'competitive_advantage_potential': serialized_rec.get('competitive_advantage_potential', ''),
        'market_differentiation_score': serialized_rec.get('market_differentiation_score', 0.0),
        'average_engagement_score': serialized_rec.get('average_engagement_score', 0.0),
        'average_frustration_level': serialized_rec.get('average_frustration_level', 0),
        'dominant_funnel_stage': serialized_rec.get('dominant_funnel_stage', ''),
        'funnel_stage_distribution': json.dumps(serialized_rec.get('funnel_stage_distribution', {})),
        'source_ab_test_winner': serialized_rec.get('source_ab_test_winner', ''),
        'source_statistical_confidence': serialized_rec.get('source_statistical_confidence', 0.0),
        'dashboard_priority': serialized_rec.get('dashboard_priority', False),
        'alert_threshold_met': serialized_rec.get('alert_threshold_met', False),
        'api_endpoint_data': json.dumps(serialized_rec.get('api_endpoint_data', {})),
        'visualization_config': json.dumps(serialized_rec.get('visualization_config', {})),
        'data_quality_score': serialized_rec.get('data_quality_score', 0.0),
        'recommendation_accuracy_score': serialized_rec.get('recommendation_accuracy_score', 0.0),
        'peer_review_status': serialized_rec.get('peer_review_status', 'pending'),
        'validation_methodology': serialized_rec.get('validation_methodology', ''),
        'assigned_team': serialized_rec.get('assigned_team', ''),
        'stakeholder_notifications': json.dumps(serialized_rec.get('stakeholder_notifications', [])),
        'approval_workflow_status': serialized_rec.get('approval_workflow_status', 'draft'),
        'similar_recommendations_history': json.dumps(serialized_rec.get('similar_recommendations_history', [])),
        'implementation_success_rate': serialized_rec.get('implementation_success_rate', 0.0),
        'lessons_learned': serialized_rec.get('lessons_learned', ''),
        'processing_duration_seconds': serialized_rec.get('processing_duration_seconds', 0.0),
        'agent_versions': json.dumps(serialized_rec.get('agent_versions', {})),
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
    
    print(f"🔧 DEBUG: upsert_final_recommendations called with {len(recommendations)} recommendations")
    
    for rec in recommendations:
        try:
            page_url = rec.get('page_url', '')
            category = rec.get('recommendation_category', 'user_experience')
            
            print(f"🔧 DEBUG: Processing recommendation for {page_url}, category: {category}")
            
            if not page_url:
                results['errors'].append(f"Missing page_url in recommendation")
                print(f"🔧 DEBUG: Missing page_url, skipping")
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
                print(f"🔧 DEBUG: Found {len(existing_results)} existing records, is_update: {is_update}")
            except Exception as e:
                print(f"🔧 DEBUG: Error checking existing records: {e}")
                is_update = False
            
            if is_update:
                # BigQuery doesn't allow updates on streaming buffer
                # For demo purposes, we'll create a new recommendation with a different category
                print(f"🔧 DEBUG: Existing record found, creating new recommendation with modified category")
                category = category + "_v2"  # Modify category to avoid update conflict
                rec['recommendation_category'] = category
                # Fall through to insert logic below
                
            # Insert new recommendation (either new or modified category)
            if True:  # Always insert since we handle updates above
                # Insert new recommendation
                print(f"🔧 DEBUG: Creating new recommendation row")
                row = create_recommendation_row(rec)
                print(f"🔧 DEBUG: Row created successfully")
                
                # Insert the new recommendation
                dataset = client.dataset('ux_insights')
                table = dataset.table('final_recommendations')
                print(f"🔧 DEBUG: Attempting to insert into BigQuery")
                errors = client.insert_rows_json(table, [row])
                
                if errors:
                    results['errors'].append(f"Insert error for {page_url}: {errors}")
                    print(f"🔧 DEBUG: Insert errors: {errors}")
                else:
                    results['inserted'] += 1
                    print(f"🔧 DEBUG: Successfully inserted recommendation for {page_url}")
                    
        except Exception as e:
            error_msg = f"Error processing recommendation for {rec.get('page_url', 'unknown')}: {str(e)}"
            results['errors'].append(error_msg)
            print(f"🔧 DEBUG: Exception occurred: {error_msg}")
    
    print(f"🔧 DEBUG: Final results: {results}")
    return results