#!/usr/bin/env python3
"""
Pattern Recognition Agent - Google Noculars
Analyzes user behavior patterns from mouse tracking data
"""

import os
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.cloud import bigquery
import json

class PatternRecognitionAgent:
    """Analyzes user behavior patterns from mouse tracking data"""
    
    def __init__(self):
        """Initialize the Pattern Recognition Agent"""
        # Set up BigQuery client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account-key.json'
        self.client = bigquery.Client()
        self.dataset = self.client.dataset('ux_insights')
        
        # Table references
        self.source_table = self.dataset.table('mouse_tracking')
        self.target_table = self.dataset.table('behavioral_patterns')
        
        print("🎯 Pattern Recognition Agent initialized")
    
    def create_behavioral_patterns_table(self):
        """Create behavioral patterns table if it doesn't exist"""
        try:
            # Read schema from file
            with open('./agents/pattern-recognition/schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            self.client.query(schema_sql).result()
            print("✅ Behavioral patterns table created/verified")
            
        except Exception as e:
            print(f"❌ Error creating behavioral patterns table: {e}")
            raise
    
    def get_sessions_to_analyze(self, hours_back: int = 24) -> List[Dict]:
        """Get sessions that need pattern analysis"""
        query = f"""
        SELECT DISTINCT
            session_id,
            page_url,
            MIN(timestamp) as session_start,
            MAX(timestamp) as session_end,
            COUNT(*) as event_count
        FROM `ux_insights.mouse_tracking`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
            AND session_id NOT IN (
                SELECT DISTINCT session_id 
                FROM `ux_insights.behavioral_patterns`
                WHERE analysis_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
            )
        GROUP BY session_id, page_url
        HAVING event_count >= 5  -- Only analyze sessions with sufficient data
        ORDER BY session_start DESC
        """
        
        try:
            result = self.client.query(query).result()
            sessions = []
            for row in result:
                sessions.append({
                    'session_id': row.session_id,
                    'page_url': row.page_url,
                    'session_start': row.session_start,
                    'session_end': row.session_end,
                    'event_count': row.event_count
                })
            
            print(f"📊 Found {len(sessions)} sessions to analyze")
            return sessions
            
        except Exception as e:
            print(f"❌ Error getting sessions to analyze: {e}")
            return []
    
    def get_session_events(self, session_id: str, page_url: str) -> List[Dict]:
        """Get all events for a specific session"""
        query = """
        SELECT *
        FROM `ux_insights.mouse_tracking`
        WHERE session_id = @session_id AND page_url = @page_url
        ORDER BY timestamp ASC
        """
        
        job_config = bigquery.QueryJobConfig()
        job_config.query_parameters = [
            bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
            bigquery.ScalarQueryParameter("page_url", "STRING", page_url)
        ]
        
        try:
            result = self.client.query(query, job_config=job_config).result()
            events = []
            for row in result:
                events.append(dict(row))
            return events
            
        except Exception as e:
            print(f"❌ Error getting session events: {e}")
            return []
    
    def analyze_session_patterns(self, session_data: Dict, events: List[Dict]) -> Dict:
        """Analyze behavioral patterns for a single session"""
        if not events:
            return None
        
        # Basic session metrics
        session_duration = (session_data['session_end'] - session_data['session_start']).total_seconds()
        total_events = len(events)
        unique_event_types = len(set(event['event_type'] for event in events))
        bounce_session = session_duration < 30  # Less than 30 seconds considered bounce
        
        # Mouse movement analysis
        mouse_movements = [e for e in events if e['event_type'] == 'mousemove']
        mouse_distance = self._calculate_mouse_distance(mouse_movements)
        avg_mouse_speed = mouse_distance / max(session_duration, 1)
        rapid_movements = self._count_rapid_movements(mouse_movements)
        
        # Click analysis
        clicks = [e for e in events if e['event_type'] == 'click']
        total_clicks = len(clicks)
        click_rate = (total_clicks / max(session_duration / 60, 0.1))  # clicks per minute
        unique_elements_clicked = len(set(f"{c.get('element_tag', '')}-{c.get('element_id', '')}" for c in clicks))
        click_precision = self._calculate_click_precision(clicks)
        
        # Scroll analysis
        scrolls = [e for e in events if e['event_type'] == 'scroll']
        scroll_distance = self._calculate_scroll_distance(scrolls)
        scroll_sessions = self._count_scroll_sessions(scrolls)
        max_scroll_depth = self._calculate_max_scroll_depth(scrolls, events)
        scroll_backs = self._count_scroll_backs(scrolls)
        
        # Engagement scoring
        engagement_score = self._calculate_engagement_score(
            session_duration, total_clicks, mouse_distance, scroll_distance, unique_event_types
        )
        frustration_indicators = self._detect_frustration_indicators(events)
        exploration_score = self._calculate_exploration_score(clicks, scrolls, mouse_movements)
        task_completion_likelihood = self._estimate_task_completion(events, session_duration)
        
        # Device context
        viewport_width = events[0].get('viewport_width', 0) if events else 0
        viewport_height = events[0].get('viewport_height', 0) if events else 0
        device_type = self._classify_device_type(viewport_width, viewport_height)
        
        # Idle time calculation
        idle_time = self._calculate_idle_time(events)
        
        return {
            'session_id': session_data['session_id'],
            'page_url': session_data['page_url'],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'session_duration_seconds': session_duration,
            'total_events': total_events,
            'unique_event_types': unique_event_types,
            'bounce_session': bounce_session,
            'mouse_movement_distance': mouse_distance,
            'average_mouse_speed': avg_mouse_speed,
            'idle_time_seconds': idle_time,
            'rapid_movements_count': rapid_movements,
            'total_clicks': total_clicks,
            'click_rate_per_minute': click_rate,
            'unique_elements_clicked': unique_elements_clicked,
            'click_precision_score': click_precision,
            'total_scroll_distance': scroll_distance,
            'scroll_sessions_count': scroll_sessions,
            'max_scroll_depth_percent': max_scroll_depth,
            'scroll_back_count': scroll_backs,
            'engagement_score': engagement_score,
            'frustration_indicators': frustration_indicators,
            'exploration_score': exploration_score,
            'task_completion_likelihood': task_completion_likelihood,
            'viewport_width': viewport_width,
            'viewport_height': viewport_height,
            'device_type': device_type,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_mouse_distance(self, movements: List[Dict]) -> float:
        """Calculate total mouse movement distance"""
        if len(movements) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(movements)):
            prev = movements[i-1]
            curr = movements[i]
            
            if prev.get('x_coordinate') and curr.get('x_coordinate'):
                dx = curr['x_coordinate'] - prev['x_coordinate']
                dy = curr['y_coordinate'] - prev['y_coordinate']
                distance = math.sqrt(dx*dx + dy*dy)
                total_distance += distance
        
        return total_distance
    
    def _count_rapid_movements(self, movements: List[Dict]) -> int:
        """Count rapid mouse movements (high velocity)"""
        if len(movements) < 2:
            return 0
        
        rapid_count = 0
        for i in range(1, len(movements)):
            prev = movements[i-1]
            curr = movements[i]
            
            if prev.get('x_coordinate') and curr.get('x_coordinate'):
                dx = curr['x_coordinate'] - prev['x_coordinate']
                dy = curr['y_coordinate'] - prev['y_coordinate']
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Time difference (assuming timestamps are consecutive)
                time_diff = (curr['timestamp'] - prev['timestamp']).total_seconds()
                if time_diff > 0:
                    velocity = distance / time_diff
                    if velocity > 1000:  # pixels per second threshold
                        rapid_count += 1
        
        return rapid_count
    
    def _calculate_click_precision(self, clicks: List[Dict]) -> float:
        """Calculate click precision score based on element targeting"""
        if not clicks:
            return 0.0
        
        targeted_clicks = sum(1 for click in clicks if click.get('element_id') or click.get('element_class'))
        return targeted_clicks / len(clicks)
    
    def _calculate_scroll_distance(self, scrolls: List[Dict]) -> int:
        """Calculate total scroll distance"""
        if not scrolls:
            return 0
        
        total_distance = 0
        for i in range(1, len(scrolls)):
            prev_y = scrolls[i-1].get('scroll_y', 0) or 0
            curr_y = scrolls[i].get('scroll_y', 0) or 0
            total_distance += abs(curr_y - prev_y)
        
        return total_distance
    
    def _count_scroll_sessions(self, scrolls: List[Dict]) -> int:
        """Count distinct scrolling sessions"""
        if not scrolls:
            return 0
        
        sessions = 1
        last_scroll_time = scrolls[0]['timestamp']
        
        for scroll in scrolls[1:]:
            time_diff = (scroll['timestamp'] - last_scroll_time).total_seconds()
            if time_diff > 5:  # 5 second gap indicates new session
                sessions += 1
            last_scroll_time = scroll['timestamp']
        
        return sessions
    
    def _calculate_max_scroll_depth(self, scrolls: List[Dict], all_events: List[Dict]) -> float:
        """Calculate maximum scroll depth as percentage"""
        if not scrolls:
            return 0.0
        
        max_scroll_y = max(scroll.get('scroll_y', 0) or 0 for scroll in scrolls)
        viewport_height = all_events[0].get('viewport_height', 600) if all_events else 600
        
        # Estimate page height (this is a rough approximation)
        estimated_page_height = max_scroll_y + viewport_height
        if estimated_page_height > 0:
            return min((max_scroll_y / estimated_page_height) * 100, 100)
        return 0.0
    
    def _count_scroll_backs(self, scrolls: List[Dict]) -> int:
        """Count how many times user scrolled back up"""
        if len(scrolls) < 2:
            return 0
        
        scroll_backs = 0
        for i in range(1, len(scrolls)):
            prev_y = scrolls[i-1].get('scroll_y', 0) or 0
            curr_y = scrolls[i].get('scroll_y', 0) or 0
            if curr_y < prev_y:  # Scrolled up
                scroll_backs += 1
        
        return scroll_backs
    
    def _calculate_engagement_score(self, duration: float, clicks: int, mouse_distance: float, 
                                  scroll_distance: int, event_types: int) -> float:
        """Calculate overall engagement score (0-100)"""
        # Normalize factors
        duration_score = min(duration / 300, 1) * 25  # Max 25 points for 5+ minutes
        click_score = min(clicks / 10, 1) * 20  # Max 20 points for 10+ clicks
        movement_score = min(mouse_distance / 10000, 1) * 20  # Max 20 points for 10k+ pixels
        scroll_score = min(scroll_distance / 5000, 1) * 20  # Max 20 points for 5k+ scroll
        variety_score = min(event_types / 5, 1) * 15  # Max 15 points for 5+ event types
        
        return duration_score + click_score + movement_score + scroll_score + variety_score
    
    def _detect_frustration_indicators(self, events: List[Dict]) -> int:
        """Detect signs of user frustration"""
        indicators = 0
        
        # Rapid clicking
        clicks = [e for e in events if e['event_type'] == 'click']
        if len(clicks) >= 2:
            rapid_clicks = 0
            for i in range(1, len(clicks)):
                time_diff = (clicks[i]['timestamp'] - clicks[i-1]['timestamp']).total_seconds()
                if time_diff < 0.5:  # Less than 500ms between clicks
                    rapid_clicks += 1
            if rapid_clicks >= 3:
                indicators += 1
        
        # Excessive scrolling
        scrolls = [e for e in events if e['event_type'] == 'scroll']
        if len(scrolls) > 50:  # Excessive scrolling
            indicators += 1
        
        # Long idle periods followed by activity
        if len(events) >= 10:
            time_gaps = []
            for i in range(1, len(events)):
                gap = (events[i]['timestamp'] - events[i-1]['timestamp']).total_seconds()
                time_gaps.append(gap)
            
            max_gap = max(time_gaps) if time_gaps else 0
            if max_gap > 30:  # More than 30 seconds idle
                indicators += 1
        
        return indicators
    
    def _calculate_exploration_score(self, clicks: List[Dict], scrolls: List[Dict], 
                                   movements: List[Dict]) -> float:
        """Calculate how exploratory user behavior was (0-100)"""
        score = 0
        
        # Diversity of clicked elements
        if clicks:
            unique_elements = len(set(f"{c.get('element_tag', '')}-{c.get('element_id', '')}" for c in clicks))
            score += min(unique_elements / 5, 1) * 40
        
        # Scroll exploration
        if scrolls:
            scroll_variance = self._calculate_scroll_variance(scrolls)
            score += min(scroll_variance / 1000, 1) * 30
        
        # Mouse movement coverage
        if movements:
            coverage = self._calculate_mouse_coverage(movements)
            score += coverage * 30
        
        return score
    
    def _estimate_task_completion(self, events: List[Dict], duration: float) -> float:
        """Estimate likelihood of task completion (0-100)"""
        score = 0
        
        # Longer sessions suggest completion attempts
        if duration > 60:
            score += 30
        
        # Form interactions suggest task engagement
        form_events = [e for e in events if e.get('element_tag') in ['input', 'textarea', 'select']]
        if form_events:
            score += 40
        
        # Button clicks suggest action completion
        button_clicks = [e for e in events if e.get('element_tag') == 'button' or 'submit' in str(e.get('element_class', '')).lower()]
        if button_clicks:
            score += 30
        
        return min(score, 100)
    
    def _classify_device_type(self, width: int, height: int) -> str:
        """Classify device type based on viewport"""
        if width <= 768:
            return 'mobile'
        elif width <= 1024:
            return 'tablet'
        else:
            return 'desktop'
    
    def _calculate_idle_time(self, events: List[Dict]) -> float:
        """Calculate total idle time in session"""
        if len(events) < 2:
            return 0.0
        
        idle_time = 0.0
        for i in range(1, len(events)):
            gap = (events[i]['timestamp'] - events[i-1]['timestamp']).total_seconds()
            if gap > 5:  # Consider gaps > 5 seconds as idle time
                idle_time += gap - 5  # Subtract 5 seconds as normal processing time
        
        return idle_time
    
    def _calculate_scroll_variance(self, scrolls: List[Dict]) -> float:
        """Calculate variance in scroll positions"""
        if len(scrolls) < 2:
            return 0.0
        
        positions = [s.get('scroll_y', 0) or 0 for s in scrolls]
        mean_pos = sum(positions) / len(positions)
        variance = sum((pos - mean_pos) ** 2 for pos in positions) / len(positions)
        return variance
    
    def _calculate_mouse_coverage(self, movements: List[Dict]) -> float:
        """Calculate what percentage of screen was covered by mouse"""
        if not movements:
            return 0.0
        
        # Simple grid-based coverage calculation
        grid_size = 50  # 50x50 pixel grid
        covered_cells = set()
        
        for movement in movements:
            x = movement.get('x_coordinate')
            y = movement.get('y_coordinate')
            if x is not None and y is not None:
                grid_x = x // grid_size
                grid_y = y // grid_size
                covered_cells.add((grid_x, grid_y))
        
        # Estimate total grid cells (rough approximation)
        if movements:
            max_x = max(m.get('x_coordinate', 0) for m in movements if m.get('x_coordinate'))
            max_y = max(m.get('y_coordinate', 0) for m in movements if m.get('y_coordinate'))
            total_cells = (max_x // grid_size + 1) * (max_y // grid_size + 1)
            if total_cells > 0:
                return len(covered_cells) / total_cells
        
        return 0.0
    
    def save_patterns_to_bigquery(self, patterns: List[Dict]):
        """Save analyzed patterns to BigQuery"""
        if not patterns:
            return
        
        try:
            # Insert patterns into BigQuery
            errors = self.client.insert_rows_json(self.target_table, patterns)
            
            if errors:
                print(f"❌ Errors inserting patterns: {errors}")
            else:
                print(f"✅ Successfully inserted {len(patterns)} behavioral patterns")
                
        except Exception as e:
            print(f"❌ Error saving patterns to BigQuery: {e}")
            raise
    
    def run_analysis(self, hours_back: int = 24):
        """Run pattern recognition analysis"""
        print(f"🚀 Starting pattern recognition analysis for last {hours_back} hours...")
        
        # Create table if needed
        self.create_behavioral_patterns_table()
        
        # Get sessions to analyze
        sessions = self.get_sessions_to_analyze(hours_back)
        
        if not sessions:
            print("✅ No new sessions to analyze")
            return
        
        patterns = []
        for session in sessions:
            print(f"📊 Analyzing session: {session['session_id']} ({session['event_count']} events)")
            
            # Get events for this session
            events = self.get_session_events(session['session_id'], session['page_url'])
            
            if events:
                # Analyze patterns
                pattern = self.analyze_session_patterns(session, events)
                if pattern:
                    patterns.append(pattern)
        
        if patterns:
            # Save to BigQuery
            self.save_patterns_to_bigquery(patterns)
            print(f"🎯 Pattern recognition complete! Analyzed {len(patterns)} sessions")
        else:
            print("📊 No patterns generated from available sessions")

if __name__ == "__main__":
    agent = PatternRecognitionAgent()
    agent.run_analysis()