#!/bin/bash

# Comprehensive DevWorkspaces Dashboard Launcher
# This script sets up and runs the comprehensive monitoring dashboard

echo "🚀 Starting DevWorkspaces Comprehensive Dashboard"
echo "================================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the dashboard directory."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if streamlit is available
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: Streamlit not found. Please check your installation."
    exit 1
fi

# Start the dashboard
echo "🌟 Launching dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo "🔄 Auto-refresh enabled (30s intervals)"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Deactivate virtual environment on exit
deactivate
