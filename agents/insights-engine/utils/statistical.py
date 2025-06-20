#!/usr/bin/env python3
"""
Statistical Analysis Utilities for Insights Engine
Contains all statistical calculation functions for data quality, correlation, and evidence scoring
"""

import math
from typing import Dict, Any, List


def calculate_sample_size_adequacy(session_count: int) -> str:
    """Determine sample size adequacy for statistical confidence"""
    if session_count < 5:
        return 'insufficient'
    elif session_count < 20:
        return 'adequate'
    elif session_count < 100:
        return 'strong'
    else:
        return 'excellent'


def calculate_statistical_power(session_count: int) -> float:
    """Calculate statistical power based on sample size and effect size"""
    # Simplified power calculation for two-sample test
    if session_count < 5:
        return 0.0
    elif session_count < 10:
        return 0.3
    elif session_count < 30:
        return 0.6
    elif session_count < 100:
        return 0.8
    else:
        return 0.95


def calculate_cross_agent_correlation(pattern_sessions: List[Dict], business_sessions: List[Dict]) -> float:
    """Calculate correlation between pattern recognition and business intelligence insights"""
    if not pattern_sessions or not business_sessions:
        return 0.0
    
    # Match sessions by session_id
    matched_pairs = []
    for pattern in pattern_sessions:
        session_id = pattern.get('session_id')
        business = next((b for b in business_sessions if b.get('session_id') == session_id), None)
        if business:
            # Compare key metrics to assess correlation
            pattern_score = pattern.get('engagement_score', 0) / 100.0  # Normalize to 0-1
            business_score = business.get('conversion_probability', 0)  # Already 0-1
            matched_pairs.append((pattern_score, business_score))
    
    if len(matched_pairs) < 2:
        return 0.5  # Default moderate correlation for small samples
    
    # Calculate Pearson correlation coefficient
    n = len(matched_pairs)
    x_vals = [pair[0] for pair in matched_pairs]
    y_vals = [pair[1] for pair in matched_pairs]
    
    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n
    
    numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
    x_variance = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
    y_variance = sum((y_vals[i] - y_mean) ** 2 for i in range(n))
    
    if x_variance == 0 or y_variance == 0:
        return 0.5  # No variance means moderate correlation
    
    correlation = numerator / (math.sqrt(x_variance * y_variance))
    return abs(correlation)  # Return absolute correlation strength


def calculate_data_consistency_score(sessions: List[Dict], metric_keys: List[str]) -> float:
    """Calculate data consistency score based on variance in key metrics"""
    if len(sessions) < 2:
        return 1.0  # Perfect consistency with only one data point
    
    consistency_scores = []
    
    for metric_key in metric_keys:
        values = [session.get(metric_key, 0) for session in sessions if session.get(metric_key) is not None]
        
        if len(values) < 2:
            continue
        
        # Calculate coefficient of variation (CV = std_dev / mean)
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            consistency_scores.append(1.0)  # Perfect consistency at zero
            continue
        
        variance = sum((val - mean_val) ** 2 for val in values) / len(values)
        std_dev = math.sqrt(variance)
        cv = std_dev / abs(mean_val)
        
        # Convert CV to consistency score (lower CV = higher consistency)
        # CV of 0 = 1.0 consistency, CV of 1+ = 0.0 consistency
        consistency_score = max(0.0, 1.0 - cv)
        consistency_scores.append(consistency_score)
    
    return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5


def calculate_evidence_strength_score(
    session_count: int,
    cross_agent_correlation: float,
    data_consistency: float,
    statistical_power: float
) -> float:
    """Calculate overall evidence strength based on multiple factors"""
    # Weight factors
    sample_size_weight = 0.3
    correlation_weight = 0.25
    consistency_weight = 0.25
    power_weight = 0.20
    
    # Sample size score (logarithmic scaling)
    if session_count >= 100:
        sample_score = 1.0
    elif session_count >= 30:
        sample_score = 0.8
    elif session_count >= 10:
        sample_score = 0.6
    elif session_count >= 5:
        sample_score = 0.4
    else:
        sample_score = 0.2
    
    # Weighted average
    evidence_strength = (
        sample_score * sample_size_weight +
        cross_agent_correlation * correlation_weight +
        data_consistency * consistency_weight +
        statistical_power * power_weight
    )
    
    return min(1.0, max(0.0, evidence_strength))


