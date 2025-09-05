#!/bin/bash

# GramOthi WebRTC Streaming Setup Script
# This script sets up the complete streaming infrastructure

set -e

echo "🚀 Setting up GramOthi WebRTC Streaming Infrastructure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    print_status "Checking Node.js installation..."
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js version 16+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) is installed"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    print_success "Python $(python3 --version) is installed"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
}

# Setup signaling server
setup_signaling_server() {
    print_status "Setting up WebRTC signaling server..."
    
    cd signaling-server
    
    # Install Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create environment file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating environment configuration..."
        cp env.example .env
        print_warning "Please update .env file with your configuration"
    fi
    
    cd ..
    print_success "Signaling server setup complete"
}

# Setup TURN server
setup_turn_server() {
    print_status "Setting up TURN server..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. TURN server will not be available."
        print_warning "Please install Docker to enable TURN server functionality."
        return
    fi
    
    # Start TURN server
    print_status "Starting TURN server with Docker..."
    docker-compose -f docker-compose.turn.yml up -d
    
    print_success "TURN server started"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p uploads
    mkdir -p logs
    mkdir -p static
    print_success "Directories created"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        print_warning "PostgreSQL is not running. Please start PostgreSQL first."
        print_warning "You can start it with: brew services start postgresql"
        return
    fi
    
    # Run database migrations
    print_status "Running database migrations..."
    alembic upgrade head
    
    print_success "Database setup complete"
}

# Create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Create start script for signaling server
    cat > start_signaling.sh << 'EOF'
#!/bin/bash
cd signaling-server
npm start
EOF
    chmod +x start_signaling.sh
    
    # Create start script for FastAPI backend
    cat > start_backend.sh << 'EOF'
#!/bin/bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start_backend.sh
    
    # Create combined start script
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting GramOthi WebRTC Streaming System..."

# Start TURN server
echo "Starting TURN server..."
docker-compose -f docker-compose.turn.yml up -d

# Start signaling server
echo "Starting signaling server..."
cd signaling-server
npm start &
SIGNALING_PID=$!
cd ..

# Wait a moment for signaling server to start
sleep 3

# Start FastAPI backend
echo "Starting FastAPI backend..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "✅ All services started!"
echo "📡 Signaling server: http://localhost:3001"
echo "🔧 FastAPI backend: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔄 TURN server: localhost:3478"

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
wait $SIGNALING_PID $BACKEND_PID
EOF
    chmod +x start_all.sh
    
    print_success "Startup scripts created"
}

# Main setup function
main() {
    echo "🎯 GramOthi WebRTC Streaming Setup"
    echo "=================================="
    
    check_nodejs
    check_python
    install_python_deps
    setup_signaling_server
    setup_turn_server
    create_directories
    setup_database
    create_startup_scripts
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update signaling-server/.env with your configuration"
    echo "2. Run './start_all.sh' to start all services"
    echo "3. Access the API docs at http://localhost:8000/docs"
    echo ""
    echo "🔧 Available commands:"
    echo "  ./start_all.sh      - Start all services"
    echo "  ./start_backend.sh  - Start only FastAPI backend"
    echo "  ./start_signaling.sh - Start only signaling server"
    echo ""
    echo "📚 Documentation:"
    echo "  - WebRTC Crash Course: https://www.youtube.com/watch?v=DvlyzDZDEq4"
    echo "  - mediasoup SFU: https://mediasoup.org/documentation/"
    echo "  - TURN setup: https://github.com/coturn/coturn"
}

# Run main function
main "$@"
