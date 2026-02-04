#!/bin/bash
set -e

echo "🚀 DevWorkspaces Dashboard Runner"
echo "=================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Redis
if ! command_exists redis-server; then
    echo -e "${YELLOW}Warning: Redis not found. For real-time features, install Redis:${NC}"
    echo "  - Ubuntu/Debian: sudo apt install redis-server"
    echo "  - Or run: docker run -d -p 6379:6379 redis:alpine"
fi

# Check for Docker
if command_exists docker; then
    echo -e "${GREEN}Docker detected. You can run with Docker:${NC}"
    echo ""
    echo "  # Build and start all services (including Redis):"
    echo "  docker-compose up -d --build"
    echo ""
    echo "  # View logs:"
    echo "  docker-compose logs -f realtime-api"
    echo ""
    echo "  # Access:"
    echo "  - Real-time Dashboard: http://localhost:8501"
    echo "  - WebSocket API: ws://localhost:8765/ws"
    echo "  - API Docs: http://localhost:8765/api/docs"
    echo ""
fi

# Run with Python directly
echo -e "${GREEN}Running Real-Time Dashboard with Python:${NC}"
echo ""
echo "  Starting WebSocket API server on port 8765..."
echo "  Starting Streamlit dashboard on port 8501..."
echo ""
echo "  To start background workers (in a separate terminal):"
echo "    cd services && python workers/start_workers.py"
echo ""
echo "  To start the real-time dashboard:"
echo "    cd projects/comprehensive-dashboard"
echo "    streamlit run realtime_dashboard.py"
echo ""
echo "  Or use the standard dashboard:"
echo "    streamlit run app.py"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Start the real-time dashboard
echo -e "${GREEN}Starting Real-Time Dashboard...${NC}"
echo "Press Ctrl+C to stop"
echo ""

cd projects/comprehensive-dashboard
exec streamlit run realtime_dashboard.py --server.port=8501 --server.address=0.0.0.0
