-- BigQuery schema for business intelligence analysis
-- This table stores business insights derived from behavioral patterns analysis

CREATE TABLE IF NOT EXISTS `ux_insights.business_insights` (
  -- Session identification
  session_id STRING NOT NULL,
  page_url STRING NOT NULL,
  analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- Conversion funnel metrics
  funnel_stage STRING, -- 'entry', 'engagement', 'intent', 'conversion', 'exit'
  funnel_completion_rate FLOAT64,
  funnel_drop_off_point STRING,
  time_to_conversion_seconds FLOAT64,
  conversion_probability FLOAT64,
  
  -- User journey analysis
  journey_path STRING, -- JSON array of user interactions
  journey_complexity_score FLOAT64,
  journey_efficiency_score FLOAT64,
  backtrack_count INTEGER,
  dead_end_encounters INTEGER,
  
  -- Performance bottlenecks
  high_friction_elements STRING, -- JSON array of problematic elements
  slow_response_areas STRING, -- JSON array of slow-loading areas
  abandonment_triggers STRING, -- JSON array of abandonment causes
  bounce_likelihood FLOAT64,
  
  -- Business impact metrics
  estimated_revenue_impact FLOAT64,
  customer_lifetime_value_indicator FLOAT64,
  retention_probability FLOAT64,
  referral_likelihood FLOAT64,
  
  -- Page-specific business metrics
  page_value_score FLOAT64,
  goal_completion_rate FLOAT64,
  micro_conversion_count INTEGER,
  macro_conversion_indicator BOOLEAN,
  
  -- Segmentation data
  user_segment STRING, -- 'new', 'returning', 'power_user', 'at_risk'
  behavioral_cohort STRING,
  value_tier STRING, -- 'high', 'medium', 'low'
  
  -- Recommendations
  optimization_priority STRING, -- 'critical', 'high', 'medium', 'low'
  recommended_actions STRING, -- JSON array of actionable recommendations
  business_impact_estimate FLOAT64,
  implementation_effort_score FLOAT64,
  
  -- Context from source behavioral patterns
  source_engagement_score FLOAT64,
  source_frustration_indicators INTEGER,
  source_session_duration FLOAT64,
  
  -- Processed data metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY session_id, page_url, user_segment;