#!/bin/bash

# GramOthi Compression Testing Setup Script
# This script sets up the environment for testing compression features

echo "🚀 Setting up GramOthi Compression Testing Environment"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the Backend directory"
    exit 1
fi

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "   $python_version"

if [[ $python_version == *"3.8"* ]] || [[ $python_version == *"3.9"* ]] || [[ $python_version == *"3.10"* ]] || [[ $python_version == *"3.11"* ]]; then
    echo "   ✅ Python version is compatible"
else
    echo "   ⚠️  Python 3.8+ recommended for best compatibility"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check FFmpeg installation
echo "🎵 Checking FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1)
    echo "   ✅ FFmpeg found: $ffmpeg_version"
else
    echo "   ❌ FFmpeg not found. Please install FFmpeg:"
    echo "      macOS: brew install ffmpeg"
    echo "      Ubuntu: sudo apt install ffmpeg"
    echo "      Windows: Download from https://ffmpeg.org/"
fi

# Check Ghostscript for PDF compression
echo "📄 Checking Ghostscript installation..."
if command -v gs &> /dev/null; then
    gs_version=$(gs --version 2>&1)
    echo "   ✅ Ghostscript found: $gs_version"
else
    echo "   ⚠️  Ghostscript not found. PDF compression will be limited."
    echo "      macOS: brew install ghostscript"
    echo "      Ubuntu: sudo apt install ghostscript"
fi

# Create test directories
echo "📁 Creating test directories..."
mkdir -p uploads/slides
mkdir -p uploads/recordings/audio
mkdir -p uploads/recordings/bundles
echo "   ✅ Upload directories created"

# Set up environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment file..."
    cp env.example .env
    echo "   ✅ Environment file created from template"
    echo "   📝 Please edit .env with your database credentials"
else
    echo "   ✅ Environment file already exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x start.sh
chmod +x test_compression.py
chmod +x verify_compression.py
echo "   ✅ Scripts made executable"

# Run verification test
echo "🧪 Running compression verification test..."
python3 verify_compression.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Start the server: ./start.sh"
echo "3. Test compression: python3 test_compression.py"
echo "4. Use Chrome DevTools to simulate slow networks"
echo ""
echo "For detailed testing instructions, see: NETWORK_TESTING_GUIDE.md"
