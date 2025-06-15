#!/usr/bin/env python3
"""
Script to create BigQuery tables for the UX Insights Platform
"""

import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

def create_page_analysis_table():
    """Create the page_analysis table in BigQuery"""
    client = bigquery.Client()
    
    dataset_id = 'ux_insights'
    table_id = 'page_analysis'
    
    # Create dataset if it doesn't exist
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = 'asia-southeast1'  # Singapore region
        dataset = client.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")
    
    # Define table schema
    schema = [
        # Basic page information
        bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("meta_description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("meta_keywords", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lang", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("viewport", "STRING", mode="NULLABLE"),
        
        # Structural metrics
        bigquery.SchemaField("total_elements", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("images_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("links_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("forms_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("inputs_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("buttons_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("divs_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("spans_count", "INTEGER", mode="NULLABLE"),
        
        # Heading counts
        bigquery.SchemaField("h1_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("h2_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("h3_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("h4_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("h5_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("h6_count", "INTEGER", mode="NULLABLE"),
        
        # Layout patterns
        bigquery.SchemaField("has_header", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("has_footer", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("has_nav", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("has_sidebar", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("has_main", "BOOLEAN", mode="NULLABLE"),
        
        # Interactive elements
        bigquery.SchemaField("clickable_elements", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("form_elements", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("media_elements", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("has_js", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("external_scripts", "INTEGER", mode="NULLABLE"),
        
        # UX insights and scores
        bigquery.SchemaField("content_density", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("accessibility_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("mobile_friendly", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("heading_hierarchy_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("alt_text_coverage", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("lazy_loading_images", "INTEGER", mode="NULLABLE"),
        
        # JSON data for complex structures
        bigquery.SchemaField("headings_data", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("layout_data", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("interactions_data", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("ux_insights_data", "JSON", mode="NULLABLE"),
        
        # Metadata
        bigquery.SchemaField("status_code", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("analysis_timestamp", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    # Create table reference
    table_ref = dataset_ref.table(table_id)
    
    # Check if table already exists
    try:
        client.get_table(table_ref)
        print(f"Table {table_id} already exists")
        return
    except NotFound:
        pass
    
    # Create table with partitioning and clustering
    table = bigquery.Table(table_ref, schema=schema)
    
    # Set up time partitioning
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="analysis_timestamp"
    )
    
    # Set up clustering (only string and boolean fields can be used)
    table.clustering_fields = ["url", "mobile_friendly"]
    
    # Create the table
    table = client.create_table(table)
    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")

def create_mouse_tracking_table():
    """Create the mouse_tracking table for storing user interaction data"""
    client = bigquery.Client()
    
    dataset_id = 'ux_insights'
    table_id = 'mouse_tracking'
    
    schema = [
        # Session information
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("page_url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("viewport_width", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("viewport_height", "INTEGER", mode="NULLABLE"),
        
        # Event data
        bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),  # mouse_move, click, scroll, etc.
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("x_coordinate", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("y_coordinate", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("scroll_x", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("scroll_y", "INTEGER", mode="NULLABLE"),
        
        # Element information
        bigquery.SchemaField("element_tag", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("element_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("element_class", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("element_text", "STRING", mode="NULLABLE"),
        
        # Additional context
        bigquery.SchemaField("page_title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("referrer", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    
    try:
        client.get_table(table_ref)
        print(f"Table {table_id} already exists")
        return
    except NotFound:
        pass
    
    table = bigquery.Table(table_ref, schema=schema)
    
    # Set up time partitioning
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )
    
    # Set up clustering
    table.clustering_fields = ["session_id", "page_url", "event_type"]
    
    table = client.create_table(table)
    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")

if __name__ == "__main__":
    print("Creating BigQuery tables for UX Insights Platform...")
    
    # Set up authentication
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/lucastay/Desktop/GitHub/google-noculars/service-account-key.json'
    
    try:
        create_page_analysis_table()
        create_mouse_tracking_table()
        print("All tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")