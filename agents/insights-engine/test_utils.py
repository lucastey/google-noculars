#!/usr/bin/env python3
"""
Unit Tests for Insights Engine Utilities
Tests statistical, data processing, and recommendation building utilities
"""

import unittest
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import List

# Test utility modules directly
try:
    from utils.statistical import *
    from utils.data_processing import *
    from utils.recommendation_builder import *
    from utils.bigquery_ops import create_recommendation_row
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the insights-engine directory")
    sys.exit(1)


class TestStatisticalUtilities(unittest.TestCase):
    """Test statistical calculation utilities"""
    
    def test_calculate_sample_size_adequacy(self):
        """Test sample size adequacy calculation"""
        self.assertEqual(calculate_sample_size_adequacy(150), 'excellent')
        self.assertEqual(calculate_sample_size_adequacy(80), 'strong') 
        self.assertEqual(calculate_sample_size_adequacy(15), 'adequate')
        self.assertEqual(calculate_sample_size_adequacy(3), 'insufficient')
    
    def test_calculate_statistical_power(self):
        """Test statistical power calculation"""
        power_150 = calculate_statistical_power(150)
        power_30 = calculate_statistical_power(30)
        power_5 = calculate_statistical_power(5)
        
        self.assertGreater(power_150, power_30)
        self.assertGreater(power_30, power_5)
        self.assertLessEqual(power_150, 0.99)
        self.assertGreaterEqual(power_5, 0.0)
    
    def test_calculate_cross_agent_correlation(self):
        """Test cross-agent correlation calculation"""
        pattern_sessions = [
            {'session_id': '1', 'engagement_score': 80},
            {'session_id': '2', 'engagement_score': 60},
        ]
        business_sessions = [
            {'session_id': '1', 'conversion_probability': 0.8},
            {'session_id': '2', 'conversion_probability': 0.6},
        ]
        
        correlation = calculate_cross_agent_correlation(pattern_sessions, business_sessions)
        self.assertIsInstance(correlation, float)
        self.assertGreaterEqual(correlation, -1.0)
        self.assertLessEqual(correlation, 1.0)
    
    def test_calculate_business_priority_rank(self):
        """Test business priority ranking"""
        rank_high = calculate_business_priority_rank(5000, 80, 90, 'simple', 0.95)
        rank_low = calculate_business_priority_rank(100, 20, 30, 'complex', 0.60)
        
        self.assertLess(rank_high, rank_low)  # Higher priority = lower rank number
        self.assertGreaterEqual(rank_high, 1)
        self.assertLessEqual(rank_low, 100)
    
    def test_calculate_evidence_strength_score(self):
        """Test evidence strength score calculation"""
        strong_evidence = calculate_evidence_strength_score(100, 0.9, 0.8, 0.85)
        weak_evidence = calculate_evidence_strength_score(10, 0.3, 0.4, 0.5)
        
        self.assertGreater(strong_evidence, weak_evidence)
        self.assertLessEqual(strong_evidence, 1.0)
        self.assertGreaterEqual(weak_evidence, 0.0)
    
    def test_calculate_data_consistency_score(self):
        """Test data consistency score calculation"""
        consistent_sessions = [
            {'engagement_score': 80, 'frustration_indicators': 1, 'conversion_probability': 0.8},
            {'engagement_score': 85, 'frustration_indicators': 1, 'conversion_probability': 0.9},
        ]
        
        inconsistent_sessions = [
            {'engagement_score': 20, 'frustration_indicators': 5, 'conversion_probability': 0.1},
            {'engagement_score': 90, 'frustration_indicators': 0, 'conversion_probability': 0.9},
        ]
        
        metrics = ['engagement_score', 'frustration_indicators', 'conversion_probability']
        
        consistent_score = calculate_data_consistency_score(consistent_sessions, metrics)
        inconsistent_score = calculate_data_consistency_score(inconsistent_sessions, metrics)
        
        self.assertGreater(consistent_score, inconsistent_score)


