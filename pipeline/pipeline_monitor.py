#!/usr/bin/env python3
"""
Pipeline Monitor - Google Noculars
Real-time monitoring and health checks for the analysis pipeline
"""

import os
import sys
import json
import time
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add current directory to path to import pipeline_runner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline_runner import PipelineRunner

class PipelineMonitor:
    """Monitor pipeline health and performance"""
    
    def __init__(self, config_path: str = None):
        """Initialize pipeline monitor"""
        self.runner = PipelineRunner(config_path)
        self.runner.load_state()
        
        self.health_thresholds = {
            'max_error_rate': 0.1,  # 10% error rate threshold
            'max_stale_hours': 4,   # 4 hours without successful run
            'min_success_rate': 0.8  # 80% success rate threshold
        }
    
    def get_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Get health status for a specific agent"""
        success_count = self.runner.pipeline_state['success_count'].get(agent_name, 0)
        error_count = self.runner.pipeline_state['error_count'].get(agent_name, 0)
        last_run = self.runner.pipeline_state['last_run'].get(agent_name)
        
        total_runs = success_count + error_count
        error_rate = error_count / total_runs if total_runs > 0 else 0
        success_rate = success_count / total_runs if total_runs > 0 else 0
        
        # Check if agent is stale
        is_stale = False
        hours_since_run = None
        if last_run:
            hours_since_run = (datetime.now() - last_run).total_seconds() / 3600
            is_stale = hours_since_run > self.health_thresholds['max_stale_hours']
        else:
            is_stale = True
        
        # Determine overall health
        is_healthy = (
            error_rate <= self.health_thresholds['max_error_rate'] and
            success_rate >= self.health_thresholds['min_success_rate'] and
            not is_stale
        )
        
        return {
            'agent': agent_name,
            'healthy': is_healthy,
            'total_runs': total_runs,
            'success_count': success_count,
            'error_count': error_count,
            'success_rate': success_rate,
            'error_rate': error_rate,
            'last_run': last_run.isoformat() if last_run else None,
            'hours_since_run': hours_since_run,
            'is_stale': is_stale,
            'currently_running': agent_name in self.runner.pipeline_state['current_runs']
        }
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """Get overall pipeline health status"""
        agent_healths = {}
        healthy_agents = 0
        total_agents = len(self.runner.agents)
        
        for agent_name in self.runner.agents.keys():
            health = self.get_agent_health(agent_name)
            agent_healths[agent_name] = health
            if health['healthy']:
                healthy_agents += 1
        
        overall_health = healthy_agents / total_agents
        is_healthy = overall_health >= 0.75  # 75% of agents must be healthy
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': is_healthy,
            'overall_health_percentage': overall_health * 100,
            'healthy_agents': healthy_agents,
            'total_agents': total_agents,
            'agents': agent_healths,
            'currently_running': list(self.runner.pipeline_state['current_runs'])
        }
    
    def print_health_dashboard(self):
        """Print a formatted health dashboard to console"""
        health = self.get_pipeline_health()
        
        print("\n" + "="*60)
        print("🔍 GOOGLE NOCULARS PIPELINE HEALTH DASHBOARD")
        print("="*60)
        print(f"⏰ Last Updated: {health['timestamp']}")
        print(f"🎯 Overall Health: {health['overall_health_percentage']:.1f}%")
        print(f"✅ Healthy Agents: {health['healthy_agents']}/{health['total_agents']}")
        
        if health['currently_running']:
            print(f"🔄 Currently Running: {', '.join(health['currently_running'])}")
        
        print("\n📊 AGENT STATUS:")
        print("-" * 60)
        
        for agent_name, agent_health in health['agents'].items():
            status_icon = "✅" if agent_health['healthy'] else "❌"
            running_icon = "🔄" if agent_health['currently_running'] else ""
            
            print(f"{status_icon} {running_icon} {agent_name.upper().replace('_', ' ')}")
            print(f"   Runs: {agent_health['total_runs']} (Success: {agent_health['success_rate']:.1%})")
            
            if agent_health['last_run'] and agent_health['hours_since_run'] is not None:
                print(f"   Last Run: {agent_health['hours_since_run']:.1f}h ago")
            else:
                print(f"   Last Run: Never")
            
            if not agent_health['healthy']:
                issues = []
                if agent_health['is_stale']:
                    issues.append("STALE")
                if agent_health['error_rate'] > self.health_thresholds['max_error_rate']:
                    issues.append(f"HIGH ERROR RATE ({agent_health['error_rate']:.1%})")
                if agent_health['success_rate'] < self.health_thresholds['min_success_rate']:
                    issues.append(f"LOW SUCCESS RATE ({agent_health['success_rate']:.1%})")
                
                print(f"   Issues: {', '.join(issues)}")
            
            print()
        
        print("="*60)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the pipeline"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'agents': {}
        }
        
        for agent_name in self.runner.agents.keys():
            health = self.get_agent_health(agent_name)
            
            # Calculate average execution time (would need to track this in runner)
            # For now, using estimated values based on agent complexity
            estimated_avg_time = {
                'pattern_recognition': 45,
                'business_intelligence': 120,
                'ab_testing': 90,
                'insights_engine': 150
            }
            
            metrics['agents'][agent_name] = {
                'success_rate': health['success_rate'],
                'error_rate': health['error_rate'],
                'total_executions': health['total_runs'],
                'estimated_avg_execution_time': estimated_avg_time.get(agent_name, 60),
                'last_execution': health['last_run'],
                'is_healthy': health['healthy']
            }
        
        return metrics
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        print("🏥 Running pipeline health check...")
        
        # Get current health
        health = self.get_pipeline_health()
        
        # Check for critical issues
        critical_issues = []
        warnings = []
        
        for agent_name, agent_health in health['agents'].items():
            if not agent_health['healthy']:
                if agent_health['is_stale']:
                    if agent_health['hours_since_run'] is not None:
                        critical_issues.append(f"{agent_name} hasn't run successfully in {agent_health['hours_since_run']:.1f} hours")
                    else:
                        critical_issues.append(f"{agent_name} has never run successfully")
                
                if agent_health['error_rate'] > 0.5:  # 50% error rate is critical
                    critical_issues.append(f"{agent_name} has high error rate: {agent_health['error_rate']:.1%}")
            
            elif agent_health['error_rate'] > 0.2:  # 20% error rate is warning
                warnings.append(f"{agent_name} has elevated error rate: {agent_health['error_rate']:.1%}")
        
        # Test basic connectivity (mock for now)
        connectivity_ok = True  # Would test BigQuery connection here
        
        return {
            'overall_healthy': health['overall_healthy'],
            'critical_issues': critical_issues,
            'warnings': warnings,
            'connectivity_ok': connectivity_ok,
            'agents_status': health['agents'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def monitor_loop(self, interval_seconds: int = 60):
        """Run continuous monitoring loop"""
        print(f"🔄 Starting pipeline monitor (checking every {interval_seconds}s)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.print_health_dashboard()
                
                # Reload state to get latest data
                self.runner.load_state()
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Google Noculars Pipeline Monitor')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--check', action='store_true', help='Run single health check')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = PipelineMonitor(config_path=args.config)
    
    if args.check:
        # Single health check
        health_result = await monitor.run_health_check()
        
        if args.json:
            print(json.dumps(health_result, indent=2))
        else:
            monitor.print_health_dashboard()
            
            if health_result['critical_issues']:
                print("🚨 CRITICAL ISSUES:")
                for issue in health_result['critical_issues']:
                    print(f"   ❌ {issue}")
            
            if health_result['warnings']:
                print("⚠️  WARNINGS:")
                for warning in health_result['warnings']:
                    print(f"   ⚠️  {warning}")
    
    elif args.monitor:
        # Continuous monitoring
        await monitor.monitor_loop(args.interval)
    
    else:
        # Default: show current status
        if args.json:
            health = monitor.get_pipeline_health()
            print(json.dumps(health, indent=2))
        else:
            monitor.print_health_dashboard()


if __name__ == "__main__":
    asyncio.run(main())