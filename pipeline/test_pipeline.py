#!/usr/bin/env python3
"""
Pipeline Runner Test Suite - Google Noculars
End-to-end testing for the pipeline orchestration system
"""

import os
import sys
import json
import asyncio
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline_runner import PipelineRunner

class TestPipelineRunner(unittest.TestCase):
    """Test cases for the PipelineRunner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        test_config = {
            'python_executable': 'python3',
            'max_concurrent_agents': 1,
            'notification_webhooks': [],
            'enable_monitoring': True
        }
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        # Initialize pipeline runner with test config
        self.runner = PipelineRunner(config_path=self.temp_config.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_config.name)
    
    def test_initialization(self):
        """Test pipeline runner initialization"""
        self.assertIsInstance(self.runner, PipelineRunner)
        self.assertIn('pattern_recognition', self.runner.agents)
        self.assertIn('business_intelligence', self.runner.agents)
        self.assertIn('ab_testing', self.runner.agents)
        self.assertIn('insights_engine', self.runner.agents)
        
        # Test agent configuration
        pr_agent = self.runner.agents['pattern_recognition']
        self.assertEqual(pr_agent['schedule'], 'every_15_minutes')
        self.assertEqual(pr_agent['dependencies'], [])
        
        bi_agent = self.runner.agents['business_intelligence']
        self.assertEqual(bi_agent['dependencies'], ['pattern_recognition'])
    
    def test_config_loading(self):
        """Test configuration loading"""
        self.assertEqual(self.runner.config['python_executable'], 'python3')
        self.assertEqual(self.runner.config['max_concurrent_agents'], 1)
        self.assertTrue(self.runner.config['enable_monitoring'])
    
    def test_dependency_checking(self):
        """Test dependency checking logic"""
        # No dependencies should pass
        self.assertTrue(self.runner._check_dependencies('pattern_recognition'))
        
        # Dependencies not met should fail
        self.assertFalse(self.runner._check_dependencies('business_intelligence'))
        
        # Mock successful dependency run
        self.runner.pipeline_state['last_run']['pattern_recognition'] = datetime.now()
        self.assertTrue(self.runner._check_dependencies('business_intelligence'))
        
        # Old dependency should fail
        old_time = datetime.now() - timedelta(hours=3)
        self.runner.pipeline_state['last_run']['pattern_recognition'] = old_time
        self.assertFalse(self.runner._check_dependencies('business_intelligence'))
    
    def test_pipeline_status(self):
        """Test pipeline status reporting"""
        status = self.runner.get_pipeline_status()
        
        self.assertIn('agents', status)
        self.assertIn('currently_running', status)
        self.assertIn('last_run_times', status)
        self.assertIn('success_counts', status)
        self.assertIn('error_counts', status)
        
        self.assertEqual(len(status['agents']), 4)
        self.assertEqual(len(status['currently_running']), 0)
    
    def test_state_persistence(self):
        """Test state saving and loading"""
        # Set some state
        self.runner.pipeline_state['success_count']['pattern_recognition'] = 5
        self.runner.pipeline_state['error_count']['business_intelligence'] = 2
        self.runner.pipeline_state['last_run']['ab_testing'] = datetime.now()
        
        # Save state
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        self.runner.save_state(state_file)
        
        # Create new runner and load state
        new_runner = PipelineRunner()
        new_runner.load_state(state_file)
        
        # Verify state was loaded
        self.assertEqual(new_runner.pipeline_state['success_count']['pattern_recognition'], 5)
        self.assertEqual(new_runner.pipeline_state['error_count']['business_intelligence'], 2)
        self.assertIn('ab_testing', new_runner.pipeline_state['last_run'])
        
        # Clean up
        os.unlink(state_file)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for pipeline execution"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.runner = PipelineRunner()
    
    @patch('asyncio.create_subprocess_exec')
    async def test_agent_execution_success(self, mock_subprocess):
        """Test successful agent execution"""
        # Mock successful process
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'Agent completed successfully', b'')
        mock_subprocess.return_value = mock_process
        
        result = await self.runner.run_agent('pattern_recognition', force=True)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('execution_time', result)
        self.assertIn('output', result)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_agent_execution_failure(self, mock_subprocess):
        """Test agent execution failure handling"""
        # Mock failed process
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'', b'Error: Agent failed')
        mock_subprocess.return_value = mock_process
        
        result = await self.runner.run_agent('pattern_recognition', force=True)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error_message', result)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_agent_timeout(self, mock_subprocess):
        """Test agent timeout handling"""
        # Mock process that times out
        mock_process = Mock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_process.kill.return_value = None
        mock_process.wait.return_value = None
        mock_subprocess.return_value = mock_process
        
        # Reduce timeout for testing
        self.runner.agents['pattern_recognition']['timeout'] = 1
        
        result = await self.runner.run_agent('pattern_recognition', force=True)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('timed out', result['error_message'])
    
    @patch('asyncio.create_subprocess_exec')
    async def test_pipeline_execution_order(self, mock_subprocess):
        """Test that pipeline executes agents in correct dependency order"""
        execution_order = []
        
        def track_execution(*args, **kwargs):
            # Extract agent name from path
            agent_path = args[1]  # Second argument is the agent path
            if 'pattern-recognition' in agent_path:
                execution_order.append('pattern_recognition')
            elif 'business-intelligence' in agent_path:
                execution_order.append('business_intelligence')
            elif 'ab-testing' in agent_path:
                execution_order.append('ab_testing')
            elif 'insights-engine' in agent_path:
                execution_order.append('insights_engine')
            
            # Mock successful process
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b'Success', b'')
            return mock_process
        
        mock_subprocess.side_effect = track_execution
        
        result = await self.runner.run_pipeline(force=True)
        
        # Verify execution order
        expected_order = ['pattern_recognition', 'business_intelligence', 'ab_testing', 'insights_engine']
        self.assertEqual(execution_order, expected_order)
        self.assertEqual(result['status'], 'success')
    
    async def test_concurrent_agent_prevention(self):
        """Test that concurrent runs of same agent are prevented"""
        # Mark agent as currently running
        self.runner.pipeline_state['current_runs'].add('pattern_recognition')
        
        result = await self.runner.run_agent('pattern_recognition')
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'already_running')


class TestPipelineScheduling(unittest.TestCase):
    """Test scheduling and timing functionality"""
    
    def setUp(self):
        """Set up scheduling tests"""
        self.runner = PipelineRunner()
    
    def test_schedule_configuration(self):
        """Test schedule configuration is correct"""
        schedules = self.runner.config['schedules']
        
        self.assertEqual(schedules['every_15_minutes'], 900)  # 15 minutes in seconds
        self.assertEqual(schedules['hourly'], 3600)  # 1 hour in seconds
        self.assertEqual(schedules['daily'], 86400)  # 24 hours in seconds
    
    def test_agent_schedule_assignments(self):
        """Test that agents have correct schedule assignments"""
        self.assertEqual(self.runner.agents['pattern_recognition']['schedule'], 'every_15_minutes')
        self.assertEqual(self.runner.agents['business_intelligence']['schedule'], 'hourly')
        self.assertEqual(self.runner.agents['ab_testing']['schedule'], 'daily')
        self.assertEqual(self.runner.agents['insights_engine']['schedule'], 'hourly')


async def run_async_tests():
    """Run async test cases"""
    # Create test suite for async tests
    suite = unittest.TestSuite()
    
    # Add async test cases
    integration_tests = TestPipelineIntegration()
    suite.addTest(TestPipelineIntegration('test_agent_execution_success'))
    suite.addTest(TestPipelineIntegration('test_agent_execution_failure'))
    suite.addTest(TestPipelineIntegration('test_agent_timeout'))
    suite.addTest(TestPipelineIntegration('test_pipeline_execution_order'))
    suite.addTest(TestPipelineIntegration('test_concurrent_agent_prevention'))
    
    # Run each test individually to handle async properly
    for test in suite:
        test_method = getattr(test, test._testMethodName)
        if asyncio.iscoroutinefunction(test_method):
            try:
                await test_method()
                print(f"✅ {test._testMethodName} passed")
            except Exception as e:
                print(f"❌ {test._testMethodName} failed: {e}")
        else:
            try:
                test_method()
                print(f"✅ {test._testMethodName} passed")
            except Exception as e:
                print(f"❌ {test._testMethodName} failed: {e}")


def main():
    """Main test execution"""
    print("🧪 Running Pipeline Runner Test Suite...")
    
    # Run synchronous tests
    print("\n📋 Running synchronous tests...")
    sync_suite = unittest.TestSuite()
    sync_suite.addTest(unittest.makeSuite(TestPipelineRunner))
    sync_suite.addTest(unittest.makeSuite(TestPipelineScheduling))
    
    runner = unittest.TextTestRunner(verbosity=2)
    sync_result = runner.run(sync_suite)
    
    # Run asynchronous tests
    print("\n🔄 Running asynchronous tests...")
    asyncio.run(run_async_tests())
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Synchronous tests: {sync_result.testsRun} run, {len(sync_result.failures)} failed, {len(sync_result.errors)} errors")
    print("Asynchronous tests: Check individual test results above")
    
    return sync_result.wasSuccessful()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)