class TestDataProcessing(unittest.TestCase):
    """Test data processing utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pattern_data = [
            {
                'session_id': 'session_1',
                'page_url': 'https://example.com/page1',
                'engagement_score': 80,
                'frustration_indicators': 1
            },
            {
                'session_id': 'session_2',
                'page_url': 'https://example.com/page1',
                'engagement_score': 60,
                'frustration_indicators': 3
            },
            {
                'session_id': 'session_3',
                'page_url': 'https://example.com/page2',
                'engagement_score': 90,
                'frustration_indicators': 0
            }
        ]
        
        self.business_data = [
            {
                'session_id': 'session_1',
                'page_url': 'https://example.com/page1',
                'conversion_probability': 0.7,
                'estimated_revenue_impact': 500.0,
                'funnel_stage': 'consideration'
            },
            {
                'session_id': 'session_2',
                'page_url': 'https://example.com/page1',
                'conversion_probability': 0.5,
                'estimated_revenue_impact': 300.0,
                'funnel_stage': 'decision'
            }
        ]
    
    def test_generate_recommendation_id(self):
        """Test recommendation ID generation"""
        rec_id = generate_recommendation_id('https://example.com/test', 'ui_design')
        
        self.assertTrue(rec_id.startswith('rec_'))
        self.assertEqual(len(rec_id), 16)  # rec_ + 12 character hash
        
        # Same inputs should generate same ID
        rec_id2 = generate_recommendation_id('https://example.com/test', 'ui_design')
        self.assertEqual(rec_id, rec_id2)
        
        # Different inputs should generate different IDs
        rec_id3 = generate_recommendation_id('https://example.com/test2', 'ui_design')
        self.assertNotEqual(rec_id, rec_id3)
    
    def test_aggregate_sessions_by_page(self):
        """Test session aggregation by page URL"""
        aggregations = aggregate_sessions_by_page(self.pattern_data, self.business_data)
        
        # Should have 2 pages
        self.assertEqual(len(aggregations), 2)
        
        # Check page1 aggregation
        page1_data = aggregations['https://example.com/page1']
        self.assertEqual(page1_data['session_count'], 2)
        self.assertEqual(page1_data['average_engagement_score'], 70.0)  # (80 + 60) / 2
        self.assertEqual(page1_data['average_frustration_level'], 2.0)  # (1 + 3) / 2
        self.assertEqual(page1_data['average_conversion_probability'], 0.6)  # (0.7 + 0.5) / 2
        self.assertEqual(page1_data['total_revenue_impact'], 800.0)  # 500 + 300
        # Both stages appear once, so max() returns the alphabetically last one
        self.assertIn(page1_data['dominant_funnel_stage'], ['consideration', 'decision'])
        
        # Check page2 aggregation
        page2_data = aggregations['https://example.com/page2']
        self.assertEqual(page2_data['session_count'], 1)
        self.assertEqual(page2_data['average_engagement_score'], 90.0)
        self.assertEqual(page2_data['average_frustration_level'], 0.0)
        self.assertEqual(page2_data['average_conversion_probability'], 0)  # No business data
        self.assertEqual(page2_data['total_revenue_impact'], 0)
    
    def test_determine_recommendation_categories(self):
        """Test recommendation category determination"""
        # High frustration should trigger performance and UI categories  
        high_frustration_data = {
            'average_engagement_score': 50,
            'average_frustration_level': 4.5,
            'average_conversion_probability': 0.6
        }
        categories = determine_recommendation_categories(high_frustration_data)
        self.assertIn('performance', categories)
        self.assertIn('ui_design', categories)
        
        # Low conversion should trigger conversion optimization
        low_conversion_data = {
            'average_engagement_score': 70,
            'average_frustration_level': 1,
            'average_conversion_probability': 0.2
        }
        categories = determine_recommendation_categories(low_conversion_data)
        self.assertIn('conversion_optimization', categories)
        
        # Low engagement should trigger content category
        low_engagement_data = {
            'average_engagement_score': 25,
            'average_frustration_level': 1,
            'average_conversion_probability': 0.6
        }
        categories = determine_recommendation_categories(low_engagement_data)
        self.assertIn('content', categories)
        
        # Good metrics should default to user_experience
        good_data = {
            'average_engagement_score': 80,
            'average_frustration_level': 1,
            'average_conversion_probability': 0.8
        }
        categories = determine_recommendation_categories(good_data)
        self.assertEqual(categories, ['user_experience'])


class TestRecommendationBuilder(unittest.TestCase):
    """Test recommendation builder utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregated_data = {
            'page_url': 'https://example.com/test',
            'session_count': 50,
            'sessions_analyzed_list': ['session_1', 'session_2', 'session_3'],
            'pattern_sessions': [
                {'session_id': 'session_1', 'engagement_score': 60, 'frustration_indicators': 2},
                {'session_id': 'session_2', 'engagement_score': 70, 'frustration_indicators': 1}
            ],
            'business_sessions': [
                {'session_id': 'session_1', 'conversion_probability': 0.5, 'estimated_revenue_impact': 300},
                {'session_id': 'session_2', 'conversion_probability': 0.7, 'estimated_revenue_impact': 400}
            ],
            'average_engagement_score': 65,
            'average_frustration_level': 1.5,
            'average_conversion_probability': 0.6,
            'total_revenue_impact': 700,
            'dominant_funnel_stage': 'consideration',
            'funnel_stage_distribution': {'consideration': 1, 'decision': 1}
        }
    
    def test_build_recommendation_details(self):
        """Test recommendation details building"""
        ui_details = build_recommendation_details('ui_design', self.aggregated_data)
        self.assertIn('title', ui_details)
        self.assertIn('description', ui_details)
        self.assertIn('complexity', ui_details)
        self.assertIn('UI Design', ui_details['title'])
        self.assertIn('https://example.com/test', ui_details['title'])
        
        perf_details = build_recommendation_details('performance', self.aggregated_data)
        self.assertIn('Optimize Performance', perf_details['title'])
        self.assertEqual(perf_details['complexity'], 'complex')
        
        conv_details = build_recommendation_details('conversion_optimization', self.aggregated_data)
        self.assertIn('Conversion Funnel', conv_details['title'])
        self.assertEqual(conv_details['complexity'], 'moderate')
    
    def test_determine_severity(self):
        """Test severity determination"""
        critical_severity = determine_severity(4.5, 15, 6000)
        self.assertEqual(critical_severity, 'critical')
        
        high_severity = determine_severity(3.5, 25, 2000)
        self.assertEqual(high_severity, 'high')
        
        medium_severity = determine_severity(2.5, 40, 500)
        self.assertEqual(medium_severity, 'medium')
        
        low_severity = determine_severity(1, 80, 50)
        self.assertEqual(low_severity, 'low')
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        high_confidence = calculate_confidence_score(150, 0.9)
        medium_confidence = calculate_confidence_score(50, 0.7)
        low_confidence = calculate_confidence_score(5, 0.3)
        
        self.assertGreater(high_confidence, medium_confidence)
        self.assertGreater(medium_confidence, low_confidence)
        self.assertLessEqual(high_confidence, 0.98)
        self.assertGreaterEqual(low_confidence, 0.0)
    
    def test_get_required_resources(self):
        """Test required resources determination"""
        ui_resources = get_required_resources('ui_design')
        self.assertIn('UX Designer', ui_resources)
        self.assertIn('Frontend Developer', ui_resources)
        
        perf_resources = get_required_resources('performance')
        self.assertIn('Performance Engineer', perf_resources)
        
        conv_resources = get_required_resources('conversion_optimization')
        self.assertIn('Marketing Analyst', conv_resources)
        
        content_resources = get_required_resources('content')
        self.assertIn('Content Strategist', content_resources)
    
    def test_create_page_recommendation(self):
        """Test page recommendation creation"""
        recommendation = create_page_recommendation(self.aggregated_data, 'ui_design')
        
        # Verify required fields
        self.assertEqual(recommendation['page_url'], 'https://example.com/test')
        self.assertEqual(recommendation['recommendation_category'], 'ui_design')
        self.assertIn('recommendation_id', recommendation)
        self.assertIn('recommendation_title', recommendation)
        self.assertIn('recommendation_description', recommendation)
        self.assertIn('business_priority_rank', recommendation)
        self.assertIn('insight_confidence', recommendation)
        
        # Verify data structure integrity
        self.assertIsInstance(recommendation['required_resources'], list)
        self.assertIsInstance(recommendation['immediate_actions'], list)
        self.assertIsInstance(recommendation['short_term_actions'], list)
        self.assertIsInstance(recommendation['long_term_actions'], list)
        self.assertIsInstance(recommendation['success_metrics'], list)
        
        # Verify calculations
        self.assertGreater(recommendation['insight_confidence'], 0)
        self.assertLessEqual(recommendation['insight_confidence'], 1)
        self.assertGreater(recommendation['business_priority_rank'], 0)
        self.assertLessEqual(recommendation['business_priority_rank'], 100)
        
        # Verify evidence aggregation
        self.assertIn('pattern_evidence_aggregated', recommendation)
        self.assertIn('business_evidence_aggregated', recommendation)
        self.assertEqual(recommendation['pattern_evidence_aggregated']['average_engagement_score'], 65)
        self.assertEqual(recommendation['business_evidence_aggregated']['average_conversion_probability'], 0.6)
    
    def test_build_confidence_evolution(self):
        """Test confidence evolution building"""
        evolution = build_confidence_evolution(None, 0.85, 50)
        
        self.assertEqual(len(evolution), 1)
        self.assertEqual(evolution[0]['confidence'], 0.85)
        self.assertEqual(evolution[0]['sample_size'], 50)
        self.assertIn('timestamp', evolution[0])
        
        # Test with existing recommendation
        existing_rec = {
            'confidence_score_evolution': '[{"timestamp": "2024-01-01T00:00:00Z", "confidence": 0.7, "sample_size": 30}]'
        }
        evolution_with_existing = build_confidence_evolution(existing_rec, 0.85, 50)
        
        self.assertEqual(len(evolution_with_existing), 2)
        self.assertEqual(evolution_with_existing[0]['confidence'], 0.7)
        self.assertEqual(evolution_with_existing[1]['confidence'], 0.85)


