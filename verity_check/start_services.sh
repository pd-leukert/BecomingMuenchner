#!/bin/bash

# Configuration
VLM_PORT=8000
API_PORT=8001
VLM_SCRIPT="./serve.sh"
CONDA_ENV="hackatum"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting VerityCheck Services...${NC}"

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    if [ ! -z "$API_PID" ]; then
        echo "Killing API server (PID $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$VLM_PID" ]; then
        echo "Killing VLM server (PID $VLM_PID)..."
        kill $VLM_PID 2>/dev/null
    fi
    echo -e "${GREEN}✅ Shutdown complete.${NC}"
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# 1. Start VLM Service
echo -e "${YELLOW}🤖 Starting VLM Service (serve.sh)...${NC}"
if [ -f "$VLM_SCRIPT" ]; then
    $VLM_SCRIPT > vlm.log 2>&1 &
    VLM_PID=$!
    echo "VLM Service started with PID $VLM_PID. Logs: vlm.log"
else
    echo -e "${RED}❌ Error: $VLM_SCRIPT not found!${NC}"
    exit 1
fi

# 2. Wait for VLM to be ready
echo -e "${YELLOW}⏳ Waiting for VLM Service to be ready on port $VLM_PORT...${NC}"
MAX_RETRIES=60
COUNT=0
VLM_READY=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://localhost:$VLM_PORT/v1/models" > /dev/null; then
        VLM_READY=true
        break
    fi
    echo -n "."
    sleep 2
    COUNT=$((COUNT+1))
done
echo ""

if [ "$VLM_READY" = true ]; then
    echo -e "${GREEN}✅ VLM Service is READY!${NC}"
else
    echo -e "${RED}⚠️ VLM Service timed out or failed to start. Check vlm.log.${NC}"
    # We continue anyway as the user might want to debug, or maybe the check failed but service is up
fi

# 3. Start API Service
echo -e "${YELLOW}🌐 Starting API Service (api.py)...${NC}"
# Use the uvicorn from the current environment or specific path
UVICORN_CMD="uvicorn"
if [ -f "/home/holmov/.local/share/mamba/envs/$CONDA_ENV/bin/uvicorn" ]; then
    UVICORN_CMD="/home/holmov/.local/share/mamba/envs/$CONDA_ENV/bin/uvicorn"
fi

$UVICORN_CMD api:app --host 0.0.0.0 --port $API_PORT > api.log 2>&1 &
API_PID=$!
echo "API Service started with PID $API_PID. Logs: api.log"

# 4. Wait for API to be ready
echo -e "${YELLOW}⏳ Waiting for API Service to be ready on port $API_PORT...${NC}"
sleep 2 # Give it a moment
if ps -p $API_PID > /dev/null; then
    echo -e "${GREEN}✅ API Service is RUNNING!${NC}"
    
    # Get Public IP
    PUBLIC_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
    
    echo -e "\n${GREEN}🎉 All services are running!${NC}"
    echo -e "   - VLM Service: http://localhost:$VLM_PORT (Internal)"
    echo -e "   - API Service: http://$PUBLIC_IP:$API_PORT (Public)"
    echo -e "\n${YELLOW}Press Ctrl+C to stop all services.${NC}"
    
    # Wait for processes
    wait $API_PID $VLM_PID
else
    echo -e "${RED}❌ API Service failed to start. Check api.log.${NC}"
    cleanup
fi
