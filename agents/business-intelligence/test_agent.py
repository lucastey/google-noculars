#!/usr/bin/env python3
"""
Test Suite for ADK-based Business Intelligence Agent - Google Noculars
Tests AI-powered business intelligence analysis functionality with full BigQuery scope
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Add the project root to the path for proper imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from agents.business_intelligence.agent import (
        get_behavioral_patterns_for_analysis,
        create_business_insights_table,
        generate_business_insights,
        store_business_insights,
        business_intelligence_agent
    )
except ImportError:
    # Fallback to local import if running from agent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from agent import (
        get_behavioral_patterns_for_analysis,
        create_business_insights_table,
        generate_business_insights,
        store_business_insights,
        business_intelligence_agent
    )

class TestADKBusinessIntelligenceAgent(unittest.TestCase):
    """Test cases for ADK-based Business Intelligence Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_behavioral_data = {
            'patterns': [
                {
                    'session_id': 'test_session_1',
                    'page_url': 'https://example.com/product',
                    'session_duration_seconds': 180.0,
                    'total_events': 45,
                    'bounce_session': False,
                    'engagement_score': 65.0,
                    'frustration_indicators': 1,
                    'click_rate_per_minute': 2.5,
                    'max_scroll_depth_percent': 85.0,
                    'task_completion_likelihood': 0.7,
                    'device_type': 'desktop',
                    'analysis_timestamp': datetime.utcnow()
                },
                {
                    'session_id': 'test_session_2',
                    'page_url': 'https://example.com/landing',
                    'session_duration_seconds': 25.0,
                    'total_events': 3,
                    'bounce_session': True,
                    'engagement_score': 15.0,
                    'frustration_indicators': 0,
                    'click_rate_per_minute': 0.0,
                    'max_scroll_depth_percent': 20.0,
                    'task_completion_likelihood': 0.1,
                    'device_type': 'mobile',
                    'analysis_timestamp': datetime.utcnow()
                }
            ],
            'summary': {
                'total_sessions': 2,
                'high_engagement_sessions': 1,
                'bounce_sessions': 1,
                'frustrated_sessions': 0,
                'bounce_rate': 0.5,
                'frustration_rate': 0.0,
                'engagement_rate': 0.5
            },
            'status': 'success'
        }
    
    @patch('agent.bigquery.Client')
    def test_get_behavioral_patterns_for_analysis(self, mock_bigquery_client):
        """Test behavioral patterns data retrieval"""
        # Mock BigQuery client and results
        mock_client_instance = Mock()
        mock_bigquery_client.return_value = mock_client_instance
        
        mock_query_job = Mock()
        mock_client_instance.query.return_value = mock_query_job
        
        # Create mock rows that behave like BigQuery Row objects
        class MockRow:
            def __init__(self, data_dict):
                for key, value in data_dict.items():
                    setattr(self, key, value)
                self._data = data_dict
            
            def __iter__(self):
                return iter(self._data.items())
            
            def __getitem__(self, key):
                return self._data[key]
            
            def get(self, key, default=None):
                return self._data.get(key, default)
            
            def keys(self):
                return self._data.keys()
            
            def values(self):
                return self._data.values()
            
            def items(self):
                return self._data.items()
        
        mock_rows = [MockRow(pattern) for pattern in self.mock_behavioral_data['patterns']]
        mock_query_job.result.return_value = mock_rows
        
        # Test the function
        result = get_behavioral_patterns_for_analysis(24)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['patterns']), 2)
        self.assertIn('summary', result)
        self.assertEqual(result['summary']['total_sessions'], 2)
        
        print("✅ Behavioral patterns retrieval test passed")
    
    @patch('agent.bigquery.Client')
    def test_create_business_insights_table(self, mock_bigquery_client):
        """Test business insights table creation"""
        # Mock BigQuery client
        mock_client_instance = Mock()
        mock_bigquery_client.return_value = mock_client_instance
        
        mock_query_job = Mock()
        mock_client_instance.query.return_value = mock_query_job
        mock_query_job.result.return_value = None
        
        # Mock file reading
        with patch('builtins.open', unittest.mock.mock_open(read_data="CREATE TABLE test")):
            result = create_business_insights_table()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('successfully', result['message'])
        
        print("✅ Business insights table creation test passed")
    
    def test_generate_business_insights(self):
        """Test business insights generation"""
        result = generate_business_insights(self.mock_behavioral_data)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['total_insights_generated'], 2)
        self.assertIn('insights', result)
        
        # Check insight structure
        insight = result['insights'][0]
        self.assertIn('session_id', insight)
        self.assertIn('source_engagement_score', insight)
        self.assertIn('funnel_stage', insight)
        self.assertIn('recommended_actions', insight)
        
        print("✅ Business insights generation test passed")
    
    @patch('agent.bigquery.Client')
    def test_store_business_insights(self, mock_bigquery_client):
        """Test business insights storage"""
        # Mock BigQuery client
        mock_client_instance = Mock()
        mock_bigquery_client.return_value = mock_client_instance
        
        mock_dataset = Mock()
        mock_table_ref = Mock()
        mock_client_instance.dataset.return_value = mock_dataset
        mock_dataset.table.return_value = mock_table_ref
        
        # Mock successful insertion
        mock_client_instance.insert_rows_json.return_value = []
        
        # Generate test insights
        insights_data = generate_business_insights(self.mock_behavioral_data)
        
        # Test storage
        result = store_business_insights(insights_data)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['insights_stored'], 2)
        
        print("✅ Business insights storage test passed")
    
    def test_adk_agent_structure(self):
        """Test ADK agent structure and configuration"""
        # Check agent properties
        self.assertEqual(business_intelligence_agent.name, 'business_intelligence_agent')
        self.assertEqual(business_intelligence_agent.model, 'gemini-2.0-flash-001')
        self.assertIsNotNone(business_intelligence_agent.description)
        self.assertIsNotNone(business_intelligence_agent.instruction)
        
        # Check tools are properly configured
        self.assertEqual(len(business_intelligence_agent.tools), 4)
        
        tool_names = [tool.func.__name__ for tool in business_intelligence_agent.tools]
        expected_tools = [
            'get_behavioral_patterns_for_analysis',
            'create_business_insights_table',
            'generate_business_insights',
            'store_business_insights'
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, tool_names)
        
        print("✅ ADK agent structure test passed")
    
    def test_no_data_handling(self):
        """Test handling of empty data scenarios"""
        # Test with no patterns
        empty_data = {
            'patterns': [],
            'summary': {},
            'status': 'success'
        }
        
        result = generate_business_insights(empty_data)
        self.assertEqual(result['status'], 'no_data')
        self.assertEqual(len(result['insights']), 0)
        
        # Test storing empty insights
        empty_insights = {'insights': []}
        storage_result = store_business_insights(empty_insights)
        self.assertEqual(storage_result['status'], 'no_data')
        
        print("✅ No data handling test passed")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with malformed data
        bad_data = {'invalid': 'structure'}
        result = generate_business_insights(bad_data)
        
        # Should handle gracefully
        self.assertIn(result['status'], ['no_data', 'error'])
        
        print("✅ Error handling test passed")
    
    def test_insight_data_structure(self):
        """Test the structure of generated insights"""
        result = generate_business_insights(self.mock_behavioral_data)
        
        if result['status'] == 'success' and result['insights']:
            insight = result['insights'][0]
            
            # Required fields for AI analysis
            required_fields = [
                'session_id', 'page_url', 'analysis_timestamp',
                'source_engagement_score', 'source_frustration_indicators', 'source_session_duration',
                'funnel_stage', 'conversion_probability', 'user_segment',
                'optimization_priority', 'recommended_actions', 'business_impact_estimate'
            ]
            
            for field in required_fields:
                self.assertIn(field, insight)
            
            # Check data types
            self.assertIsInstance(insight['source_engagement_score'], (int, float))
            self.assertIsInstance(insight['conversion_probability'], (int, float))
            
            # Check JSON fields
            try:
                json.loads(insight['recommended_actions'])
            except json.JSONDecodeError:
                self.fail("recommended_actions should be valid JSON")
        
        print("✅ Insight data structure test passed")

