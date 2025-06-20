#!/usr/bin/env python3
"""
Data Processing Utilities for Insights Engine
Handles session aggregation and page-centric data processing
"""

from typing import Dict, Any, List
import hashlib


def generate_recommendation_id(page_url: str, category: str):
    """Generate page-centric recommendation ID based on page URL and category"""
    # Create a consistent hash from page_url + category
    content = f"{page_url}_{category}"
    hash_value = hashlib.md5(content.encode()).hexdigest()[:12]
    return f"rec_{hash_value}"


def aggregate_sessions_by_page(pattern_data: List[Dict], business_data: List[Dict]) -> Dict[str, Dict]:
    """Aggregate session data by page URL for page-centric analysis"""
    page_aggregations = {}
    
    # Process pattern data
    for pattern in pattern_data:
        page_url = pattern.get('page_url', '')
        if not page_url:
            continue
            
        if page_url not in page_aggregations:
            page_aggregations[page_url] = {
                'page_url': page_url,
                'sessions': [],
                'pattern_sessions': [],
                'business_sessions': [],
                'unique_session_ids': set()
            }
        
        session_id = pattern.get('session_id', '')
        if session_id:
            page_aggregations[page_url]['unique_session_ids'].add(session_id)
            page_aggregations[page_url]['pattern_sessions'].append(pattern)
    
    # Process business data
    for business in business_data:
        page_url = business.get('page_url', '')
        if not page_url:
            continue
            
        if page_url not in page_aggregations:
            page_aggregations[page_url] = {
                'page_url': page_url,
                'sessions': [],
                'pattern_sessions': [],
                'business_sessions': [],
                'unique_session_ids': set()
            }
        
        session_id = business.get('session_id', '')
        if session_id:
            page_aggregations[page_url]['unique_session_ids'].add(session_id)
            page_aggregations[page_url]['business_sessions'].append(business)
    
    # Calculate aggregated metrics for each page
    for page_url, data in page_aggregations.items():
        data['session_count'] = len(data['unique_session_ids'])
        data['sessions_analyzed_list'] = list(data['unique_session_ids'])
        
        # Aggregate pattern metrics
        if data['pattern_sessions']:
            engagement_scores = [s.get('engagement_score', 0) for s in data['pattern_sessions']]
            frustration_levels = [s.get('frustration_indicators', 0) for s in data['pattern_sessions']]
            
            data['average_engagement_score'] = sum(engagement_scores) / len(engagement_scores)
            data['average_frustration_level'] = sum(frustration_levels) / len(frustration_levels)
            data['max_frustration_level'] = max(frustration_levels)
        else:
            data['average_engagement_score'] = 0
            data['average_frustration_level'] = 0
            data['max_frustration_level'] = 0
        
        # Aggregate business metrics
        if data['business_sessions']:
            conversion_probs = [s.get('conversion_probability', 0) for s in data['business_sessions']]
            revenue_impacts = [s.get('estimated_revenue_impact', 0) for s in data['business_sessions']]
            funnel_stages = [s.get('funnel_stage', 'entry') for s in data['business_sessions']]
            
            data['average_conversion_probability'] = sum(conversion_probs) / len(conversion_probs)
            data['total_revenue_impact'] = sum(revenue_impacts)
            data['dominant_funnel_stage'] = max(set(funnel_stages), key=funnel_stages.count)
            
            # Calculate funnel stage distribution
            stage_counts = {}
            for stage in funnel_stages:
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
            data['funnel_stage_distribution'] = stage_counts
        else:
            data['average_conversion_probability'] = 0
            data['total_revenue_impact'] = 0
            data['dominant_funnel_stage'] = 'entry'
            data['funnel_stage_distribution'] = {}
    
    return page_aggregations


def determine_recommendation_categories(aggregated_data: Dict) -> List[str]:
    """Determine which recommendation categories are needed for this page"""
    categories = []
    
    avg_engagement = aggregated_data.get('average_engagement_score', 0)
    avg_frustration = aggregated_data.get('average_frustration_level', 0)
    avg_conversion = aggregated_data.get('average_conversion_probability', 0)
    
    # User experience issues
    if avg_frustration >= 2 or avg_engagement < 40:
        categories.append('ui_design')
    
    # Performance issues
    if avg_frustration >= 4:
        categories.append('performance')
    
    # Conversion optimization
    if avg_conversion < 0.4:
        categories.append('conversion_optimization')
    
    # Content issues
    if avg_engagement < 30:
        categories.append('content')
    
    # Default to user experience if no specific issues
    if not categories:
        categories.append('user_experience')
    
    return categories