#!/usr/bin/env python3
"""
Pipeline Runner - Google Noculars
Orchestrates the 4-agent analysis pipeline with error handling and monitoring
"""

import os
import sys
import time
import json
import logging
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PipelineRunner:
    """Orchestrates the 4-agent analysis pipeline"""
    
    def __init__(self, config_path: str = None):
        """Initialize the pipeline runner"""
        self.config = self._load_config(config_path)
        self.agents = {
            'pattern_recognition': {
                'path': 'agents/pattern-recognition/agent.py',
                'method': 'run_analysis',
                'schedule': 'every_15_minutes',
                'timeout': 300,  # 5 minutes
                'retry_count': 3,
                'dependencies': []
            },
            'business_intelligence': {
                'path': 'agents/business-intelligence/agent.py', 
                'method': 'main',
                'schedule': 'hourly',
                'timeout': 600,  # 10 minutes
                'retry_count': 3,
                'dependencies': ['pattern_recognition']
            },
            'ab_testing': {
                'path': 'agents/ab-testing/agent.py',
                'method': 'main', 
                'schedule': 'daily',
                'timeout': 900,  # 15 minutes
                'retry_count': 2,
                'dependencies': ['business_intelligence']
            },
            'insights_engine': {
                'path': 'agents/insights-engine/agent.py',
                'method': 'main',
                'schedule': 'hourly',
                'timeout': 600,  # 10 minutes
                'retry_count': 3,
                'dependencies': ['pattern_recognition', 'business_intelligence', 'ab_testing']
            }
        }
        
        # Track pipeline state
        self.pipeline_state = {
            'last_run': {},
            'success_count': {},
            'error_count': {},
            'current_runs': set()
        }
        
        logger.info("🚀 Pipeline Runner initialized")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load pipeline configuration"""
        default_config = {
            'python_executable': 'project_venv/bin/python',
            'max_concurrent_agents': 2,
            'data_retention_days': 30,
            'notification_webhooks': [],
            'enable_monitoring': True,
            'schedules': {
                'every_15_minutes': 900,  # seconds
                'hourly': 3600,
                'daily': 86400
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
                logger.info(f"✅ Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Error loading config from {config_path}: {e}. Using defaults.")
        
        return default_config
    
    async def run_agent(self, agent_name: str, force: bool = False) -> Dict[str, Any]:
        """Run a single agent with error handling and monitoring"""
        agent_info = self.agents[agent_name]
        
        # Check if agent is already running
        if agent_name in self.pipeline_state['current_runs'] and not force:
            logger.warning(f"⚠️ Agent {agent_name} is already running, skipping")
            return {'status': 'skipped', 'reason': 'already_running'}
        
        # Check dependencies
        if not force and not self._check_dependencies(agent_name):
            logger.warning(f"⚠️ Dependencies not met for {agent_name}")
            return {'status': 'skipped', 'reason': 'dependencies_not_met'}
        
        # Mark as running
        self.pipeline_state['current_runs'].add(agent_name)
        start_time = time.time()
        
        try:
            logger.info(f"🔄 Starting {agent_name} agent...")
            
            # Execute agent
            result = await self._execute_agent(agent_name, agent_info)
            
            # Update success tracking
            execution_time = time.time() - start_time
            self.pipeline_state['last_run'][agent_name] = datetime.now()
            self.pipeline_state['success_count'][agent_name] = self.pipeline_state['success_count'].get(agent_name, 0) + 1
            
            logger.info(f"✅ {agent_name} completed successfully in {execution_time:.2f}s")
            
            return {
                'status': 'success',
                'execution_time': execution_time,
                'output': result
            }
            
        except Exception as e:
            # Update error tracking
            execution_time = time.time() - start_time
            self.pipeline_state['error_count'][agent_name] = self.pipeline_state['error_count'].get(agent_name, 0) + 1
            
            error_msg = f"❌ {agent_name} failed after {execution_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            
            # Send notification if configured
            await self._send_error_notification(agent_name, str(e))
            
            return {
                'status': 'error',
                'error_message': str(e),
                'execution_time': execution_time
            }
            
        finally:
            # Mark as no longer running
            self.pipeline_state['current_runs'].discard(agent_name)
    
    async def _execute_agent(self, agent_name: str, agent_info: Dict) -> str:
        """Execute a single agent with timeout and retry logic"""
        python_exec = self.config['python_executable']
        agent_path = agent_info['path']
        timeout = agent_info['timeout']
        max_retries = agent_info['retry_count']
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt}/{max_retries} for {agent_name}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                # Execute the agent
                process = await asyncio.create_subprocess_exec(
                    python_exec, agent_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go to project root
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=timeout
                    )
                    
                    if process.returncode == 0:
                        output = stdout.decode('utf-8')
                        if stderr:
                            logger.warning(f"⚠️ {agent_name} stderr: {stderr.decode('utf-8')}")
                        return output
                    else:
                        error_output = stderr.decode('utf-8')
                        raise Exception(f"Agent exited with code {process.returncode}: {error_output}")
                        
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    raise Exception(f"Agent timed out after {timeout} seconds")
                    
            except Exception as e:
                if attempt == max_retries:
                    raise e
                logger.warning(f"⚠️ Attempt {attempt + 1} failed for {agent_name}: {str(e)}")
    
    def _check_dependencies(self, agent_name: str) -> bool:
        """Check if agent dependencies have been satisfied"""
        agent_info = self.agents[agent_name]
        dependencies = agent_info.get('dependencies', [])
        
        for dep in dependencies:
            # Check if dependency ran recently
            last_run = self.pipeline_state['last_run'].get(dep)
            if not last_run:
                logger.debug(f"Dependency {dep} has never run")
                return False
            
            # Check if dependency ran within acceptable time window
            time_since_run = datetime.now() - last_run
            max_age = timedelta(hours=2)  # Dependencies must be fresh within 2 hours
            
            if time_since_run > max_age:
                logger.debug(f"Dependency {dep} is too old ({time_since_run} ago)")
                return False
        
        return True
    
    async def run_pipeline(self, force: bool = False) -> Dict[str, Any]:
        """Run the complete pipeline in dependency order"""
        logger.info("🚀 Starting complete pipeline execution")
        start_time = time.time()
        
        # Execution order based on dependencies
        execution_order = [
            'pattern_recognition',
            'business_intelligence', 
            'ab_testing',
            'insights_engine'
        ]
        
        results = {}
        failed_agents = []
        
        for agent_name in execution_order:
            result = await self.run_agent(agent_name, force=force)
            results[agent_name] = result
            
            if result['status'] == 'error':
                failed_agents.append(agent_name)
                logger.error(f"❌ Pipeline stopped due to {agent_name} failure")
                break
            elif result['status'] == 'skipped':
                logger.info(f"⏭️ {agent_name} skipped: {result['reason']}")
        
        total_time = time.time() - start_time
        
        pipeline_result = {
            'status': 'success' if not failed_agents else 'partial_failure',
            'total_execution_time': total_time,
            'agents_executed': len([r for r in results.values() if r['status'] == 'success']),
            'agents_failed': len(failed_agents),
            'failed_agents': failed_agents,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🏁 Pipeline completed in {total_time:.2f}s - Status: {pipeline_result['status']}")
        
        return pipeline_result
    
    async def run_single_agent(self, agent_name: str, force: bool = False) -> Dict[str, Any]:
        """Run a single agent by name"""
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}")
        
        return await self.run_agent(agent_name, force=force)
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics"""
        return {
            'agents': list(self.agents.keys()),
            'currently_running': list(self.pipeline_state['current_runs']),
            'last_run_times': {
                name: time.isoformat() if time else None 
                for name, time in self.pipeline_state['last_run'].items()
            },
            'success_counts': self.pipeline_state['success_count'],
            'error_counts': self.pipeline_state['error_count'],
            'config': self.config
        }
    
    async def _send_error_notification(self, agent_name: str, error_message: str):
        """Send error notifications to configured webhooks"""
        webhooks = self.config.get('notification_webhooks', [])
        
        if not webhooks:
            return
        
        notification_data = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'error': error_message,
            'service': 'google-noculars-pipeline'
        }
        
        # Implementation would depend on your notification service
        # For now, just log the notification
        logger.info(f"📧 Notification sent for {agent_name} failure")
    
    def save_state(self, filepath: str = 'pipeline_state.json'):
        """Save pipeline state to file"""
        try:
            state_data = {
                'last_run': {
                    name: time.isoformat() if time else None 
                    for name, time in self.pipeline_state['last_run'].items()
                },
                'success_count': self.pipeline_state['success_count'],
                'error_count': self.pipeline_state['error_count']
            }
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(f"💾 Pipeline state saved to {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error saving pipeline state: {e}")
    
    def load_state(self, filepath: str = 'pipeline_state.json'):
        """Load pipeline state from file"""
        try:
            if not os.path.exists(filepath):
                logger.info(f"📁 No state file found at {filepath}, starting fresh")
                return
            
            with open(filepath, 'r') as f:
                state_data = json.load(f)
            
            # Restore last run times
            for name, time_str in state_data.get('last_run', {}).items():
                if time_str:
                    self.pipeline_state['last_run'][name] = datetime.fromisoformat(time_str)
            
            # Restore counters
            self.pipeline_state['success_count'] = state_data.get('success_count', {})
            self.pipeline_state['error_count'] = state_data.get('error_count', {})
            
            logger.info(f"📂 Pipeline state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error loading pipeline state: {e}")


async def main():
    """Main execution function for testing pipeline runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Noculars Pipeline Runner')
    parser.add_argument('--agent', help='Run specific agent only')
    parser.add_argument('--force', action='store_true', help='Force execution ignoring dependencies')
    parser.add_argument('--status', action='store_true', help='Show pipeline status')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Initialize pipeline runner
    runner = PipelineRunner(config_path=args.config)
    runner.load_state()
    
    try:
        if args.status:
            # Show pipeline status
            status = runner.get_pipeline_status()
            print(json.dumps(status, indent=2))
            
        elif args.agent:
            # Run specific agent
            result = await runner.run_single_agent(args.agent, force=args.force)
            print(json.dumps(result, indent=2))
            
        else:
            # Run complete pipeline
            result = await runner.run_pipeline(force=args.force)
            print(json.dumps(result, indent=2))
            
    finally:
        # Save state before exit
        runner.save_state()


if __name__ == "__main__":
    asyncio.run(main())