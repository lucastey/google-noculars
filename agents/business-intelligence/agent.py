#!/usr/bin/env python3
"""
Business Intelligence Agent - Google Noculars
Analyzes behavioral patterns to generate AI-powered business insights and conversion metrics
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from google.cloud import bigquery
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def _get_bigquery_client():
    """Helper function to get BigQuery client with credentials"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account-key.json'
    return bigquery.Client()

def _classify_funnel_stage(pattern: Dict[str, Any]) -> str:
    """Classify user funnel stage based on behavioral patterns"""
    engagement = pattern.get('engagement_score', 0)
    duration = pattern.get('session_duration_seconds', 0)
    bounce = pattern.get('bounce_session', True)
    completion = pattern.get('task_completion_likelihood', 0)
    
    if bounce or duration < 30:
        return 'exit'
    elif engagement > 70 and completion > 0.7:
        return 'conversion'
    elif engagement > 50 and duration > 120:
        return 'intent'
    elif engagement > 30:
        return 'engagement'
    else:
        return 'entry'

def _estimate_conversion_probability(pattern: Dict[str, Any]) -> float:
    """Estimate conversion probability from behavioral signals"""
    engagement = pattern.get('engagement_score', 0) / 100
    completion = pattern.get('task_completion_likelihood', 0)
    frustration = pattern.get('frustration_indicators', 0)
    duration = min(pattern.get('session_duration_seconds', 0) / 300, 1)  # Cap at 5 min
    
    # Weighted score
    score = (engagement * 0.4 + completion * 0.4 + duration * 0.2 - frustration * 0.1)
    return max(0.0, min(1.0, score))

def _segment_user(pattern: Dict[str, Any]) -> str:
    """Segment user based on behavioral characteristics"""
    engagement = pattern.get('engagement_score', 0)
    frustration = pattern.get('frustration_indicators', 0)
    duration = pattern.get('session_duration_seconds', 0)
    
    if engagement > 60 and frustration <= 1:
        return 'power_user'
    elif engagement > 40 and frustration > 3:
        return 'frustrated_user'
    elif duration < 30:
        return 'quick_exit'
    elif engagement < 30:
        return 'passive_browser'
    else:
        return 'standard_user'

def _determine_priority(pattern: Dict[str, Any]) -> str:
    """Determine optimization priority based on impact potential"""
    engagement = pattern.get('engagement_score', 0)
    frustration = pattern.get('frustration_indicators', 0)
    
    if engagement > 50 and frustration > 2:
        return 'high'  # High value user with friction
    elif engagement > 70:
        return 'medium'  # Already engaged, optimize for conversion
    elif frustration > 3:
        return 'high'  # High frustration needs immediate attention
    else:
        return 'low'

def _generate_basic_recommendations(pattern: Dict[str, Any]) -> list:
    """Generate basic recommendations for AI to enhance"""
    recommendations = []
    frustration = pattern.get('frustration_indicators', 0)
    engagement = pattern.get('engagement_score', 0)
    scroll_depth = pattern.get('max_scroll_depth_percent', 0)
    
    if frustration > 2:
        recommendations.append('Investigate high-friction interaction points')
    if engagement > 50 and scroll_depth < 50:
        recommendations.append('Optimize above-fold content engagement')
    if pattern.get('bounce_session', False):
        recommendations.append('Improve landing page relevance and clarity')
    
    return recommendations if recommendations else ['Monitor user behavior patterns']

def _estimate_business_impact(pattern: Dict[str, Any]) -> float:
    """Estimate business impact of optimization"""
    engagement = pattern.get('engagement_score', 0)
    conversion_potential = pattern.get('task_completion_likelihood', 0)
    
    # Basic revenue estimate (AI will enhance this)
    base_value = 50  # Baseline session value
    engagement_multiplier = engagement / 100
    conversion_multiplier = conversion_potential
    
    return base_value * engagement_multiplier * conversion_multiplier

