#!/bin/bash

# OSINT NER Tool - Startup Script
# Starts both Python backend and Tauri frontend

echo "🚀 Starting OSINT NER Tool..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ -n "$PYTHON_PID" ]; then
        kill $PYTHON_PID 2>/dev/null
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Python backend
echo -e "${BLUE}Starting Python backend...${NC}"
cd /home/ares/Documents/HARISWB/media-pipeline/osint/osint-cli
uv run python src/api_server.py &
PYTHON_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠ Backend might not be ready yet, continuing anyway...${NC}"
    fi
done

echo ""

# Start Tauri frontend
echo -e "${BLUE}Starting Tauri frontend...${NC}"
cd /home/ares/Documents/HARISWB/media-pipeline/osint/osint-app
npm run tauri:dev

# When frontend exits, cleanup
cleanup
