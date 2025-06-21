-- BigQuery schema for insights engine final recommendations
-- This table stores page-centric coordinated multi-agent insights and priority-ranked actionable recommendations
-- Updated to support dynamic recommendations that evolve as more user data is collected

CREATE TABLE IF NOT EXISTS `ux_insights.final_recommendations` (
  -- Page-centric recommendation identification (PRIMARY KEY)
  page_url STRING NOT NULL,
  recommendation_category STRING NOT NULL, -- 'ui_design', 'content', 'functionality', 'performance', 'analytics'
  recommendation_id STRING NOT NULL, -- Generated from page_url + category hash
  
  -- Temporal tracking for dynamic updates
  first_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP(), -- When this page was first analyzed
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP(), -- When recommendation was last updated
  analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(), -- Current analysis timestamp
  data_freshness_hours FLOAT64, -- How fresh is the underlying data
  
  -- Session aggregation and sample size tracking
  sessions_analyzed_count INTEGER, -- Total number of sessions analyzed for this page
  sessions_analyzed_list STRING, -- JSON array of session IDs that contributed to this recommendation
  unique_users_count INTEGER, -- Number of unique users across all sessions
  sample_size_adequacy STRING, -- 'insufficient', 'adequate', 'strong', 'excellent'
  statistical_power FLOAT64, -- Statistical power of the analysis based on sample size
  
  -- Multi-agent coordination metadata
  agents_analyzed STRING, -- JSON array of agents that contributed to this recommendation
  data_sources_used STRING, -- JSON array of source tables analyzed
  coordination_confidence FLOAT64, -- Confidence in multi-agent coordination (evolves with sample size)
  analysis_completeness_score FLOAT64, -- How complete the analysis pipeline was
  confidence_score_evolution STRING, -- JSON array tracking confidence over time
  
  -- Consolidated insights summary
  primary_insight_category STRING, -- 'user_experience', 'conversion_optimization', 'performance', 'engagement'
  insight_severity STRING, -- 'critical', 'high', 'medium', 'low'
  insight_urgency STRING, -- 'immediate', 'short_term', 'medium_term', 'long_term'
  insight_confidence FLOAT64, -- Overall confidence in the insight
  
  -- Aggregated business impact (across all sessions for this page)
  estimated_revenue_impact FLOAT64, -- Aggregated revenue impact from all sessions
  average_conversion_probability FLOAT64, -- Average conversion probability across sessions
  conversion_impact_percent FLOAT64, -- Expected conversion rate improvement
  user_experience_impact_score FLOAT64, -- Aggregated UX improvement score (1-100)
  statistical_significance FLOAT64, -- A/B test statistical backing if available
  business_priority_rank INTEGER, -- 1 (highest) to 100 (lowest) - recalculated with each update
  priority_rank_evolution STRING, -- JSON array tracking priority changes over time
  
  -- Recommendation details
  recommendation_title STRING, -- Clear, actionable title
  recommendation_description STRING, -- Detailed description of what to do
  implementation_complexity STRING, -- 'simple', 'moderate', 'complex', 'major'
  estimated_implementation_hours FLOAT64,
  required_resources STRING, -- JSON array of resources needed
  
  -- Aggregated supporting evidence from all agents (across all sessions)
  pattern_evidence_aggregated STRING, -- JSON object with aggregated behavioral patterns
  business_evidence_aggregated STRING, -- JSON object with aggregated business metrics  
  ab_test_evidence STRING, -- JSON object with supporting A/B test data
  cross_agent_correlation FLOAT64, -- How well agents agree on this recommendation (improves with sample size)
  evidence_strength_score FLOAT64, -- Overall strength of supporting evidence (0-1)
  
  -- Data quality and reliability tracking
  data_consistency_score FLOAT64, -- How consistent the data is across sessions
  outlier_sessions_count INTEGER, -- Number of sessions that were statistical outliers
  data_quality_issues STRING, -- JSON array of any data quality concerns
  
  -- Action plan and timeline
  immediate_actions STRING, -- JSON array of actions to take now
  short_term_actions STRING, -- JSON array of actions for next 1-4 weeks
  long_term_actions STRING, -- JSON array of actions for 1-3 months
  success_metrics STRING, -- JSON array of KPIs to track improvement
  monitoring_plan STRING, -- JSON object describing how to monitor success
  
  -- Risk assessment
  implementation_risks STRING, -- JSON array of potential risks
  risk_mitigation_strategies STRING, -- JSON array of risk mitigation approaches
  rollback_plan STRING, -- Description of how to rollback if needed
  
  -- Segmentation and targeting
  affected_user_segments STRING, -- JSON array of user segments this affects
  device_specific_considerations STRING, -- JSON object with device-specific notes
  geographic_considerations STRING, -- JSON object with location-specific notes
  
  -- Performance tracking
  baseline_metrics STRING, -- JSON object with current performance baseline
  target_metrics STRING, -- JSON object with target performance goals
  measurement_methodology STRING, -- How to measure success
  expected_timeline_to_impact_days INTEGER,
  
  -- Competitive analysis context
  industry_benchmark_comparison STRING, -- How does this compare to industry standards
  competitive_advantage_potential STRING, -- Potential competitive advantage
  market_differentiation_score FLOAT64,
  
  -- Aggregated source agent summaries (across all sessions for this page)
  average_engagement_score FLOAT64, -- Average engagement score from pattern recognition
  average_frustration_level FLOAT64, -- Average frustration level from pattern recognition
  dominant_funnel_stage STRING, -- Most common funnel stage from business intelligence
  funnel_stage_distribution STRING, -- JSON object with funnel stage breakdown
  source_ab_test_winner STRING, -- From A/B testing (if applicable)
  source_statistical_confidence FLOAT64, -- From A/B testing (if applicable)
  
  -- API and dashboard integration
  dashboard_priority BOOLEAN, -- Should this appear on main dashboard
  alert_threshold_met BOOLEAN, -- Does this meet criteria for alerts
  api_endpoint_data STRING, -- JSON formatted for API consumption
  visualization_config STRING, -- Configuration for dashboard charts/graphs
  
  -- Quality and validation
  data_quality_score FLOAT64, -- Overall quality of underlying data
  recommendation_accuracy_score FLOAT64, -- Historical accuracy of similar recommendations
  peer_review_status STRING, -- 'pending', 'approved', 'flagged'
  validation_methodology STRING, -- How this recommendation was validated
  
  -- Collaboration and workflow
  assigned_team STRING, -- Team responsible for implementation
  stakeholder_notifications STRING, -- JSON array of who should be notified
  approval_workflow_status STRING, -- 'draft', 'review', 'approved', 'implemented'
  
  -- Historical tracking
  similar_recommendations_history STRING, -- JSON array of similar past recommendations
  implementation_success_rate FLOAT64, -- Success rate of similar recommendations
  lessons_learned STRING, -- Key lessons from similar implementations
  
  -- Processed data metadata
  processing_duration_seconds FLOAT64, -- How long the analysis took
  agent_versions STRING, -- JSON object with version info of all agents
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(last_updated)
CLUSTER BY page_url, recommendation_category, business_priority_rank;