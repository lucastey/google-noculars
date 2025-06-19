#!/usr/bin/env python3
"""
Test Suite for A/B Testing Analysis Agent - Google Noculars
Tests statistical analysis and A/B testing functionality with full BigQuery scope
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import math
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path for proper imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from agents.ab_testing.agent import (
        get_business_insights_for_ab_testing,
        create_ab_test_results_table,
        analyze_ab_test_performance,
        store_ab_test_results,
        ab_testing_agent,
        _calculate_statistical_significance,
        _calculate_confidence_interval,
        _determine_winner_probability,
        _calculate_variant_metrics,
        _generate_ab_test_recommendation
    )
except ImportError:
    # Fallback to local import if running from agent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from agent import (
        get_business_insights_for_ab_testing,
        create_ab_test_results_table,
        analyze_ab_test_performance,
        store_ab_test_results,
        ab_testing_agent,
        _calculate_statistical_significance,
        _calculate_confidence_interval,
        _determine_winner_probability,
        _calculate_variant_metrics,
        _generate_ab_test_recommendation
    )

class TestABTestingAnalysisAgent(unittest.TestCase):
    """Test cases for A/B Testing Analysis Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_business_insights = {
            'insights': [
                {
                    'session_id': 'session_1',
                    'page_url': 'https://example.com/product',
                    'analysis_timestamp': '2024-01-15T10:00:00',
                    'conversion_probability': 0.65,
                    'estimated_revenue_impact': 45.0,
                    'user_segment': 'power_user',
                    'funnel_stage': 'intent',
                    'engagement_score': 75.0,
                    'goal_completion_rate': 0.8,
                    'macro_conversion_indicator': True,
                    'optimization_priority': 'high',
                    'session_duration': 180.0
                },
                {
                    'session_id': 'session_2',
                    'page_url': 'https://example.com/product',
                    'analysis_timestamp': '2024-01-15T10:05:00',
                    'conversion_probability': 0.35,
                    'estimated_revenue_impact': 12.0,
                    'user_segment': 'standard_user',
                    'funnel_stage': 'engagement',
                    'engagement_score': 45.0,
                    'goal_completion_rate': 0.3,
                    'macro_conversion_indicator': False,
                    'optimization_priority': 'medium',
                    'session_duration': 120.0
                },
                {
                    'session_id': 'session_3',
                    'page_url': 'https://example.com/landing',
                    'analysis_timestamp': '2024-01-15T10:10:00',
                    'conversion_probability': 0.85,
                    'estimated_revenue_impact': 78.0,
                    'user_segment': 'power_user',
                    'funnel_stage': 'conversion',
                    'engagement_score': 90.0,
                    'goal_completion_rate': 0.95,
                    'macro_conversion_indicator': True,
                    'optimization_priority': 'high',
                    'session_duration': 300.0
                },
                {
                    'session_id': 'session_4',
                    'page_url': 'https://example.com/landing',
                    'analysis_timestamp': '2024-01-15T10:15:00',
                    'conversion_probability': 0.25,
                    'estimated_revenue_impact': 5.0,
                    'user_segment': 'new_user',
                    'funnel_stage': 'entry',
                    'engagement_score': 30.0,
                    'goal_completion_rate': 0.1,
                    'macro_conversion_indicator': False,
                    'optimization_priority': 'low',
                    'session_duration': 60.0
                }
            ],
            'summary': {
                'total_sessions': 4,
                'total_conversions': 2,
                'overall_conversion_rate': 0.5,
                'total_revenue': 140.0,
                'average_revenue_per_session': 35.0,
                'time_range_hours': 168
            }
        }
        
        self.mock_config = {
            'ab_test_config': {
                'statistical_settings': {
                    'confidence_level': 0.95,
                    'minimum_sample_size': 100,
                    'minimum_detectable_effect': 0.05,
                    'power': 0.80,
                    'alpha': 0.05
                },
                'significance_thresholds': {
                    'statistical_significance': 0.95,
                    'business_significance': {
                        'high': 0.10,
                        'medium': 0.05,
                        'low': 0.02
                    },
                    'winner_probability': 0.90
                }
            }
        }

    @patch('agents.ab_testing.agent._get_bigquery_client')
    def test_get_business_insights_for_ab_testing_success(self, mock_get_client):
        """Test successful retrieval of business insights for A/B testing"""
        # Mock BigQuery client and results
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock query results
        mock_row = MagicMock()
        mock_row.session_id = 'test_session_1'
        mock_row.page_url = 'https://example.com/test'
        mock_row.analysis_timestamp = datetime.now()
        mock_row.conversion_probability = 0.65
        mock_row.estimated_revenue_impact = 45.0
        mock_row.user_segment = 'power_user'
        mock_row.funnel_stage = 'intent'
        mock_row.source_engagement_score = 75.0
        mock_row.goal_completion_rate = 0.8
        mock_row.macro_conversion_indicator = True
        mock_row.optimization_priority = 'high'
        mock_row.source_session_duration = 180.0
        
        mock_client.query.return_value.result.return_value = [mock_row]
        
        # Test the function
        result = get_business_insights_for_ab_testing(24)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['insights']), 1)
        self.assertEqual(result['insights'][0]['session_id'], 'test_session_1')
        self.assertEqual(result['insights'][0]['conversion_probability'], 0.65)
        self.assertEqual(result['summary']['total_sessions'], 1)
        self.assertEqual(result['summary']['total_conversions'], 1)

    @patch('agents.ab_testing.agent._get_bigquery_client')
    def test_create_ab_test_results_table_success(self, mock_get_client):
        """Test successful creation of A/B test results table"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.query.return_value.result.return_value = None
        
        with patch('builtins.open', mock_open_schema_file()):
            result = create_ab_test_results_table()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('created successfully', result['message'])

    def test_calculate_statistical_significance(self):
        """Test statistical significance calculation"""
        # Test case: significant result
        result = _calculate_statistical_significance(50, 1000, 65, 1000)
        
        self.assertIsInstance(result['p_value'], float)
        self.assertIsInstance(result['z_score'], float)
        self.assertIsInstance(result['significance'], float)
        self.assertGreater(result['z_score'], 0)  # Variant performs better
        self.assertLess(result['p_value'], 0.05)  # Should be significant
        
        # Test case: no difference
        result_no_diff = _calculate_statistical_significance(50, 1000, 50, 1000)
        self.assertAlmostEqual(result_no_diff['z_score'], 0.0, places=2)
        self.assertAlmostEqual(result_no_diff['p_value'], 1.0, places=1)

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation"""
        result = _calculate_confidence_interval(50, 1000, 0.95)
        
        self.assertIsInstance(result['lower'], float)
        self.assertIsInstance(result['upper'], float)
        self.assertLess(result['lower'], 0.05)  # True rate is 5%
        self.assertGreater(result['upper'], 0.05)
        self.assertLess(result['lower'], result['upper'])
        
        # Test edge case: no conversions
        result_zero = _calculate_confidence_interval(0, 1000, 0.95)
        self.assertEqual(result_zero['lower'], 0.0)
        self.assertGreater(result_zero['upper'], 0.0)

    def test_determine_winner_probability(self):
        """Test winner probability calculation"""
        # Test variant clearly better
        prob_higher = _determine_winner_probability(0.05, 0.08, 1000, 1000)
        self.assertGreater(prob_higher, 0.5)
        
        # Test control better
        prob_lower = _determine_winner_probability(0.08, 0.05, 1000, 1000)
        self.assertLess(prob_lower, 0.5)
        
        # Test equal rates
        prob_equal = _determine_winner_probability(0.05, 0.05, 1000, 1000)
        self.assertAlmostEqual(prob_equal, 0.5, places=1)

    def test_calculate_variant_metrics(self):
        """Test variant metrics calculation"""
        sessions = [
            {'macro_conversion_indicator': True, 'estimated_revenue_impact': 45, 'engagement_score': 75, 'session_duration': 180},
            {'macro_conversion_indicator': False, 'estimated_revenue_impact': 12, 'engagement_score': 45, 'session_duration': 120},
        ]
        
        metrics = _calculate_variant_metrics(sessions, 'test_variant')
        
        self.assertEqual(metrics['variant_name'], 'test_variant')
        self.assertEqual(metrics['sessions'], 2)
        self.assertEqual(metrics['conversions'], 1)
        self.assertEqual(metrics['conversion_rate'], 0.5)
        self.assertEqual(metrics['revenue'], 57.0)
        self.assertEqual(metrics['revenue_per_session'], 28.5)
        self.assertEqual(metrics['avg_engagement'], 60.0)
        self.assertEqual(metrics['avg_session_duration'], 150.0)

    def test_generate_ab_test_recommendation(self):
        """Test A/B test recommendation generation"""
        # Test case: clear winner
        stats = {'significance': 0.95, 'p_value': 0.01}
        recommendation = _generate_ab_test_recommendation(stats, 15.0, 0.92, True, self.mock_config)
        
        self.assertEqual(recommendation['action'], 'implement')
        self.assertGreater(recommendation['confidence'], 0.8)
        self.assertIn('lift', recommendation['rationale'])
        
        # Test case: inconclusive
        stats_inconclusive = {'significance': 0.3, 'p_value': 0.15}
        recommendation_inc = _generate_ab_test_recommendation(stats_inconclusive, 2.0, 0.6, False, self.mock_config)
        
        self.assertEqual(recommendation_inc['action'], 'extend')
        self.assertLess(recommendation_inc['confidence'], 0.7)

    @patch('agents.ab_testing.agent._load_config')
    def test_analyze_ab_test_performance_success(self, mock_load_config):
        """Test successful A/B test performance analysis"""
        mock_load_config.return_value = self.mock_config
        
        test_data = {
            'status': 'success',
            'insights': self.mock_business_insights['insights'],
            'summary': self.mock_business_insights['summary']
        }
        
        result = analyze_ab_test_performance(test_data)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertIn('analysis', result)
        
        analysis = result['analysis']
        self.assertIn('test_id', analysis)
        self.assertIn('control_metrics', analysis)
        self.assertIn('variant_metrics', analysis)
        self.assertIn('statistical_analysis', analysis)
        self.assertIn('lift_percent', analysis)
        self.assertIn('winner_probability', analysis)
        self.assertIn('recommendation', analysis)
        
        # Verify metrics structure
        self.assertIn('sessions', analysis['control_metrics'])
        self.assertIn('conversion_rate', analysis['control_metrics'])
        self.assertIn('revenue', analysis['control_metrics'])

    @patch('agents.ab_testing.agent._get_bigquery_client')
    def test_store_ab_test_results_success(self, mock_get_client):
        """Test successful storage of A/B test results"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.insert_rows_json.return_value = []  # No errors
        
        # Mock analysis data
        analysis_data = {
            'status': 'success',
            'analysis': {
                'test_id': 'test_123',
                'test_name': 'Test Campaign',
                'control_metrics': {
                    'sessions': 100,
                    'conversions': 10,
                    'conversion_rate': 0.1,
                    'revenue': 500.0,
                    'revenue_per_session': 5.0,
                    'avg_engagement': 60.0,
                    'avg_session_duration': 150.0
                },
                'variant_metrics': {
                    'sessions': 100,
                    'conversions': 15,
                    'conversion_rate': 0.15,
                    'revenue': 750.0,
                    'revenue_per_session': 7.5,
                    'avg_engagement': 70.0,
                    'avg_session_duration': 180.0
                },
                'statistical_analysis': {
                    'significance': 0.95,
                    'p_value': 0.02,
                    'z_score': 2.1
                },
                'lift_percent': 50.0,
                'winner_probability': 0.92,
                'business_significant': True,
                'recommendation': {
                    'action': 'implement',
                    'confidence': 0.9,
                    'next_steps': ['Deploy variant', 'Monitor results']
                }
            }
        }
        
        result = store_ab_test_results(analysis_data)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertIn('Successfully stored', result['message'])
        self.assertEqual(result['records_inserted'], 2)  # Control + variant
        
        # Verify BigQuery insertion was called
        mock_client.insert_rows_json.assert_called_once()

class TestIntegrationABTestingAgent(unittest.TestCase):
    """Integration tests for A/B Testing Analysis Agent workflow"""
    
    @patch('agents.ab_testing.agent._get_bigquery_client')
    @patch('agents.ab_testing.agent._load_config')
    def test_full_workflow_integration(self, mock_load_config, mock_get_client):
        """Test complete A/B testing analysis workflow"""
        # Setup mocks
        mock_config = {
            'ab_test_config': {
                'statistical_settings': {'confidence_level': 0.95},
                'significance_thresholds': {
                    'statistical_significance': 0.95,
                    'business_significance': {'medium': 0.05},
                    'winner_probability': 0.90
                }
            }
        }
        mock_load_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock BigQuery responses
        mock_row1 = create_mock_insight_row('session_1', True, 45.0, 75.0)
        mock_row2 = create_mock_insight_row('session_2', False, 12.0, 45.0) 
        mock_row3 = create_mock_insight_row('session_3', True, 78.0, 90.0)
        mock_row4 = create_mock_insight_row('session_4', False, 5.0, 30.0)
        
        mock_client.query.return_value.result.return_value = [mock_row1, mock_row2, mock_row3, mock_row4]
        mock_client.insert_rows_json.return_value = []
        
        # Test complete workflow
        with patch('builtins.open', mock_open_schema_file()):
            # 1. Get business insights
            insights = get_business_insights_for_ab_testing(168)
            self.assertEqual(insights['status'], 'success')
            
            # 2. Create table
            table_result = create_ab_test_results_table()
            self.assertEqual(table_result['status'], 'success')
            
            # 3. Analyze performance
            analysis = analyze_ab_test_performance(insights)
            self.assertEqual(analysis['status'], 'success')
            
            # 4. Store results
            storage = store_ab_test_results(analysis)
            self.assertEqual(storage['status'], 'success')
        
        print("✅ Full A/B Testing workflow integration test passed")

def create_mock_insight_row(session_id: str, conversion: bool, revenue: float, engagement: float):
    """Helper function to create mock BigQuery row"""
    mock_row = MagicMock()
    mock_row.session_id = session_id
    mock_row.page_url = 'https://example.com/test'
    mock_row.analysis_timestamp = datetime.now()
    mock_row.conversion_probability = 0.65 if conversion else 0.35
    mock_row.estimated_revenue_impact = revenue
    mock_row.user_segment = 'power_user' if conversion else 'standard_user'
    mock_row.funnel_stage = 'conversion' if conversion else 'engagement'
    mock_row.source_engagement_score = engagement
    mock_row.goal_completion_rate = 0.8 if conversion else 0.3
    mock_row.macro_conversion_indicator = conversion
    mock_row.optimization_priority = 'high' if conversion else 'medium'
    mock_row.source_session_duration = 180.0 if conversion else 120.0
    return mock_row

def mock_open_schema_file():
    """Mock file opening for schema.sql"""
    from unittest.mock import mock_open
    schema_content = "CREATE TABLE IF NOT EXISTS `ux_insights.ab_test_results` (test_id STRING);"
    return mock_open(read_data=schema_content)

def run_tests():
    """Run all tests with detailed output"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestABTestingAnalysisAgent))
    test_suite.addTest(unittest.makeSuite(TestIntegrationABTestingAgent))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"🧪 A/B TESTING ANALYSIS AGENT TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print(f"\n✅ All tests passed! A/B Testing Analysis Agent is ready for production.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)