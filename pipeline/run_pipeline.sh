#!/bin/bash
# Pipeline Runner Script - Google Noculars
# Convenience script for running the analysis pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PYTHON_ENV="../project_venv/bin/python"
CONFIG_FILE="pipeline_config.json"
LOG_FILE="pipeline.log"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -f "$PYTHON_ENV" ]]; then
        log_error "Python virtual environment not found at $PYTHON_ENV"
        log_info "Please run: python -m venv project_venv && source project_venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# Check if required files exist
check_requirements() {
    local missing_files=()
    
    if [[ ! -f "pipeline_runner.py" ]]; then
        missing_files+=("pipeline_runner.py")
    fi
    
    if [[ ! -f "../service-account-key.json" ]]; then
        missing_files+=("../service-account-key.json")
    fi
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
}

# Show usage
show_usage() {
    cat << EOF
Google Noculars Pipeline Runner

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    run-all          Run complete pipeline (all 4 agents)
    run-agent        Run specific agent only
    status           Show pipeline status
    monitor          Start real-time monitoring
    health-check     Run health check
    test             Run pipeline tests
    help             Show this help message

Options:
    --agent NAME     Specify agent name (pattern_recognition, business_intelligence, ab_testing, insights_engine)
    --force          Force execution ignoring dependencies
    --config FILE    Use custom configuration file (default: $CONFIG_FILE)
    --json           Output in JSON format
    --interval SEC   Monitoring interval in seconds (default: 60)

Examples:
    $0 run-all                          # Run complete pipeline
    $0 run-agent --agent pattern_recognition  # Run specific agent
    $0 status --json                    # Show status in JSON
    $0 monitor --interval 30            # Monitor every 30 seconds
    $0 health-check                     # Check pipeline health

EOF
}

# Run complete pipeline
run_pipeline() {
    local force_flag=""
    [[ "$FORCE" == "true" ]] && force_flag="--force"
    
    log_info "Starting complete pipeline execution..."
    $PYTHON_ENV pipeline_runner.py $force_flag --config "$CONFIG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Pipeline completed successfully"
    else
        log_error "Pipeline execution failed"
        exit 1
    fi
}

# Run specific agent
run_agent() {
    if [[ -z "$AGENT_NAME" ]]; then
        log_error "Agent name required. Use --agent option"
        echo "Available agents: pattern_recognition, business_intelligence, ab_testing, insights_engine"
        exit 1
    fi
    
    local force_flag=""
    [[ "$FORCE" == "true" ]] && force_flag="--force"
    
    log_info "Running agent: $AGENT_NAME"
    $PYTHON_ENV pipeline_runner.py --agent "$AGENT_NAME" $force_flag --config "$CONFIG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Agent $AGENT_NAME completed successfully"
    else
        log_error "Agent $AGENT_NAME execution failed"
        exit 1
    fi
}

# Show status
show_status() {
    local json_flag=""
    [[ "$JSON_OUTPUT" == "true" ]] && json_flag="--json"
    
    log_info "Fetching pipeline status..."
    $PYTHON_ENV pipeline_runner.py --status $json_flag --config "$CONFIG_FILE"
}

# Start monitoring
start_monitoring() {
    local interval_flag=""
    [[ -n "$MONITOR_INTERVAL" ]] && interval_flag="--interval $MONITOR_INTERVAL"
    
    log_info "Starting pipeline monitoring..."
    $PYTHON_ENV pipeline_monitor.py --monitor $interval_flag --config "$CONFIG_FILE"
}

# Run health check
run_health_check() {
    local json_flag=""
    [[ "$JSON_OUTPUT" == "true" ]] && json_flag="--json"
    
    log_info "Running pipeline health check..."
    $PYTHON_ENV pipeline_monitor.py --check $json_flag --config "$CONFIG_FILE"
}

# Run tests
run_tests() {
    log_info "Running pipeline tests..."
    $PYTHON_ENV test_pipeline.py
    
    if [[ $? -eq 0 ]]; then
        log_success "All tests passed"
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Parse command line arguments
COMMAND=""
AGENT_NAME=""
FORCE="false"
JSON_OUTPUT="false"
MONITOR_INTERVAL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        run-all|run-agent|status|monitor|health-check|test|help)
            COMMAND="$1"
            shift
            ;;
        --agent)
            AGENT_NAME="$2"
            shift 2
            ;;
        --force)
            FORCE="true"
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT="true"
            shift
            ;;
        --interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Show usage if no command provided
if [[ -z "$COMMAND" ]]; then
    show_usage
    exit 0
fi

# Show help
if [[ "$COMMAND" == "help" ]]; then
    show_usage
    exit 0
fi

# Pre-flight checks
log_info "Running pre-flight checks..."
check_venv
check_requirements
log_success "Pre-flight checks passed"

# Execute command
case $COMMAND in
    run-all)
        run_pipeline
        ;;
    run-agent)
        run_agent
        ;;
    status)
        show_status
        ;;
    monitor)
        start_monitoring
        ;;
    health-check)
        run_health_check
        ;;
    test)
        run_tests
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac