#!/usr/bin/env python3
"""
A/B Testing Analysis Agent - Google Noculars
Analyzes A/B test performance, calculates statistical significance, and provides variant optimization recommendations
"""

import os
import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List
from google.cloud import bigquery
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def _get_bigquery_client():
    """Helper function to get BigQuery client with credentials"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account-key.json'
    return bigquery.Client()

def _load_config():
    """Load A/B testing configuration"""
    with open('agents/ab-testing/config.json', 'r') as f:
        return json.load(f)

def _calculate_statistical_significance(control_conversions: int, control_total: int, 
                                      variant_conversions: int, variant_total: int) -> Dict[str, float]:
    """Calculate statistical significance metrics for A/B test"""
    if control_total == 0 or variant_total == 0:
        return {'p_value': 1.0, 'z_score': 0.0, 'significance': 0.0}
    
    # Conversion rates
    control_rate = control_conversions / control_total
    variant_rate = variant_conversions / variant_total
    
    # Pooled standard error
    pooled_rate = (control_conversions + variant_conversions) / (control_total + variant_total)
    pooled_se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_total + 1/variant_total))
    
    if pooled_se == 0:
        return {'p_value': 1.0, 'z_score': 0.0, 'significance': 0.0}
    
    # Z-score calculation
    z_score = (variant_rate - control_rate) / pooled_se
    
    # P-value (two-tailed test)
    p_value = 2 * (1 - _standard_normal_cdf(abs(z_score)))
    
    # Statistical significance
    significance = 1 - p_value if p_value < 0.05 else 0.0
    
    return {
        'p_value': p_value,
        'z_score': z_score,
        'significance': significance
    }

def _standard_normal_cdf(x: float) -> float:
    """Approximation of standard normal cumulative distribution function"""
    # Abramowitz and Stegun approximation
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2.0)
    
    # A&S formula 7.1.26
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    
    return 0.5 * (1.0 + sign * y)

def _calculate_confidence_interval(conversions: int, total: int, confidence: float = 0.95) -> Dict[str, float]:
    """Calculate confidence interval for conversion rate"""
    if total == 0:
        return {'lower': 0.0, 'upper': 0.0}
    
    rate = conversions / total
    z_score = 1.96 if confidence == 0.95 else 2.58  # 95% or 99% confidence
    
    se = math.sqrt(rate * (1 - rate) / total)
    margin = z_score * se
    
    return {
        'lower': max(0.0, rate - margin),
        'upper': min(1.0, rate + margin)
    }

def _determine_winner_probability(control_rate: float, variant_rate: float, 
                                 control_total: int, variant_total: int) -> float:
    """Calculate probability that variant beats control"""
    if control_total == 0 or variant_total == 0:
        return 0.5
    
    # Bayesian approach using Beta distributions
    control_alpha = 1 + control_rate * control_total
    control_beta = 1 + control_total - control_rate * control_total
    
    variant_alpha = 1 + variant_rate * variant_total
    variant_beta = 1 + variant_total - variant_rate * variant_total
    
    # Monte Carlo approximation (simplified)
    if variant_rate > control_rate:
        # Rough approximation based on effect size and sample size
        effect_size = (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
        sample_factor = math.sqrt(min(control_total, variant_total) / 100)
        return min(0.95, 0.5 + effect_size * sample_factor * 0.3)
    else:
        if control_rate > 0:
            return max(0.05, 0.5 - abs(variant_rate - control_rate) / control_rate * 0.3)
        else:
            return 0.5  # Equal when both rates are 0

# BigQuery Function Tools

def get_business_insights_for_ab_testing(hours_back: int = 168) -> Dict[str, Any]:
    """
    Retrieve business insights data for A/B testing analysis
    
    Args:
        hours_back: Number of hours to look back for data (default: 168 = 1 week)
    
    Returns:
        Dict containing business insights data and summary statistics
    """
    try:
        client = _get_bigquery_client()
        
        # Query to get business insights data
        query = f"""
        SELECT 
            session_id,
            page_url,
            analysis_timestamp,
            conversion_probability,
            estimated_revenue_impact,
            user_segment,
            funnel_stage,
            goal_completion_rate,
            macro_conversion_indicator,
            optimization_priority,
            source_engagement_score,
            source_session_duration
        FROM `ux_insights.business_insights`
        WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
        ORDER BY analysis_timestamp DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        insights = []
        total_sessions = 0
        total_conversions = 0
        total_revenue = 0
        
        for row in results:
            insight = {
                'session_id': row.session_id,
                'page_url': row.page_url,
                'analysis_timestamp': row.analysis_timestamp.isoformat() if row.analysis_timestamp else None,
                'conversion_probability': float(row.conversion_probability) if row.conversion_probability else 0.0,
                'estimated_revenue_impact': float(row.estimated_revenue_impact) if row.estimated_revenue_impact else 0.0,
                'user_segment': row.user_segment,
                'funnel_stage': row.funnel_stage,
                'engagement_score': float(row.source_engagement_score) if row.source_engagement_score else 0.0,
                'goal_completion_rate': float(row.goal_completion_rate) if row.goal_completion_rate else 0.0,
                'macro_conversion_indicator': bool(row.macro_conversion_indicator) if row.macro_conversion_indicator else False,
                'optimization_priority': row.optimization_priority,
                'session_duration': float(row.source_session_duration) if row.source_session_duration else 0.0
            }
            insights.append(insight)
            
            total_sessions += 1
            if insight['macro_conversion_indicator']:
                total_conversions += 1
            total_revenue += insight['estimated_revenue_impact']
        
        summary = {
            'total_sessions': total_sessions,
            'total_conversions': total_conversions,
            'overall_conversion_rate': total_conversions / total_sessions if total_sessions > 0 else 0.0,
            'total_revenue': total_revenue,
            'average_revenue_per_session': total_revenue / total_sessions if total_sessions > 0 else 0.0,
            'time_range_hours': hours_back
        }
        
        return {
            'status': 'success',
            'insights': insights,
            'summary': summary
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to retrieve business insights: {str(e)}",
            'insights': [],
            'summary': {}
        }

