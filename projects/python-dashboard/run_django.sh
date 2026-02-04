#!/bin/bash
# Django API Startup Script for DevWorkspaces
# This script handles port conflicts, migrations, and starts the Django server

set -e  # Exit on error

echo "🚀 Starting Django API Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to the Django project directory
cd "$(dirname "$0")"

# Kill any existing process on port 8000
echo "🔍 Checking for processes on port 8000..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Killing existing process...${NC}"
    kill $(lsof -ti:8000) 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}✅ Port 8000 is now free${NC}"
else
    echo -e "${GREEN}✅ Port 8000 is available${NC}"
fi

# Check if virtual environment exists and activate it
if [ -d "../venv" ]; then
    echo "🐍 Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "../../venv" ]; then
    echo "🐍 Activating virtual environment..."
    source ../../venv/bin/activate
fi

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating admin user..."
python manage.py shell -c "
from django.contrib.auth.models import User;
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Admin user created')
else:
    print('✅ Admin user already exists')
" 2>/dev/null || echo "ℹ️  Admin user creation skipped (can be created via /admin)"

# Start the Django server
echo "🌐 Starting Django server on http://0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000
