#!/usr/bin/env python3
"""
Integration Tests for Insights Engine Agent
Tests the complete workflow with mocked BigQuery and ADK dependencies
"""

import unittest
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import agent and utilities
try:
    from agent import InsightsEngineAgent
    from utils.data_retrieval import get_pattern_recognition_data, get_business_intelligence_data, get_ab_testing_data
    from utils.bigquery_ops import upsert_final_recommendations
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure Google ADK and cloud libraries are installed")
    sys.exit(1)


class MockRow:
    """Mock BigQuery row object for testing"""
    def __init__(self, data_dict):
        for key, value in data_dict.items():
            setattr(self, key, value)
        self._data = data_dict
    
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
    
    def __iter__(self):
        return iter(self._data)


class TestInsightsEngineIntegration(unittest.TestCase):
    """Integration tests for complete insights engine workflow"""
    
    def setUp(self):
        """Set up comprehensive test fixtures"""
        self.comprehensive_pattern_data = [
            {
                'session_id': 'session_001',
                'page_url': 'https://example.com/page1',
                'engagement_score': 65,
                'frustration_indicators': 3,
                'user_segment': 'premium',
                'analysis_timestamp': '2024-01-01T10:00:00Z'
            },
            {
                'session_id': 'session_002',
                'page_url': 'https://example.com/page1',
                'engagement_score': 45,
                'frustration_indicators': 4,
                'user_segment': 'standard',
                'analysis_timestamp': '2024-01-01T10:15:00Z'
            },
            {
                'session_id': 'session_003',
                'page_url': 'https://example.com/page2',
                'engagement_score': 85,
                'frustration_indicators': 1,
                'user_segment': 'premium',
                'analysis_timestamp': '2024-01-01T10:30:00Z'
            }
        ]
        
        self.comprehensive_business_data = [
            {
                'session_id': 'session_001',
                'page_url': 'https://example.com/page1',
                'conversion_probability': 0.35,
                'estimated_revenue_impact': 250.0,
                'funnel_stage': 'consideration',
                'analysis_timestamp': '2024-01-01T10:00:00Z'
            },
            {
                'session_id': 'session_002',
                'page_url': 'https://example.com/page1',
                'conversion_probability': 0.25,
                'estimated_revenue_impact': 150.0,
                'funnel_stage': 'entry',
                'analysis_timestamp': '2024-01-01T10:15:00Z'
            },
            {
                'session_id': 'session_003',
                'page_url': 'https://example.com/page2',
                'conversion_probability': 0.75,
                'estimated_revenue_impact': 800.0,
                'funnel_stage': 'decision',
                'analysis_timestamp': '2024-01-01T10:30:00Z'
            }
        ]
        
        self.ab_test_data = [
            {
                'test_id': 'ab_test_001',
                'page_url': 'https://example.com/page1',
                'winning_variant': 'B',
                'statistical_confidence': 0.92,
                'conversion_lift': 0.18,
                'analysis_timestamp': '2024-01-01T09:00:00Z'
            }
        ]
    
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_agent_initialization_success(self, mock_open, mock_get_client):
        """Test successful agent initialization with mocked dependencies"""
        # Mock BigQuery client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock schema file reading
        mock_open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE..."
        
        # Initialize agent
        agent = InsightsEngineAgent()
        
        # Verify initialization
        self.assertIsNotNone(agent.client)
        self.assertIsNotNone(agent.agent)
        self.assertIsNotNone(agent.dataset)
        mock_get_client.assert_called_once()
    
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_table_creation_success(self, mock_open, mock_get_client):
        """Test table creation workflow"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock schema file content
        schema_content = """
        CREATE TABLE `ux_insights.final_recommendations` (
            page_url STRING,
            recommendation_category STRING,
            created_at TIMESTAMP
        )
        """
        mock_open.return_value.__enter__.return_value.read.return_value = schema_content
        
        # Mock successful query execution
        mock_client.query.return_value.result.return_value = None
        
        agent = InsightsEngineAgent()
        agent.create_final_recommendations_table()
        
        # Verify table creation was attempted
        mock_client.query.assert_called()
        query_call_args = mock_client.query.call_args[0][0]
        self.assertIn('CREATE TABLE', query_call_args)
    
    @patch('utils.data_retrieval.get_bigquery_client')
    def test_data_retrieval_functions(self, mock_get_client):
        """Test all data retrieval functions work correctly"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Test pattern recognition data retrieval
        mock_client.query.return_value.result.return_value = [
            MockRow(data) for data in self.comprehensive_pattern_data
        ]
        pattern_result = get_pattern_recognition_data(hours_back=24)
        self.assertEqual(len(pattern_result), 3)
        self.assertEqual(pattern_result[0]['session_id'], 'session_001')
        
        # Test business intelligence data retrieval
        mock_client.query.return_value.result.return_value = [
            MockRow(data) for data in self.comprehensive_business_data
        ]
        business_result = get_business_intelligence_data(hours_back=24)
        self.assertEqual(len(business_result), 3)
        self.assertEqual(business_result[0]['conversion_probability'], 0.35)
        
        # Test A/B testing data retrieval
        mock_client.query.return_value.result.return_value = [
            MockRow(data) for data in self.ab_test_data
        ]
        ab_result = get_ab_testing_data(hours_back=168)
        self.assertEqual(len(ab_result), 1)
        self.assertEqual(ab_result[0]['winning_variant'], 'B')
    
    @patch('utils.bigquery_ops.get_bigquery_client')
    def test_recommendation_upsert_insert(self, mock_get_client):
        """Test recommendation insertion workflow"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock no existing recommendations (insert scenario)
        mock_client.query.return_value.result.return_value = []
        
        # Mock successful insertion
        mock_client.insert_rows_json.return_value = []
        
        test_recommendation = {
            'page_url': 'https://example.com/test',
            'recommendation_category': 'ui_design',
            'recommendation_id': 'rec_test123',
            'business_priority_rank': 15,
            'insight_confidence': 0.85
        }
        
        result = upsert_final_recommendations([test_recommendation])
        
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(len(result['errors']), 0)
        mock_client.insert_rows_json.assert_called_once()
    
    @patch('utils.bigquery_ops.get_bigquery_client')
    def test_recommendation_upsert_update(self, mock_get_client):
        """Test recommendation update workflow"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock existing recommendation (update scenario)
        existing_row = MockRow({
            'recommendation_id': 'rec_test123',
            'sessions_analyzed_count': 20,
            'sessions_analyzed_list': '["old_session"]',
            'last_updated': '2024-01-01T00:00:00Z'
        })
        
        # Mock query results: first call returns existing row, second call is update
        mock_query_result = MagicMock()
        mock_query_result.result.return_value = [existing_row]
        mock_client.query.return_value = mock_query_result
        
        test_recommendation = {
            'page_url': 'https://example.com/test',
            'recommendation_category': 'ui_design',
            'sessions_analyzed_list': ['new_session'],
            'business_priority_rank': 20
        }
        
        result = upsert_final_recommendations([test_recommendation])
        
        self.assertEqual(result['updated'], 1)
        self.assertEqual(result['inserted'], 0)
    
    @patch('agent.upsert_final_recommendations')
    @patch('agent.get_existing_recommendations')
    @patch('agent.get_ab_testing_data')
    @patch('agent.get_business_intelligence_data')
    @patch('agent.get_pattern_recognition_data')
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_full_analysis_workflow_success(self, mock_open, mock_get_client, 
                                          mock_pattern, mock_business, mock_ab, 
                                          mock_existing, mock_upsert):
        """Test complete analysis workflow with realistic data"""
        # Setup all mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE..."
        
        # Mock data retrieval
        mock_pattern.return_value = self.comprehensive_pattern_data
        mock_business.return_value = self.comprehensive_business_data
        mock_ab.return_value = self.ab_test_data
        mock_existing.return_value = []
        
        # Mock successful upsert
        mock_upsert.return_value = {'inserted': 3, 'updated': 0, 'errors': []}
        
        # Run analysis
        agent = InsightsEngineAgent()
        result = agent.analyze_and_coordinate(hours_back=24)
        
        # Verify successful result structure
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['pages_analyzed'], 2)  # 2 unique pages
        self.assertGreater(result['recommendations_generated'], 0)
        self.assertIn('processing_time_seconds', result)
        self.assertGreater(result['processing_time_seconds'], 0)
        
        # Verify data source counts
        self.assertEqual(result['data_sources_analyzed']['behavioral_patterns'], 3)
        self.assertEqual(result['data_sources_analyzed']['business_insights'], 3)
        self.assertEqual(result['data_sources_analyzed']['ab_tests'], 1)
        
        # Verify function calls
        mock_pattern.assert_called_with(hours_back=24)
        mock_business.assert_called_with(hours_back=24)
        mock_ab.assert_called_with(hours_back=168)  # 24 * 7 for A/B tests
        mock_upsert.assert_called()
    
    @patch('agent.get_pattern_recognition_data')
    @patch('agent.get_business_intelligence_data')
    @patch('agent.get_ab_testing_data')
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_no_data_handling(self, mock_open, mock_get_client, mock_ab, mock_business, mock_pattern):
        """Test graceful handling of no data scenarios"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE..."
        
        # Return empty data
        mock_pattern.return_value = []
        mock_business.return_value = []
        mock_ab.return_value = []
        
        agent = InsightsEngineAgent()
        result = agent.analyze_and_coordinate(hours_back=24)
        
        self.assertEqual(result['status'], 'no_data')
        self.assertEqual(result['recommendations'], [])
    
    @patch('agent.get_pattern_recognition_data')
    @patch('agent.get_business_intelligence_data')
    @patch('agent.get_ab_testing_data')
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_error_handling(self, mock_open, mock_get_client, mock_ab, mock_business, mock_pattern):
        """Test error handling in analysis workflow"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE..."
        
        # Simulate data retrieval error
        mock_pattern.side_effect = Exception("Database connection failed")
        mock_business.return_value = []
        mock_ab.return_value = []
        
        agent = InsightsEngineAgent()
        result = agent.analyze_and_coordinate(hours_back=24)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['recommendations'], [])
    
    @patch('agent.upsert_final_recommendations')
    @patch('agent.get_existing_recommendations')
    @patch('agent.get_ab_testing_data')
    @patch('agent.get_business_intelligence_data')
    @patch('agent.get_pattern_recognition_data')
    @patch('agent.get_bigquery_client')
    @patch('builtins.open')
    def test_recommendation_quality_metrics(self, mock_open, mock_get_client, 
                                          mock_pattern, mock_business, mock_ab, 
                                          mock_existing, mock_upsert):
        """Test that generated recommendations have proper quality metrics"""
        # Setup mocks
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_open.return_value.__enter__.return_value.read.return_value = "CREATE TABLE..."
        
        mock_pattern.return_value = self.comprehensive_pattern_data
        mock_business.return_value = self.comprehensive_business_data
        mock_ab.return_value = self.ab_test_data
        mock_existing.return_value = []
        
        # Capture the recommendations passed to upsert
        captured_recommendations = []
        def capture_upsert(recommendations):
            captured_recommendations.extend(recommendations)
            return {'inserted': len(recommendations), 'updated': 0, 'errors': []}
        
        mock_upsert.side_effect = capture_upsert
        
        # Run analysis
        agent = InsightsEngineAgent()
        result = agent.analyze_and_coordinate(hours_back=24)
        
        # Verify recommendations were generated
        self.assertGreater(len(captured_recommendations), 0)
        
        # Check quality of first recommendation
        first_rec = captured_recommendations[0]
        
        # Verify required fields exist
        required_fields = [
            'page_url', 'recommendation_category', 'recommendation_id',
            'business_priority_rank', 'insight_confidence', 'recommendation_title',
            'recommendation_description', 'evidence_strength_score'
        ]
        for field in required_fields:
            self.assertIn(field, first_rec, f"Missing required field: {field}")
        
        # Verify data quality
        self.assertIsInstance(first_rec['business_priority_rank'], (int, float))
        self.assertGreaterEqual(first_rec['business_priority_rank'], 1)
        self.assertLessEqual(first_rec['business_priority_rank'], 100)
        
        self.assertIsInstance(first_rec['insight_confidence'], (int, float))
        self.assertGreaterEqual(first_rec['insight_confidence'], 0)
        self.assertLessEqual(first_rec['insight_confidence'], 1)
        
        self.assertTrue(first_rec['recommendation_title'])
        self.assertTrue(first_rec['recommendation_description'])


def run_tests():
    """Run all integration test suites with detailed reporting"""
    print("🧪 Running Insights Engine Integration Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test class
    tests = unittest.TestLoader().loadTestsFromTestCase(TestInsightsEngineIntegration)
    test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Print failed tests details
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\n🚨 ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
            error_line = traceback.split(chr(10))[-2] if traceback.split(chr(10)) else "Unknown error"
            print(f"    {error_line}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ All integration tests passed successfully!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} tests failed")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)