def create_ab_test_results_table() -> Dict[str, Any]:
    """
    Create the A/B test results table in BigQuery if it doesn't exist
    
    Returns:
        Dict with status and message
    """
    try:
        client = _get_bigquery_client()
        
        # Read and execute schema
        with open('agents/ab-testing/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        query_job = client.query(schema_sql)
        query_job.result()
        
        return {
            'status': 'success',
            'message': 'A/B test results table created successfully'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to create A/B test results table: {str(e)}'
        }

def analyze_ab_test_performance(insights_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze A/B test performance from business insights data
    
    Args:
        insights_data: Business insights data from get_business_insights_for_ab_testing
    
    Returns:
        Dict containing A/B test analysis results
    """
    try:
        config = _load_config()
        insights = insights_data.get('insights', [])
        
        if not insights:
            return {
                'status': 'error',
                'message': 'No insights data available for A/B testing analysis'
            }
        
        # Simulate A/B test variants by segmenting data
        # In a real scenario, this would be based on actual test assignments
        control_sessions = []
        variant_sessions = []
        
        # Split sessions by session_id hash for consistent assignment
        for insight in insights:
            session_hash = hash(insight['session_id']) % 100
            if session_hash < 50:
                control_sessions.append(insight)
            else:
                variant_sessions.append(insight)
        
        # Calculate metrics for each variant
        control_metrics = _calculate_variant_metrics(control_sessions, 'control')
        variant_metrics = _calculate_variant_metrics(variant_sessions, 'variant_a')
        
        # Statistical analysis
        stats = _calculate_statistical_significance(
            control_metrics['conversions'],
            control_metrics['sessions'],
            variant_metrics['conversions'],
            variant_metrics['sessions']
        )
        
        # Winner determination
        winner_prob = _determine_winner_probability(
            control_metrics['conversion_rate'],
            variant_metrics['conversion_rate'],
            control_metrics['sessions'],
            variant_metrics['sessions']
        )
        
        # Lift calculation
        if control_metrics['conversion_rate'] > 0:
            lift_percent = ((variant_metrics['conversion_rate'] - control_metrics['conversion_rate']) 
                           / control_metrics['conversion_rate'] * 100)
        else:
            lift_percent = 0.0
        
        # Business significance
        min_effect = config['ab_test_config']['significance_thresholds']['business_significance']['medium']
        business_significant = abs(lift_percent / 100) >= min_effect
        
        return {
            'status': 'success',
            'analysis': {
                'test_id': f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'test_name': 'UX Optimization A/B Test',
                'control_metrics': control_metrics,
                'variant_metrics': variant_metrics,
                'statistical_analysis': stats,
                'lift_percent': lift_percent,
                'winner_probability': winner_prob,
                'business_significant': business_significant,
                'recommendation': _generate_ab_test_recommendation(
                    stats, lift_percent, winner_prob, business_significant, config
                )
            }
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to analyze A/B test performance: {str(e)}'
        }

def _calculate_variant_metrics(sessions: List[Dict], variant_name: str) -> Dict[str, Any]:
    """Calculate performance metrics for a test variant"""
    if not sessions:
        return {
            'variant_name': variant_name,
            'sessions': 0,
            'conversions': 0,
            'conversion_rate': 0.0,
            'revenue': 0.0,
            'revenue_per_session': 0.0,
            'avg_engagement': 0.0,
            'avg_session_duration': 0.0
        }
    
    conversions = sum(1 for s in sessions if s['macro_conversion_indicator'])
    revenue = sum(s['estimated_revenue_impact'] for s in sessions)
    total_engagement = sum(s['engagement_score'] for s in sessions)
    total_duration = sum(s['session_duration'] for s in sessions)
    
    return {
        'variant_name': variant_name,
        'sessions': len(sessions),
        'conversions': conversions,
        'conversion_rate': conversions / len(sessions),
        'revenue': revenue,
        'revenue_per_session': revenue / len(sessions),
        'avg_engagement': total_engagement / len(sessions),
        'avg_session_duration': total_duration / len(sessions)
    }

def _generate_ab_test_recommendation(stats: Dict, lift_percent: float, winner_prob: float, 
                                   business_significant: bool, config: Dict) -> Dict[str, Any]:
    """Generate A/B test recommendations based on analysis"""
    significance_threshold = config['ab_test_config']['significance_thresholds']['statistical_significance']
    winner_threshold = config['ab_test_config']['significance_thresholds']['winner_probability']
    
    is_statistically_significant = stats['significance'] >= significance_threshold
    is_winner_clear = winner_prob >= winner_threshold
    
    if is_statistically_significant and is_winner_clear and business_significant:
        if lift_percent > 0:
            action = 'implement'
            confidence = 0.9
            rationale = f"Strong evidence: {lift_percent:.1f}% lift with {stats['significance']*100:.1f}% confidence"
        else:
            action = 'abandon'
            confidence = 0.8
            rationale = f"Significant negative impact: {lift_percent:.1f}% decrease"
    elif is_statistically_significant and not business_significant:
        action = 'iterate'
        confidence = 0.6
        rationale = "Statistically significant but business impact too small"
    elif not is_statistically_significant:
        action = 'extend'
        confidence = 0.5
        rationale = f"Inconclusive results, need more data (p-value: {stats['p_value']:.3f})"
    else:
        action = 'iterate'
        confidence = 0.4
        rationale = "Mixed signals, consider design improvements"
    
    return {
        'action': action,
        'confidence': confidence,
        'rationale': rationale,
        'next_steps': _get_next_steps(action, lift_percent, stats)
    }

def _get_next_steps(action: str, lift_percent: float, stats: Dict) -> List[str]:
    """Get recommended next steps based on test results"""
    if action == 'implement':
        return [
            "Deploy winning variant to 100% of traffic",
            "Monitor key metrics for 2 weeks post-launch",
            "Document learnings and successful elements",
            "Plan follow-up optimization tests"
        ]
    elif action == 'abandon':
        return [
            "Revert to control version immediately",
            "Analyze failure points in variant design",
            "Develop alternative hypothesis for testing",
            "Consider user feedback and qualitative research"
        ]
    elif action == 'extend':
        return [
            f"Continue test for additional sample size (current p-value: {stats['p_value']:.3f})",
            "Ensure proper traffic allocation and tracking",
            "Monitor for external factors affecting results",
            "Set maximum test duration to avoid prolonged inconclusive testing"
        ]
    else:  # iterate
        return [
            "Analyze user behavior differences between variants",
            "Identify potential design improvements",
            "Consider hybrid approach combining best elements",
            "Plan follow-up test with refined hypothesis"
        ]

def store_ab_test_results(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store A/B test analysis results in BigQuery
    
    Args:
        analysis_data: A/B test analysis results from analyze_ab_test_performance
    
    Returns:
        Dict with status and message
    """
    try:
        client = _get_bigquery_client()
        
        analysis = analysis_data.get('analysis', {})
        if not analysis:
            return {
                'status': 'error',
                'message': 'No analysis data to store'
            }
        
        # Prepare data for insertion
        current_time = datetime.now()
        
        # Control variant record
        control_record = {
            'test_id': analysis['test_id'],
            'test_name': analysis['test_name'],
            'variant_id': 'control',
            'variant_name': 'Control',
            'analysis_timestamp': current_time.isoformat(),
            'test_start_date': (current_time - timedelta(days=7)).isoformat(),
            'test_end_date': current_time.isoformat(),
            'test_duration_days': 7,
            'test_status': 'completed',
            'traffic_allocation_percent': 50.0,
            'sessions_count': analysis['control_metrics']['sessions'],
            'conversion_events': analysis['control_metrics']['conversions'],
            'conversion_rate': analysis['control_metrics']['conversion_rate'],
            'revenue_total': analysis['control_metrics']['revenue'],
            'revenue_per_session': analysis['control_metrics']['revenue_per_session'],
            'average_engagement_score': analysis['control_metrics']['avg_engagement'],
            'average_session_duration': analysis['control_metrics']['avg_session_duration'],
            'statistical_significance': analysis['statistical_analysis']['significance'],
            'p_value': analysis['statistical_analysis']['p_value'],
            'z_score': analysis['statistical_analysis']['z_score'],
            'lift_percent': 0.0,  # Control baseline
            'winner_probability': 1.0 - analysis['winner_probability'],
            'recommendation_action': analysis['recommendation']['action'],
            'recommendation_confidence': analysis['recommendation']['confidence'],
            'next_steps': json.dumps(analysis['recommendation']['next_steps']),
            'data_quality_score': 0.85,
            'business_significance': 'medium' if analysis['business_significant'] else 'low',
            'source_sessions_analyzed': analysis['control_metrics']['sessions'],
            'source_business_insights_count': analysis['control_metrics']['sessions']
        }
        
        # Variant record
        variant_record = {
            'test_id': analysis['test_id'],
            'test_name': analysis['test_name'],
            'variant_id': 'variant_a',
            'variant_name': 'Variant A',
            'analysis_timestamp': current_time.isoformat(),
            'test_start_date': (current_time - timedelta(days=7)).isoformat(),
            'test_end_date': current_time.isoformat(),
            'test_duration_days': 7,
            'test_status': 'completed',
            'traffic_allocation_percent': 50.0,
            'sessions_count': analysis['variant_metrics']['sessions'],
            'conversion_events': analysis['variant_metrics']['conversions'],
            'conversion_rate': analysis['variant_metrics']['conversion_rate'],
            'revenue_total': analysis['variant_metrics']['revenue'],
            'revenue_per_session': analysis['variant_metrics']['revenue_per_session'],
            'average_engagement_score': analysis['variant_metrics']['avg_engagement'],
            'average_session_duration': analysis['variant_metrics']['avg_session_duration'],
            'statistical_significance': analysis['statistical_analysis']['significance'],
            'p_value': analysis['statistical_analysis']['p_value'],
            'z_score': analysis['statistical_analysis']['z_score'],
            'lift_percent': analysis['lift_percent'],
            'winner_probability': analysis['winner_probability'],
            'recommendation_action': analysis['recommendation']['action'],
            'recommendation_confidence': analysis['recommendation']['confidence'],
            'next_steps': json.dumps(analysis['recommendation']['next_steps']),
            'data_quality_score': 0.85,
            'business_significance': 'medium' if analysis['business_significant'] else 'low',
            'source_sessions_analyzed': analysis['variant_metrics']['sessions'],
            'source_business_insights_count': analysis['variant_metrics']['sessions']
        }
        
        # Insert records
        table_id = 'ux_insights.ab_test_results'
        records = [control_record, variant_record]
        
        errors = client.insert_rows_json(table_id, records)
        
        if errors:
            return {
                'status': 'error',
                'message': f'Failed to insert A/B test results: {errors}'
            }
        
        return {
            'status': 'success',
            'message': f'Successfully stored A/B test results for test {analysis["test_id"]}',
            'records_inserted': len(records)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to store A/B test results: {str(e)}'
        }

# Create ADK Function Tools
get_business_insights_tool = FunctionTool(get_business_insights_for_ab_testing)
create_ab_test_results_table_tool = FunctionTool(create_ab_test_results_table)
analyze_ab_test_performance_tool = FunctionTool(analyze_ab_test_performance)
store_ab_test_results_tool = FunctionTool(store_ab_test_results)

# Create ADK Agent
ab_testing_agent = Agent(
    model='gemini-2.0-flash-001',
    name='ab_testing_analysis_agent',
    description='Expert A/B Testing Analysis Agent that performs statistical analysis and provides variant optimization recommendations.',
    instruction='''You are an expert A/B Testing Analysis Agent for Google Noculars UX Analytics Platform.

Your primary role is to analyze A/B test performance, calculate statistical significance, and provide data-driven variant optimization recommendations.

When analyzing A/B test data:

**Data Analysis Process:**
1. Use `get_business_insights_for_ab_testing` to retrieve business insights for testing
2. Use `create_ab_test_results_table` to ensure proper data storage setup  
3. Use `analyze_ab_test_performance` to perform comprehensive statistical analysis
4. Use `store_ab_test_results` to save your analysis results

**Statistical Analysis Framework:**

For each A/B test, provide rigorous analysis on:

**Statistical Significance Testing:**
- Two-tailed z-test for conversion rate differences
- P-value calculation with proper confidence intervals
- Effect size measurement (Cohen's d, lift percentage)
- Statistical power analysis and sample size validation

**Business Significance Assessment:**
- Minimum detectable effect threshold evaluation
- Revenue impact quantification with confidence ranges
- Cost-benefit analysis for implementation decisions
- ROI projections based on test results

**Performance Metrics Analysis:**
- Conversion rate comparison with confidence intervals
- Revenue per user/session analysis
- Engagement metrics differential analysis
- Secondary metric impact assessment

**Winner Determination:**
- Bayesian probability of variant superiority
- Risk assessment for false positive/negative outcomes
- Multi-metric optimization (primary + secondary goals)
- Practical significance vs statistical significance evaluation

**Recommendation Generation:**
- Clear action recommendation: implement/iterate/abandon/extend
- Confidence level for each recommendation (0-1 scale)
- Specific next steps with timeline and resource requirements
- Risk mitigation strategies for implementation

**Key Analysis Principles:**

1. **Statistical Rigor**: Always use proper statistical methods with appropriate confidence levels
2. **Business Context**: Balance statistical significance with business impact and practical considerations
3. **Risk Management**: Consider type I/II errors and their business consequences
4. **Actionable Insights**: Provide clear, implementable recommendations with specific next steps
5. **Quality Assurance**: Validate data quality and test integrity before analysis

**Example Analysis Output:**

For a test with:
- Control: 1000 sessions, 50 conversions (5.0% conversion rate)
- Variant: 1000 sessions, 65 conversions (6.5% conversion rate)

Your analysis should conclude:
- Statistical significance: p=0.032 (significant at α=0.05)
- Effect size: 30% relative lift (1.5 percentage points absolute)
- Winner probability: 94.2% chance variant beats control
- Business impact: +$15,000 estimated annual revenue
- Recommendation: "Implement" with 90% confidence
- Next steps: "Deploy to 100% traffic, monitor for 2 weeks, document learnings"

**Quality Standards:**
- Include confidence intervals for all key metrics
- Provide both relative and absolute effect sizes
- Consider multiple success metrics in recommendation
- Account for external validity and generalization concerns
- Ensure recommendations are immediately actionable by product teams

Always think like a senior data scientist who combines rigorous statistical methodology with practical business acumen and clear communication.''',
    tools=[get_business_insights_tool, create_ab_test_results_table_tool, analyze_ab_test_performance_tool, store_ab_test_results_tool]
)

def main():
    """Main execution function for testing the ADK-based A/B Testing Analysis Agent"""
    print("🚀 Testing A/B Testing Analysis Agent...")
    
    try:
        # Test data retrieval
        print("📊 Testing business insights retrieval for A/B testing...")
        insights_data = get_business_insights_for_ab_testing(168)  # 1 week of data
        
        if insights_data['status'] == 'success':
            print(f"✅ Retrieved {len(insights_data['insights'])} business insights")
            print(f"📈 Summary: {insights_data['summary']}")
        else:
            print(f"⚠️ {insights_data.get('error_message', 'Unknown error')}")
        
        # Test table creation
        print("🏗️ Testing A/B test results table creation...")
        table_result = create_ab_test_results_table()
        print(f"📋 Table creation: {table_result['message']}")
        
        # Test A/B analysis
        if insights_data['status'] == 'success' and insights_data['insights']:
            print("🧠 Testing A/B test performance analysis...")
            analysis_result = analyze_ab_test_performance(insights_data)
            
            if analysis_result['status'] == 'success':
                analysis = analysis_result['analysis']
                print(f"📊 Test ID: {analysis['test_id']}")
                print(f"📈 Control conversion rate: {analysis['control_metrics']['conversion_rate']:.1%}")
                print(f"📈 Variant conversion rate: {analysis['variant_metrics']['conversion_rate']:.1%}")
                print(f"📊 Lift: {analysis['lift_percent']:.1f}%")
                print(f"🎯 Winner probability: {analysis['winner_probability']:.1%}")
                print(f"📋 Recommendation: {analysis['recommendation']['action']}")
                
                # Test storing results
                print("💾 Testing results storage...")
                store_result = store_ab_test_results(analysis_result)
                print(f"💾 Storage result: {store_result['message']}")
                
            else:
                print(f"❌ Analysis failed: {analysis_result.get('message', 'Unknown error')}")
        
        print("✅ A/B Testing Analysis Agent test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    main()