class TestBigQueryOperations(unittest.TestCase):
    """Test BigQuery operations utilities"""
    
    def test_create_recommendation_row(self):
        """Test BigQuery row creation"""
        test_recommendation = {
            'page_url': 'https://example.com/test',
            'recommendation_category': 'ui_design',
            'recommendation_id': 'rec_test123',
            'sessions_analyzed_count': 25,
            'sessions_analyzed_list': ['session_1', 'session_2'],
            'business_priority_rank': 15,
            'insight_confidence': 0.85,
            'recommendation_title': 'Test Recommendation',
            'recommendation_description': 'Test description',
            'required_resources': ['UX Designer', 'Developer'],
            'immediate_actions': ['Action 1', 'Action 2'],
            'pattern_evidence_aggregated': {'avg_engagement': 70},
            'business_evidence_aggregated': {'avg_conversion': 0.6}
        }
        
        row = create_recommendation_row(test_recommendation)
        
        # Verify required fields are present
        self.assertEqual(row['page_url'], 'https://example.com/test')
        self.assertEqual(row['recommendation_category'], 'ui_design')
        self.assertEqual(row['business_priority_rank'], 15)
        self.assertEqual(row['insight_confidence'], 0.85)
        self.assertEqual(row['recommendation_title'], 'Test Recommendation')
        
        # Verify JSON serialization for list/dict fields
        self.assertIsInstance(row['sessions_analyzed_list'], str)
        self.assertIsInstance(row['required_resources'], str)
        self.assertIsInstance(row['immediate_actions'], str)
        self.assertIsInstance(row['pattern_evidence_aggregated'], str)
        self.assertIsInstance(row['business_evidence_aggregated'], str)
        
        # Test JSON parsing
        parsed_sessions = json.loads(row['sessions_analyzed_list'])
        self.assertEqual(parsed_sessions, ['session_1', 'session_2'])
        
        parsed_resources = json.loads(row['required_resources'])
        self.assertEqual(parsed_resources, ['UX Designer', 'Developer'])
        
        parsed_pattern_evidence = json.loads(row['pattern_evidence_aggregated'])
        self.assertEqual(parsed_pattern_evidence, {'avg_engagement': 70})
        
        # Verify timestamp fields
        self.assertIn('first_analyzed', row)
        self.assertIn('last_updated', row)
        self.assertIn('analysis_timestamp', row)
        self.assertIn('created_at', row)
        
        # Verify default values for missing fields
        test_minimal = {'page_url': 'https://test.com'}
        row_minimal = create_recommendation_row(test_minimal)
        self.assertEqual(row_minimal['recommendation_category'], 'user_experience')
        self.assertEqual(row_minimal['sessions_analyzed_count'], 0)
        self.assertEqual(row_minimal['business_priority_rank'], 50)


def run_tests():
    """Run all utility test suites with detailed reporting"""
    print("🧪 Running Insights Engine Utilities Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestStatisticalUtilities,
        TestDataProcessing,
        TestRecommendationBuilder,
        TestBigQueryOperations
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
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
        print("\n✅ All utility tests passed successfully!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} tests failed")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)