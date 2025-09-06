#!/bin/bash

echo "🚀 Starting Unified GramOthi Application..."
echo "============================================="

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn\|http.server\|unified_server" 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Wait a moment
sleep 2

# Check if Backend directory exists
if [ ! -d "Backend" ]; then
    echo "❌ Backend directory not found!"
    exit 1
fi

# Install backend dependencies if needed
if [ ! -f "Backend/.env" ]; then
    echo "📝 Creating Backend/.env file..."
    echo "DATABASE_URL=sqlite:///./gramothi.db" > Backend/.env
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    cd Backend
    pip3 install -r requirements.txt
    cd ..
fi

# Start the unified server
echo "🌐 Starting unified server on http://localhost:3000"
echo "   - Frontend: http://localhost:3000"
echo "   - API: http://localhost:3000/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================="

python3 simple_unified_server.py
