#!/bin/bash

# Colors for terminal output
GREEN=$(printf "\033[0;32m")
YELLOW=$(printf "\033[1;33m")
RED=$(printf "\033[0;31m")
BLUE=$(printf "\033[0;34m")
NC=$(printf "\033[0m")

# Store process IDs
FASTAPI_PID=""
CELERY_WORKER_PID=""
CELERY_BEAT_PID=""

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        printf "${YELLOW}Activating virtual environment...${NC}\n"
        source "venv/bin/activate"
    else
        printf "${RED}Error: Not running in a virtual environment and venv not found.${NC}\n"
        exit 1
    fi
fi

# Check if Redis is running
printf "${BLUE}Checking if Redis is running...${NC}\n"
if ! redis-cli ping > /dev/null 2>&1; then
    printf "${YELLOW}Starting Redis...${NC}\n"
    redis-server --daemonize yes
    sleep 1
    if ! redis-cli ping > /dev/null 2>&1; then
        printf "${RED}Failed to start Redis. Please start it manually.${NC}\n"
        exit 1
    fi
fi
printf "${GREEN}Redis is running.${NC}\n"

# Start the FastAPI application
printf "${BLUE}Starting FastAPI application...${NC}\n"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!
sleep 2

# Verify FastAPI is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    printf "${RED}Failed to start FastAPI application. Check logs/fastapi.log for details.${NC}\n"
    exit 1
fi
printf "${GREEN}FastAPI is running on http://localhost:8000${NC}\n"

# Start the Celery worker
printf "${BLUE}Starting Celery worker...${NC}\n"
celery -A app.worker worker --loglevel=info > logs/celery_worker.log 2>&1 &
CELERY_WORKER_PID=$!
sleep 2

# Start the Celery beat scheduler
printf "${BLUE}Starting Celery beat scheduler...${NC}\n"
celery -A app.worker beat --loglevel=info > logs/celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
sleep 2

printf "\n${GREEN}All services started successfully!${NC}\n"
printf "FastAPI: http://localhost:8000\n"
printf "API Documentation: http://localhost:8000/docs\n"
printf "Health Check: http://localhost:8000/health\n"
printf "\nProcess IDs:\n"
printf "FastAPI: ${FASTAPI_PID}\n"
printf "Celery Worker: ${CELERY_WORKER_PID}\n"
printf "Celery Beat: ${CELERY_BEAT_PID}\n"

# Cleanup function
cleanup() {
    printf "\n${YELLOW}Shutting down services...${NC}\n"
    
    if [ -n "$FASTAPI_PID" ]; then
        printf "Stopping FastAPI (PID: $FASTAPI_PID)...\n"
        kill $FASTAPI_PID 2>/dev/null
    fi
    
    if [ -n "$CELERY_WORKER_PID" ]; then
        printf "Stopping Celery worker (PID: $CELERY_WORKER_PID)...\n"
        kill $CELERY_WORKER_PID 2>/dev/null
    fi
    
    if [ -n "$CELERY_BEAT_PID" ]; then
        printf "Stopping Celery beat (PID: $CELERY_BEAT_PID)...\n"
        kill $CELERY_BEAT_PID 2>/dev/null
    fi
    
    printf "${GREEN}All services stopped${NC}\n"
    exit 0
}

# Set up trap
trap cleanup INT TERM

printf "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for signals
wait
