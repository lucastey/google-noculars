#!/usr/bin/env python3
"""
Data Retrieval Utilities for Insights Engine
Handles BigQuery data fetching from all source agents
"""

import os
from typing import Dict, Any, List
from google.cloud import bigquery


def get_bigquery_client():
    """Helper function to get BigQuery client with credentials"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account-key.json'
    return bigquery.Client()


def get_pattern_recognition_data(session_id: str = None, hours_back: int = 24):
    """Function tool: Get behavioral pattern data"""
    client = get_bigquery_client()
    
    where_clause = ""
    if session_id:
        where_clause = f"AND session_id = '{session_id}'"
    
    query = f"""
    SELECT *
    FROM `ux_insights.behavioral_patterns`
    WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
    {where_clause}
    ORDER BY analysis_timestamp DESC
    LIMIT 100
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_business_intelligence_data(session_id: str = None, hours_back: int = 24):
    """Function tool: Get business intelligence insights"""
    client = get_bigquery_client()
    
    where_clause = ""
    if session_id:
        where_clause = f"AND session_id = '{session_id}'"
    
    query = f"""
    SELECT *
    FROM `ux_insights.business_insights`
    WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
    {where_clause}
    ORDER BY analysis_timestamp DESC
    LIMIT 100
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_ab_testing_data(test_id: str = None, hours_back: int = 168):  # 1 week default
    """Function tool: Get A/B testing analysis results"""
    client = get_bigquery_client()
    
    where_clause = ""
    if test_id:
        where_clause = f"AND test_id = '{test_id}'"
    
    query = f"""
    SELECT *
    FROM `ux_insights.ab_test_results`
    WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
    {where_clause}
    ORDER BY analysis_timestamp DESC
    LIMIT 50
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]


def get_existing_recommendations(page_url: str = None):
    """Function tool: Get existing recommendations for a page to check for updates"""
    client = get_bigquery_client()
    
    where_clause = ""
    if page_url:
        where_clause = f"WHERE page_url = '{page_url}'"
    
    query = f"""
    SELECT *
    FROM `ux_insights.final_recommendations`
    {where_clause}
    ORDER BY last_updated DESC
    """
    
    try:
        results = client.query(query).result()
        return [dict(row) for row in results]
    except Exception as e:
        # Table might not exist yet
        print(f"⚠️ Could not retrieve existing recommendations: {e}")
        return []