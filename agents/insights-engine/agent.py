#!/usr/bin/env python3
"""
Insights Engine Agent - Google Noculars (Refactored)
Coordinates multi-agent results to generate priority-ranked actionable insights and business recommendations
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Import utilities
from utils.data_retrieval import (
    get_bigquery_client, get_pattern_recognition_data, 
    get_business_intelligence_data, get_ab_testing_data, get_existing_recommendations
)
from utils.data_processing import aggregate_sessions_by_page, determine_recommendation_categories
from utils.recommendation_builder import create_page_recommendation
from utils.bigquery_ops import upsert_final_recommendations
from utils.statistical import calculate_sample_size_adequacy, calculate_statistical_power


class InsightsEngineAgent:
    """Coordinates multi-agent results to generate priority-ranked actionable insights"""
    
    def __init__(self):
        """Initialize the Insights Engine Agent"""
        self.client = get_bigquery_client()
        self.dataset = self.client.dataset('ux_insights')
        
        # Initialize ADK agent with function tools
        self.agent = Agent(
            name="insights_engine",
            model="gemini-2.0-flash-exp",
            instruction="""You are an expert business insights coordinator that synthesizes data from multiple analytics agents to generate actionable recommendations.

Your primary functions:
1. Analyze behavioral patterns, business intelligence, and A/B testing data
2. Identify cross-agent correlations and insights
3. Prioritize recommendations based on business impact
4. Generate clear, actionable insights for stakeholders
5. Provide implementation guidance and success metrics

Key principles:
- Focus on actionable recommendations with clear business value
- Correlate findings across all data sources
- Prioritize based on impact vs effort
- Provide specific implementation steps
- Include measurement and monitoring plans
- Consider user segments and device differences
- Assess risks and provide mitigation strategies