def identify_outlier_sessions(sessions: List[Dict], metric_keys: List[str]) -> int:
    """Identify sessions that are statistical outliers"""
    if len(sessions) < 3:
        return 0  # Need at least 3 sessions to identify outliers
    
    outlier_count = 0
    
    for metric_key in metric_keys:
        values = [session.get(metric_key, 0) for session in sessions if session.get(metric_key) is not None]
        
        if len(values) < 3:
            continue
        
        # Calculate mean and standard deviation
        mean_val = sum(values) / len(values)
        variance = sum((val - mean_val) ** 2 for val in values) / len(values)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            continue  # No variance, no outliers
        
        # Identify outliers (values more than 2 standard deviations from mean)
        outlier_threshold = 2 * std_dev
        
        for i, session in enumerate(sessions):
            value = session.get(metric_key)
            if value is not None and abs(value - mean_val) > outlier_threshold:
                # Mark this session as having an outlier value
                session[f'{metric_key}_outlier'] = True
                outlier_count += 1
    
    return outlier_count


def calculate_data_quality_score(
    session_count: int,
    data_consistency: float,
    outlier_count: int,
    missing_data_ratio: float = 0.0
) -> float:
    """Calculate overall data quality score"""
    # Base score from sample size
    if session_count >= 50:
        size_score = 1.0
    elif session_count >= 20:
        size_score = 0.8
    elif session_count >= 10:
        size_score = 0.6
    elif session_count >= 5:
        size_score = 0.4
    else:
        size_score = 0.2
    
    # Penalty for outliers
    outlier_ratio = outlier_count / max(session_count, 1)
    outlier_penalty = min(0.3, outlier_ratio * 0.5)  # Max 30% penalty
    
    # Penalty for missing data
    missing_penalty = min(0.2, missing_data_ratio * 0.4)  # Max 20% penalty
    
    # Combine scores
    quality_score = (size_score * 0.4 + data_consistency * 0.6) - outlier_penalty - missing_penalty
    
    return min(1.0, max(0.0, quality_score))


def calculate_business_priority_rank(
    revenue_impact: float,
    conversion_impact: float, 
    ux_impact: float,
    implementation_complexity: str,
    statistical_confidence: float
) -> int:
    """Calculate business priority rank (1=highest, 100=lowest)"""
    # Normalize inputs to 0-1 scale
    revenue_score = min(abs(revenue_impact) / 10000, 1.0)  # Cap at $10k impact
    conversion_score = min(abs(conversion_impact) / 100, 1.0)  # Cap at 100% improvement
    ux_score = ux_impact / 100.0  # Already 0-100 scale
    
    # Complexity penalty
    complexity_penalties = {'simple': 0.0, 'moderate': 0.2, 'complex': 0.4, 'major': 0.6}
    complexity_penalty = complexity_penalties.get(implementation_complexity, 0.3)
    
    # Confidence boost
    confidence_boost = statistical_confidence * 0.3
    
    # Calculate composite score (higher is better)
    composite_score = (revenue_score * 0.4 + conversion_score * 0.3 + ux_score * 0.2 + confidence_boost) - complexity_penalty
    
    # Convert to rank (1-100, where 1 is highest priority)
    priority_rank = max(1, min(100, int(101 - (composite_score * 100))))
    
    return priority_rank


def determine_insight_severity(
    pattern_data: Dict,
    business_data: Dict,
    ab_data: Dict = None
) -> str:
    """Determine insight severity based on multi-agent data"""
    # Check for critical issues
    frustration = pattern_data.get('frustration_indicators', 0)
    bounce_rate = business_data.get('bounce_likelihood', 0)
    revenue_impact = abs(business_data.get('estimated_revenue_impact', 0))
    
    if frustration >= 5 or bounce_rate >= 0.8 or revenue_impact >= 5000:
        return 'critical'
    elif frustration >= 3 or bounce_rate >= 0.6 or revenue_impact >= 1000:
        return 'high'
    elif frustration >= 1 or bounce_rate >= 0.4 or revenue_impact >= 100:
        return 'medium'
    else:
        return 'low'


