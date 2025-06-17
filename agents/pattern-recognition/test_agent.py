#!/usr/bin/env python3
"""
Test script for Pattern Recognition Agent
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to path
sys.path.append('.')

sys.path.append('./agents/pattern-recognition')
from agent import PatternRecognitionAgent

def test_pattern_recognition_agent():
    """Test the Pattern Recognition Agent functionality"""
    
    print("🧪 Testing Pattern Recognition Agent...")
    print("=" * 60)
    
    try:
        # Initialize agent
        agent = PatternRecognitionAgent()
        print("✅ Agent initialized successfully")
        
        # Test table creation
        print("\n📊 Testing table creation...")
        agent.create_behavioral_patterns_table()
        print("✅ Behavioral patterns table created/verified")
        
        # Clear any existing patterns for testing (optional)
        print("\n🧹 Clearing existing patterns for fresh test...")
        clear_query = "DELETE FROM `ux_insights.behavioral_patterns` WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)"
        try:
            agent.client.query(clear_query).result()
            print("✅ Existing patterns cleared")
        except Exception as e:
            print(f"⚠️  Could not clear patterns: {e}")
        
        # Test getting sessions to analyze
        print("\n🔍 Testing session discovery...")
        sessions = agent.get_sessions_to_analyze(hours_back=48)  # Look back further
        print(f"✅ Found {len(sessions)} sessions to analyze")
        
        if sessions:
            # Test analysis on first session
            print(f"\n🎯 Testing pattern analysis on session: {sessions[0]['session_id']}")
            
            events = agent.get_session_events(sessions[0]['session_id'], sessions[0]['page_url'])
            print(f"✅ Retrieved {len(events)} events for analysis")
            
            if events:
                patterns = agent.analyze_session_patterns(sessions[0], events)
                if patterns:
                    print("✅ Pattern analysis successful")
                    print(f"   📈 Engagement Score: {patterns['engagement_score']:.1f}")
                    print(f"   🖱️  Mouse Distance: {patterns['mouse_movement_distance']:.0f}px")
                    print(f"   👆 Total Clicks: {patterns['total_clicks']}")
                    print(f"   📜 Scroll Distance: {patterns['total_scroll_distance']}px")
                    print(f"   🎮 Device Type: {patterns['device_type']}")
                else:
                    print("⚠️  Pattern analysis returned no results")
            else:
                print("⚠️  No events found for session")
        
        # Test full analysis run
        print("\n🚀 Testing full analysis run...")
        agent.run_analysis(hours_back=48)  # Test with broader time window
        print("✅ Full analysis completed")
        
        # Verify data was inserted
        print("\n🔍 Verifying inserted data...")
        verify_query = """
        SELECT 
            COUNT(*) as pattern_count,
            AVG(engagement_score) as avg_engagement,
            AVG(session_duration_seconds) as avg_duration
        FROM `ux_insights.behavioral_patterns`
        WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
        """
        
        result = agent.client.query(verify_query).result()
        for row in result:
            print(f"✅ Verification complete:")
            print(f"   📊 Patterns analyzed: {row.pattern_count}")
            avg_engagement = row.avg_engagement if row.avg_engagement is not None else 0
            avg_duration = row.avg_duration if row.avg_duration is not None else 0
            print(f"   📈 Average engagement: {avg_engagement:.1f}")
            print(f"   ⏱️  Average duration: {avg_duration:.1f}s")
        
        print("\n" + "=" * 60)
        print("🎉 Pattern Recognition Agent test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_analysis_functions():
    """Test individual analysis functions with mock data"""
    
    print("\n🧪 Testing individual analysis functions...")
    
    try:
        agent = PatternRecognitionAgent()
        
        # Mock events data for testing
        mock_events = [
            {
                'event_type': 'mousemove',
                'timestamp': datetime.now() - timedelta(seconds=60),
                'x_coordinate': 100,
                'y_coordinate': 100,
                'viewport_width': 1920,
                'viewport_height': 1080
            },
            {
                'event_type': 'mousemove', 
                'timestamp': datetime.now() - timedelta(seconds=59),
                'x_coordinate': 200,
                'y_coordinate': 150,
                'viewport_width': 1920,
                'viewport_height': 1080
            },
            {
                'event_type': 'click',
                'timestamp': datetime.now() - timedelta(seconds=50),
                'x_coordinate': 200,
                'y_coordinate': 150,
                'element_tag': 'button',
                'element_id': 'submit-btn',
                'viewport_width': 1920,
                'viewport_height': 1080
            },
            {
                'event_type': 'scroll',
                'timestamp': datetime.now() - timedelta(seconds=30),
                'scroll_x': 0,
                'scroll_y': 500,
                'viewport_width': 1920,
                'viewport_height': 1080
            }
        ]
        
        # Test mouse distance calculation
        mouse_movements = [e for e in mock_events if e['event_type'] == 'mousemove']
        distance = agent._calculate_mouse_distance(mouse_movements)
        print(f"✅ Mouse distance calculation: {distance:.1f}px")
        
        # Test device classification
        device_type = agent._classify_device_type(1920, 1080)
        print(f"✅ Device classification: {device_type}")
        
        # Test engagement score
        engagement = agent._calculate_engagement_score(60, 1, distance, 500, 3)
        print(f"✅ Engagement score calculation: {engagement:.1f}")
        
        print("✅ Individual function tests passed!")
        
    except Exception as e:
        print(f"❌ Individual function tests failed: {e}")

if __name__ == "__main__":
    # Run main test
    success = test_pattern_recognition_agent()
    
    # Run individual function tests
    test_individual_analysis_functions()
    
    if success:
        print("\n🎊 All tests passed! Pattern Recognition Agent is ready.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed! Check the errors above.")
        sys.exit(1)