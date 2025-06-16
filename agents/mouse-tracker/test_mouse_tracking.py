#!/usr/bin/env python3
"""
Test script to verify mouse tracking data in BigQuery
"""

import os
from google.cloud import bigquery
from datetime import datetime, timedelta

def test_mouse_tracking_data():
    """Query and display recent mouse tracking data"""
    
    # Set up BigQuery client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account-key.json'
    client = bigquery.Client()
    
    print("🔍 Checking mouse tracking data in BigQuery...")
    print("=" * 60)
    
    # Query recent sessions
    sessions_query = """
        SELECT 
            session_id,
            page_url,
            MIN(timestamp) as session_start,
            MAX(timestamp) as session_end,
            COUNT(*) as total_events,
            COUNT(DISTINCT event_type) as unique_event_types
        FROM `ux_insights.mouse_tracking`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        GROUP BY session_id, page_url
        ORDER BY session_start DESC
        LIMIT 10
    """
    
    try:
        print("📊 Recent Sessions (last hour):")
        sessions = client.query(sessions_query).to_dataframe()
        
        if len(sessions) == 0:
            print("   ❌ No recent sessions found")
            print("   💡 Try interacting with the demo page first")
        else:
            for _, session in sessions.iterrows():
                print(f"   🎯 Session: {session['session_id']}")
                print(f"      URL: {session['page_url']}")
                print(f"      Events: {session['total_events']}")
                print(f"      Event Types: {session['unique_event_types']}")
                print(f"      Duration: {session['session_start']} → {session['session_end']}")
                print()
        
        # Query event type breakdown
        events_query = """
            SELECT 
                event_type,
                COUNT(*) as event_count,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM `ux_insights.mouse_tracking`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
            GROUP BY event_type
            ORDER BY event_count DESC
        """
        
        print("📈 Event Type Breakdown (last hour):")
        events = client.query(events_query).to_dataframe()
        
        if len(events) == 0:
            print("   ❌ No events found")
        else:
            for _, event in events.iterrows():
                print(f"   🎬 {event['event_type']}: {event['event_count']} events from {event['unique_sessions']} sessions")
        
        print("\n" + "=" * 60)
        print("✅ Mouse tracking data check completed!")
        
    except Exception as e:
        print(f"❌ Error querying BigQuery: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_mouse_tracking_data()