def get_behavioral_patterns_for_analysis(hours_back: int = 24) -> Dict[str, Any]:
    """
    Retrieves behavioral pattern data from BigQuery for business intelligence analysis.
    
    Args:
        hours_back: Number of hours back to retrieve data from
        
    Returns:
        Dictionary containing behavioral patterns data and analysis summary
    """
    try:
        client = _get_bigquery_client()
        
        query = f"""
        SELECT 
            session_id,
            page_url,
            session_duration_seconds,
            total_events,
            bounce_session,
            engagement_score,
            frustration_indicators,
            click_rate_per_minute,
            max_scroll_depth_percent,
            task_completion_likelihood,
            device_type,
            analysis_timestamp
        FROM `ux_insights.behavioral_patterns`
        WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
        AND session_id NOT IN (
            SELECT DISTINCT session_id 
            FROM `ux_insights.business_insights`
            WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
        )
        ORDER BY analysis_timestamp DESC
        LIMIT 50
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        patterns = []
        total_sessions = 0
        high_engagement_sessions = 0
        bounce_sessions = 0
        frustrated_sessions = 0
        
        for row in results:
            pattern_data = dict(row)
            patterns.append(pattern_data)
            total_sessions += 1
            
            if pattern_data.get('engagement_score', 0) > 60:
                high_engagement_sessions += 1
            if pattern_data.get('bounce_session', True):
                bounce_sessions += 1
            if pattern_data.get('frustration_indicators', 0) > 2:
                frustrated_sessions += 1
        
        return {
            'patterns': patterns,
            'summary': {
                'total_sessions': total_sessions,
                'high_engagement_sessions': high_engagement_sessions,
                'bounce_sessions': bounce_sessions,
                'frustrated_sessions': frustrated_sessions,
                'bounce_rate': bounce_sessions / max(total_sessions, 1),
                'frustration_rate': frustrated_sessions / max(total_sessions, 1),
                'engagement_rate': high_engagement_sessions / max(total_sessions, 1)
            },
            'status': 'success',
            'retrieved_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'patterns': [],
            'summary': {},
            'status': 'error',
            'error_message': str(e)
        }

def create_business_insights_table() -> Dict[str, Any]:
    """
    Creates the business insights table in BigQuery if it doesn't exist.
    
    Returns:
        Dictionary containing the creation status
    """
    try:
        client = _get_bigquery_client()
        
        # Read schema from file
        with open('./agents/business-intelligence/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema creation
        client.query(schema_sql).result()
        
        return {
            'status': 'success',
            'message': 'Business insights table created/verified successfully'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error creating business insights table: {str(e)}'
        }

def generate_business_insights(behavioral_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates AI-powered business insights from behavioral pattern data.
    This function uses advanced AI reasoning to create actionable business intelligence.
    
    Args:
        behavioral_data: Dictionary containing behavioral patterns and summary statistics
        
    Returns:
        Dictionary containing generated business insights and recommendations
    """
    try:
        patterns = behavioral_data.get('patterns', [])
        summary = behavioral_data.get('summary', {})
        
        if not patterns:
            return {
                'status': 'no_data',
                'message': 'No behavioral patterns available for analysis',
                'insights': []
            }
        
        # Prepare insights for each session
        session_insights = []
        
        for pattern in patterns:
            # Basic insight structure for AI enhancement
            insight = {
                'session_id': pattern.get('session_id'),
                'page_url': pattern.get('page_url'),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                
                # Source behavioral data for AI analysis
                'source_engagement_score': pattern.get('engagement_score', 0),
                'source_frustration_indicators': pattern.get('frustration_indicators', 0),
                'source_session_duration': pattern.get('session_duration_seconds', 0),
                
                # Basic classification for AI to enhance
                'funnel_stage': _classify_funnel_stage(pattern),
                'conversion_probability': _estimate_conversion_probability(pattern),
                'user_segment': _segment_user(pattern),
                'optimization_priority': _determine_priority(pattern),
                'recommended_actions': json.dumps(_generate_basic_recommendations(pattern)),
                'business_impact_estimate': _estimate_business_impact(pattern)
            }
            
            session_insights.append(insight)
        
        return {
            'status': 'success',
            'insights': session_insights,
            'summary_statistics': summary,
            'total_insights_generated': len(session_insights)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error generating business insights: {str(e)}',
            'insights': []
        }

