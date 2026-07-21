#!/bin/bash
# macOS/Linux startup script for the Distributed Task Queue System
# This script starts the API server and workers

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in the correct directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}Warning: Virtual environment not found. Make sure dependencies are installed.${NC}"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Print header
echo ""
echo "============================================================"
echo "Distributed Task Queue System - Startup"
echo "============================================================"
echo ""
echo -e "${YELLOW}This will start all components. Please ensure:${NC}"
echo "1. Redis is running (redis-server)"
echo "2. Python 3.11+ is installed"
echo "3. Dependencies are installed (pip install -r requirements.txt)"
echo ""
echo "Press Enter to continue, or Ctrl+C to cancel..."
read -r

# Check for Redis
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}Warning: Redis CLI not found. Make sure Redis server is running.${NC}"
elif ! redis-cli ping &> /dev/null; then
    echo -e "${RED}Error: Redis server is not running. Please start it first:${NC}"
    echo "  redis-server"
    exit 1
else
    echo -e "${GREEN}✓ Redis is running${NC}"
fi

# Create a log directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    # Kill all background jobs
    jobs -p | xargs -r kill
    echo -e "${GREEN}Services stopped${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Start API server
echo -e "${GREEN}Starting FastAPI server...${NC}"
python main.py > logs/api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"

# Wait for API to start
sleep 2

# Start worker
echo -e "${GREEN}Starting worker process...${NC}"
python worker_main.py > logs/worker.log 2>&1 &
WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

echo ""
echo "============================================================"
echo -e "${GREEN}Services started successfully!${NC}"
echo "============================================================"
echo ""
echo "API Server:"
echo -e "  URL:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "Logs:"
echo "  API:    logs/api.log"
echo "  Worker: logs/worker.log"
echo ""
echo "View logs in real-time:"
echo "  tail -f logs/api.log"
echo "  tail -f logs/worker.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all background processes
wait
