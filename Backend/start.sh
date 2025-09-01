#!/bin/bash

# GramOthi Backend Startup Script

echo "🚀 Starting GramOthi Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy env.example to .env and configure it."
    echo "   cp env.example .env"
    exit 1
fi

# Check if database is accessible
echo "🔍 Checking database connection..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from app.config import engine
try:
    with engine.connect() as conn:
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the application
echo "🌐 Starting FastAPI server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m app.main