def run_integration_test():
    """Run integration test with mocked components"""
    print("\n🧪 Running ADK Business Intelligence Agent Integration Test...")
    
    # Mock all BigQuery operations
    with patch('agent.bigquery.Client') as mock_client:
        # Mock the BigQuery client
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        # Mock query results for pattern retrieval
        mock_query_job = Mock()
        mock_client_instance.query.return_value = mock_query_job
        
        # Create test data
        test_pattern = {
            'session_id': 'integration_test_session',
            'page_url': 'https://example.com/integration-test',
            'session_duration_seconds': 240.0,
            'total_events': 55,
            'bounce_session': False,
            'engagement_score': 78.0,
            'frustration_indicators': 2,
            'click_rate_per_minute': 3.2,
            'max_scroll_depth_percent': 92.0,
            'task_completion_likelihood': 0.8,
            'device_type': 'desktop',
            'analysis_timestamp': datetime.utcnow()
        }
        
        # Create MockRow for integration test (same as unit test)
        class MockRow:
            def __init__(self, data_dict):
                for key, value in data_dict.items():
                    setattr(self, key, value)
                self._data = data_dict
            
            def __iter__(self):
                return iter(self._data.items())
            
            def __getitem__(self, key):
                return self._data[key]
            
            def get(self, key, default=None):
                return self._data.get(key, default)
            
            def keys(self):
                return self._data.keys()
            
            def values(self):
                return self._data.values()
            
            def items(self):
                return self._data.items()
        
        mock_query_job.result.return_value = [MockRow(test_pattern)]
        
        # Mock table operations
        mock_dataset = Mock()
        mock_table_ref = Mock()
        mock_client_instance.dataset.return_value = mock_dataset
        mock_dataset.table.return_value = mock_table_ref
        mock_client_instance.insert_rows_json.return_value = []
        
        # Mock file reading for schema
        schema_content = "CREATE TABLE IF NOT EXISTS test_table (id STRING);"
        with patch('builtins.open', unittest.mock.mock_open(read_data=schema_content)):
            # Test the complete workflow
            print("📊 Step 1: Retrieving behavioral patterns...")
            patterns_data = get_behavioral_patterns_for_analysis(24)
            
            print("🏗️ Step 2: Creating business insights table...")
            table_result = create_business_insights_table()
            
            print("🧠 Step 3: Generating business insights...")
            insights_result = generate_business_insights(patterns_data)
            
            print("💾 Step 4: Storing business insights...")
            storage_result = store_business_insights(insights_result)
            
            # Verify results
            assert patterns_data['status'] == 'success'
            assert table_result['status'] == 'success'
            assert insights_result['status'] == 'success'
            assert storage_result['status'] == 'success'
            
            print("✅ Integration test completed successfully")
            print(f"📊 Retrieved: {len(patterns_data['patterns'])} patterns")
            print(f"💡 Generated: {insights_result['total_insights_generated']} insights")
            print(f"💾 Stored: {storage_result['insights_stored']} insights")
            
            # Display sample insight
            if insights_result['insights']:
                sample_insight = insights_result['insights'][0]
                print(f"\n📋 Sample Insight for session: {sample_insight['session_id']}")
                print(f"   Engagement Score: {sample_insight['source_engagement_score']}")
                print(f"   Funnel Stage: {sample_insight['funnel_stage']}")
                print(f"   User Segment: {sample_insight['user_segment']}")
                print(f"   Priority: {sample_insight['optimization_priority']}")
                
            print(f"\n🤖 Note: This is the baseline functionality. The ADK agent will enhance these insights with:")
            print(f"   • Advanced AI reasoning and contextual analysis")
            print(f"   • Sophisticated business impact calculations")
            print(f"   • Nuanced user segmentation and recommendations")
            print(f"   • Strategic business insights beyond rule-based analysis")

def main():
    """Main test execution"""
    print("🧪 Running ADK-based Business Intelligence Agent Tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration test
    run_integration_test()
    
    print("\n🎉 All ADK Business Intelligence Agent tests completed!")

if __name__ == "__main__":
    main()