Output format should be comprehensive business recommendations with:
- Clear priority ranking
- Specific action items
- Expected business impact
- Implementation timeline and resources
- Success metrics and monitoring plan
""",
            tools=[
                FunctionTool(get_pattern_recognition_data),
                FunctionTool(get_business_intelligence_data),
                FunctionTool(get_ab_testing_data),
                FunctionTool(get_existing_recommendations),
                FunctionTool(upsert_final_recommendations)
            ]
        )
        
        print("🧠 Insights Engine Agent initialized with ADK integration")
    
    def create_final_recommendations_table(self):
        """Create final recommendations table if it doesn't exist"""
        try:
            with open('./agents/insights-engine/schema.sql', 'r') as f:
                schema_sql = f.read()
            
            self.client.query(schema_sql).result()
            print("✅ Final recommendations table created/verified")
            
        except Exception as e:
            print(f"❌ Error creating final recommendations table: {e}")
            raise
    
    def analyze_and_coordinate(self, hours_back: int = 24) -> Dict[str, Any]:
        """Main method to analyze all agent data and generate page-centric coordinated insights"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Get data from all agents
            pattern_data = get_pattern_recognition_data(hours_back=hours_back)
            business_data = get_business_intelligence_data(hours_back=hours_back)
            ab_data = get_ab_testing_data(hours_back=hours_back * 7)  # A/B tests run longer
            
            print(f"📊 Retrieved data: {len(pattern_data)} patterns, {len(business_data)} business insights, {len(ab_data)} A/B tests")
            
            if not pattern_data and not business_data:
                print("⚠️ No data available for analysis")
                return {"status": "no_data", "recommendations": []}
            
            # Aggregate sessions by page URL for page-centric analysis
            page_aggregations = aggregate_sessions_by_page(pattern_data, business_data)
            
            print(f"🔄 Aggregated data for {len(page_aggregations)} unique pages")
            
            # Process each page separately
            all_recommendations = []
            upsert_results = {'inserted': 0, 'updated': 0, 'errors': []}
            
            for page_url, aggregated_data in page_aggregations.items():
                # Get existing recommendations for this page
                existing_recommendations = get_existing_recommendations(page_url=page_url)
                
                # Generate or update recommendations for this page
                page_recommendations = self._process_page_data(
                    aggregated_data, existing_recommendations, ab_data
                )
                
                if page_recommendations:
                    # Upsert page recommendations
                    page_result = upsert_final_recommendations(page_recommendations)
                    upsert_results['inserted'] += page_result.get('inserted', 0)
                    upsert_results['updated'] += page_result.get('updated', 0)
                    upsert_results['errors'].extend(page_result.get('errors', []))
                    
                    all_recommendations.extend(page_recommendations)
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                "status": "success",
                "processing_time_seconds": processing_time,
                "pages_analyzed": len(page_aggregations),
                "recommendations_generated": len(all_recommendations),
                "recommendations_inserted": upsert_results['inserted'],
                "recommendations_updated": upsert_results['updated'],
                "errors": upsert_results['errors'],
                "data_sources_analyzed": {
                    "behavioral_patterns": len(pattern_data),
                    "business_insights": len(business_data),
                    "ab_tests": len(ab_data)
                },
                "recommendations": all_recommendations[:10]  # Return top 10 for API response
            }
            
            print(f"✅ Processed {len(page_aggregations)} pages: {upsert_results['inserted']} inserted, {upsert_results['updated']} updated")
            return result
            
        except Exception as e:
            print(f"❌ Error in insights coordination: {e}")
            return {"status": "error", "error": str(e), "recommendations": []}
    
    def _process_page_data(
        self, 
        aggregated_data: Dict,
        existing_recommendations: List[Dict],
        ab_data: List[Dict]
    ) -> List[Dict]:
        """Process aggregated page data and create page-centric recommendations"""
        recommendations = []
        
        session_count = aggregated_data['session_count']
        
        # Calculate data freshness from latest timestamp
        if aggregated_data.get('pattern_sessions') or aggregated_data.get('business_sessions'):
            from datetime import datetime, timezone
            latest_timestamp = datetime.now(timezone.utc)
            for session in (aggregated_data.get('pattern_sessions', []) + aggregated_data.get('business_sessions', [])):
                if 'analysis_timestamp' in session:
                    try:
                        session_time = datetime.fromisoformat(session['analysis_timestamp'].replace('Z', '+00:00'))
                        if session_time < latest_timestamp:
                            latest_timestamp = session_time
                    except:
                        pass
            data_freshness_hours = max(1, (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 3600)
        else:
            data_freshness_hours = 24  # Default when no data available
        
        # Calculate sample size adequacy and statistical power
        sample_adequacy = calculate_sample_size_adequacy(session_count)
        statistical_power = calculate_statistical_power(session_count)
        
        # Determine recommendation categories needed for this page
        categories_to_analyze = determine_recommendation_categories(aggregated_data)
        
        for category in categories_to_analyze:
            # Check if recommendation already exists for this page/category
            existing_rec = next(
                (rec for rec in existing_recommendations 
                 if rec.get('recommendation_category') == category), 
                None
            )
            
            # Create or update recommendation
            recommendation = create_page_recommendation(
                aggregated_data, category, existing_rec, ab_data
            )
            
            if recommendation:
                # Add metadata about the analysis
                recommendation.update({
                    'sessions_analyzed_count': session_count,
                    'sessions_analyzed_list': aggregated_data['sessions_analyzed_list'],
                    'unique_users_count': session_count,  # Simplified assumption
                    'sample_size_adequacy': sample_adequacy,
                    'statistical_power': statistical_power,
                    'data_freshness_hours': data_freshness_hours,
                    'agents_analyzed': ['pattern-recognition', 'business-intelligence'],
                    'data_sources_used': ['behavioral_patterns', 'business_insights']
                })
                
                recommendations.append(recommendation)
        
        return recommendations


def main():
    """Main execution function"""
    print("🚀 Starting Insights Engine Agent Analysis")
    
    # Initialize agent
    agent = InsightsEngineAgent()
    
    # Create table
    agent.create_final_recommendations_table()
    
    # Run analysis
    result = agent.analyze_and_coordinate(hours_back=24)
    
    print(f"\n📋 Analysis Results:")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Processing time: {result['processing_time_seconds']:.2f} seconds")
        print(f"Recommendations generated: {result['recommendations_generated']}")
        print(f"Data sources analyzed: {result['data_sources_analyzed']}")
        
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"{i}. {rec['recommendation_title']} (Priority: {rec['business_priority_rank']})")
            print(f"   {rec['recommendation_description']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()