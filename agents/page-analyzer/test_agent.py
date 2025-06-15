#!/usr/bin/env python3
"""
Test script for the Page Analyzer Agent
Tests end-to-end data flow from web page analysis to BigQuery storage
"""

import os
import sys
from agent import page_analyzer_agent, analyze_page_structure, store_analysis_to_bigquery

def test_page_analysis():
    """Test the page analysis functionality"""
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://google.com",
        "https://github.com"
    ]
    
    print("Testing Page Analyzer Agent...")
    print("="*50)
    
    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        print("-" * 30)
        
        try:
            # Step 1: Analyze page structure
            analysis_result = analyze_page_structure(url)
            
            if 'error' in analysis_result:
                print(f"❌ Analysis failed: {analysis_result['error']}")
                continue
                
            print(f"✅ Page analysis completed")
            print(f"   - Title: {analysis_result.get('metadata', {}).get('title', 'N/A')}")
            print(f"   - Total elements: {analysis_result.get('structure', {}).get('total_elements', 'N/A')}")
            print(f"   - Accessibility score: {analysis_result.get('ux_insights', {}).get('accessibility_score', 'N/A')}")
            print(f"   - Mobile friendly: {analysis_result.get('ux_insights', {}).get('mobile_friendly', 'N/A')}")
            
            # Step 2: Store to BigQuery
            storage_result = store_analysis_to_bigquery(analysis_result)
            
            if storage_result.get('status') == 'success':
                print(f"✅ Data stored to BigQuery successfully")
            else:
                print(f"❌ BigQuery storage failed: {storage_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Test failed for {url}: {str(e)}")
    
    print("\n" + "="*50)
    print("Testing completed!")

def test_agent_interaction():
    """Test the agent's conversational interface"""
    
    print("\nTesting Agent Interaction...")
    print("="*50)
    
    test_message = "Please analyze the website https://example.com and store the results."
    
    try:
        # This would normally be done through the ADK framework
        # For now, we'll simulate the interaction
        print(f"📝 Test message: {test_message}")
        print("🤖 Agent would process this request and:")
        print("   1. Call analyze_page_structure('https://example.com')")
        print("   2. Call store_analysis_to_bigquery(results)")
        print("   3. Return insights and recommendations")
        
    except Exception as e:
        print(f"❌ Agent interaction test failed: {str(e)}")

if __name__ == "__main__":
    # Set up environment
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/lucastay/Desktop/GitHub/google-noculars/service-account-key.json'
    
    print("🚀 Starting Page Analyzer Agent Tests")
    print("🌍 Testing with real websites...")
    
    test_page_analysis()
    test_agent_interaction()
    
    print("\n🎉 All tests completed!")