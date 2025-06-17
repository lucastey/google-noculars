-- BigQuery schema for behavioral patterns analysis
-- This table stores analyzed user behavior patterns from mouse tracking data

CREATE TABLE IF NOT EXISTS `ux_insights.behavioral_patterns` (
  -- Session identification
  session_id STRING NOT NULL,
  page_url STRING NOT NULL,
  analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- Session metrics
  session_duration_seconds FLOAT64,
  total_events INTEGER,
  unique_event_types INTEGER,
  bounce_session BOOLEAN,
  
  -- Mouse movement patterns
  mouse_movement_distance FLOAT64,
  average_mouse_speed FLOAT64,
  idle_time_seconds FLOAT64,
  rapid_movements_count INTEGER,
  
  -- Click behavior
  total_clicks INTEGER,
  click_rate_per_minute FLOAT64,
  unique_elements_clicked INTEGER,
  click_precision_score FLOAT64,
  
  -- Scroll behavior  
  total_scroll_distance INTEGER,
  scroll_sessions_count INTEGER,
  max_scroll_depth_percent FLOAT64,
  scroll_back_count INTEGER,
  
  -- Engagement scoring
  engagement_score FLOAT64,
  frustration_indicators INTEGER,
  exploration_score FLOAT64,
  task_completion_likelihood FLOAT64,
  
  -- Viewport and device context
  viewport_width INTEGER,
  viewport_height INTEGER,
  device_type STRING,
  
  -- Processed data metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY session_id, page_url;