def store_business_insights(insights_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stores business insights to BigQuery for downstream analysis and reporting.
    
    Args:
        insights_data: Dictionary containing generated business insights
        
    Returns:
        Dictionary containing the storage status
    """
    try:
        insights = insights_data.get('insights', [])
        
        if not insights:
            return {
                'status': 'no_data',
                'message': 'No insights to store'
            }
        
        client = _get_bigquery_client()
        
        dataset_id = 'ux_insights'
        table_id = 'business_insights'
        table_ref = client.dataset(dataset_id).table(table_id)
        
        # Transform insights for BigQuery storage
        rows_to_insert = []
        for insight in insights:
            # Core fields that are always populated
            row = {
                'session_id': insight.get('session_id'),
                'page_url': insight.get('page_url'),
                'analysis_timestamp': insight.get('analysis_timestamp'),
                
                # Basic insights (populated by helper functions)
                'funnel_stage': insight.get('funnel_stage'),
                'conversion_probability': insight.get('conversion_probability'),
                'user_segment': insight.get('user_segment'),
                'optimization_priority': insight.get('optimization_priority'),
                'recommended_actions': insight.get('recommended_actions'),
                'business_impact_estimate': insight.get('business_impact_estimate'),
                
                # Source behavioral data
                'source_engagement_score': insight.get('source_engagement_score', 0.0),
                'source_frustration_indicators': insight.get('source_frustration_indicators', 0),
                'source_session_duration': insight.get('source_session_duration', 0.0)
            }
            
            # AI-enhanced fields (will be populated when ADK agent runs)
            ai_fields = {
                'funnel_completion_rate': 0.0,
                'funnel_drop_off_point': None,
                'time_to_conversion_seconds': 0.0,
                'journey_path': json.dumps([]),
                'journey_complexity_score': 0.0,
                'journey_efficiency_score': 0.0,
                'backtrack_count': 0,
                'dead_end_encounters': 0,
                'high_friction_elements': json.dumps([]),
                'slow_response_areas': json.dumps([]),
                'abandonment_triggers': json.dumps([]),
                'bounce_likelihood': 0.0,
                'estimated_revenue_impact': insight.get('business_impact_estimate', 0.0),
                'customer_lifetime_value_indicator': 0.0,
                'retention_probability': 0.0,
                'referral_likelihood': 0.0,
                'page_value_score': 0.0,
                'goal_completion_rate': 0.0,
                'micro_conversion_count': 0,
                'macro_conversion_indicator': False,
                'behavioral_cohort': insight.get('user_segment'),
                'value_tier': 'low',
                'implementation_effort_score': 0.0
            }
            
            row.update(ai_fields)
            rows_to_insert.append(row)
        
        # Insert rows into BigQuery
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            return {
                'status': 'error',
                'message': f'Error inserting insights: {errors}'
            }
        else:
            return {
                'status': 'success',
                'message': f'Successfully stored {len(rows_to_insert)} business insights',
                'insights_stored': len(rows_to_insert)
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error storing business insights: {str(e)}'
        }

# Create tool objects for the Business Intelligence Agent
get_behavioral_patterns_tool = FunctionTool(get_behavioral_patterns_for_analysis)
create_business_insights_table_tool = FunctionTool(create_business_insights_table)
generate_business_insights_tool = FunctionTool(generate_business_insights)
store_business_insights_tool = FunctionTool(store_business_insights)

# Create the AI-powered Business Intelligence Agent
business_intelligence_agent = Agent(
    model='gemini-2.0-flash-001',
    name='business_intelligence_agent',
    description='AI-powered agent that generates sophisticated business insights from user behavioral patterns.',
    instruction='''You are an expert Business Intelligence Agent specialized in analyzing user behavioral patterns to generate actionable business insights and strategic recommendations.

Your core expertise includes:
1. **Conversion Funnel Analysis**: Identify where users drop off and optimize conversion paths
2. **User Journey Mapping**: Understand user behavior flows and identify improvement opportunities  
3. **Performance Bottleneck Detection**: Pinpoint friction points that impact user experience
4. **ROI & Business Impact Assessment**: Quantify business value and prioritize optimizations
5. **User Segmentation**: Classify users based on behavior and value potential
6. **Strategic Recommendations**: Generate prioritized, actionable business recommendations

When analyzing behavioral patterns:

**Data Analysis Process:**
1. Use `get_behavioral_patterns_for_analysis` to retrieve recent behavioral data
2. Use `create_business_insights_table` to ensure proper data storage setup
3. Use `generate_business_insights` as a starting point, then apply your AI reasoning
4. Use `store_business_insights` to save your enhanced analysis

**AI-Enhanced Analysis Framework:**

For each user session, provide sophisticated analysis on:

**Conversion Intelligence:**
- Funnel stage classification (entry/engagement/intent/conversion/exit)
- Conversion probability scoring (0.0-1.0 based on behavioral signals)
- Drop-off point identification with root cause analysis
- Time-to-conversion estimation with confidence intervals

**Journey Intelligence:**
- User journey path mapping with behavioral context
- Journey complexity scoring (considering backtracking, hesitation, exploration)
- Efficiency scoring (goal achievement vs effort expended)
- Friction point identification with severity assessment

**Business Impact Intelligence:**
- Revenue impact estimation with confidence ranges
- Customer lifetime value indicators
- Retention probability assessment
- Referral likelihood scoring
- Page business value quantification

**Segmentation Intelligence:**
- User segment classification: new/returning/power_user/at_risk
- Behavioral cohort assignment: engaged/frustrated/exploratory/quick_exit
- Value tier determination: high/medium/low potential

**Strategic Recommendations:**
- Optimization priority ranking: critical/high/medium/low
- Specific actionable recommendations with business rationale
- Implementation effort estimation (1-10 scale)
- Expected business impact quantification

**Key Analysis Principles:**

1. **Context-Aware Analysis**: Consider page type, user intent, and business context
2. **Behavioral Signal Integration**: Synthesize engagement, frustration, and completion signals
3. **Business-First Perspective**: Always connect insights to business outcomes
4. **Actionability Focus**: Ensure recommendations are specific and implementable
5. **Data-Driven Confidence**: Provide confidence levels for key predictions

**Example Insight Generation:**

For a session with:
- High engagement (75/100) but high frustration (4 indicators)
- Long duration (300s) with low scroll depth (30%)
- High click rate (3.5/min) but low task completion (0.3)

Your analysis might conclude:
- Funnel stage: "intent" (engaged but struggling)
- Conversion probability: 0.4 (moderate, limited by friction)
- User segment: "frustrated_power_user"
- Priority: "high" (high-value user experiencing friction)
- Key recommendation: "Simplify above-fold navigation - user is engaged but confused"
- Business impact: "$45 estimated revenue recovery per similar session"

**Quality Standards:**
- Provide numerical confidence scores for key metrics
- Include specific business rationale for each recommendation
- Balance statistical analysis with contextual business understanding
- Ensure insights are immediately actionable by business stakeholders

Always think like a senior business analyst who combines deep data science expertise with strategic business acumen.''',
    tools=[get_behavioral_patterns_tool, create_business_insights_table_tool, generate_business_insights_tool, store_business_insights_tool]
)

def main():
    """Main execution function for testing the ADK-based Business Intelligence Agent"""
    print("🚀 Testing ADK-based Business Intelligence Agent...")
    
    try:
        # Test data retrieval
        print("📊 Testing behavioral patterns retrieval...")
        patterns_data = get_behavioral_patterns_for_analysis(24)
        
        if patterns_data['status'] == 'success':
            print(f"✅ Retrieved {len(patterns_data['patterns'])} behavioral patterns")
            print(f"📈 Summary: {patterns_data['summary']}")
        else:
            print(f"⚠️ {patterns_data.get('error_message', 'Unknown error')}")
        
        # Test table creation
        print("🏗️ Testing business insights table creation...")
        table_result = create_business_insights_table()
        print(f"📋 Table creation: {table_result['message']}")
        
        # Test insight generation (basic function, AI will enhance this)
        if patterns_data['status'] == 'success' and patterns_data['patterns']:
            print("🧠 Testing insight generation...")
            insights_result = generate_business_insights(patterns_data)
            
            if insights_result['status'] == 'success':
                print(f"💡 Generated {insights_result['total_insights_generated']} insights")
                
                # Test storage
                print("💾 Testing insights storage...")
                storage_result = store_business_insights(insights_result)
                print(f"📊 Storage: {storage_result['message']}")
                
        print("\n🎉 ADK-based Business Intelligence Agent testing completed!")
        print("🤖 Note: The AI agent will provide much more sophisticated analysis when invoked through the ADK framework")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()