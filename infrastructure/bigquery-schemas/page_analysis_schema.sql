-- BigQuery table schema for page analysis data
-- This table stores comprehensive page structure and UX analysis results

CREATE TABLE IF NOT EXISTS `stellar-brace-463007-c0.ux_insights.page_analysis` (
  -- Basic page information
  url STRING NOT NULL,
  title STRING,
  meta_description STRING,
  meta_keywords STRING,
  lang STRING,
  viewport STRING,
  
  -- Structural metrics
  total_elements INT64,
  images_count INT64,
  links_count INT64,
  forms_count INT64,
  inputs_count INT64,
  buttons_count INT64,
  divs_count INT64,
  spans_count INT64,
  
  -- Heading analysis
  h1_count INT64,
  h2_count INT64,
  h3_count INT64,
  h4_count INT64,
  h5_count INT64,
  h6_count INT64,
  
  -- Layout patterns
  has_header BOOL,
  has_footer BOOL,
  has_nav BOOL,
  has_sidebar BOOL,
  has_main BOOL,
  
  -- Interactive elements
  clickable_elements INT64,
  form_elements INT64,
  media_elements INT64,
  has_js BOOL,
  external_scripts INT64,
  
  -- UX insights and scores
  content_density FLOAT64,
  accessibility_score FLOAT64,
  mobile_friendly BOOL,
  heading_hierarchy_score FLOAT64,
  alt_text_coverage FLOAT64,
  lazy_loading_images INT64,
  
  -- JSON data for complex structures
  headings_data JSON,
  layout_data JSON,
  interactions_data JSON,
  ux_insights_data JSON,
  
  -- Metadata
  status_code INT64,
  analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY url, mobile_friendly, accessibility_score;

-- Index for common queries
CREATE OR REPLACE VIEW `stellar-brace-463007-c0.ux_insights.page_analysis_summary` AS
SELECT 
  url,
  title,
  accessibility_score,
  mobile_friendly,
  total_elements,
  clickable_elements,
  content_density,
  DATE(analysis_timestamp) as analysis_date,
  analysis_timestamp
FROM `stellar-brace-463007-c0.ux_insights.page_analysis`
WHERE status_code = 200
ORDER BY analysis_timestamp DESC;