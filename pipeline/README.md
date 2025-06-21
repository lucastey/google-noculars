# Pipeline Orchestration System

This directory contains the pipeline orchestration system for Google Noculars, which coordinates the execution of all 4 analysis agents.

## Files Overview

- **`pipeline_runner.py`** - Main orchestration engine that runs agents in dependency order
- **`pipeline_monitor.py`** - Real-time monitoring and health dashboard  
- **`pipeline_config.json`** - Configuration settings for the pipeline
- **`test_pipeline.py`** - Comprehensive test suite for the pipeline system
- **`run_pipeline.sh`** - Convenient shell script for common operations

## Quick Start

```bash
# Navigate to pipeline directory
cd pipeline

# Run complete pipeline
./run_pipeline.sh run-all

# Run specific agent
./run_pipeline.sh run-agent --agent pattern_recognition

# Monitor pipeline health
./run_pipeline.sh monitor

# Check pipeline status
./run_pipeline.sh status
```

## Usage Examples

### Running the Complete Pipeline
```bash
# Basic execution
python pipeline_runner.py

# Force execution (ignore dependencies)
python pipeline_runner.py --force

# Use custom config
python pipeline_runner.py --config custom_config.json
```

### Running Individual Agents
```bash
# Run pattern recognition agent
python pipeline_runner.py --agent pattern_recognition

# Run business intelligence agent
python pipeline_runner.py --agent business_intelligence --force
```

### Monitoring
```bash
# Real-time monitoring (updates every 60s)
python pipeline_monitor.py --monitor

# Single health check
python pipeline_monitor.py --check

# JSON output for integration
python pipeline_monitor.py --check --json
```

### Testing
```bash
# Run all tests
python test_pipeline.py

# Or use the shell script
./run_pipeline.sh test
```

## Agent Execution Order

The pipeline executes agents in the following dependency order:

1. **Pattern Recognition** → Analyzes mouse tracking data
2. **Business Intelligence** → Processes behavioral patterns  
3. **A/B Testing** → Analyzes business insights for tests
4. **Insights Engine** → Coordinates all results into final recommendations

## Configuration

The `pipeline_config.json` file contains:

- **Python executable path** - Virtual environment location
- **Agent timeouts** - Maximum execution time per agent
- **Retry policies** - Error handling and retry logic
- **Schedules** - How often each agent should run
- **Logging settings** - Log levels and file management

## Monitoring & Health Checks

The monitoring system tracks:

- ✅ **Success rates** per agent
- ❌ **Error rates** and failure patterns  
- ⏰ **Last run times** and staleness detection
- 🔄 **Currently running** agents
- 📊 **Overall pipeline health**

## Error Handling

The pipeline includes:

- **Automatic retries** with exponential backoff
- **Dependency checking** before agent execution
- **Timeout protection** to prevent hanging
- **State persistence** across restarts
- **Comprehensive logging** for debugging

## Integration

To integrate with external systems:

```python
from pipeline_runner import PipelineRunner

# Initialize pipeline
runner = PipelineRunner(config_path='pipeline_config.json')

# Run pipeline programmatically
result = await runner.run_pipeline()

# Check results
if result['status'] == 'success':
    print(f"Pipeline completed: {result['agents_executed']} agents")
```

## Troubleshooting

### Common Issues

1. **"Virtual environment not found"**
   - Ensure `../project_venv/bin/python` exists
   - Update path in `pipeline_config.json`

2. **"Agent failed with timeout"**
   - Increase timeout in agent configuration
   - Check BigQuery connectivity

3. **"Dependencies not met"**
   - Run with `--force` flag to skip dependency checks
   - Check agent execution history

### Log Files

- **`pipeline.log`** - Main pipeline execution log
- Individual agent logs in their respective directories

### Getting Help

```bash
# Show all available commands
./run_pipeline.sh help

# Check pipeline status
./run_pipeline.sh status --json
```