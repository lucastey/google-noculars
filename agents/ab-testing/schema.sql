-- BigQuery schema for A/B testing analysis
-- This table stores A/B test performance metrics and statistical analysis results

CREATE TABLE IF NOT EXISTS `ux_insights.ab_test_results` (
  -- Test identification
  test_id STRING NOT NULL,
  test_name STRING NOT NULL,
  variant_id STRING NOT NULL,
  variant_name STRING NOT NULL,
  analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- Test configuration
  test_start_date TIMESTAMP,
  test_end_date TIMESTAMP,
  test_duration_days INTEGER,
  test_status STRING, -- 'running', 'completed', 'paused', 'stopped'
  traffic_allocation_percent FLOAT64,
  
  -- Performance metrics
  sessions_count INTEGER,
  unique_users_count INTEGER,
  page_views INTEGER,
  bounce_rate FLOAT64,
  average_session_duration FLOAT64,
  
  -- Conversion metrics
  conversion_events INTEGER,
  conversion_rate FLOAT64,
  micro_conversions INTEGER,
  macro_conversions INTEGER,
  goal_completion_rate FLOAT64,
  
  -- Revenue metrics
  revenue_total FLOAT64,
  revenue_per_session FLOAT64,
  revenue_per_user FLOAT64,
  average_order_value FLOAT64,
  
  -- Engagement metrics
  average_engagement_score FLOAT64,
  time_on_page_seconds FLOAT64,
  click_through_rate FLOAT64,
  scroll_depth_percent FLOAT64,
  
  -- Statistical analysis
  statistical_significance FLOAT64,
  confidence_interval_lower FLOAT64,
  confidence_interval_upper FLOAT64,
  p_value FLOAT64,
  z_score FLOAT64,
  sample_size INTEGER,
  minimum_detectable_effect FLOAT64,
  
  -- Comparative analysis
  lift_percent FLOAT64,
  lift_significance STRING, -- 'positive', 'negative', 'neutral', 'inconclusive'
  relative_improvement FLOAT64,
  winner_probability FLOAT64,
  
  -- Segmentation analysis
  segment_performance STRING, -- JSON object with segment breakdowns
  device_performance STRING, -- JSON object with device-specific results
  geographic_performance STRING, -- JSON object with location-based results
  
  -- Business impact
  projected_annual_impact FLOAT64,
  cost_benefit_ratio FLOAT64,
  roi_estimate FLOAT64,
  business_significance STRING, -- 'high', 'medium', 'low', 'none'
  
  -- Recommendations
  recommendation_action STRING, -- 'implement', 'iterate', 'abandon', 'extend'
  recommendation_confidence FLOAT64,
  next_steps STRING, -- JSON array of recommended actions
  risk_assessment STRING,
  
  -- Quality metrics
  data_quality_score FLOAT64,
  sample_ratio_mismatch BOOLEAN,
  external_validity_score FLOAT64,
  
  -- Source data context
  source_sessions_analyzed INTEGER,
  source_business_insights_count INTEGER,
  source_data_timeframe_days INTEGER,
  
  -- Processed data metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY test_id, variant_id, test_status;